"""API endpoints for NWU token staking and yield."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ..models import StakingPosition, YieldEvent, STAKING_APY, STAKING_LOCK_DAYS
from ..utils.validators import normalize_ethereum_address

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/staking", tags=["staking"])

SECONDS_PER_YEAR = 365 * 24 * 3600


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class StakeRequest(BaseModel):
    wallet: str
    amount: float

    @field_validator("wallet")
    @classmethod
    def validate_wallet(cls, value: str) -> str:
        if not value.startswith("0x") or len(value) != 42:
            raise ValueError("wallet must be a 42-character Ethereum address starting with 0x")
        return value.lower()

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("amount must be positive")
        return value


class UnstakeRequest(BaseModel):
    wallet: str
    amount: float

    @field_validator("wallet")
    @classmethod
    def validate_wallet(cls, value: str) -> str:
        if not value.startswith("0x") or len(value) != 42:
            raise ValueError("wallet must be a 42-character Ethereum address starting with 0x")
        return value.lower()

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("amount must be positive")
        return value


class ClaimRequest(BaseModel):
    wallet: str

    @field_validator("wallet")
    @classmethod
    def validate_wallet(cls, value: str) -> str:
        if not value.startswith("0x") or len(value) != 42:
            raise ValueError("wallet must be a 42-character Ethereum address starting with 0x")
        return value.lower()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _calculate_pending_yield(position: StakingPosition, now: datetime) -> float:
    """
    Calculate yield accrued since ``last_yield_update`` using simple-interest
    12% APY, converted to a per-second rate.
    """
    if position.staked_amount <= 0:
        return 0.0
    elapsed_seconds = (now - position.last_yield_update).total_seconds()
    if elapsed_seconds <= 0:
        return 0.0
    return position.staked_amount * STAKING_APY * elapsed_seconds / SECONDS_PER_YEAR


def _flush_yield(position: StakingPosition, now: datetime) -> None:
    """Accrue pending yield into ``accumulated_yield`` and update timestamp."""
    pending = _calculate_pending_yield(position, now)
    position.accumulated_yield += pending
    position.last_yield_update = now


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/stake", status_code=status.HTTP_200_OK)
async def stake(request: StakeRequest, db: Session = Depends(get_db)):
    """
    Stake NWU tokens.

    Creates a new staking position or adds to an existing one.
    The 7-day lock period resets on every new stake.

    - **wallet**: Ethereum wallet address
    - **amount**: NWU token amount to stake
    """
    wallet = request.wallet
    now = datetime.utcnow()
    lock_expiry = now + timedelta(days=STAKING_LOCK_DAYS)

    position = db.query(StakingPosition).filter(StakingPosition.wallet == wallet).first()

    if position is None:
        position = StakingPosition(
            wallet=wallet,
            staked_amount=request.amount,
            staked_at=now,
            lock_expires_at=lock_expiry,
            accumulated_yield=0.0,
            last_yield_update=now,
            is_active=True,
        )
        db.add(position)
    else:
        # Accrue yield on existing stake before modifying principal
        _flush_yield(position, now)
        position.staked_amount += request.amount
        position.lock_expires_at = lock_expiry
        position.is_active = True

    db.add(YieldEvent(wallet=wallet, event_type="stake", amount=request.amount))
    db.commit()
    db.refresh(position)

    return {
        "wallet": wallet,
        "staked_amount": position.staked_amount,
        "lock_expires_at": position.lock_expires_at.isoformat(),
        "accumulated_yield": position.accumulated_yield,
    }


@router.post("/unstake", status_code=status.HTTP_200_OK)
async def unstake(request: UnstakeRequest, db: Session = Depends(get_db)):
    """
    Unstake NWU tokens.

    Enforces a 7-day lock period.  Callers must wait until the lock
    has expired before tokens can be withdrawn.

    - **wallet**: Ethereum wallet address
    - **amount**: NWU token amount to unstake
    """
    wallet = request.wallet
    now = datetime.utcnow()

    position = db.query(StakingPosition).filter(
        StakingPosition.wallet == wallet,
        StakingPosition.is_active,
    ).first()

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active staking position found for this wallet",
        )

    if now < position.lock_expires_at:
        remaining_seconds = int((position.lock_expires_at - now).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Tokens are locked for {remaining_seconds} more seconds "
                f"(lock expires at {position.lock_expires_at.isoformat()})"
            ),
        )

    if request.amount > position.staked_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot unstake {request.amount}; only {position.staked_amount} staked",
        )

    # Accrue yield before reducing principal
    _flush_yield(position, now)
    position.staked_amount -= request.amount

    if position.staked_amount == 0:
        position.is_active = False

    db.add(YieldEvent(wallet=wallet, event_type="unstake", amount=request.amount))
    db.commit()
    db.refresh(position)

    return {
        "wallet": wallet,
        "unstaked_amount": request.amount,
        "remaining_staked": position.staked_amount,
        "accumulated_yield": position.accumulated_yield,
    }


@router.get("/position/{wallet}", status_code=status.HTTP_200_OK)
async def get_position(wallet: str, db: Session = Depends(get_db)):
    """
    Return staking position for a wallet.

    Returns staked amount, total accrued yield (including pending
    since last update), and lock expiry timestamp.

    - **wallet**: Ethereum wallet address
    """
    wallet = wallet.lower()
    now = datetime.utcnow()

    position = db.query(StakingPosition).filter(StakingPosition.wallet == wallet).first()

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No staking position found for this wallet",
        )

    pending_yield = _calculate_pending_yield(position, now)
    total_yield = position.accumulated_yield + pending_yield

    return {
        "wallet": wallet,
        "staked_amount": position.staked_amount,
        "yield_accrued": total_yield,
        "lock_expires_at": position.lock_expires_at.isoformat(),
        "is_active": position.is_active,
        "staked_at": position.staked_at.isoformat(),
    }


@router.post("/claim", status_code=status.HTTP_200_OK)
async def claim_yield(request: ClaimRequest, db: Session = Depends(get_db)):
    """
    Claim accrued yield as new NWU tokens.

    Calculates all pending yield, mints it as accumulated yield, then
    resets the accumulated yield counter to zero.

    - **wallet**: Ethereum wallet address
    """
    wallet = request.wallet
    now = datetime.utcnow()

    position = db.query(StakingPosition).filter(StakingPosition.wallet == wallet).first()

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No staking position found for this wallet",
        )

    # Flush pending yield first
    _flush_yield(position, now)

    claimable = position.accumulated_yield
    if claimable <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No yield available to claim",
        )

    position.accumulated_yield = 0.0

    db.add(YieldEvent(wallet=wallet, event_type="claim", amount=claimable))
    db.commit()
    db.refresh(position)

    return {
        "wallet": wallet,
        "claimed_yield": claimable,
        "remaining_staked": position.staked_amount,
        "new_accumulated_yield": position.accumulated_yield,
    }
