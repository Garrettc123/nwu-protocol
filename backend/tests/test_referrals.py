"""Tests for the referral (customer acquisition) endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base, User, Referral
from app.database import get_db

TEST_DATABASE_URL = "sqlite:///./test_referrals.db"

_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


ADDRESS_A = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
ADDRESS_B = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
ADDRESS_C = "0xcccccccccccccccccccccccccccccccccccccccc"


def _create_user(db, address: str) -> User:
    user = User(address=address.lower())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# get_referral_code
# ---------------------------------------------------------------------------

def test_get_referral_code_returns_code(client, db):
    """Getting a referral code for an existing user returns a code."""
    _create_user(db, ADDRESS_A)
    response = client.get(f"/api/v1/referrals/code/{ADDRESS_A}")
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == ADDRESS_A.lower()
    assert "referral_code" in data
    assert len(data["referral_code"]) == 10
    assert "referral_url" in data


def test_get_referral_code_idempotent(client, db):
    """Calling get_referral_code twice returns the same code."""
    _create_user(db, ADDRESS_A)
    r1 = client.get(f"/api/v1/referrals/code/{ADDRESS_A}")
    r2 = client.get(f"/api/v1/referrals/code/{ADDRESS_A}")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["referral_code"] == r2.json()["referral_code"]


def test_get_referral_code_user_not_found(client):
    """404 is returned for an unknown user."""
    response = client.get(f"/api/v1/referrals/code/{ADDRESS_A}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# get_referral_stats
# ---------------------------------------------------------------------------

def test_get_referral_stats_no_referrals(client, db):
    """Stats endpoint returns zeroes when no referrals have been made."""
    _create_user(db, ADDRESS_A)
    response = client.get(f"/api/v1/referrals/stats/{ADDRESS_A}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_referrals"] == 0
    assert data["completed_referrals"] == 0
    assert data["pending_referrals"] == 0
    assert data["total_reputation_earned"] == 0


def test_get_referral_stats_after_completed_referral(client, db):
    """Stats reflect completed referrals and accumulated reputation."""
    user_a = _create_user(db, ADDRESS_A)
    user_b = _create_user(db, ADDRESS_B)

    # Simulate a completed referral
    referral = Referral(referrer_id=user_a.id, referee_id=user_b.id, status="completed", reward_granted=True)
    db.add(referral)
    db.commit()

    response = client.get(f"/api/v1/referrals/stats/{ADDRESS_A}")
    assert response.status_code == 200
    data = response.json()
    assert data["completed_referrals"] == 1
    assert data["total_reputation_earned"] == 10.0


def test_get_referral_stats_user_not_found(client):
    """404 is returned for an unknown user."""
    response = client.get(f"/api/v1/referrals/stats/{ADDRESS_A}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# apply_referral_code
# ---------------------------------------------------------------------------

def test_apply_referral_code_success(client, db):
    """A valid referral code can be applied by a new user."""
    user_a = _create_user(db, ADDRESS_A)
    _create_user(db, ADDRESS_B)

    # Generate code for user A
    r = client.get(f"/api/v1/referrals/code/{ADDRESS_A}")
    code = r.json()["referral_code"]

    response = client.post(
        "/api/v1/referrals/apply",
        params={"address": ADDRESS_B, "referral_code": code},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["referee_address"] == ADDRESS_B.lower()
    assert data["referrer_address"] == ADDRESS_A.lower()
    assert data["referee_reputation_bonus"] == 5.0
    assert data["referrer_reputation_bonus"] == 10.0


def test_apply_referral_code_grants_reputation(client, db):
    """Applying a referral code increases reputation for both users."""
    user_a = _create_user(db, ADDRESS_A)
    user_b = _create_user(db, ADDRESS_B)

    r = client.get(f"/api/v1/referrals/code/{ADDRESS_A}")
    code = r.json()["referral_code"]

    client.post(
        "/api/v1/referrals/apply",
        params={"address": ADDRESS_B, "referral_code": code},
    )

    db.refresh(user_a)
    db.refresh(user_b)
    assert user_a.reputation_score == 10.0
    assert user_b.reputation_score == 5.0


def test_apply_referral_code_cannot_use_own_code(client, db):
    """A user cannot apply their own referral code."""
    _create_user(db, ADDRESS_A)

    r = client.get(f"/api/v1/referrals/code/{ADDRESS_A}")
    code = r.json()["referral_code"]

    response = client.post(
        "/api/v1/referrals/apply",
        params={"address": ADDRESS_A, "referral_code": code},
    )
    assert response.status_code == 400


def test_apply_referral_code_invalid_code(client, db):
    """404 is returned for a non-existent referral code."""
    _create_user(db, ADDRESS_B)
    response = client.post(
        "/api/v1/referrals/apply",
        params={"address": ADDRESS_B, "referral_code": "INVALIDCODE"},
    )
    assert response.status_code == 404


def test_apply_referral_code_duplicate(client, db):
    """A user cannot apply a referral code twice."""
    _create_user(db, ADDRESS_A)
    _create_user(db, ADDRESS_B)

    r = client.get(f"/api/v1/referrals/code/{ADDRESS_A}")
    code = r.json()["referral_code"]

    client.post(
        "/api/v1/referrals/apply",
        params={"address": ADDRESS_B, "referral_code": code},
    )

    # Second attempt with a different code (but same referee) should conflict
    _create_user(db, ADDRESS_C)
    r2 = client.get(f"/api/v1/referrals/code/{ADDRESS_C}")
    code2 = r2.json()["referral_code"]

    response = client.post(
        "/api/v1/referrals/apply",
        params={"address": ADDRESS_B, "referral_code": code2},
    )
    assert response.status_code == 409


def test_apply_referral_code_referee_not_found(client, db):
    """404 is returned when the referee address is unknown."""
    response = client.post(
        "/api/v1/referrals/apply",
        params={"address": ADDRESS_B, "referral_code": "SOMECODE1"},
    )
    assert response.status_code == 404
