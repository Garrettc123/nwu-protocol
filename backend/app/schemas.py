"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """File type enumeration."""
    CODE = "code"
    DATASET = "dataset"
    DOCUMENT = "document"


class ContributionStatus(str, Enum):
    """Contribution status enumeration."""
    PENDING = "pending"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    REJECTED = "rejected"


class RewardStatus(str, Enum):
    """Reward status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    DISTRIBUTED = "distributed"
    FAILED = "failed"


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    address: str = Field(..., min_length=42, max_length=42)
    username: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """User creation schema."""
    pass


class UserResponse(UserBase):
    """User response schema."""
    id: int
    reputation_score: float
    total_contributions: int
    total_rewards: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Contribution Schemas
class ContributionBase(BaseModel):
    """Base contribution schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    file_type: FileType


class ContributionCreate(ContributionBase):
    """Contribution creation schema."""
    pass


class ContributionUpload(BaseModel):
    """Contribution upload schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    file_type: FileType
    metadata: Optional[Dict[str, Any]] = None


class ContributionResponse(ContributionBase):
    """Contribution response schema."""
    id: int
    user_id: int
    ipfs_hash: str
    file_name: str
    file_size: int
    status: ContributionStatus
    quality_score: Optional[float]
    verification_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Verification Schemas
class VerificationBase(BaseModel):
    """Base verification schema."""
    agent_id: str
    agent_type: str
    vote_score: float = Field(..., ge=0, le=100)
    reasoning: Optional[str] = None


class VerificationCreate(VerificationBase):
    """Verification creation schema."""
    contribution_id: int
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    originality_score: Optional[float] = Field(None, ge=0, le=100)
    security_score: Optional[float] = Field(None, ge=0, le=100)
    documentation_score: Optional[float] = Field(None, ge=0, le=100)
    details: Optional[Dict[str, Any]] = None


class VerificationResponse(VerificationBase):
    """Verification response schema."""
    id: int
    contribution_id: int
    quality_score: Optional[float]
    originality_score: Optional[float]
    security_score: Optional[float]
    documentation_score: Optional[float]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Reward Schemas
class RewardBase(BaseModel):
    """Base reward schema."""
    amount: float = Field(..., gt=0)


class RewardCreate(RewardBase):
    """Reward creation schema."""
    user_id: int
    contribution_id: int


class RewardResponse(RewardBase):
    """Reward response schema."""
    id: int
    user_id: int
    contribution_id: int
    status: RewardStatus
    tx_hash: Optional[str]
    blockchain: str
    created_at: datetime
    distributed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Health Check Schema
class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    service: str
    version: str
    timestamp: datetime
    database: bool
    redis: bool
    ipfs: bool
    rabbitmq: bool


# API Info Schema
class APIInfo(BaseModel):
    """API information schema."""
    name: str
    description: str
    version: str
    docs_url: str
    endpoints: list[str]
