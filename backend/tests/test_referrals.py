"""Tests for the referral (customer acquisition) endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base, User, Referral, ReferralCode, ReferralEvent, NWU_REWARD_PER_REFERRAL, AFFILIATE_REFERRAL_THRESHOLD
from app.database import get_db
from app.services.auth_service import auth_service

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


def _make_token(address: str) -> str:
    """Return a valid JWT for the given address."""
    return auth_service.create_access_token({"sub": address.lower(), "type": "access"})


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


# ---------------------------------------------------------------------------
# POST /generate  (JWT-authenticated affiliate programme)
# ---------------------------------------------------------------------------

def test_generate_code_returns_code(client, db):
    """POST /generate creates a ReferralCode and returns the code."""
    _create_user(db, ADDRESS_A)
    token = _make_token(ADDRESS_A)
    response = client.post(
        "/api/v1/referrals/generate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "referral_code" in data
    assert len(data["referral_code"]) == 10
    assert "referral_url" in data
    assert "is_affiliate" in data


def test_generate_code_idempotent(client, db):
    """Calling POST /generate twice returns the same code."""
    _create_user(db, ADDRESS_A)
    token = _make_token(ADDRESS_A)
    r1 = client.post("/api/v1/referrals/generate", headers={"Authorization": f"Bearer {token}"})
    r2 = client.post("/api/v1/referrals/generate", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["referral_code"] == r2.json()["referral_code"]


def test_generate_code_requires_auth(client, db):
    """POST /generate returns 401 when no token is provided."""
    _create_user(db, ADDRESS_A)
    response = client.post("/api/v1/referrals/generate")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /stats  (JWT-authenticated)
# ---------------------------------------------------------------------------

def test_stats_returns_nwu_fields(client, db):
    """GET /stats returns NWU reward fields for an authenticated user."""
    _create_user(db, ADDRESS_A)
    token = _make_token(ADDRESS_A)
    response = client.get(
        "/api/v1/referrals/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_nwu_earned" in data
    assert "pending_rewards" in data
    assert "is_affiliate" in data
    assert "revenue_share_percent" in data
    assert data["total_nwu_earned"] == 0.0
    assert data["pending_rewards"] == 0.0
    assert data["is_affiliate"] is False


def test_stats_reflects_pending_rewards(client, db):
    """GET /stats shows accumulated NWU pending after a referral event."""
    user_a = _create_user(db, ADDRESS_A)
    token_a = _make_token(ADDRESS_A)

    # Generate a ReferralCode for user A
    client.post("/api/v1/referrals/generate", headers={"Authorization": f"Bearer {token_a}"})

    # Fetch the code
    code_record = db.query(ReferralCode).filter(ReferralCode.referrer_id == user_a.id).first()
    assert code_record is not None

    # Simulate a signup event
    _create_user(db, ADDRESS_B)
    event = ReferralEvent(
        referral_code_id=code_record.id,
        referee_id=db.query(User).filter(User.address == ADDRESS_B.lower()).first().id,
        event_type="signup",
        nwu_reward=NWU_REWARD_PER_REFERRAL,
        status="pending",
    )
    db.add(event)
    db.commit()

    response = client.get(
        "/api/v1/referrals/stats",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pending_rewards"] == NWU_REWARD_PER_REFERRAL
    assert data["total_conversions"] == 1


def test_stats_requires_auth(client, db):
    """GET /stats returns 401 when no token is provided."""
    response = client.get("/api/v1/referrals/stats")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /claim
# ---------------------------------------------------------------------------

def test_claim_no_rewards(client, db):
    """POST /claim returns 200 with zero amount when there are no pending rewards."""
    _create_user(db, ADDRESS_A)
    token = _make_token(ADDRESS_A)
    response = client.post(
        "/api/v1/referrals/claim",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nwu_claimed"] == 0.0


def test_claim_pending_rewards(client, db):
    """POST /claim transfers pending NWU rewards to claimed balance."""
    user_a = _create_user(db, ADDRESS_A)
    token_a = _make_token(ADDRESS_A)

    # Generate code and add a pending event
    client.post("/api/v1/referrals/generate", headers={"Authorization": f"Bearer {token_a}"})
    code_record = db.query(ReferralCode).filter(ReferralCode.referrer_id == user_a.id).first()
    _create_user(db, ADDRESS_B)
    referee_b = db.query(User).filter(User.address == ADDRESS_B.lower()).first()
    event = ReferralEvent(
        referral_code_id=code_record.id,
        referee_id=referee_b.id,
        event_type="signup",
        nwu_reward=NWU_REWARD_PER_REFERRAL,
        status="pending",
    )
    db.add(event)
    db.commit()

    response = client.post(
        "/api/v1/referrals/claim",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nwu_claimed"] == NWU_REWARD_PER_REFERRAL
    assert data["total_nwu_claimed"] == NWU_REWARD_PER_REFERRAL

    # Verify event is now claimed
    db.refresh(event)
    assert event.status == "claimed"


def test_claim_requires_auth(client, db):
    """POST /claim returns 401 when no token is provided."""
    response = client.post("/api/v1/referrals/claim")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Affiliate tier
# ---------------------------------------------------------------------------

def test_affiliate_status_unlocked_at_threshold(client, db):
    """User becomes an Affiliate after reaching AFFILIATE_REFERRAL_THRESHOLD conversions."""
    user_a = _create_user(db, ADDRESS_A)
    token_a = _make_token(ADDRESS_A)

    # Generate a ReferralCode for user A
    client.post("/api/v1/referrals/generate", headers={"Authorization": f"Bearer {token_a}"})
    code_record = db.query(ReferralCode).filter(ReferralCode.referrer_id == user_a.id).first()

    # Add AFFILIATE_REFERRAL_THRESHOLD signup events
    for i in range(AFFILIATE_REFERRAL_THRESHOLD):
        addr = f"0x{'a' * 38}{i:02x}"[:42]
        fake_user = User(address=addr)
        db.add(fake_user)
        db.flush()
        event = ReferralEvent(
            referral_code_id=code_record.id,
            referee_id=fake_user.id,
            event_type="signup",
            nwu_reward=NWU_REWARD_PER_REFERRAL,
            status="pending",
        )
        db.add(event)
    db.commit()

    response = client.get(
        "/api/v1/referrals/stats",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_affiliate"] is True
    assert data["revenue_share_percent"] == 10.0

    db.refresh(user_a)
    assert user_a.is_affiliate is True


def test_nwu_reward_amount_on_apply(client, db):
    """Applying a referral code with a matching ReferralCode creates a 50 NWU pending event."""
    user_a = _create_user(db, ADDRESS_A)
    user_b = _create_user(db, ADDRESS_B)
    token_a = _make_token(ADDRESS_A)

    # Generate a ReferralCode for user A
    r = client.post("/api/v1/referrals/generate", headers={"Authorization": f"Bearer {token_a}"})
    affiliate_code = r.json()["referral_code"]

    # Also create a legacy Referral record so /apply can find the code
    from sqlalchemy.exc import IntegrityError as _IE
    legacy_ref = Referral(referrer_id=user_a.id, referral_code=affiliate_code)
    db.add(legacy_ref)
    try:
        db.commit()
    except _IE:
        db.rollback()

    response = client.post(
        "/api/v1/referrals/apply",
        params={"address": ADDRESS_B, "referral_code": affiliate_code},
    )
    assert response.status_code == 200

    # A ReferralEvent for 50 NWU should exist
    db.expire_all()
    code_record = db.query(ReferralCode).filter(ReferralCode.code == affiliate_code).first()
    event = (
        db.query(ReferralEvent)
        .filter(ReferralEvent.referral_code_id == code_record.id, ReferralEvent.event_type == "signup")
        .first()
    )
    assert event is not None
    assert event.nwu_reward == NWU_REWARD_PER_REFERRAL
    assert event.status == "pending"
