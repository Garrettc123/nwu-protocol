"""Configuration management for NWU Protocol."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import field_validator
import secrets
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )

    # Application
    app_name: str = "NWU Protocol API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://nwu_user:rocket69!@postgres:5432/nwu_db"
    mongo_url: str = "mongodb://admin:rocket69!@mongodb:27017/nwu_db?authSource=admin"

    # Redis
    redis_url: str = "redis://redis:6379"

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672"

    # IPFS
    ipfs_host: str = "ipfs"
    ipfs_port: int = 5001
    ipfs_thread_pool_size: int = 4  # Thread pool size for async IPFS operations

    # JWT Authentication - Will auto-generate if not set via environment
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours

    # Legacy auth settings (for backward compatibility)
    secret_key: Optional[str] = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OpenAI
    openai_api_key: Optional[str] = None

    # Blockchain
    eth_rpc_url: Optional[str] = None
    contract_address: Optional[str] = None

    # Payment Integration (Stripe)
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_price_id_pro: Optional[str] = None
    stripe_price_id_enterprise: Optional[str] = None

    # Subscription Tiers
    subscription_tier_free_rate_limit: int = 100  # requests per day
    subscription_tier_pro_rate_limit: int = 10000  # requests per day
    subscription_tier_enterprise_rate_limit: int = 100000  # requests per day

    # Admin
    admin_addresses: str = ""  # Comma-separated list of admin Ethereum addresses (lowercase)

    @field_validator('jwt_secret_key', mode='after')
    @classmethod
    def generate_jwt_secret_if_missing(cls, v: Optional[str]) -> str:
        """Generate secure JWT secret key if not provided."""
        if not v:
            generated_key = secrets.token_urlsafe(32)
            logger.warning(
                "JWT_SECRET_KEY not set in environment. Auto-generated a secure key. "
                "For production, set JWT_SECRET_KEY in environment variables."
            )
            return generated_key
        return v

    @field_validator('secret_key', mode='after')
    @classmethod
    def generate_secret_if_missing(cls, v: Optional[str]) -> str:
        """Generate secure secret key if not provided."""
        if not v:
            generated_key = secrets.token_urlsafe(32)
            logger.warning(
                "SECRET_KEY not set in environment. Auto-generated a secure key. "
                "For production, set SECRET_KEY in environment variables."
            )
            return generated_key
        return v


settings = Settings()
