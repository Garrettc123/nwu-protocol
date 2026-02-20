"""API endpoints for users."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Contribution, Reward
from ..schemas import UserResponse, UserCreate
from ..utils import get_user_by_address_or_404

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.address == user_data.address).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this address already exists"
        )
    
    user = User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{address}", response_model=UserResponse)
def get_user(address: str, db: Session = Depends(get_db)):
    """Get user by Ethereum address."""
    user = get_user_by_address_or_404(db, address)
    return user


@router.get("/{address}/contributions")
def get_user_contributions(
    address: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all contributions by a user."""
    user = get_user_by_address_or_404(db, address)

    contributions = db.query(Contribution).filter(
        Contribution.user_id == user.id
    ).offset(skip).limit(limit).all()

    return {
        "user_address": address,
        "total_contributions": user.total_contributions,
        "contributions": contributions
    }


@router.get("/{address}/rewards")
def get_user_rewards(
    address: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all rewards for a user."""
    user = get_user_by_address_or_404(db, address)

    rewards = db.query(Reward).filter(
        Reward.user_id == user.id
    ).offset(skip).limit(limit).all()

    # Calculate totals
    pending_amount = sum(r.amount for r in rewards if r.status == "pending")
    distributed_amount = sum(r.amount for r in rewards if r.status == "distributed")

    return {
        "user_address": address,
        "total_rewards": user.total_rewards,
        "pending_amount": pending_amount,
        "distributed_amount": distributed_amount,
        "rewards": rewards
    }


@router.get("/{address}/stats")
def get_user_stats(address: str, db: Session = Depends(get_db)):
    """Get user statistics."""
    user = get_user_by_address_or_404(db, address)

    # Get contribution stats
    contributions = db.query(Contribution).filter(Contribution.user_id == user.id).all()
    verified_count = sum(1 for c in contributions if c.status == "verified")
    avg_quality_score = sum(c.quality_score or 0 for c in contributions) / len(contributions) if contributions else 0

    return {
        "user_address": address,
        "reputation_score": user.reputation_score,
        "total_contributions": user.total_contributions,
        "verified_contributions": verified_count,
        "average_quality_score": round(avg_quality_score, 2),
        "total_rewards": user.total_rewards,
        "joined_at": user.created_at
    }
