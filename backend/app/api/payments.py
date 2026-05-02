"""API endpoints for payments and subscriptions."""

import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging

from ..database import get_db
from ..models import User, Subscription, Payment, APIKey, SubscriptionTier
from ..schemas import UserResponse
from ..services.payment_service import payment_service
from ..services.auth_service import auth_service
from ..utils.db_helpers import get_user_by_address_or_404
from ..utils.validators import validate_subscription_tier, normalize_ethereum_address

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/payments", tags=["payments"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Verifies JWT token and returns the authenticated user.

    Args:
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Verify JWT token
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user address from token
    address = payload.get("sub")
    if not address:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Normalize and get user
    address = normalize_ethereum_address(address)
    return get_user_by_address_or_404(db, address)


@router.post("/subscriptions/create")
async def create_subscription(
    tier: str,
    stripe_price_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Create a new subscription for the authenticated user.

    - **tier**: Subscription tier (free, pro, enterprise)
    - **stripe_price_id**: Stripe price ID for the subscription
    """

    # Validate tier
    tier_enum = validate_subscription_tier(tier)
    
    # Create subscription
    subscription = await payment_service.create_subscription(
        db, user, tier_enum, stripe_price_id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )
    
    return {
        "subscription_id": subscription.id,
        "tier": subscription.tier.value,
        "status": subscription.status,
        "api_key": subscription.api_key,
        "rate_limit": subscription.rate_limit,
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
    }


@router.get("/subscriptions/current")
async def get_subscription(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get authenticated user's current subscription."""
    
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        return {
            "subscription_id": None,
            "tier": "free",
            "status": "none",
            "rate_limit": 100
        }
    
    return {
        "subscription_id": subscription.id,
        "tier": subscription.tier.value,
        "status": subscription.status,
        "rate_limit": subscription.rate_limit,
        "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        "cancel_at_period_end": subscription.cancel_at_period_end
    }


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: int,
    immediately: bool = False,
    db: Session = Depends(get_db)
):
    """
    Cancel a subscription.
    
    - **subscription_id**: ID of the subscription to cancel
    - **immediately**: If true, cancel immediately; otherwise at period end
    """
    success = await payment_service.cancel_subscription(db, subscription_id, immediately)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )
    
    return {
        "message": "Subscription canceled successfully",
        "immediately": immediately
    }


@router.post("/payment-intent/create")
async def create_payment_intent(
    amount: float,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Create a payment intent for one-time payments.

    - **amount**: Amount in USD
    - **description**: Optional payment description
    """
    
    intent = await payment_service.create_payment_intent(
        db, user, amount, "usd", description
    )
    
    if not intent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment intent"
        )
    
    return intent


@router.get("/payments/history")
async def get_payments(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get payment history for authenticated user."""
    
    payments = db.query(Payment).filter(
        Payment.user_id == user.id
    ).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "payments": [
            {
                "id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status.value,
                "description": payment.description,
                "created_at": payment.created_at.isoformat()
            }
            for payment in payments
        ],
        "total": db.query(func.count(Payment.id)).filter(Payment.user_id == user.id).scalar()
    }


@router.post("/api-keys/create")
async def create_api_key(
    name: str,
    tier: str = "free",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Create an API key for authenticated user.

    - **name**: Name/description for the API key
    - **tier**: Tier level (free, pro, enterprise)
    """

    # Validate tier
    tier_enum = validate_subscription_tier(tier)
    
    # Check if user has active subscription for non-free tiers
    if tier_enum != SubscriptionTier.FREE:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.tier == tier_enum
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Active {tier} subscription required"
            )
    
    api_key = await payment_service.create_api_key(db, user, name, tier_enum)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )
    
    return api_key


@router.get("/api-keys/list")
async def list_api_keys(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all API keys for authenticated user."""
    
    keys = db.query(APIKey).filter(
        APIKey.user_id == user.id
    ).order_by(APIKey.created_at.desc()).all()
    
    return {
        "keys": [
            {
                "id": api_key.id,
                "name": api_key.name,
                "prefix": api_key.prefix,
                "tier": api_key.tier.value,
                "is_active": api_key.is_active,
                "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "created_at": api_key.created_at.isoformat()
            }
            for api_key in keys
        ]
    }


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Revoke an API key for authenticated user."""
    
    key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == user.id
    ).first()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    key.is_active = False
    db.commit()
    
    return {"message": "API key revoked successfully"}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    This endpoint receives webhook events from Stripe for payment
    and subscription updates.
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    payload = await request.body()
    
    success = await payment_service.handle_webhook(db, payload, stripe_signature)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook handling failed"
        )
    
    return {"status": "success"}


@router.get("/pricing")
async def get_pricing():
    """Get pricing information for subscription tiers."""
    from ..config import settings
    return {
        "publishable_key": settings.stripe_publishable_key,
        "tiers": [
            {
                "name": "free",
                "display_name": "Free",
                "price": 0,
                "currency": "usd",
                "billing_period": "monthly",
                "features": [
                    "100 API requests per day",
                    "Basic verification",
                    "Community support"
                ],
                "rate_limit": 100,
                "stripe_price_id": None
            },
            {
                "name": "pro",
                "display_name": "Pro",
                "price": 99,
                "currency": "usd",
                "billing_period": "monthly",
                "features": [
                    "10,000 API requests per day",
                    "Advanced verification",
                    "Priority support",
                    "Custom AI agents",
                    "Analytics dashboard"
                ],
                "rate_limit": 10000,
                "stripe_price_id": settings.stripe_price_id_pro
            },
            {
                "name": "enterprise",
                "display_name": "Enterprise",
                "price": 999,
                "currency": "usd",
                "billing_period": "monthly",
                "features": [
                    "100,000 API requests per day",
                    "Premium verification",
                    "24/7 dedicated support",
                    "Custom integrations",
                    "SLA guarantee",
                    "Advanced analytics",
                    "White-label options"
                ],
                "rate_limit": 100000,
                "stripe_price_id": settings.stripe_price_id_enterprise
            }
        ]
    }


@router.post("/checkout-session")
async def create_checkout_session(
    tier: str,
    success_url: str,
    cancel_url: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Create a Stripe Checkout Session for subscription signup.

    - **tier**: 'pro' or 'enterprise'
    - **success_url**: URL to redirect after successful payment
    - **cancel_url**: URL to redirect after cancellation
    """
    if not payment_service.stripe_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment processing is not configured"
        )

    tier_enum = validate_subscription_tier(tier)
    if tier_enum.value == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Free tier does not require checkout"
        )

    from ..config import settings
    price_id_map = {
        "pro": settings.stripe_price_id_pro,
        "enterprise": settings.stripe_price_id_enterprise,
    }
    price_id = price_id_map.get(tier_enum.value)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Stripe price not configured for {tier} tier"
        )

    # Get or create Stripe customer
    stripe_customer_id = None
    existing_sub = db.query(Subscription).filter(
        Subscription.user_id == user.id
    ).order_by(Subscription.created_at.desc()).first()
    if existing_sub and existing_sub.stripe_customer_id:
        stripe_customer_id = existing_sub.stripe_customer_id
    else:
        stripe_customer_id = await payment_service.create_customer(user)

    if not stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer record"
        )

    try:
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": user.id, "tier": tier_enum.value},
            subscription_data={"metadata": {"user_id": user.id, "tier": tier_enum.value}},
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/customer-portal")
async def create_customer_portal(
    return_url: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Create a Stripe Customer Portal session for subscription management.

    - **return_url**: URL to return to after leaving the portal
    """
    if not payment_service.stripe_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment processing is not configured"
        )

    # Find the user's Stripe customer ID from their most recent subscription
    sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.stripe_customer_id.isnot(None)
    ).order_by(Subscription.created_at.desc()).first()

    if not sub or not sub.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No billing account found"
        )

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=return_url,
        )
        return {"portal_url": portal_session.url}
    except Exception as e:
        logger.error(f"Failed to create customer portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )
