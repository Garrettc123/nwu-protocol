"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import auth_service

client = TestClient(app)


def test_auth_connect():
    """Test wallet connection endpoint."""
    response = client.post(
        "/api/v1/auth/connect",
        json={"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "nonce" in data
    assert "message" in data
    assert data["address"] == "0x742d35cc6634c0532925a3b844bc9e7595f0beb"  # Lowercase


def test_auth_verify_invalid_nonce():
    """Test signature verification with invalid nonce."""
    response = client.post(
        "/api/v1/auth/verify",
        json={
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "signature": "0x1234567890",
            "nonce": "invalid_nonce"
        }
    )
    
    assert response.status_code == 400


def test_generate_nonce_message():
    """Test nonce message generation."""
    address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    nonce = "test_nonce_123"
    
    message = auth_service.generate_nonce_message(address, nonce)
    
    assert address in message
    assert nonce in message
    assert "Sign this message" in message


def test_create_access_token():
    """Test JWT token creation."""
    data = {"sub": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "user_id": 1}
    
    token = auth_service.create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_token():
    """Test JWT token verification."""
    data = {"sub": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "user_id": 1}
    
    token = auth_service.create_access_token(data)
    payload = auth_service.verify_token(token)
    
    assert payload is not None
    assert payload["sub"] == data["sub"]
    assert payload["user_id"] == data["user_id"]


def test_verify_invalid_token():
    """Test verification of invalid token."""
    payload = auth_service.verify_token("invalid_token")
    
    assert payload is None


def test_auth_status_not_authenticated():
    """Test authentication status check for non-authenticated user."""
    response = client.get(
        "/api/v1/auth/status",
        params={"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
