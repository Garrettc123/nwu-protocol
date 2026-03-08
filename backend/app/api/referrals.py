"""API endpoints for the customer referral programme."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

from ..database import get_db
from ..models import User, Referral, REFERRAL_REPUTATION_BONUS_REFERRER, REFERRAL_REPUTATION_BONUS_REFEREE
from ..utils.db_helpers import get_user_by_address_or_404

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/referrals", tags=["referrals"])

_MAX_CODE_GENERATION_ATTEMPTS = 5


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
    referral.completed_at = datetime.utcnow()

    # Grant reputation bonuses
    if referrer:
        referrer.reputation_score = (referrer.reputation_score or 0.0) + REFERRAL_REPUTATION_BONUS_REFERRER
    referee.reputation_score = (referee.reputation_score or 0.0) + REFERRAL_REPUTATION_BONUS_REFEREE

    db.commit()

    return {
        "message": "Referral code applied successfully",
        "referee_address": referee.address,
        "referrer_address": referrer.address if referrer else None,
        "referee_reputation_bonus": REFERRAL_REPUTATION_BONUS_REFEREE,
        "referrer_reputation_bonus": REFERRAL_REPUTATION_BONUS_REFERRER,
    }
