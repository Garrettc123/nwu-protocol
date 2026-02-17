"""Configuration for Business Cooperation Lead Agent."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Business Lead Agent configuration."""

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
    AGENT_ID = "business-lead-001"
    AGENT_TYPE = "business-lead"

    # Business Agent Settings
    MAX_CONCURRENT_AGENTS = int(os.getenv("MAX_CONCURRENT_AGENTS", "10"))
    AGENT_CREATION_ENABLED = os.getenv("AGENT_CREATION_ENABLED", "true").lower() == "true"

    # Task Assignment Settings
    AUTO_DELEGATE = os.getenv("AUTO_DELEGATE", "true").lower() == "true"
    PRIORITY_THRESHOLD = float(os.getenv("PRIORITY_THRESHOLD", "7.0"))


config = Config()
