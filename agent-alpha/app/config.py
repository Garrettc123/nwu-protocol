"""Configuration for Agent-Alpha."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Agent configuration."""
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Backend API
    BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
    
    # RabbitMQ
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672")
    
    # IPFS
    IPFS_HOST = os.getenv("IPFS_HOST", "ipfs")
    IPFS_PORT = int(os.getenv("IPFS_PORT", "5001"))
    
    # Agent Settings
    AGENT_ID = "agent-alpha-001"
    AGENT_TYPE = "alpha"
    
    # Verification Thresholds
    MIN_QUALITY_SCORE = 0
    MAX_QUALITY_SCORE = 100


config = Config()
