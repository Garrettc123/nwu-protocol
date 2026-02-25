"""API endpoints for payments and subscriptions."""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging

from ..database import get_db
from ..models import User, Subscription, Payment, APIKey, SubscriptionTier
from ..schemas import UserResponse
from ..services.payment_service import payment_service
from ..utils.db_helpers import get_user_by_address_or_404
from ..utils.validators import validate_subscription_tier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


# TODO: Replace with proper JWT-based authentication
# WARNING: Current implementation is NOT secure for production
# This is a placeholder that accepts address without verification
# MUST implement proper authentication before deployment
async def get_current_user(
    address: str,
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from address.

    ⚠️ SECURITY WARNING: This is a placeholder implementation.
    In production, this MUST verify:
    - JWT token validity
    - Wallet signature
    - Session authentication

    DO NOT use this in production without implementing proper auth!
    """
    return get_user_by_address_or_404(db, address)


@router.post("/subscriptions/create")
async def create_subscription(
    address: str,
    tier: str,
    stripe_price_id: str,
    db: Session = Depends(get_db)
):
    """
    Create a new subscription for a user.
    
    - **address**: User's Ethereum address
    - **tier**: Subscription tier (free, pro, enterprise)
    - **stripe_price_id**: Stripe price ID for the subscription
    """
    user = await get_current_user(address, db)

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


@router.get("/subscriptions/{address}")
async def get_subscription(
    address: str,
    db: Session = Depends(get_db)
):
    """Get user's current subscription."""
    user = await get_current_user(address, db)
    
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
    address: str,
    amount: float,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a payment intent for one-time payments.
    
    - **address**: User's Ethereum address
    - **amount**: Amount in USD
    - **description**: Optional payment description
    """
    user = await get_current_user(address, db)
    
    intent = await payment_service.create_payment_intent(
        db, user, amount, "usd", description
    )
    
    if not intent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment intent"
        )
    
    return intent


@router.get("/payments/{address}")
async def get_payments(
    address: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get payment history for a user."""
    user = await get_current_user(address, db)
    
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
    address: str,
    name: str,
    tier: str = "free",
    db: Session = Depends(get_db)
):
    """
    Create an API key for a user.
    
    - **address**: User's Ethereum address
    - **name**: Name/description for the API key
    - **tier**: Tier level (free, pro, enterprise)
    """
    user = await get_current_user(address, db)

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


@router.get("/api-keys/{address}")
async def list_api_keys(
    address: str,
    db: Session = Depends(get_db)
):
    """List all API keys for a user."""
    user = await get_current_user(address, db)
    
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
    address: str,
    db: Session = Depends(get_db)
):
    """Revoke an API key."""
    user = await get_current_user(address, db)
    
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
    """
    Get pricing information for subscription tiers.
    """
    return {
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
                "rate_limit": 100
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
                "rate_limit": 10000
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
                "rate_limit": 100000
            }
        ]
    }
