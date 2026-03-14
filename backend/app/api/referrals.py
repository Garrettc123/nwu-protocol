"""API endpoints for the customer referral and affiliate programme."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import logging

from ..database import get_db
from ..models import (
    User,
    Referral,
    ReferralCode,
    ReferralEvent,
    REFERRAL_REPUTATION_BONUS_REFERRER,
    REFERRAL_REPUTATION_BONUS_REFEREE,
    NWU_REWARD_PER_REFERRAL,
    SUBSCRIPTION_REWARD_PERCENT,
    AFFILIATE_REFERRAL_THRESHOLD,
    AFFILIATE_REVENUE_SHARE_PERCENT,
)
from ..services.auth_service import auth_service
from ..utils.db_helpers import get_user_by_address_or_404
from ..utils.validators import normalize_ethereum_address

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/referrals", tags=["referrals"])
security = HTTPBearer()

_MAX_CODE_GENERATION_ATTEMPTS = 5


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get the currently authenticated user from a JWT Bearer token."""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
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
# JWT-authenticated affiliate programme endpoints
# ---------------------------------------------------------------------------

@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_referral_code_for_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate (or return the existing) unique referral code for the authenticated user.

    Returns an existing active code when one is already present so the
    operation is idempotent.
    """
    existing_code = (
        db.query(ReferralCode)
        .filter(ReferralCode.referrer_id == current_user.id, ReferralCode.is_active.is_(True))
        .first()
    )
    if existing_code:
        return {
            "referral_code": existing_code.code,
            "referral_url": f"/signup?ref={existing_code.code}",
            "is_affiliate": current_user.is_affiliate,
        }

    for _ in range(_MAX_CODE_GENERATION_ATTEMPTS):
        try:
            new_code = ReferralCode(referrer_id=current_user.id)
            db.add(new_code)
            db.commit()
            db.refresh(new_code)
            return {
                "referral_code": new_code.code,
                "referral_url": f"/signup?ref={new_code.code}",
                "is_affiliate": current_user.is_affiliate,
            }
        except IntegrityError:
            db.rollback()

    logger.error(
        "Failed to generate a unique ReferralCode after %d attempts for user %d",
        _MAX_CODE_GENERATION_ATTEMPTS,
        current_user.id,
    )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate a unique referral code. Please try again.",
    )


@router.get("/stats")
async def get_referral_stats_for_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return referral statistics for the authenticated user.

    Includes total referrals made, conversions, total NWU earned, pending
    rewards, and whether the user has reached Affiliate tier.
    """
    referral_codes = (
        db.query(ReferralCode).filter(ReferralCode.referrer_id == current_user.id).all()
    )
    referral_code_ids = [rc.id for rc in referral_codes]

    total_conversions = 0
    total_nwu_earned = 0.0
    pending_rewards = 0.0

    if referral_code_ids:
        all_events = (
            db.query(ReferralEvent)
            .filter(ReferralEvent.referral_code_id.in_(referral_code_ids))
            .all()
        )
        total_conversions = len(
            {event.referee_id for event in all_events if event.event_type == "signup"}
        )
        for event in all_events:
            if event.status == "claimed":
                total_nwu_earned += event.nwu_reward
            elif event.status in ("pending", "completed"):
                pending_rewards += event.nwu_reward

    total_referrals = len(referral_codes)

    # Check and update affiliate status
    if not current_user.is_affiliate and total_conversions >= AFFILIATE_REFERRAL_THRESHOLD:
        current_user.is_affiliate = True
        db.commit()

    return {
        "address": current_user.address,
        "total_referrals": total_referrals,
        "total_conversions": total_conversions,
        "total_nwu_earned": total_nwu_earned,
        "pending_rewards": pending_rewards,
        "is_affiliate": current_user.is_affiliate,
        "revenue_share_percent": (
            AFFILIATE_REVENUE_SHARE_PERCENT if current_user.is_affiliate else SUBSCRIPTION_REWARD_PERCENT
        ),
    }


@router.post("/claim", status_code=status.HTTP_200_OK)
async def claim_referral_rewards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Claim all pending referral rewards as NWU tokens.

    Marks every pending/completed ``ReferralEvent`` owned by the user as
    ``claimed`` and adds the total to the user's ``nwu_claimed_rewards``
    balance.
    """
    referral_codes = (
        db.query(ReferralCode).filter(ReferralCode.referrer_id == current_user.id).all()
    )
    referral_code_ids = [rc.id for rc in referral_codes]

    if not referral_code_ids:
        return {
            "message": "No referral rewards to claim",
            "nwu_claimed": 0.0,
            "total_nwu_claimed": current_user.nwu_claimed_rewards,
        }

    claimable_events = (
        db.query(ReferralEvent)
        .filter(
            ReferralEvent.referral_code_id.in_(referral_code_ids),
            ReferralEvent.status.in_(["pending", "completed"]),
        )
        .all()
    )

    if not claimable_events:
        return {
            "message": "No pending rewards to claim",
            "nwu_claimed": 0.0,
            "total_nwu_claimed": current_user.nwu_claimed_rewards,
        }

    claimed_amount = 0.0
    now = datetime.now(timezone.utc)
    for event in claimable_events:
        claimed_amount += event.nwu_reward
        event.status = "claimed"
        event.completed_at = now

    current_user.nwu_claimed_rewards = (current_user.nwu_claimed_rewards or 0.0) + claimed_amount
    current_user.nwu_pending_rewards = max(
        0.0, (current_user.nwu_pending_rewards or 0.0) - claimed_amount
    )

    db.commit()

    logger.info(
        "User %s claimed %.2f NWU referral rewards", current_user.address, claimed_amount
    )

    return {
        "message": "Referral rewards claimed successfully",
        "nwu_claimed": claimed_amount,
        "total_nwu_claimed": current_user.nwu_claimed_rewards,
    }


# ---------------------------------------------------------------------------
# Legacy endpoints (address-based, no JWT required)
# ---------------------------------------------------------------------------

@router.get("/code/{address}")
async def get_referral_code(address: str, db: Session = Depends(get_db)):
    """
    Get the referral code for a user, generating one if it doesn't exist yet.

    - **address**: User's Ethereum address
    """
    user = get_user_by_address_or_404(db, address)

    referral = db.query(Referral).filter(
        Referral.referrer_id == user.id,
        Referral.referee_id.is_(None),
    ).first()

    if not referral:
        for _ in range(_MAX_CODE_GENERATION_ATTEMPTS):
            try:
                referral = Referral(referrer_id=user.id)
                db.add(referral)
                db.commit()
                db.refresh(referral)
                break
            except IntegrityError:
                db.rollback()
        else:
            logger.error("Failed to generate a unique referral code after %d attempts", _MAX_CODE_GENERATION_ATTEMPTS)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate a unique referral code. Please try again.",
            )

    return {
        "address": user.address,
        "referral_code": referral.referral_code,
        "referral_url": f"/signup?ref={referral.referral_code}",
    }


@router.get("/stats/{address}")
async def get_referral_stats(address: str, db: Session = Depends(get_db)):
    """
    Get referral statistics for a user.

    - **address**: User's Ethereum address
    """
    user = get_user_by_address_or_404(db, address)

    completed_referrals = (
        db.query(Referral)
        .filter(Referral.referrer_id == user.id, Referral.status == "completed")
        .all()
    )
    pending_referrals = (
        db.query(Referral)
        .filter(Referral.referrer_id == user.id, Referral.status == "pending", Referral.referee_id.isnot(None))
        .all()
    )

    total_reward = len(completed_referrals) * REFERRAL_REPUTATION_BONUS_REFERRER

    return {
        "address": user.address,
        "total_referrals": len(completed_referrals) + len(pending_referrals),
        "completed_referrals": len(completed_referrals),
        "pending_referrals": len(pending_referrals),
        "total_reputation_earned": total_reward,
    }


@router.post("/apply", status_code=status.HTTP_200_OK)
async def apply_referral_code(
    address: str,
    referral_code: str,
    db: Session = Depends(get_db),
):
    """
    Apply a referral code for a new user.

    Links the referee to the referrer, grants reputation bonuses, and — when a
    ``ReferralCode`` record exists for the supplied code — creates a
    ``ReferralEvent`` that accumulates 50 NWU for the referrer.

    - **address**: New user's Ethereum address
    - **referral_code**: The referral code shared by the referrer
    """
    referee = get_user_by_address_or_404(db, address)

    # Ensure the user has not already used a referral code
    existing = db.query(Referral).filter(Referral.referee_id == referee.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Referral code already applied for this user",
        )

    # Find the open (unclaimed) referral record that owns this code
    referral = (
        db.query(Referral)
        .filter(
            Referral.referral_code == referral_code,
            Referral.referee_id.is_(None),
        )
        .first()
    )

    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or already-used referral code",
        )

    referrer = db.query(User).filter(User.id == referral.referrer_id).first()

    if referrer and referrer.id == referee.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot use your own referral code",
        )

    # Mark the referral as completed and link the referee
    referral.referee_id = referee.id
    referral.status = "completed"
    referral.reward_granted = True
    referral.completed_at = datetime.now(timezone.utc)

    # Grant reputation bonuses
    if referrer:
        referrer.reputation_score = (referrer.reputation_score or 0.0) + REFERRAL_REPUTATION_BONUS_REFERRER
    referee.reputation_score = (referee.reputation_score or 0.0) + REFERRAL_REPUTATION_BONUS_REFEREE

    # If a ReferralCode record also exists for this code, create a ReferralEvent
    # so that NWU rewards accumulate for the referrer.
    affiliate_code = (
        db.query(ReferralCode)
        .filter(ReferralCode.code == referral_code, ReferralCode.is_active.is_(True))
        .first()
    )
    if affiliate_code and referrer:
        reward_percent = (
            AFFILIATE_REVENUE_SHARE_PERCENT
            if referrer.is_affiliate
            else SUBSCRIPTION_REWARD_PERCENT
        )
        signup_event = ReferralEvent(
            referral_code_id=affiliate_code.id,
            referee_id=referee.id,
            event_type="signup",
            nwu_reward=NWU_REWARD_PER_REFERRAL,
            status="pending",
        )
        db.add(signup_event)
        referrer.nwu_pending_rewards = (referrer.nwu_pending_rewards or 0.0) + NWU_REWARD_PER_REFERRAL

        # Check and update affiliate status
        completed_conversions = (
            db.query(ReferralEvent)
            .filter(
                ReferralEvent.referral_code_id.in_(
                    db.query(ReferralCode.id).filter(ReferralCode.referrer_id == referrer.id)
                ),
                ReferralEvent.event_type == "signup",
            )
            .count()
        ) + 1  # +1 for the event we're about to commit
        if not referrer.is_affiliate and completed_conversions >= AFFILIATE_REFERRAL_THRESHOLD:
            referrer.is_affiliate = True
    else:
        reward_percent = SUBSCRIPTION_REWARD_PERCENT

    db.commit()

    return {
        "message": "Referral code applied successfully",
        "referee_address": referee.address,
        "referrer_address": referrer.address if referrer else None,
        "referee_reputation_bonus": REFERRAL_REPUTATION_BONUS_REFEREE,
        "referrer_reputation_bonus": REFERRAL_REPUTATION_BONUS_REFERRER,
    }

