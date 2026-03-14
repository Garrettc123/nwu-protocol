"""Subscription plan constants.

Centralised definition of plan catalogue data (prices, rate limits,
staking multipliers, feature flags) and the subscription status helper so
they can be imported from either ``app.api.subscriptions`` or
``routers.subscriptions`` without pulling in the full API package and its
transitive dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from .models import SubscriptionTier

if TYPE_CHECKING:
    from .models import Subscription

# ---------------------------------------------------------------------------
# Monthly prices (USD)
# ---------------------------------------------------------------------------

PLAN_PRICES: Dict[SubscriptionTier, int] = {
    SubscriptionTier.BASIC: 29,
    SubscriptionTier.PRO: 99,
    SubscriptionTier.ENTERPRISE: 499,
}

# ---------------------------------------------------------------------------
# API request rate limits (requests per day)
# ---------------------------------------------------------------------------

PLAN_RATE_LIMITS: Dict[SubscriptionTier, int] = {
    SubscriptionTier.FREE: 100,
    SubscriptionTier.BASIC: 1_000,
    SubscriptionTier.PRO: 10_000,
    SubscriptionTier.ENTERPRISE: 100_000,
}

# ---------------------------------------------------------------------------
# Staking reward multipliers
# ---------------------------------------------------------------------------

PLAN_STAKING_MULTIPLIERS: Dict[SubscriptionTier, float] = {
    SubscriptionTier.FREE: 1.0,
    SubscriptionTier.BASIC: 1.5,
    SubscriptionTier.PRO: 2.0,
    SubscriptionTier.ENTERPRISE: 5.0,
}

# ---------------------------------------------------------------------------
# Feature flags per tier
# ---------------------------------------------------------------------------

PLAN_FEATURES: Dict[SubscriptionTier, Dict[str, Any]] = {
    SubscriptionTier.FREE: {
        "basic_api": True,
        "advanced_api": False,
        "custom_integrations": False,
        "priority_support": False,
        "analytics_dashboard": False,
        "sla_guarantee": False,
    },
    SubscriptionTier.BASIC: {
        "basic_api": True,
        "advanced_api": False,
        "custom_integrations": False,
        "priority_support": False,
        "analytics_dashboard": False,
        "sla_guarantee": False,
    },
    SubscriptionTier.PRO: {
        "basic_api": True,
        "advanced_api": True,
        "custom_integrations": False,
        "priority_support": True,
        "analytics_dashboard": True,
        "sla_guarantee": False,
    },
    SubscriptionTier.ENTERPRISE: {
        "basic_api": True,
        "advanced_api": True,
        "custom_integrations": True,
        "priority_support": True,
        "analytics_dashboard": True,
        "sla_guarantee": True,
    },
}

# ---------------------------------------------------------------------------
# Tier ordering (lowest → highest)
# ---------------------------------------------------------------------------

TIER_ORDER = [
    SubscriptionTier.FREE,
    SubscriptionTier.BASIC,
    SubscriptionTier.PRO,
    SubscriptionTier.ENTERPRISE,
]


# ---------------------------------------------------------------------------
# Status helper (usable without importing app.api)
# ---------------------------------------------------------------------------


def subscription_status_payload(subscription: "Optional[Subscription]") -> Dict[str, Any]:
    """Build the subscription status response payload.

    Args:
        subscription: Active Subscription ORM object, or ``None`` for users
            without an active subscription.

    Returns:
        Dictionary suitable for returning as a JSON response.
    """
    if not subscription:
        tier = SubscriptionTier.FREE
        return {
            "subscription_id": None,
            "plan": tier.value,
            "status": "none",
            "renewal_date": None,
            "cancel_at_period_end": False,
            "api_quota": PLAN_RATE_LIMITS[tier],
            "staking_multiplier": PLAN_STAKING_MULTIPLIERS[tier],
            "features": PLAN_FEATURES[tier],
            "monthly_price_usd": 0,
        }
    tier = subscription.tier
    return {
        "subscription_id": subscription.id,
        "plan": tier.value,
        "status": subscription.status,
        "renewal_date": (
            subscription.current_period_end.isoformat()
            if subscription.current_period_end
            else None
        ),
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "api_quota": subscription.rate_limit,
        "staking_multiplier": subscription.staking_multiplier,
        "features": PLAN_FEATURES.get(tier, {}),
        "monthly_price_usd": PLAN_PRICES.get(tier, 0),
    }
