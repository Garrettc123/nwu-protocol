"""Tests for Contribution Manager service."""

import pytest
from nwu_protocol.services.contribution_manager import ContributionManager
from nwu_protocol.models.contribution import (
    ContributionCreate,
    ContributionMetadata,
    ContributionType,
    ContributionStatus,
)


def test_create_contribution():
    """Test creating a contribution."""
    manager = ContributionManager()
    
    metadata = ContributionMetadata(
        title="Test Contribution",
        description="A test contribution",
        tags=["test"],
        language="python"
    )
    
    contribution_data = ContributionCreate(
        file_type=ContributionType.CODE,
        metadata=metadata,
        content_hash="abc123"
    )
    
    contribution = manager.create_contribution("0x123", contribution_data)
    
    assert contribution.id.startswith("contrib_")
    assert contribution.submitter == "0x123"
    assert contribution.status == ContributionStatus.PENDING
    assert contribution.metadata.title == "Test Contribution"


def test_get_contribution():
    """Test retrieving a contribution."""
    manager = ContributionManager()
    
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
    
    created = manager.create_contribution("0x123", contribution_data)
    retrieved = manager.get_contribution(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.submitter == "0x123"


def test_list_contributions():
    """Test listing contributions."""
    manager = ContributionManager()
    
    for i in range(3):
        metadata = ContributionMetadata(
            title=f"Test {i}",
            description="Test",
            tags=[]
        )
        contribution_data = ContributionCreate(
            file_type=ContributionType.CODE,
            metadata=metadata,
            content_hash=f"hash{i}"
        )
        manager.create_contribution("0x123", contribution_data)
    
    contributions = manager.list_contributions()
    assert len(contributions) == 3


def test_update_contribution_status():
    """Test updating contribution status."""
    manager = ContributionManager()
    
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
    updated = manager.update_contribution_status(contribution.id, ContributionStatus.VERIFIED)
    
    assert updated is not None
    assert updated.status == ContributionStatus.VERIFIED


def test_compute_content_hash():
    """Test content hashing."""
    content = b"Hello, World!"
    hash_value = ContributionManager.compute_content_hash(content)
    
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA-256 produces 64 hex characters
    assert hash_value == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
