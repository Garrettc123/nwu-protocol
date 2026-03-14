"""Tests for the subscription billing engine.

Covers the full subscription lifecycle:
- Model creation and field validation
- Plan features, rate limits and staking multipliers
- Subscription cancel-at-period-end flag
- Invoice model
- upgrade_subscription service logic (mocked Stripe calls)
- webhook invoice.paid handler
- API key subscription status check logic
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base,
    Invoice,
    Subscription,
    SubscriptionTier,
    User,
    APIKey,
)
from app.services.payment_service import PaymentService

# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///./test_subscriptions.db"

_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def user(db):
    u = User(
        address="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        username="subscriptiontestuser",
        email="sub@test.com",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_subscription(db, user, tier=SubscriptionTier.BASIC, stripe_sub_id="sub_test123"):
    subscription = Subscription(
        user_id=user.id,
        tier=tier,
        stripe_subscription_id=stripe_sub_id,
        stripe_customer_id="cus_test123",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
        api_key="nwu_testkey123",
        rate_limit=1_000,
        staking_multiplier=1.5,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


# ===========================================================================
# 1. Subscription model creation
# ===========================================================================


def test_subscription_model_basic_tier(db, user):
    """Subscription model stores BASIC tier attributes correctly."""
    subscription = _make_subscription(db, user)

    assert subscription.id is not None
    assert subscription.tier == SubscriptionTier.BASIC
    assert subscription.status == "active"
    assert subscription.rate_limit == 1_000
    assert subscription.staking_multiplier == pytest.approx(1.5)
    assert subscription.cancel_at_period_end is False


def test_subscription_model_pro_tier(db, user):
    """Subscription model stores PRO tier attributes correctly."""
    subscription = _make_subscription(
        db, user, tier=SubscriptionTier.PRO, stripe_sub_id="sub_pro_001"
    )

    assert subscription.tier == SubscriptionTier.PRO


def test_subscription_model_enterprise_tier(db, user):
    """Subscription model stores ENTERPRISE tier attributes correctly."""
    subscription = _make_subscription(
        db, user, tier=SubscriptionTier.ENTERPRISE, stripe_sub_id="sub_ent_001"
    )

    assert subscription.tier == SubscriptionTier.ENTERPRISE
    assert subscription.id is not None


# ===========================================================================
# 2. Invoice model creation
# ===========================================================================


def test_invoice_model_creation(db, user):
    """Invoice model stores paid invoice data correctly."""
    subscription = _make_subscription(db, user)

    invoice = Invoice(
        user_id=user.id,
        subscription_id=subscription.id,
        stripe_invoice_id="in_test_001",
        amount_due=29.0,
        amount_paid=29.0,
        currency="usd",
        status="paid",
        period_start=datetime.utcnow() - timedelta(days=30),
        period_end=datetime.utcnow(),
        paid_at=datetime.utcnow(),
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    assert invoice.id is not None
    assert invoice.stripe_invoice_id == "in_test_001"
    assert invoice.status == "paid"
    assert invoice.amount_paid == pytest.approx(29.0)


# ===========================================================================
# 3. Plan catalogue – rate limits and staking multipliers
# ===========================================================================


def test_plan_rate_limits():
    """Verify plan rate limit constants in subscriptions router."""
    from routers.subscriptions import PLAN_RATE_LIMITS, PLAN_STAKING_MULTIPLIERS

    assert PLAN_RATE_LIMITS[SubscriptionTier.BASIC] == 1_000
    assert PLAN_RATE_LIMITS[SubscriptionTier.PRO] == 10_000
    assert PLAN_RATE_LIMITS[SubscriptionTier.ENTERPRISE] == 100_000


def test_plan_staking_multipliers():
    """Verify staking multiplier constants in subscriptions router."""
    from routers.subscriptions import PLAN_STAKING_MULTIPLIERS

    assert PLAN_STAKING_MULTIPLIERS[SubscriptionTier.BASIC] == pytest.approx(1.5)
    assert PLAN_STAKING_MULTIPLIERS[SubscriptionTier.PRO] == pytest.approx(2.0)
    assert PLAN_STAKING_MULTIPLIERS[SubscriptionTier.ENTERPRISE] == pytest.approx(5.0)


def test_plan_prices():
    """Verify subscription plan prices: Basic $29, Pro $99, Enterprise $499."""
    from routers.subscriptions import PLAN_PRICES

    assert PLAN_PRICES[SubscriptionTier.BASIC] == 29
    assert PLAN_PRICES[SubscriptionTier.PRO] == 99
    assert PLAN_PRICES[SubscriptionTier.ENTERPRISE] == 499


# ===========================================================================
# 4. Cancel subscription sets cancel_at_period_end flag
# ===========================================================================


@pytest.mark.asyncio
async def test_cancel_subscription_at_period_end(db, user):
    """cancel_subscription sets cancel_at_period_end and keeps status active."""
    subscription = _make_subscription(db, user)
    service = PaymentService()

    # Mock the stripe call
    mock_stripe_modify = MagicMock()
    with patch("stripe.Subscription.modify", mock_stripe_modify):
        with patch.object(service, "stripe_configured", True):
            result = await service.cancel_subscription(db, subscription.id, immediately=False)

    assert result is True
    db.refresh(subscription)
    assert subscription.cancel_at_period_end is True
    mock_stripe_modify.assert_called_once_with(
        subscription.stripe_subscription_id,
        cancel_at_period_end=True,
    )


# ===========================================================================
# 5. Upgrade subscription
# ===========================================================================


@pytest.mark.asyncio
async def test_upgrade_subscription_basic_to_pro(db, user):
    """upgrade_subscription upgrades tier from BASIC to PRO and updates DB."""
    subscription = _make_subscription(db, user, tier=SubscriptionTier.BASIC)
    service = PaymentService()

    now_ts = int(datetime.utcnow().timestamp())
    end_ts = int((datetime.utcnow() + timedelta(days=30)).timestamp())

    # Stripe SDK objects support attribute access; use SimpleNamespace for the mock
    from types import SimpleNamespace

    mock_retrieve = {
        "items": {"data": [{"id": "si_item_001"}]},
        "status": "active",
        "current_period_start": now_ts,
        "current_period_end": end_ts,
    }

    mock_modify = SimpleNamespace(
        status="active",
        current_period_start=now_ts,
        current_period_end=end_ts,
    )

    with patch("stripe.Subscription.retrieve", return_value=mock_retrieve):
        with patch("stripe.Subscription.modify", return_value=mock_modify):
            with patch.object(service, "stripe_configured", True):
                upgraded = await service.upgrade_subscription(
                    db,
                    subscription,
                    SubscriptionTier.PRO,
                    "price_pro_stripe_id",
                )

    assert upgraded is not None
    assert upgraded.tier == SubscriptionTier.PRO
    assert upgraded.rate_limit == 10_000
    assert upgraded.staking_multiplier == pytest.approx(2.0)


# ===========================================================================
# 6. Webhook invoice.paid handler
# ===========================================================================


@pytest.mark.asyncio
async def test_webhook_invoice_paid_creates_invoice_record(db, user):
    """handle_webhook invoice.paid creates an Invoice row and activates subscription."""
    subscription = _make_subscription(db, user)
    service = PaymentService()

    now_ts = int(datetime.utcnow().timestamp())

    # Build a fake Stripe invoice object
    fake_invoice = MagicMock()
    fake_invoice.id = "in_webhook_001"
    fake_invoice.subscription = subscription.stripe_subscription_id
    fake_invoice.amount_due = 2900  # cents
    fake_invoice.amount_paid = 2900
    fake_invoice.currency = "usd"
    fake_invoice.period_start = now_ts - 2_592_000  # 30 days ago
    fake_invoice.period_end = now_ts
    fake_invoice.status_transitions = MagicMock()
    fake_invoice.status_transitions.paid_at = now_ts

    # Build a fake Stripe event
    fake_event = MagicMock()
    fake_event.type = "invoice.paid"
    fake_event.data.object = fake_invoice

    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        with patch.object(service, "stripe_configured", True):
            with patch.object(
                service, "_get_webhook_secret", return_value="whsec_test", create=True
            ):
                from unittest.mock import PropertyMock
                type(service).stripe_configured = PropertyMock(return_value=True)
                # Temporarily set the webhook secret
                from app.config import settings
                original_secret = settings.stripe_webhook_secret
                settings.stripe_webhook_secret = "whsec_test"

                result = await service.handle_webhook(db, b"payload", "stripe-sig")

                settings.stripe_webhook_secret = original_secret

    assert result is True
    invoice = db.query(Invoice).filter(Invoice.stripe_invoice_id == "in_webhook_001").first()
    assert invoice is not None
    assert invoice.status == "paid"
    assert invoice.amount_paid == pytest.approx(29.0)
    assert invoice.subscription_id == subscription.id


# ===========================================================================
# 7. Subscription status helper returns correct features
# ===========================================================================


def test_subscription_status_payload_no_subscription():
    """Status helper returns free tier defaults when no subscription exists."""
    from routers.subscriptions import _subscription_status_payload

    result = _subscription_status_payload(None)

    assert result["plan"] == "free"
    assert result["status"] == "none"
    assert result["staking_multiplier"] == pytest.approx(1.0)
    assert result["api_quota"] == 100
    assert result["features"]["basic_api"] is True
    assert result["features"]["advanced_api"] is False


def test_subscription_status_payload_pro_subscription(db, user):
    """Status helper returns PRO tier features for an active PRO subscription."""
    from routers.subscriptions import _subscription_status_payload

    subscription = _make_subscription(
        db, user, tier=SubscriptionTier.PRO, stripe_sub_id="sub_pro_status"
    )
    subscription.rate_limit = 10_000
    subscription.staking_multiplier = 2.0
    db.commit()

    result = _subscription_status_payload(subscription)

    assert result["plan"] == "pro"
    assert result["status"] == "active"
    assert result["staking_multiplier"] == pytest.approx(2.0)
    assert result["api_quota"] == 10_000
    assert result["features"]["advanced_api"] is True
    assert result["features"]["priority_support"] is True


# ===========================================================================
# 8. SubscriptionTier enum now includes BASIC
# ===========================================================================


def test_subscription_tier_basic_exists():
    """SubscriptionTier enum includes BASIC tier."""
    assert SubscriptionTier.BASIC.value == "basic"
    valid_values = [tier.value for tier in SubscriptionTier]
    assert "basic" in valid_values
