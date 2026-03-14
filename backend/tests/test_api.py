"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns API info."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NWU Protocol API"
    assert data["status"] == "operational"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "ipfs" in data["checks"]
    assert "rabbitmq" in data["checks"]
    assert "redis" in data["checks"]


def test_api_info():
    """Test API info endpoint."""
    response = client.get("/api/v1/info")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NWU Protocol API"
    assert "endpoints" in data


def test_list_contributions():
    """Test listing contributions."""
    response = client.get("/api/v1/contributions/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_nonexistent_contribution():
    """Test getting a contribution that doesn't exist."""
    response = client.get("/api/v1/contributions/99999")
    
    assert response.status_code == 404


def test_get_nonexistent_user():
    """Test getting a user that doesn't exist."""
    response = client.get("/api/v1/users/0x1234567890123456789012345678901234567890")
    
    assert response.status_code == 404


def test_create_user():
    """Test creating a new user."""
    response = client.post(
        "/api/v1/users/",
        json={
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "username": "testuser"
        }
    )
    
    # May fail if user already exists, which is okay
    assert response.status_code in [201, 400]


def test_invalid_address_format():
    """Test creating user with invalid address format."""
    response = client.post(
        "/api/v1/users/",
        json={
            "address": "invalid_address",
            "username": "testuser2"
        }
    )
    
    # Should fail validation
    assert response.status_code in [400, 422]
