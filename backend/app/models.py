"""Database models for NWU Protocol."""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, Index, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum
import secrets
import string

# API Key tier rate limits (requests per day; -1 = unlimited)
FREE_TIER_DAILY_LIMIT = 100
PRO_TIER_DAILY_LIMIT = 10_000
ENTERPRISE_TIER_DAILY_LIMIT = -1  # Unlimited

# Monthly quotas (derived from daily limits × 30 days)
FREE_TIER_MONTHLY_QUOTA = FREE_TIER_DAILY_LIMIT * 30
PRO_TIER_MONTHLY_QUOTA = PRO_TIER_DAILY_LIMIT * 30
ENTERPRISE_TIER_MONTHLY_QUOTA = -1  # Unlimited

TIER_DAILY_LIMITS = {
    "free": FREE_TIER_DAILY_LIMIT,
    "pro": PRO_TIER_DAILY_LIMIT,
    "enterprise": ENTERPRISE_TIER_DAILY_LIMIT,
}

TIER_MONTHLY_QUOTAS = {
    "free": FREE_TIER_MONTHLY_QUOTA,
    "pro": PRO_TIER_MONTHLY_QUOTA,
    "enterprise": ENTERPRISE_TIER_MONTHLY_QUOTA,
}

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
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referral_used = relationship("Referral", foreign_keys="Referral.referee_id", back_populates="referee", uselist=False)


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
    status = Column(String(50), default="pending", index=True)  # pending, verifying, verified, rejected, halted, paused, resumed
    quality_score = Column(Float, nullable=True)
    verification_count = Column(Integer, default=0)
    engagement_count = Column(Integer, default=0)  # Track user engagement interactions
    engagement_score = Column(Float, default=0.0)  # Calculated engagement metric
    iteration_count = Column(Integer, default=0)  # Number of revision iterations
    halt_reason = Column(Text, nullable=True)  # Reason for halting the process
    halt_status = Column(String(50), nullable=True, index=True)  # active, halted, paused, resumed
    process_stage = Column(String(50), default="initial", index=True)  # Track progressive automation stage
    automation_level = Column(Integer, default=0)  # Progressive automation capability level (0-5)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    halted_at = Column(DateTime, nullable=True)
    resumed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="contributions")
    verifications = relationship("Verification", back_populates="contribution")
    rewards = relationship("Reward", back_populates="contribution")
    engagement_history = relationship("EngagementHistory", back_populates="contribution")
    process_iterations = relationship("ProcessIteration", back_populates="contribution")
    workflow_executions = relationship("WorkflowExecution", back_populates="contribution")


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
    stripe_payment_id = Column(String(100), unique=True, nullable=True, index=True)
    stripe_invoice_id = Column(String(100), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="usd")
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    description = Column(Text, nullable=True)
    payment_metadata = Column("metadata", Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")


class UsageRecord(Base):
    """Usage tracking for metered billing."""
    __tablename__ = "usage_records"
    __table_args__ = (
        Index('ix_usage_subscription_date', 'subscription_id', 'record_date'),
    )

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
    rate_limit_per_day = Column(Integer, nullable=False, default=FREE_TIER_DAILY_LIMIT)
    monthly_quota = Column(Integer, nullable=False, default=FREE_TIER_MONTHLY_QUOTA)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="api_keys")
    usage_records = relationship("APIKeyUsage", back_populates="api_key", cascade="all, delete-orphan")


class APIKeyUsage(Base):
    """Per-day usage tracking for API keys."""
    __tablename__ = "api_key_usage"
    __table_args__ = (
        UniqueConstraint("api_key_id", "usage_date", name="uq_api_key_usage_date"),
        Index("ix_api_key_usage_key_date", "api_key_id", "usage_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False, index=True)
    usage_date = Column(Date, nullable=False, index=True)
    request_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    api_key = relationship("APIKey", back_populates="usage_records")


REFERRAL_CODE_LENGTH = 10
REFERRAL_CODE_ALPHABET = string.ascii_uppercase + string.digits
REFERRAL_REPUTATION_BONUS_REFERRER = 10.0
REFERRAL_REPUTATION_BONUS_REFEREE = 5.0


def generate_referral_code() -> str:
    """Generate a unique, URL-safe referral code."""
    return "".join(secrets.choice(REFERRAL_CODE_ALPHABET) for _ in range(REFERRAL_CODE_LENGTH))


class Referral(Base):
    """Referral model for customer acquisition tracking."""
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referral_code = Column(String(20), unique=True, nullable=False, index=True, default=generate_referral_code)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(20), default="pending", index=True)  # pending, completed
    reward_granted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referee = relationship("User", foreign_keys=[referee_id], back_populates="referral_used")


class EngagementHistory(Base):
    """Engagement history tracking for contributions."""
    __tablename__ = "engagement_history"

    id = Column(Integer, primary_key=True, index=True)
    contribution_id = Column(Integer, ForeignKey("contributions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    engagement_type = Column(String(50), nullable=False, index=True)  # view, comment, share, iterate, halt, resume
    engagement_data = Column(Text, nullable=True)  # JSON string with additional context
    engagement_source = Column(String(50), nullable=True)  # web, api, automation
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    contribution = relationship("Contribution", back_populates="engagement_history")
    user = relationship("User")


class ProcessIteration(Base):
    """Process iteration tracking for contribution revisions."""
    __tablename__ = "process_iterations"

    id = Column(Integer, primary_key=True, index=True)
    contribution_id = Column(Integer, ForeignKey("contributions.id"), nullable=False, index=True)
    iteration_number = Column(Integer, nullable=False)
    previous_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    iteration_type = Column(String(50), nullable=False)  # automatic, manual, triggered
    iteration_reason = Column(Text, nullable=True)
    changes_summary = Column(Text, nullable=True)  # JSON string with change details
    quality_delta = Column(Float, nullable=True)  # Change in quality score
    created_at = Column(DateTime, default=datetime.utcnow)

    contribution = relationship("Contribution", back_populates="process_iterations")


class WorkflowExecution(Base):
    """Workflow execution tracking for progressive automation."""
    __tablename__ = "workflow_executions"
    __table_args__ = (
        Index('ix_workflow_contribution_status', 'contribution_id', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    contribution_id = Column(Integer, ForeignKey("contributions.id"), nullable=False, index=True)
    workflow_name = Column(String(100), nullable=False, index=True)
    workflow_stage = Column(String(50), nullable=False)  # initial, processing, completed, failed, halted
    automation_level = Column(Integer, default=0)  # Progressive automation level applied
    execution_data = Column(Text, nullable=True)  # JSON string with execution details
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed, halted
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    contribution = relationship("Contribution", back_populates="workflow_executions")


class BusinessAgentType(enum.Enum):
    """Business agent type enum."""
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    FINANCE = "finance"
    CUSTOMER_SERVICE = "customer_service"
    RESEARCH = "research"
    DEVELOPMENT = "development"
    QA = "qa"
    HR = "hr"
    LEGAL = "legal"
    STRATEGY = "strategy"
    PROJECT_MANAGEMENT = "project_management"


class BusinessAgentStatus(enum.Enum):
    """Business agent lifecycle status."""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    PAUSED = "paused"
    TERMINATED = "terminated"


class BusinessTaskStatus(enum.Enum):
    """Business task status."""
    QUEUED = "queued"
    DELEGATED = "delegated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BusinessAgent(Base):
    """Business agent model for the Business Cooperation Lead system."""
    __tablename__ = "business_agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(100), unique=True, nullable=False, index=True)
    agent_type = Column(SQLEnum(BusinessAgentType), nullable=False, index=True)
    status = Column(SQLEnum(BusinessAgentStatus), nullable=False, default=BusinessAgentStatus.IDLE, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    capabilities = Column(Text, nullable=True)  # JSON array of capability strings
    config = Column(Text, nullable=True)  # JSON object with agent configuration
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    last_active_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    terminated_at = Column(DateTime, nullable=True)

    tasks = relationship("BusinessTask", back_populates="assigned_agent",
                         foreign_keys="BusinessTask.agent_id")


class BusinessTask(Base):
    """Business task model for the Business Cooperation Lead system."""
    __tablename__ = "business_tasks"
    __table_args__ = (
        Index('ix_business_tasks_status_priority', 'status', 'priority'),
    )

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(100), nullable=False, index=True)
    required_agent_type = Column(SQLEnum(BusinessAgentType), nullable=True, index=True)
    agent_id = Column(Integer, ForeignKey("business_agents.id"), nullable=True, index=True)
    status = Column(SQLEnum(BusinessTaskStatus), nullable=False, default=BusinessTaskStatus.QUEUED, index=True)
    priority = Column(Integer, default=5, index=True)  # 1 (highest) to 10 (lowest)
    task_data = Column(Text, nullable=True)  # JSON object with task payload
    result_data = Column(Text, nullable=True)  # JSON object with task result
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_agent = relationship("BusinessAgent", back_populates="tasks",
                                  foreign_keys=[agent_id])


class KnowledgeThread(Base):
    """Knowledge thread management for perplexity integration."""
    __tablename__ = "knowledge_threads"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(100), unique=True, nullable=False, index=True)
    contribution_id = Column(Integer, ForeignKey("contributions.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    thread_type = Column(String(50), nullable=False)  # verification, engagement, automation
    context_data = Column(Text, nullable=True)  # JSON string with thread context
    status = Column(String(50), default="active", index=True)  # active, closed, archived
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    contribution = relationship("Contribution")
    user = relationship("User")
