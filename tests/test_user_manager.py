"""Tests for UserManager service and Users API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app import app
from nwu_protocol.services.user_manager import UserManager
from nwu_protocol.models.user import UserCreate

client = TestClient(app)

ADDRESS = "0xABCDEF1234567890abcdef1234567890ABCDef12"
ADDRESS_2 = "0x1234567890ABCDEFabcdef1234567890abcdef56"


# ---------------------------------------------------------------------------
# Unit tests for UserManager
# ---------------------------------------------------------------------------

def test_create_user_manager():
    """UserManager can be instantiated."""
    manager = UserManager()
    assert manager is not None


def test_user_manager_create_user():
    """Creating a user returns a User with generated id."""
    manager = UserManager()
    user = manager.create_user(UserCreate(address=ADDRESS))
    assert user.id.startswith("user_")
    assert user.address == ADDRESS
    assert user.reputation_score == 0.0


def test_user_manager_create_duplicate_raises():
    """Registering the same address twice raises ValueError."""
    manager = UserManager()
    manager.create_user(UserCreate(address=ADDRESS))
    with pytest.raises(ValueError):
        manager.create_user(UserCreate(address=ADDRESS))


def test_user_manager_get_user():
    """get_user returns the user by id."""
    manager = UserManager()
    created = manager.create_user(UserCreate(address=ADDRESS))
    fetched = manager.get_user(created.id)
    assert fetched is not None
    assert fetched.id == created.id


def test_user_manager_get_user_not_found():
    """get_user returns None for unknown id."""
    manager = UserManager()
    assert manager.get_user("user_nonexistent") is None


def test_user_manager_get_user_by_address():
    """get_user_by_address returns the correct user."""
    manager = UserManager()
    created = manager.create_user(UserCreate(address=ADDRESS))
    fetched = manager.get_user_by_address(ADDRESS)
    assert fetched is not None
    assert fetched.id == created.id


def test_user_manager_get_user_by_address_not_found():
    """get_user_by_address returns None for unknown address."""
    manager = UserManager()
    assert manager.get_user_by_address("0xUnknown") is None


def test_user_manager_list_users():
    """list_users returns all registered users."""
    manager = UserManager()
    manager.create_user(UserCreate(address=ADDRESS))
    manager.create_user(UserCreate(address=ADDRESS_2))
    users = manager.list_users()
    assert len(users) == 2


def test_user_manager_list_users_limit():
    """list_users respects the limit parameter."""
    manager = UserManager()
    for i in range(5):
        manager.create_user(UserCreate(address=f"0x{'00' * 19}{i:02x}"))
    users = manager.list_users(limit=3)
    assert len(users) == 3


def test_user_manager_update_reputation():
    """update_reputation changes the user's score."""
    manager = UserManager()
    created = manager.create_user(UserCreate(address=ADDRESS))
    updated = manager.update_reputation(created.id, 4.5)
    assert updated is not None
    assert updated.reputation_score == 4.5


def test_user_manager_update_reputation_clamps_to_zero():
    """update_reputation clamps negative values to 0."""
    manager = UserManager()
    created = manager.create_user(UserCreate(address=ADDRESS))
    updated = manager.update_reputation(created.id, -10.0)
    assert updated.reputation_score == 0.0


def test_user_manager_update_reputation_not_found():
    """update_reputation returns None for unknown user."""
    manager = UserManager()
    assert manager.update_reputation("user_missing", 3.0) is None


def test_user_manager_get_user_stats_no_contributions():
    """get_user_stats with no contributions returns zeroed stats."""
    manager = UserManager()
    created = manager.create_user(UserCreate(address=ADDRESS))
    stats = manager.get_user_stats(created.id, [])
    assert stats is not None
    assert stats.user_id == created.id
    assert stats.contributions_pending == 0
    assert stats.contributions_verified == 0
    assert stats.contributions_rejected == 0
    assert stats.average_quality_score is None
    assert stats.total_rewards == 0.0


def test_user_manager_get_user_stats_not_found():
    """get_user_stats returns None for unknown user."""
    manager = UserManager()
    assert manager.get_user_stats("user_missing", []) is None


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------

def _create_user_via_api(address: str = ADDRESS) -> dict:
    response = client.post("/api/v1/users", json={"address": address})
    assert response.status_code == 201
    return response.json()


def test_api_create_user():
    """POST /api/v1/users creates a user and returns 201."""
    data = _create_user_via_api(f"0x{'aa' * 20}")
    assert data["id"].startswith("user_")
    assert data["address"] == f"0x{'aa' * 20}"


def test_api_create_user_duplicate_returns_409():
    """POST /api/v1/users with duplicate address returns 409."""
    unique_address = f"0x{'bb' * 20}"
    _create_user_via_api(unique_address)
    response = client.post("/api/v1/users", json={"address": unique_address})
    assert response.status_code == 409


def test_api_get_user():
    """GET /api/v1/users/{user_id} returns the user."""
    created = _create_user_via_api(f"0x{'cc' * 20}")
    response = client.get(f"/api/v1/users/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_api_get_user_not_found():
    """GET /api/v1/users/{user_id} returns 404 for unknown user."""
    response = client.get("/api/v1/users/user_notexist")
    assert response.status_code == 404


def test_api_list_users():
    """GET /api/v1/users returns a list."""
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_get_user_by_address():
    """GET /api/v1/users/address/{address} returns the user."""
    unique_address = f"0x{'dd' * 20}"
    created = _create_user_via_api(unique_address)
    response = client.get(f"/api/v1/users/address/{unique_address}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_api_get_user_by_address_not_found():
    """GET /api/v1/users/address/{address} returns 404 for unknown address."""
    response = client.get("/api/v1/users/address/0xUnknownAddress")
    assert response.status_code == 404


def test_api_get_user_stats():
    """GET /api/v1/users/{user_id}/stats returns stats."""
    unique_address = f"0x{'ee' * 20}"
    created = _create_user_via_api(unique_address)
    response = client.get(f"/api/v1/users/{created['id']}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == created["id"]
    assert data["contributions_pending"] == 0
    assert data["contributions_verified"] == 0


def test_api_get_user_stats_not_found():
    """GET /api/v1/users/{user_id}/stats returns 404 for unknown user."""
    response = client.get("/api/v1/users/user_notexist/stats")
    assert response.status_code == 404
