"""Referral and affiliate programme SQLAlchemy models.

These models are defined in ``backend/app/models`` (so they share the common
``Base`` and are included in every Alembic migration) and re-exported here for
the conventional ``backend/models/referral`` import path.

Models
------
ReferralCode
    A unique referral code owned by a single user.  One code is generated per
    user on demand and stays active until the owner deactivates it.

ReferralEvent
    An individual event produced by a referral (e.g. a new sign-up or a first
    subscription payment).  Each event carries the NWU reward owed to the
    referrer and a lifecycle status (pending → completed → claimed).
"""

from app.models import (  # noqa: F401
    ReferralCode,
    ReferralEvent,
    NWU_REWARD_PER_REFERRAL,
    SUBSCRIPTION_REWARD_PERCENT,
    AFFILIATE_REFERRAL_THRESHOLD,
    AFFILIATE_REVENUE_SHARE_PERCENT,
    generate_referral_code,
)

__all__ = [
    "ReferralCode",
    "ReferralEvent",
    "NWU_REWARD_PER_REFERRAL",
    "SUBSCRIPTION_REWARD_PERCENT",
    "AFFILIATE_REFERRAL_THRESHOLD",
    "AFFILIATE_REVENUE_SHARE_PERCENT",
    "generate_referral_code",
]
