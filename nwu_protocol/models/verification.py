"""Verification data models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class VerificationVote(str, Enum):
    """Verification vote values."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


class AgentType(str, Enum):
    """Types of verification agents."""
    ALPHA = "agent-alpha"  # Quality verifier
    BETA = "agent-beta"    # Domain expert (future)
    GAMMA = "agent-gamma"  # Security specialist (future)


class VerificationCreate(BaseModel):
    """Schema for creating a verification."""
    contribution_id: str
    agent_id: AgentType
    vote: VerificationVote
    score: float = Field(..., ge=0, le=100, description="Score 0-100")
    reasoning: str = Field(..., description="Explanation for the verification decision")
    details: dict = Field(default_factory=dict, description="Additional verification details")


class Verification(BaseModel):
    """Complete verification model."""
    id: str = Field(..., description="Unique verification ID")
    contribution_id: str
    agent_id: AgentType
    vote: VerificationVote
    score: float = Field(..., ge=0, le=100)
    reasoning: str
    details: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "verif_456def",
                "contribution_id": "contrib_123abc",
                "agent_id": "agent-alpha",
                "vote": "approve",
                "score": 85.5,
                "reasoning": "High quality code with good documentation and test coverage",
                "details": {
                    "code_quality": 90,
                    "documentation": 85,
                    "security": 80,
                    "originality": 87
                },
                "created_at": "2025-12-30T00:02:00Z"
            }
        }
