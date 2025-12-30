"""User data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for creating a user."""
    address: str = Field(..., description="Ethereum wallet address")


class User(BaseModel):
    """Complete user model."""
    id: str = Field(..., description="Unique user ID")
    address: str = Field(..., description="Ethereum wallet address")
    reputation_score: float = Field(0.0, ge=0, description="User reputation score")
    total_contributions: int = Field(0, ge=0, description="Total number of contributions")
    total_rewards: float = Field(0.0, ge=0, description="Total NWU tokens earned")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "user_789ghi",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "reputation_score": 4.5,
                "total_contributions": 12,
                "total_rewards": 1250.0,
                "joined_at": "2025-12-01T00:00:00Z",
                "last_active": "2025-12-30T00:00:00Z"
            }
        }


class UserStats(BaseModel):
    """User statistics model."""
    user_id: str
    contributions_pending: int = 0
    contributions_verified: int = 0
    contributions_rejected: int = 0
    average_quality_score: Optional[float] = None
    total_rewards: float = 0.0
    reputation_score: float = 0.0
