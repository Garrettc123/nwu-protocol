"""Database models for NWU Protocol."""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

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


class Contribution(Base):
    """Contribution model."""
    __tablename__ = "contributions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ipfs_hash = Column(String(100), unique=True, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # code, dataset, document
    file_size = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string
    status = Column(String(50), default="pending")  # pending, verifying, verified, rejected
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
    contribution_id = Column(Integer, ForeignKey("contributions.id"), nullable=False)
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contribution_id = Column(Integer, ForeignKey("contributions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, distributed, failed
    tx_hash = Column(String(100), nullable=True)
    blockchain = Column(String(50), default="ethereum")
    created_at = Column(DateTime, default=datetime.utcnow)
    distributed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="rewards")
    contribution = relationship("Contribution", back_populates="rewards")


class BusinessAgent(Base):
    """Business Agent model for tracking specialized agents."""
    __tablename__ = "business_agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(100), unique=True, nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)  # sales, marketing, operations, etc.
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="idle")  # idle, busy, paused, error, terminated
    capabilities = Column(Text, nullable=True)  # JSON string
    config = Column(Text, nullable=True)  # JSON string
    tasks_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    terminated_at = Column(DateTime, nullable=True)

    tasks = relationship("BusinessTask", back_populates="agent")


class BusinessTask(Base):
    """Business Task model for tracking tasks processed by agents."""
    __tablename__ = "business_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    task_type = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True)
    priority = Column(Integer, default=5)
    status = Column(String(50), default="pending")  # pending, analyzing, executing, completed, failed, error
    agent_id = Column(String(100), ForeignKey("business_agents.agent_id"), nullable=True)
    task_data = Column(Text, nullable=True)  # JSON string
    result = Column(Text, nullable=True)  # JSON string
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    agent = relationship("BusinessAgent", back_populates="tasks")
