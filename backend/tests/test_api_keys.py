"""Tests for API key management and usage metering system."""

import hashlib
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import (
    APIKey,
    APIKeyUsage,
    Base,
    SubscriptionTier,
    User,
    FREE_TIER_DAILY_LIMIT,
    PRO_TIER_DAILY_LIMIT,
    ENTERPRISE_TIER_DAILY_LIMIT,
    FREE_TIER_MONTHLY_QUOTA,
    PRO_TIER_MONTHLY_QUOTA,
)
from app.database import get_db

# ---------------------------------------------------------------------------
# Test database setup
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///./test_api_keys.db"


@pytest.fixture(scope="module")
def db_engine():
    """Create a test-only SQLite engine with all tables."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(db_engine):
    """Provide a clean transactional session that rolls back after each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    """
    TestClient that overrides the ``get_db`` dependency with the isolated
    test session so we can inspect the DB from both the app and the test.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(db, suffix="a") -> User:
    """Create and persist a test user."""
    address = f"0x{'0' * (39 - len(suffix))}{suffix}"
    user = User(address=address)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_api_key(db, user: User, tier: SubscriptionTier = SubscriptionTier.FREE) -> tuple[APIKey, str]:
    """
    Create an APIKey record directly in the DB (bypasses hashing for speed)
    and return ``(record, raw_key_prefix)``.
    """
    from app.services.payment_service import payment_service as ps
    raw_key = ps.generate_api_key()
    key_hash = ps.hash_api_key(raw_key)
    prefix = raw_key[:12]

    from app.models import TIER_DAILY_LIMITS, TIER_MONTHLY_QUOTAS
    daily = TIER_DAILY_LIMITS.get(tier.value, FREE_TIER_DAILY_LIMIT)
    monthly = TIER_MONTHLY_QUOTAS.get(tier.value, FREE_TIER_MONTHLY_QUOTA)

    api_key = APIKey(
        user_id=user.id,
        key_hash=key_hash,
        name="test-key",
        prefix=prefix,
        tier=tier,
        rate_limit_per_day=daily,
        monthly_quota=monthly,
        expires_at=datetime.utcnow() + timedelta(days=365),
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key, raw_key


def _jwt_for_user(user: User) -> str:
    """Generate a real JWT token for a test user."""
    from app.services.auth_service import auth_service
    token_data = {"sub": user.address, "user_id": user.id}
    return auth_service.create_access_token(token_data)


# ---------------------------------------------------------------------------
# 1. Model – APIKeyUsage creation
# ---------------------------------------------------------------------------

def test_api_key_usage_model_creation(db_session):
    """APIKeyUsage records can be created and linked to an APIKey."""
    user = _make_user(db_session, suffix="b")
    api_key, _ = _make_api_key(db_session, user)

    usage = APIKeyUsage(
        api_key_id=api_key.id,
        usage_date=date.today(),
        request_count=42,
    )
    db_session.add(usage)
    db_session.commit()
    db_session.refresh(usage)

    assert usage.id is not None
    assert usage.request_count == 42
    assert usage.api_key_id == api_key.id


# ---------------------------------------------------------------------------
# 2. Model – Tier rate limits are stored on APIKey
# ---------------------------------------------------------------------------

def test_api_key_stores_tier_limits(db_session):
    """APIKey records carry the correct rate_limit_per_day and monthly_quota."""
    user = _make_user(db_session, suffix="c")
    free_key, _ = _make_api_key(db_session, user, SubscriptionTier.FREE)
    pro_key, _ = _make_api_key(db_session, user, SubscriptionTier.PRO)
    ent_key, _ = _make_api_key(db_session, user, SubscriptionTier.ENTERPRISE)

    assert free_key.rate_limit_per_day == FREE_TIER_DAILY_LIMIT
    assert pro_key.rate_limit_per_day == PRO_TIER_DAILY_LIMIT
    assert ent_key.rate_limit_per_day == ENTERPRISE_TIER_DAILY_LIMIT


# ---------------------------------------------------------------------------
# 3. Endpoint – POST /api/v1/api-keys/create (free tier)
# ---------------------------------------------------------------------------

def test_create_free_api_key_endpoint(client, db_session):
    """POST /api/v1/api-keys/create returns 201 and includes the raw key."""
    user = _make_user(db_session, suffix="d")
    token = _jwt_for_user(user)

    response = client.post(
        "/api/v1/api-keys/create",
        json={"name": "my-free-key", "tier": "free"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert "key" in data
    assert data["tier"] == "free"
    assert data["rate_limit_per_day"] == FREE_TIER_DAILY_LIMIT
    assert data["monthly_quota"] == FREE_TIER_MONTHLY_QUOTA
    assert data["is_active"] is True


# ---------------------------------------------------------------------------
# 4. Endpoint – GET /api/v1/api-keys/list
# ---------------------------------------------------------------------------

def test_list_api_keys_endpoint(client, db_session):
    """GET /api/v1/api-keys/list returns all keys owned by the user."""
    user = _make_user(db_session, suffix="e")
    _make_api_key(db_session, user, SubscriptionTier.FREE)
    _make_api_key(db_session, user, SubscriptionTier.FREE)
    token = _jwt_for_user(user)

    response = client.get(
        "/api/v1/api-keys/list",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "keys" in data
    assert len(data["keys"]) >= 2


# ---------------------------------------------------------------------------
# 5. Endpoint – DELETE /api/v1/api-keys/{key_id}
# ---------------------------------------------------------------------------

def test_revoke_api_key_endpoint(client, db_session):
    """DELETE /api/v1/api-keys/{key_id} marks the key as inactive."""
    user = _make_user(db_session, suffix="f")
    api_key, _ = _make_api_key(db_session, user)
    token = _jwt_for_user(user)

    response = client.delete(
        f"/api/v1/api-keys/{api_key.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    db_session.refresh(api_key)
    assert api_key.is_active is False


def test_revoke_nonexistent_key_returns_404(client, db_session):
    """DELETE /api/v1/api-keys/{key_id} returns 404 for unknown key."""
    user = _make_user(db_session, suffix="g")
    token = _jwt_for_user(user)

    response = client.delete(
        "/api/v1/api-keys/99999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 6. Endpoint – GET /api/v1/api-keys/usage/{key_id}
# ---------------------------------------------------------------------------

def test_usage_endpoint_no_requests(client, db_session):
    """GET /api/v1/api-keys/usage returns zeros when the key has not been used."""
    user = _make_user(db_session, suffix="h")
    api_key, _ = _make_api_key(db_session, user)
    token = _jwt_for_user(user)

    response = client.get(
        f"/api/v1/api-keys/usage/{api_key.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["requests_today"] == 0
    assert data["requests_this_month"] == 0
    assert data["daily_limit"] == FREE_TIER_DAILY_LIMIT
    assert data["quota_remaining_today"] == FREE_TIER_DAILY_LIMIT


def test_usage_endpoint_counts_existing_records(client, db_session):
    """GET /api/v1/api-keys/usage reflects pre-existing usage records."""
    user = _make_user(db_session, suffix="i")
    api_key, _ = _make_api_key(db_session, user)
    token = _jwt_for_user(user)

    # Seed a usage record for today
    usage = APIKeyUsage(
        api_key_id=api_key.id,
        usage_date=date.today(),
        request_count=17,
    )
    db_session.add(usage)
    db_session.commit()

    response = client.get(
        f"/api/v1/api-keys/usage/{api_key.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["requests_today"] == 17
    assert data["quota_remaining_today"] == FREE_TIER_DAILY_LIMIT - 17


# ---------------------------------------------------------------------------
# 7. Middleware – valid API key passes through
# ---------------------------------------------------------------------------

def test_middleware_allows_valid_api_key(db_session):
    """A request with a valid X-API-Key header reaches the endpoint."""
    user = _make_user(db_session, suffix="j")
    _, raw_key = _make_api_key(db_session, user)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch(
        "app.middleware.api_key_auth.SessionLocal",
        return_value=db_session,
    ):
        # Prevent the middleware from closing the shared test session
        db_session.close = lambda: None  # type: ignore[method-assign]
        test_client = TestClient(app, raise_server_exceptions=False)
        response = test_client.get("/", headers={"X-API-Key": raw_key})

    app.dependency_overrides.clear()
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 8. Middleware – invalid API key is rejected
# ---------------------------------------------------------------------------

def test_middleware_rejects_invalid_api_key(db_session):
    """A request with a bogus X-API-Key header receives HTTP 401."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch(
        "app.middleware.api_key_auth.SessionLocal",
        return_value=db_session,
    ):
        db_session.close = lambda: None  # type: ignore[method-assign]
        test_client = TestClient(app, raise_server_exceptions=False)
        response = test_client.get("/", headers={"X-API-Key": "nwu_invalid_key_xyz"})

    app.dependency_overrides.clear()
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 9. Middleware – quota enforcement blocks requests when limit reached
# ---------------------------------------------------------------------------

def test_middleware_enforces_daily_quota(db_session):
    """Once the daily quota is exhausted, the middleware returns HTTP 429."""
    user = _make_user(db_session, suffix="k")
    api_key, raw_key = _make_api_key(db_session, user, SubscriptionTier.FREE)

    # Pre-fill the usage to exactly the daily limit
    usage = APIKeyUsage(
        api_key_id=api_key.id,
        usage_date=date.today(),
        request_count=FREE_TIER_DAILY_LIMIT,
    )
    db_session.add(usage)
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch(
        "app.middleware.api_key_auth.SessionLocal",
        return_value=db_session,
    ):
        db_session.close = lambda: None  # type: ignore[method-assign]
        test_client = TestClient(app, raise_server_exceptions=False)
        response = test_client.get("/", headers={"X-API-Key": raw_key})

    app.dependency_overrides.clear()
    assert response.status_code == 429


# ---------------------------------------------------------------------------
# 10. Middleware – enterprise tier is never quota-blocked
# ---------------------------------------------------------------------------

def test_middleware_enterprise_unlimited(db_session):
    """Enterprise keys bypass the daily quota check entirely."""
    user = _make_user(db_session, suffix="l")
    api_key, raw_key = _make_api_key(db_session, user, SubscriptionTier.ENTERPRISE)

    # Pre-fill an astronomically high usage count
    usage = APIKeyUsage(
        api_key_id=api_key.id,
        usage_date=date.today(),
        request_count=10_000_000,
    )
    db_session.add(usage)
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch(
        "app.middleware.api_key_auth.SessionLocal",
        return_value=db_session,
    ):
        db_session.close = lambda: None  # type: ignore[method-assign]
        test_client = TestClient(app, raise_server_exceptions=False)
        response = test_client.get("/", headers={"X-API-Key": raw_key})

    app.dependency_overrides.clear()
    # Should NOT be rate-limited
    assert response.status_code != 429
