"""Subscription billing router – canonical path.

Re-exports the FastAPI router and plan catalogue constants from
``app.api.subscriptions`` and ``app.subscription_plans`` respectively,
so clients can import from ``backend/routers/subscriptions`` as specified
by the project requirements without duplicating any logic.
"""

from app.subscription_plans import (  # noqa: F401  (re-export)
    PLAN_FEATURES,
    PLAN_PRICES,
    PLAN_RATE_LIMITS,
    PLAN_STAKING_MULTIPLIERS,
    TIER_ORDER,
    subscription_status_payload,
)

# Backward-compatible alias used by tests and router re-exports
_subscription_status_payload = subscription_status_payload

# Router is imported via the api.subscriptions submodule; the relative
# imports there do not cause app.api.__init__ to be executed when importing
# directly by full dotted path.
from app.api.subscriptions import (  # noqa: F401  (re-export)
    _active_subscription,
    router,
)

__all__ = [
    "router",
    "PLAN_PRICES",
    "PLAN_RATE_LIMITS",
    "PLAN_STAKING_MULTIPLIERS",
    "PLAN_FEATURES",
    "TIER_ORDER",
    "subscription_status_payload",
    "_subscription_status_payload",
    "_active_subscription",
]
