"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app import app
from nwu_protocol.models.contribution import ContributionType

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns health information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "NWU Protocol API"
    assert "docs" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_api_status():
    """Test API status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "timestamp" in data


def test_api_info():
    """Test API info endpoint."""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NWU Protocol"
    assert "endpoints" in data


def test_create_contribution():
    """Test creating a contribution via API."""
    contribution_data = {
        "file_type": "code",
        "metadata": {
            "title": "Test Contribution",
            "description": "A test contribution",
            "tags": ["test"],
            "language": "python"
        },
        "content_hash": "abc123def456",
        "ipfs_hash": "QmTest123"
    }
    
    response = client.post(
        "/api/v1/contributions",
        json=contribution_data,
        params={"submitter": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("contrib_")
    assert data["submitter"] == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    assert data["file_type"] == "code"
    assert data["status"] == "pending"
    
    return data["id"]


def test_get_contribution():
    """Test retrieving a contribution via API."""
    # First create a contribution
    contribution_id = test_create_contribution()
    
    # Then retrieve it
    response = client.get(f"/api/v1/contributions/{contribution_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contribution_id


def test_get_nonexistent_contribution():
    """Test retrieving a non-existent contribution returns 404."""
    response = client.get("/api/v1/contributions/nonexistent_id")
    assert response.status_code == 404


def test_get_contribution_status():
    """Test getting contribution status via API."""
    contribution_id = test_create_contribution()
    
    response = client.get(f"/api/v1/contributions/{contribution_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["contribution_id"] == contribution_id
    assert data["status"] == "pending"


def test_list_contributions():
    """Test listing contributions via API."""
    response = client.get("/api/v1/contributions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_submit_verification():
    """Test submitting a verification via API."""
    # First create a contribution
    contribution_id = test_create_contribution()
    
    # Submit verification
    verification_data = {
        "contribution_id": contribution_id,
        "agent_id": "agent-alpha",
        "vote": "approve",
        "score": 85.0,
        "reasoning": "High quality code with good documentation",
        "details": {
            "code_quality": 90,
            "documentation": 85
        }
    }
    
    response = client.post("/api/v1/verifications", json=verification_data)
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("verif_")
    assert data["contribution_id"] == contribution_id
    assert data["vote"] == "approve"


def test_get_contribution_verifications():
    """Test getting verifications for a contribution."""
    # Create contribution and submit verification
    contribution_id = test_create_contribution()
    
    verification_data = {
        "contribution_id": contribution_id,
        "agent_id": "agent-alpha",
        "vote": "approve",
        "score": 85.0,
        "reasoning": "Good quality"
    }
    client.post("/api/v1/verifications", json=verification_data)
    
    # Get verifications
    response = client.get(f"/api/v1/verifications/contribution/{contribution_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_get_consensus():
    """Test getting consensus for a contribution."""
    # Create contribution and submit verification
    contribution_id = test_create_contribution()
    
    verification_data = {
        "contribution_id": contribution_id,
        "agent_id": "agent-alpha",
        "vote": "approve",
        "score": 90.0,
        "reasoning": "Excellent quality"
    }
    client.post("/api/v1/verifications", json=verification_data)
    
    # Get consensus
    response = client.get(f"/api/v1/verifications/contribution/{contribution_id}/consensus")
    assert response.status_code == 200
    data = response.json()
    assert data["contribution_id"] == contribution_id
    assert data["consensus_reached"] is True
    assert data["average_score"] == 90.0
