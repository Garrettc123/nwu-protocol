"""
Dedicated FastAPI router for enterprise API key management and usage metering.

Endpoints
---------
POST   /api/v1/api-keys/create          – create a new API key
GET    /api/v1/api-keys/list            – list all API keys for the current user
DELETE /api/v1/api-keys/{key_id}        – revoke (deactivate) an API key
GET    /api/v1/api-keys/usage/{key_id}  – fetch usage statistics for a key
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    APIKey,
    APIKeyUsage,
    SubscriptionTier,
    Subscription,
    User,
    TIER_DAILY_LIMITS,
    TIER_MONTHLY_QUOTAS,
    FREE_TIER_DAILY_LIMIT,
    FREE_TIER_MONTHLY_QUOTA,
    PRO_TIER_DAILY_LIMIT,
    PRO_TIER_MONTHLY_QUOTA,
    ENTERPRISE_TIER_DAILY_LIMIT,
    ENTERPRISE_TIER_MONTHLY_QUOTA,
)
from ..services.payment_service import payment_service
from ..utils.validators import validate_subscription_tier
from .payments import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


# ---------------------------------------------------------------------------
# Pydantic v2 schemas
# ---------------------------------------------------------------------------

class APIKeyCreateRequest(BaseModel):
    """Request body for API key creation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100, description="Human-readable label for the key")
    tier: str = Field("free", description="Tier level: free | pro | enterprise")


class APIKeyResponse(BaseModel):
    """Response for a single API key (without the raw secret)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prefix: str
    tier: str
    rate_limit_per_day: int
    monthly_quota: int
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime


class APIKeyCreatedResponse(APIKeyResponse):
    """Response for a newly created key – includes the raw secret (shown once only)."""
    key: str


class APIKeyListResponse(BaseModel):
    """Response wrapper for a list of API keys."""
    keys: list[APIKeyResponse]


class APIKeyUsageResponse(BaseModel):
    """Usage statistics for a single API key."""
    key_id: int
    tier: str
    requests_today: int
    requests_this_month: int
    daily_limit: int
    monthly_quota: int
    quota_remaining_today: int  # -1 for unlimited
    quota_remaining_month: int  # -1 for unlimited


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_limits(tier: SubscriptionTier) -> tuple[int, int]:
    """Return (daily_limit, monthly_quota) for the given tier."""
    daily = TIER_DAILY_LIMITS.get(tier.value, FREE_TIER_DAILY_LIMIT)
    monthly = TIER_MONTHLY_QUOTAS.get(tier.value, FREE_TIER_MONTHLY_QUOTA)
    return daily, monthly


def _remaining_quota(limit: int, used: int) -> int:
    """
    Return remaining quota given a limit and current usage.

    Returns -1 for unlimited tiers (limit == -1), otherwise max(0, limit - used).
    """
    if limit == ENTERPRISE_TIER_DAILY_LIMIT:  # sentinel for unlimited (-1)
        return -1
    return max(0, limit - used)


def _build_key_response(api_key: APIKey) -> dict:
    return {
        "id": api_key.id,
        "name": api_key.name,
        "prefix": api_key.prefix,
        "tier": api_key.tier.value,
        "rate_limit_per_day": api_key.rate_limit_per_day,
        "monthly_quota": api_key.monthly_quota,
        "is_active": api_key.is_active,
        "last_used_at": api_key.last_used_at,
        "expires_at": api_key.expires_at,
        "created_at": api_key.created_at,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/create", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Generate a new API key for the authenticated user.

    - **name**: Human-readable label for the key.
    - **tier**: ``free`` (100 req/day), ``pro`` (10 000 req/day), or
      ``enterprise`` (unlimited).  For non-free tiers the user must have an
      active subscription at that tier.

    The raw key is returned **once** in the ``key`` field.  Store it securely;
    it cannot be retrieved again.
    """
    tier_enum = validate_subscription_tier(request.tier)

    # Non-free tiers require an active subscription
    if tier_enum != SubscriptionTier.FREE:
        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == user.id,
                Subscription.status == "active",
                Subscription.tier == tier_enum,
            )
            .first()
        )
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"An active {request.tier} subscription is required to create a {request.tier} API key",
            )

    key_data = await payment_service.create_api_key(db, user, request.name, tier_enum)

    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )

    # Persist tier-derived limits onto the stored record
    daily_limit, monthly_quota = _resolve_limits(tier_enum)
    stored_key = db.query(APIKey).filter(APIKey.id == key_data["id"]).first()
    if stored_key:
        stored_key.rate_limit_per_day = daily_limit
        stored_key.monthly_quota = monthly_quota
        db.commit()
        db.refresh(stored_key)

    return {
        **_build_key_response(stored_key),
        "key": key_data["key"],
    }


@router.get("/list", response_model=APIKeyListResponse)
async def list_api_keys(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all API keys (active and inactive) for the authenticated user."""
    keys = (
        db.query(APIKey)
        .filter(APIKey.user_id == user.id)
        .order_by(APIKey.created_at.desc())
        .all()
    )
    return {"keys": [_build_key_response(api_key) for api_key in keys]}


@router.delete("/{key_id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Revoke (deactivate) an API key.

    Only the owner of the key may revoke it.
    """
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == key_id, APIKey.user_id == user.id)
        .first()
    )
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    api_key.is_active = False
    db.commit()
    return {"message": "API key revoked successfully"}


@router.get("/usage/{key_id}", response_model=APIKeyUsageResponse)
async def get_api_key_usage(
    key_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Return usage statistics for the given API key.

    Includes:
    - **requests_today** – total requests made today (UTC calendar date).
    - **requests_this_month** – total requests in the current calendar month.
    - **daily_limit** / **monthly_quota** – tier limits (-1 = unlimited).
    - **quota_remaining_today** / **quota_remaining_month** – remaining quota
      (-1 = unlimited).
    """
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == key_id, APIKey.user_id == user.id)
        .first()
    )
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    today = date.today()
    first_of_month = today.replace(day=1)

    # Requests today
    today_record = (
        db.query(APIKeyUsage)
        .filter(
            APIKeyUsage.api_key_id == key_id,
            APIKeyUsage.usage_date == today,
        )
        .first()
    )
    requests_today = today_record.request_count if today_record else 0

    # Requests this month (sum of all daily records in the current month)
    requests_this_month = (
        db.query(func.sum(APIKeyUsage.request_count))
        .filter(
            APIKeyUsage.api_key_id == key_id,
            APIKeyUsage.usage_date >= first_of_month,
        )
        .scalar()
    ) or 0

    daily_limit = api_key.rate_limit_per_day
    monthly_quota = api_key.monthly_quota

    quota_remaining_today = _remaining_quota(daily_limit, requests_today)
    quota_remaining_month = _remaining_quota(monthly_quota, requests_this_month)

    return APIKeyUsageResponse(
        key_id=key_id,
        tier=api_key.tier.value,
        requests_today=requests_today,
        requests_this_month=requests_this_month,
        daily_limit=daily_limit,
        monthly_quota=monthly_quota,
        quota_remaining_today=quota_remaining_today,
        quota_remaining_month=quota_remaining_month,
    )
