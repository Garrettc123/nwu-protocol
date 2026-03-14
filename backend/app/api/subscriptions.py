"""Subscription billing router.

FastAPI router providing full subscription lifecycle management integrated with Stripe.
Plans:
  - Basic  $29/mo  — 1 000 req/day, staking multiplier ×1.5
  - Pro    $99/mo  — 10 000 req/day, staking multiplier ×2.0
  - Enterprise $499/mo — 100 000 req/day, staking multiplier ×5.0
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Subscription, SubscriptionTier, User
from ..services.auth_service import auth_service
from ..services.payment_service import payment_service
from ..subscription_plans import (
    PLAN_FEATURES,
    PLAN_PRICES,
    PLAN_RATE_LIMITS,
    PLAN_STAKING_MULTIPLIERS,
    TIER_ORDER,
    subscription_status_payload,
)
from ..utils.db_helpers import get_user_by_address_or_404
from ..utils.validators import normalize_ethereum_address

logger = logging.getLogger(__name__)

router = APIRouter(tags=["subscriptions"])
security = HTTPBearer()


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT Bearer token and return the authenticated user."""
    payload = auth_service.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    address = payload.get("sub")
    if not address:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return get_user_by_address_or_404(db, normalize_ethereum_address(address))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


# Alias for backward compatibility and router re-exports
_subscription_status_payload = subscription_status_payload


def _active_subscription(db: Session, user: User) -> Optional[Subscription]:
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.status == "active")
        .first()
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/subscriptions/create")
async def create_subscription(
    tier: str,
    stripe_price_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a Stripe subscription for the authenticated user.

    - **tier**: `basic`, `pro`, or `enterprise`
    - **stripe_price_id**: Stripe Price ID for the selected plan
    """
    try:
        tier_enum = SubscriptionTier[tier.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier '{tier}'. Must be one of: basic, pro, enterprise",
        )

    if tier_enum == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a paid subscription for the free tier",
        )

    # Delegate to payment_service (creates Stripe subscription + DB row)
    subscription = await payment_service.create_subscription(
        db, user, tier_enum, stripe_price_id
    )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription",
        )

    # Apply plan-specific attributes
    subscription.staking_multiplier = PLAN_STAKING_MULTIPLIERS[tier_enum]
    subscription.rate_limit = PLAN_RATE_LIMITS[tier_enum]
    db.commit()
    db.refresh(subscription)

    return {
        "subscription_id": subscription.id,
        "plan": subscription.tier.value,
        "status": subscription.status,
        "api_key": subscription.api_key,
        "api_quota": subscription.rate_limit,
        "staking_multiplier": subscription.staking_multiplier,
        "features": PLAN_FEATURES[tier_enum],
        "monthly_price_usd": PLAN_PRICES[tier_enum],
        "renewal_date": (
            subscription.current_period_end.isoformat()
            if subscription.current_period_end
            else None
        ),
    }


@router.post("/subscriptions/cancel")
async def cancel_subscription(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cancel the authenticated user's active subscription at the end of the billing period."""
    subscription = _active_subscription(db, user)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )

    success = await payment_service.cancel_subscription(
        db, subscription.id, immediately=False
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription",
        )

    return {
        "message": "Subscription will be canceled at the end of the current billing period",
        "renewal_date": (
            subscription.current_period_end.isoformat()
            if subscription.current_period_end
            else None
        ),
    }


@router.get("/subscriptions/status")
async def subscription_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return the authenticated user's current plan, renewal date, and unlocked features."""
    subscription = _active_subscription(db, user)
    return _subscription_status_payload(subscription)


@router.post("/subscriptions/upgrade")
async def upgrade_subscription(
    new_tier: str,
    stripe_price_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Prorate and immediately upgrade the authenticated user's subscription plan.

    - **new_tier**: Target tier (`basic`, `pro`, or `enterprise`)
    - **stripe_price_id**: Stripe Price ID for the new plan
    """
    try:
        new_tier_enum = SubscriptionTier[new_tier.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier '{new_tier}'. Must be one of: basic, pro, enterprise",
        )

    subscription = _active_subscription(db, user)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found to upgrade",
        )

    current_order = TIER_ORDER.index(subscription.tier) if subscription.tier in TIER_ORDER else 0
    new_order = TIER_ORDER.index(new_tier_enum) if new_tier_enum in TIER_ORDER else 0
    if new_order <= current_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"New tier '{new_tier}' is not higher than current tier "
                f"'{subscription.tier.value}'. Use the cancel endpoint to downgrade."
            ),
        )

    upgraded = await payment_service.upgrade_subscription(
        db, subscription, new_tier_enum, stripe_price_id
    )
    if not upgraded:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade subscription",
        )

    return {
        "subscription_id": upgraded.id,
        "plan": upgraded.tier.value,
        "status": upgraded.status,
        "api_quota": upgraded.rate_limit,
        "staking_multiplier": upgraded.staking_multiplier,
        "features": PLAN_FEATURES.get(upgraded.tier, {}),
        "monthly_price_usd": PLAN_PRICES.get(upgraded.tier, 0),
        "renewal_date": (
            upgraded.current_period_end.isoformat()
            if upgraded.current_period_end
            else None
        ),
    }


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook events.

    Supported events:
    - ``invoice.paid``
    - ``customer.subscription.deleted``
    - ``payment_intent.payment_failed``
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header",
        )

    payload = await request.body()

    success = await payment_service.handle_webhook(db, payload, stripe_signature)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook processing failed",
        )

    return {"status": "ok"}
