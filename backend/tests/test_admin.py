"""Tests for admin revenue dashboard endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch
from app.main import app
from app.models import Base, User as UserModel
from app.database import get_db
from app.api.admin import get_current_admin_user
from app.services import auth_service

# ---------------------------------------------------------------------------
# SQLite test database setup
# ---------------------------------------------------------------------------

from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# SQLite test database setup
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables once
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Mock admin user returned by dependency overrides
_mock_admin_user = MagicMock(spec=UserModel)
_mock_admin_user.address = "0xadmin0000000000000000000000000000000001"
_mock_admin_user.id = 1


def override_get_current_admin_user():
    return _mock_admin_user


# Apply dependency overrides
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

client = TestClient(app)

# A fake non-admin Ethereum address used for auth tests
NON_ADMIN_ADDRESS = "0x1111111111111111111111111111111111111111"
ADMIN_ADDRESS = "0xadmin0000000000000000000000000000000001"


def _make_token(address: str) -> str:
    """Create a JWT token for the given Ethereum address."""
    return auth_service.create_access_token({"sub": address, "user_id": 999})


def _auth_header(address: str) -> dict:
    return {"Authorization": f"Bearer {_make_token(address)}"}


# ---------------------------------------------------------------------------
# Tests: unauthenticated / forbidden access (use a fresh client without overrides)
# ---------------------------------------------------------------------------

def test_revenue_summary_requires_auth():
    """GET /admin/revenue/summary must return 401 without valid JWT."""
    # Use a plain client with no dependency overrides for this test
    from fastapi.testclient import TestClient as _TestClient

    plain_app_client = _TestClient(app, raise_server_exceptions=False)
    # Remove admin override temporarily
    del app.dependency_overrides[get_current_admin_user]
    try:
        response = plain_app_client.get("/api/v1/admin/revenue/summary")
        assert response.status_code == 401
    finally:
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user


def test_revenue_summary_forbidden_for_non_admin():
    """Non-admin authenticated user should receive 403."""
    # Temporarily restore the real admin check but keep DB override
    del app.dependency_overrides[get_current_admin_user]
    try:
        with patch("app.api.admin.settings.admin_addresses", ADMIN_ADDRESS.lower()):
            # Use a different mock user (non-admin address) for get_current_user
            mock_non_admin = MagicMock(spec=UserModel)
            mock_non_admin.address = NON_ADMIN_ADDRESS.lower()
            mock_non_admin.id = 2
            from app.api.payments import get_current_user
            app.dependency_overrides[get_current_user] = lambda: mock_non_admin
            try:
                response = client.get(
                    "/api/v1/admin/revenue/summary",
                    headers=_auth_header(NON_ADMIN_ADDRESS),
                )
                assert response.status_code == 403
            finally:
                del app.dependency_overrides[get_current_user]
    finally:
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user


# ---------------------------------------------------------------------------
# Tests: revenue summary
# ---------------------------------------------------------------------------

def test_revenue_summary_returns_expected_keys():
    """Admin revenue summary should return all required metric keys."""
    response = client.get("/api/v1/admin/revenue/summary")
    assert response.status_code == 200
    data = response.json()
    assert "mrr" in data
    assert "arr" in data
    assert "revenue_this_month" in data
    assert "churn_rate" in data
    assert "active_subscriptions" in data


def test_revenue_summary_numeric_values():
    """Admin revenue summary values should be non-negative numbers."""
    response = client.get("/api/v1/admin/revenue/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["mrr"] >= 0
    assert data["arr"] >= 0
    assert data["revenue_this_month"] >= 0
    assert 0.0 <= data["churn_rate"] <= 100.0
    assert data["active_subscriptions"] >= 0


# ---------------------------------------------------------------------------
# Tests: daily revenue
# ---------------------------------------------------------------------------

def test_daily_revenue_structure():
    """GET /admin/revenue/daily should return a 'daily' array of date/amount objects."""
    response = client.get("/api/v1/admin/revenue/daily")
    assert response.status_code == 200
    data = response.json()
    assert "daily" in data
    assert isinstance(data["daily"], list)
    # Should cover exactly 90 entries (days 89 down to today)
    assert len(data["daily"]) == 90
    first = data["daily"][0]
    assert "date" in first
    assert "amount" in first


# ---------------------------------------------------------------------------
# Tests: user stats
# ---------------------------------------------------------------------------

def test_user_stats_keys():
    """GET /admin/users/stats should return user count metrics."""
    response = client.get("/api/v1/admin/users/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "active_users_30d" in data
    assert "new_users_this_week" in data
    assert data["total_users"] >= 0


# ---------------------------------------------------------------------------
# Tests: API key stats
# ---------------------------------------------------------------------------

def test_api_key_stats_keys():
    """GET /admin/api-keys/stats should return call count metrics."""
    response = client.get("/api/v1/admin/api-keys/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_calls_today" in data
    assert "total_calls_this_month" in data
    assert "top_consumers" in data
    assert isinstance(data["top_consumers"], list)


# ---------------------------------------------------------------------------
# Tests: staking stats
# ---------------------------------------------------------------------------

def test_staking_stats_keys():
    """GET /admin/staking/stats should return staking metric keys."""
    response = client.get("/api/v1/admin/staking/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_nwu_staked" in data
    assert "yield_distributed" in data
    assert "staking_participation_rate" in data

