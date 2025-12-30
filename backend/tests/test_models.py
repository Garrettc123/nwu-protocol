"""Tests for database models."""

import pytest
from datetime import datetime
from app.models import User, Contribution, Verification, Reward


def test_create_user(db_session):
    """Test user creation."""
    user = User(
        address="0x1234567890123456789012345678901234567890",
        username="testuser",
        email="test@example.com"
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.address == "0x1234567890123456789012345678901234567890"
    assert user.reputation_score == 0.0
    assert user.total_contributions == 0


def test_create_contribution(db_session):
    """Test contribution creation."""
    user = User(address="0x" + "1" * 40)
    db_session.add(user)
    db_session.commit()
    
    contribution = Contribution(
        user_id=user.id,
        ipfs_hash="QmTest1234567890",
        file_name="test.py",
        file_type="code",
        file_size=1024,
        title="Test Contribution",
        description="A test contribution"
    )
    db_session.add(contribution)
    db_session.commit()
    
    assert contribution.id is not None
    assert contribution.status == "pending"
    assert contribution.verification_count == 0


def test_create_verification(db_session):
    """Test verification creation."""
    user = User(address="0x" + "1" * 40)
    db_session.add(user)
    db_session.commit()
    
    contribution = Contribution(
        user_id=user.id,
        ipfs_hash="QmTest",
        file_name="test.py",
        file_type="code",
        file_size=1024,
        title="Test",
    )
    db_session.add(contribution)
    db_session.commit()
    
    verification = Verification(
        contribution_id=contribution.id,
        agent_id="agent-test-001",
        agent_type="alpha",
        vote_score=85.0,
        quality_score=80.0,
        reasoning="Good code quality"
    )
    db_session.add(verification)
    db_session.commit()
    
    assert verification.id is not None
    assert verification.vote_score == 85.0


def test_create_reward(db_session):
    """Test reward creation."""
    user = User(address="0x" + "1" * 40)
    db_session.add(user)
    db_session.commit()
    
    contribution = Contribution(
        user_id=user.id,
        ipfs_hash="QmTest",
        file_name="test.py",
        file_type="code",
        file_size=1024,
        title="Test",
    )
    db_session.add(contribution)
    db_session.commit()
    
    reward = Reward(
        user_id=user.id,
        contribution_id=contribution.id,
        amount=100.0,
        status="pending"
    )
    db_session.add(reward)
    db_session.commit()
    
    assert reward.id is not None
    assert reward.amount == 100.0
    assert reward.status == "pending"
