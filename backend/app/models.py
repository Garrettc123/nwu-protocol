"""Database models for NWU Protocol."""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(42), unique=True, index=True, nullable=False)  # Ethereum address
    username = Column(String(100), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    reputation_score = Column(Float, default=0.0)
    total_contributions = Column(Integer, default=0)
    total_rewards = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    contributions = relationship("Contribution", back_populates="user")
    rewards = relationship("Reward", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


class Contribution(Base):
    """Contribution model."""
    __tablename__ = "contributions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ipfs_hash = Column(String(100), unique=True, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # code, dataset, document
    file_size = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    meta_data = Column("metadata", Text, nullable=True)  # JSON string
    status = Column(String(50), default="pending", index=True)  # pending, verifying, verified, rejected
    quality_score = Column(Float, nullable=True)
    verification_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="contributions")
    verifications = relationship("Verification", back_populates="contribution")
    rewards = relationship("Reward", back_populates="contribution")


class Verification(Base):
    """Verification model."""
    __tablename__ = "verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    contribution_id = Column(Integer, ForeignKey("contributions.id"), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)  # alpha, beta, etc.
    vote_score = Column(Float, nullable=False)  # 0-100
    quality_score = Column(Float, nullable=True)
    originality_score = Column(Float, nullable=True)
    security_score = Column(Float, nullable=True)
    documentation_score = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    details = Column(Text, nullable=True)  # JSON string with detailed analysis
    status = Column(String(50), default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    contribution = relationship("Contribution", back_populates="verifications")


class Reward(Base):
    """Reward model."""
    __tablename__ = "rewards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    contribution_id = Column(Integer, ForeignKey("contributions.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending", index=True)  # pending, processing, distributed, failed
    tx_hash = Column(String(100), nullable=True)
    blockchain = Column(String(50), default="ethereum")
    created_at = Column(DateTime, default=datetime.utcnow)
    distributed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="rewards")
    contribution = relationship("Contribution", back_populates="rewards")


class SubscriptionTier(enum.Enum):
    """Subscription tier enum."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PaymentStatus(enum.Enum):
    """Payment status enum."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"


class Subscription(Base):
    """Subscription model for paid tiers."""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tier = Column(SQLEnum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE)
    stripe_subscription_id = Column(String(100), unique=True, nullable=True)
    stripe_customer_id = Column(String(100), nullable=True, index=True)
    status = Column(String(50), default="active")  # active, canceled, past_due, incomplete
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    api_key = Column(String(100), unique=True, nullable=True, index=True)
    rate_limit = Column(Integer, default=100)  # requests per day
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")
    usage_records = relationship("UsageRecord", back_populates="subscription")


class Payment(Base):
    """Payment model for tracking transactions."""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True, index=True)
    stripe_payment_id = Column(String(100), unique=True, nullable=True)
    stripe_invoice_id = Column(String(100), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="usd")
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    description = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")


class UsageRecord(Base):
    """Usage tracking for metered billing."""
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    request_count = Column(Integer, default=0)
    record_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    subscription = relationship("Subscription", back_populates="usage_records")


class APIKey(Base):
    """API Key model for authentication."""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    prefix = Column(String(20), nullable=False)  # First 12 chars for display
    tier = Column(SQLEnum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="api_keys")
