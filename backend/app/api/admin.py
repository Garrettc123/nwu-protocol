"""API endpoints for admin revenue dashboard and analytics."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta
from typing import List
import logging

from ..database import get_db
from ..models import User, Subscription, Payment, PaymentStatus, APIKey, UsageRecord
from ..config import settings
from .payments import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Number of days to include in daily revenue breakdown
DAILY_REVENUE_DAYS = 90

# Tier monthly prices in USD (mirrors pricing endpoint)
TIER_MONTHLY_PRICE = {"pro": 99.0, "enterprise": 999.0}


def _get_admin_addresses() -> List[str]:
    """Return the configured admin addresses (lowercased)."""
    raw = settings.admin_addresses or ""
    return [addr.strip().lower() for addr in raw.split(",") if addr.strip()]


async def get_current_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    Require the authenticated user to be an admin.

    Admin addresses are controlled via the ADMIN_ADDRESSES environment variable
    (comma-separated Ethereum addresses).

    Raises:
        HTTPException 403: If the user is not an admin.
    """
    admin_addresses = _get_admin_addresses()
    if not admin_addresses or user.address.lower() not in admin_addresses:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


# ---------------------------------------------------------------------------
# Revenue endpoints
# ---------------------------------------------------------------------------

@router.get("/revenue/summary")
async def get_revenue_summary(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """
    Return high-level revenue metrics.

    - **mrr**: Monthly Recurring Revenue (active subscriptions only)
    - **arr**: Annual Recurring Revenue (MRR * 12)
    - **revenue_this_month**: Total succeeded payments this calendar month
    - **churn_rate**: Percentage of subscriptions canceled in the last 30 days
    - **active_subscriptions**: Number of currently active subscriptions
    """
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Active subscriptions
    active_subscriptions = (
        db.query(func.count(Subscription.id))
        .filter(Subscription.status == "active")
        .scalar()
        or 0
    )

    # MRR: sum monthly price for each active subscription tier
    active_tiers = (
        db.query(Subscription.tier, func.count(Subscription.id))
        .filter(Subscription.status == "active")
        .group_by(Subscription.tier)
        .all()
    )
    mrr = sum(
        TIER_MONTHLY_PRICE.get(getattr(tier, "value", tier), 0.0) * count
        for tier, count in active_tiers
    )
    arr = mrr * 12

    # Revenue this month: sum of succeeded payments
    revenue_this_month = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(
            Payment.status == PaymentStatus.SUCCEEDED,
            Payment.created_at >= month_start,
        )
        .scalar()
        or 0.0
    )

    # Churn rate: (canceled in last 30d) / (active 30d ago) * 100
    thirty_days_ago = now - timedelta(days=30)
    canceled_last_30d = (
        db.query(func.count(Subscription.id))
        .filter(
            Subscription.status == "canceled",
            Subscription.updated_at >= thirty_days_ago,
        )
        .scalar()
        or 0
    )
    subscriptions_30d_ago = (
        db.query(func.count(Subscription.id))
        .filter(Subscription.created_at <= thirty_days_ago)
        .scalar()
        or 0
    )
    churn_rate = (
        round(canceled_last_30d / subscriptions_30d_ago * 100, 2)
        if subscriptions_30d_ago > 0
        else 0.0
    )

    return {
        "mrr": round(mrr, 2),
        "arr": round(arr, 2),
        "revenue_this_month": round(float(revenue_this_month), 2),
        "churn_rate": churn_rate,
        "active_subscriptions": active_subscriptions,
    }


@router.get("/revenue/daily")
async def get_daily_revenue(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """
    Return daily revenue for the last 90 days.

    Returns an array of ``{date, amount}`` objects sorted ascending by date.
    Days with no payments are included with ``amount: 0``.
    """
    cutoff = datetime.utcnow() - timedelta(days=DAILY_REVENUE_DAYS)

    rows = (
        db.query(
            cast(Payment.created_at, Date).label("day"),
            func.coalesce(func.sum(Payment.amount), 0.0).label("total"),
        )
        .filter(
            Payment.status == PaymentStatus.SUCCEEDED,
            Payment.created_at >= cutoff,
        )
        .group_by(cast(Payment.created_at, Date))
        .order_by(cast(Payment.created_at, Date))
        .all()
    )

    # Build a full date map so every day in the 90-day window is represented
    day_map = {row.day: float(row.total) for row in rows}
    today = datetime.utcnow().date()
    result = []
    for offset in range(DAILY_REVENUE_DAYS - 1, -1, -1):
        day = today - timedelta(days=offset)
        result.append({"date": day.isoformat(), "amount": round(day_map.get(day, 0.0), 2)})

    return {"daily": result}


# ---------------------------------------------------------------------------
# User stats endpoint
# ---------------------------------------------------------------------------

@router.get("/users/stats")
async def get_user_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """
    Return user statistics.

    - **total_users**: Total registered users
    - **active_users_30d**: Users who were updated (active) in the last 30 days
    - **new_users_this_week**: Users created in the last 7 days
    """
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users_30d = (
        db.query(func.count(User.id))
        .filter(User.updated_at >= thirty_days_ago, User.is_active == True)
        .scalar()
        or 0
    )
    new_users_this_week = (
        db.query(func.count(User.id))
        .filter(User.created_at >= seven_days_ago)
        .scalar()
        or 0
    )

    return {
        "total_users": total_users,
        "active_users_30d": active_users_30d,
        "new_users_this_week": new_users_this_week,
    }


# ---------------------------------------------------------------------------
# API key stats endpoint
# ---------------------------------------------------------------------------

@router.get("/api-keys/stats")
async def get_api_key_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """
    Return API key usage statistics.

    - **total_calls_today**: Total API calls recorded today across all subscriptions
    - **total_calls_this_month**: Total API calls this calendar month
    - **top_consumers**: Top 10 subscriptions by call volume this month
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_calls_today = (
        db.query(func.coalesce(func.sum(UsageRecord.request_count), 0))
        .filter(UsageRecord.record_date >= today_start)
        .scalar()
        or 0
    )

    total_calls_this_month = (
        db.query(func.coalesce(func.sum(UsageRecord.request_count), 0))
        .filter(UsageRecord.record_date >= month_start)
        .scalar()
        or 0
    )

    top_consumer_rows = (
        db.query(
            UsageRecord.subscription_id,
            func.sum(UsageRecord.request_count).label("total_calls"),
        )
        .filter(UsageRecord.record_date >= month_start)
        .group_by(UsageRecord.subscription_id)
        .order_by(func.sum(UsageRecord.request_count).desc())
        .limit(10)
        .all()
    )

    top_consumers = [
        {"subscription_id": row.subscription_id, "total_calls": int(row.total_calls)}
        for row in top_consumer_rows
    ]

    return {
        "total_calls_today": int(total_calls_today),
        "total_calls_this_month": int(total_calls_this_month),
        "top_consumers": top_consumers,
    }


# ---------------------------------------------------------------------------
# Staking stats endpoint
# ---------------------------------------------------------------------------

@router.get("/staking/stats")
async def get_staking_stats(
    _admin: User = Depends(get_current_admin_user),
):
    """
    Return NWU staking statistics.

    Returns placeholder data for on-chain staking metrics that are not yet
    stored in the relational database. Wire this up to the smart-contract
    indexer or a dedicated staking service when available.
    """
    return {
        "total_nwu_staked": 0.0,
        "yield_distributed": 0.0,
        "staking_participation_rate": 0.0,
        "note": "Staking data will be populated once the on-chain indexer is integrated.",
    }
