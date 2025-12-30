"""Contribution data models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ContributionStatus(str, Enum):
    """Status of a contribution."""
    PENDING = "pending"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    REJECTED = "rejected"
    FAILED = "failed"


class ContributionType(str, Enum):
    """Type of contribution."""
    CODE = "code"
    DATASET = "dataset"
    DOCUMENT = "document"
    OTHER = "other"


class ContributionMetadata(BaseModel):
    """Metadata for a contribution."""
    title: str = Field(..., description="Title of the contribution")
    description: str = Field(..., description="Description of the contribution")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    language: Optional[str] = Field(None, description="Programming language or content type")


class ContributionCreate(BaseModel):
    """Schema for creating a new contribution."""
    file_type: ContributionType
    metadata: ContributionMetadata
    content_hash: str = Field(..., description="SHA-256 hash of the content")
    ipfs_hash: Optional[str] = Field(None, description="IPFS hash for stored content")


class Contribution(BaseModel):
    """Complete contribution model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "contrib_123abc",
                "submitter": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "file_type": "code",
                "metadata": {
                    "title": "Smart Contract Optimizer",
                    "description": "Gas optimization algorithm for Solidity contracts",
                    "tags": ["solidity", "optimization", "blockchain"],
                    "language": "python"
                },
                "content_hash": "abc123def456...",
                "ipfs_hash": "QmT4AeW...",
                "status": "verified",
                "quality_score": 85.5,
                "verification_count": 3,
                "reward_amount": 100.0,
                "created_at": "2025-12-30T00:00:00Z",
                "updated_at": "2025-12-30T00:05:00Z"
            }
        }
    )

    id: str = Field(..., description="Unique contribution ID")
    submitter: str = Field(..., description="Ethereum address of submitter")
    file_type: ContributionType
    metadata: ContributionMetadata
    content_hash: str
    ipfs_hash: Optional[str] = None
    status: ContributionStatus = ContributionStatus.PENDING
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="Quality score 0-100")
    verification_count: int = Field(0, description="Number of verifications received")
    reward_amount: Optional[float] = Field(None, description="Calculated reward in NWU tokens")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
