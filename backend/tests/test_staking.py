"""Tests for the NWU token staking and yield endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base, StakingPosition, YieldEvent, STAKING_LOCK_DAYS
from app.database import get_db

TEST_DATABASE_URL = "sqlite:///./test_staking.db"

_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

WALLET_A = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
WALLET_B = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    # Install override only for staking tests, restore afterwards to avoid
    # polluting other test modules that also override get_db.
    original = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)
    if original is not None:
        app.dependency_overrides[get_db] = original
    else:
        app.dependency_overrides.pop(get_db, None)


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


# ---------------------------------------------------------------------------
# POST /staking/stake
# ---------------------------------------------------------------------------

def test_stake_creates_new_position(client):
    """Staking creates a new position with the correct amount."""
    response = client.post(
        "/api/v1/staking/stake",
        json={"wallet": WALLET_A, "amount": 100.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["wallet"] == WALLET_A
    assert data["staked_amount"] == 100.0
    assert "lock_expires_at" in data
    assert data["accumulated_yield"] == 0.0


def test_stake_adds_to_existing_position(client):
    """Staking again increases the staked amount."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 100.0})
    response = client.post(
        "/api/v1/staking/stake",
        json={"wallet": WALLET_A, "amount": 50.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["staked_amount"] == 150.0


def test_stake_records_yield_event(client, db):
    """A YieldEvent of type 'stake' is persisted when staking."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 200.0})
    events = db.query(YieldEvent).filter(YieldEvent.wallet == WALLET_A).all()
    assert len(events) == 1
    assert events[0].event_type == "stake"
    assert events[0].amount == 200.0


def test_stake_resets_lock_expiry(client):
    """Each stake resets the lock expiry to 7 days from now."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 10.0})
    response = client.post(
        "/api/v1/staking/stake",
        json={"wallet": WALLET_A, "amount": 10.0},
    )
    data = response.json()
    expiry = datetime.fromisoformat(data["lock_expires_at"])
    now = datetime.utcnow()
    # Lock should be approximately 7 days from now (within a few seconds of tolerance)
    expected = now + timedelta(days=STAKING_LOCK_DAYS)
    assert abs((expiry - expected).total_seconds()) < 5


def test_stake_invalid_wallet_returns_422(client):
    """An invalid wallet address is rejected with HTTP 422."""
    response = client.post(
        "/api/v1/staking/stake",
        json={"wallet": "not_an_address", "amount": 10.0},
    )
    assert response.status_code == 422


def test_stake_zero_amount_returns_422(client):
    """A zero stake amount is rejected with HTTP 422."""
    response = client.post(
        "/api/v1/staking/stake",
        json={"wallet": WALLET_A, "amount": 0.0},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /staking/unstake
# ---------------------------------------------------------------------------

def test_unstake_within_lock_period_returns_400(client):
    """Unstaking before the lock period expires returns HTTP 400."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 100.0})
    response = client.post(
        "/api/v1/staking/unstake",
        json={"wallet": WALLET_A, "amount": 50.0},
    )
    assert response.status_code == 400
    error_message = response.json().get("detail") or response.json().get("error", "")
    assert "lock" in error_message.lower()


def test_unstake_after_lock_period_succeeds(client, db):
    """Unstaking after the lock period reduces the staked amount."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 100.0})

    # Manually expire the lock
    position = db.query(StakingPosition).filter(StakingPosition.wallet == WALLET_A).first()
    position.lock_expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    response = client.post(
        "/api/v1/staking/unstake",
        json={"wallet": WALLET_A, "amount": 40.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["unstaked_amount"] == 40.0
    assert data["remaining_staked"] == 60.0


def test_unstake_more_than_staked_returns_400(client, db):
    """Attempting to unstake more than is staked returns HTTP 400."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 50.0})

    position = db.query(StakingPosition).filter(StakingPosition.wallet == WALLET_A).first()
    position.lock_expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    response = client.post(
        "/api/v1/staking/unstake",
        json={"wallet": WALLET_A, "amount": 100.0},
    )
    assert response.status_code == 400


def test_unstake_no_position_returns_404(client):
    """Unstaking when no position exists returns HTTP 404."""
    response = client.post(
        "/api/v1/staking/unstake",
        json={"wallet": WALLET_B, "amount": 10.0},
    )
    assert response.status_code == 404


def test_unstake_records_yield_event(client, db):
    """A YieldEvent of type 'unstake' is persisted on successful unstake."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 100.0})

    position = db.query(StakingPosition).filter(StakingPosition.wallet == WALLET_A).first()
    position.lock_expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    client.post("/api/v1/staking/unstake", json={"wallet": WALLET_A, "amount": 30.0})

    events = db.query(YieldEvent).filter(
        YieldEvent.wallet == WALLET_A,
        YieldEvent.event_type == "unstake",
    ).all()
    assert len(events) == 1
    assert events[0].amount == 30.0


# ---------------------------------------------------------------------------
# GET /staking/position/{wallet}
# ---------------------------------------------------------------------------

def test_get_position_returns_correct_data(client):
    """The position endpoint returns staked amount, yield, and lock expiry."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 250.0})
    response = client.get(f"/api/v1/staking/position/{WALLET_A}")
    assert response.status_code == 200
    data = response.json()
    assert data["wallet"] == WALLET_A
    assert data["staked_amount"] == 250.0
    assert "yield_accrued" in data
    assert "lock_expires_at" in data
    assert data["is_active"] is True


def test_get_position_not_found_returns_404(client):
    """Fetching a position for an unknown wallet returns HTTP 404."""
    response = client.get(f"/api/v1/staking/position/{WALLET_B}")
    assert response.status_code == 404


def test_get_position_yield_is_non_negative(client):
    """Yield accrued in the position endpoint is always non-negative."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 100.0})
    response = client.get(f"/api/v1/staking/position/{WALLET_A}")
    assert response.json()["yield_accrued"] >= 0.0


# ---------------------------------------------------------------------------
# POST /staking/claim
# ---------------------------------------------------------------------------

def test_claim_no_yield_returns_400(client, db):
    """Claiming when no yield has accrued returns HTTP 400."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 100.0})
    # Push last_yield_update into the future so no pending yield accrues
    position = db.query(StakingPosition).filter(StakingPosition.wallet == WALLET_A).first()
    position.accumulated_yield = 0.0
    position.last_yield_update = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    response = client.post("/api/v1/staking/claim", json={"wallet": WALLET_A})
    assert response.status_code == 400


def test_claim_after_yield_accrued_succeeds(client, db):
    """Claiming yield after time has passed returns the accrued amount."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 1000.0})

    # Manually set last_yield_update to 30 days ago to simulate accrued yield
    position = db.query(StakingPosition).filter(StakingPosition.wallet == WALLET_A).first()
    position.last_yield_update = datetime.utcnow() - timedelta(days=30)
    db.commit()

    response = client.post("/api/v1/staking/claim", json={"wallet": WALLET_A})
    assert response.status_code == 200
    data = response.json()
    assert data["claimed_yield"] > 0
    assert data["new_accumulated_yield"] == 0.0


def test_claim_resets_accumulated_yield(client, db):
    """After claiming, accumulated yield is reset to zero in the position."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 500.0})

    position = db.query(StakingPosition).filter(StakingPosition.wallet == WALLET_A).first()
    position.accumulated_yield = 10.0
    position.last_yield_update = datetime.utcnow()
    db.commit()

    client.post("/api/v1/staking/claim", json={"wallet": WALLET_A})

    db.refresh(position)
    assert position.accumulated_yield == 0.0


def test_claim_records_yield_event(client, db):
    """A YieldEvent of type 'claim' is persisted on successful claim."""
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": 500.0})

    position = db.query(StakingPosition).filter(StakingPosition.wallet == WALLET_A).first()
    position.accumulated_yield = 5.0
    position.last_yield_update = datetime.utcnow()
    db.commit()

    client.post("/api/v1/staking/claim", json={"wallet": WALLET_A})

    events = db.query(YieldEvent).filter(
        YieldEvent.wallet == WALLET_A,
        YieldEvent.event_type == "claim",
    ).all()
    assert len(events) == 1
    assert events[0].amount > 0


def test_claim_no_position_returns_404(client):
    """Claiming for a wallet with no position returns HTTP 404."""
    response = client.post("/api/v1/staking/claim", json={"wallet": WALLET_B})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Yield calculation sanity check
# ---------------------------------------------------------------------------

def test_yield_rate_approximately_12pct_apy(client, db):
    """Verify the yield over one year is approximately 12% of the principal."""
    principal = 1000.0
    client.post("/api/v1/staking/stake", json={"wallet": WALLET_A, "amount": principal})

    position = db.query(StakingPosition).filter(StakingPosition.wallet == WALLET_A).first()
    position.last_yield_update = datetime.utcnow() - timedelta(days=365)
    db.commit()

    response = client.get(f"/api/v1/staking/position/{WALLET_A}")
    yield_accrued = response.json()["yield_accrued"]

    expected = principal * 0.12
    # Allow 1% tolerance for timing differences
    assert abs(yield_accrued - expected) / expected < 0.01
