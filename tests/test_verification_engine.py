"""Tests for Verification Engine service."""

import pytest
from nwu_protocol.services.verification_engine import VerificationEngine
from nwu_protocol.services.contribution_manager import ContributionManager
from nwu_protocol.models.verification import (
    VerificationCreate,
    VerificationVote,
    AgentType,
)
from nwu_protocol.models.contribution import (
    ContributionCreate,
    ContributionMetadata,
    ContributionType,
)


def test_submit_verification():
    """Test submitting a verification."""
    manager = ContributionManager()
    engine = VerificationEngine(manager)
    
    # Create a contribution first
    metadata = ContributionMetadata(
        title="Test",
        description="Test",
        tags=[]
    )
    contribution_data = ContributionCreate(
        file_type=ContributionType.CODE,
        metadata=metadata,
        content_hash="hash123"
    )
    contribution = manager.create_contribution("0x123", contribution_data)
    
    # Submit verification
    verification_data = VerificationCreate(
        contribution_id=contribution.id,
        agent_id=AgentType.ALPHA,
        vote=VerificationVote.APPROVE,
        score=85.0,
        reasoning="Good quality code"
    )
    
    verification = engine.submit_verification(verification_data)
    
    assert verification.id.startswith("verif_")
    assert verification.contribution_id == contribution.id
    assert verification.vote == VerificationVote.APPROVE
    assert verification.score == 85.0


def test_calculate_consensus():
    """Test consensus calculation."""
    manager = ContributionManager()
    engine = VerificationEngine(manager)
    
    # Create a contribution
    metadata = ContributionMetadata(
        title="Test",
        description="Test",
        tags=[]
    )
    contribution_data = ContributionCreate(
        file_type=ContributionType.CODE,
        metadata=metadata,
        content_hash="hash123"
    )
    contribution = manager.create_contribution("0x123", contribution_data)
    
    # Submit verification with approval
    verification_data = VerificationCreate(
        contribution_id=contribution.id,
        agent_id=AgentType.ALPHA,
        vote=VerificationVote.APPROVE,
        score=85.0,
        reasoning="Good quality"
    )
    engine.submit_verification(verification_data)
    
    consensus = engine.calculate_consensus(contribution.id)
    
    assert consensus["total_verifications"] == 1
    assert consensus["approval_rate"] == 1.0
    assert consensus["average_score"] == 85.0
    assert consensus["consensus_reached"] is True


def test_consensus_updates_contribution():
    """Test that reaching consensus updates contribution status."""
    manager = ContributionManager()
    engine = VerificationEngine(manager)
    
    # Create a contribution
    metadata = ContributionMetadata(
        title="Test",
        description="Test",
        tags=[]
    )
    contribution_data = ContributionCreate(
        file_type=ContributionType.CODE,
        metadata=metadata,
        content_hash="hash123"
    )
    contribution = manager.create_contribution("0x123", contribution_data)
    
    # Submit verification
    verification_data = VerificationCreate(
        contribution_id=contribution.id,
        agent_id=AgentType.ALPHA,
        vote=VerificationVote.APPROVE,
        score=90.0,
        reasoning="Excellent"
    )
    engine.submit_verification(verification_data)
    
    # Check that contribution was updated
    updated_contribution = manager.get_contribution(contribution.id)
    assert updated_contribution.status.value == "verified"
    assert updated_contribution.quality_score == 90.0
