"""API endpoints for users."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..database import get_db
from ..models import User, Contribution, Reward
from ..schemas import UserResponse, UserCreate

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
    user = db.query(User).filter(User.address == address).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/{address}/contributions")
def get_user_contributions(
    address: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all contributions by a user."""
    user = db.query(User).filter(User.address == address).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
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
    user = db.query(User).filter(User.address == address).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    rewards = db.query(Reward).filter(
        Reward.user_id == user.id
    ).offset(skip).limit(limit).all()
    
    # Calculate totals using database aggregation
    pending_amount = db.query(func.sum(Reward.amount)).filter(
        Reward.user_id == user.id,
        Reward.status == "pending"
    ).scalar() or 0.0
    
    distributed_amount = db.query(func.sum(Reward.amount)).filter(
        Reward.user_id == user.id,
        Reward.status == "distributed"
    ).scalar() or 0.0
    
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
    user = db.query(User).filter(User.address == address).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get contribution stats using database aggregations
    verified_count = db.query(func.count(Contribution.id)).filter(
        Contribution.user_id == user.id,
        Contribution.status == "verified"
    ).scalar() or 0
    
    avg_quality_score = db.query(func.avg(Contribution.quality_score)).filter(
        Contribution.user_id == user.id,
        Contribution.quality_score.isnot(None)
    ).scalar() or 0.0
    
    return {
        "user_address": address,
        "reputation_score": user.reputation_score,
        "total_contributions": user.total_contributions,
        "verified_contributions": verified_count,
        "average_quality_score": round(float(avg_quality_score), 2),
        "total_rewards": user.total_rewards,
        "joined_at": user.created_at
    }
