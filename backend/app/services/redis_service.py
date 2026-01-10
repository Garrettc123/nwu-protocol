"""Redis service for caching and session management."""

import redis.asyncio as redis
import json
import logging
from typing import Optional, Any
from ..config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for caching and session management."""
    
    def __init__(self):
        """Initialize Redis client."""
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            if not self.client:
                await self.connect()
            
            value = await self.client.get(key)
            return value
        except Exception as e:
            logger.error(f"Failed to get from Redis: {e}")
            return None
    
    async def set(self, key: str, value: str, expiry: int = 3600):
        """
        Set value in Redis with expiry.
        
        Args:
            key: Cache key
            value: Value to cache
            expiry: Expiration time in seconds (default: 1 hour)
        """
        try:
            if not self.client:
                await self.connect()
            
            await self.client.setex(key, expiry, value)
            logger.debug(f"Set Redis key: {key}")
        except Exception as e:
            logger.error(f"Failed to set in Redis: {e}")
    
    async def delete(self, key: str):
        """
        Delete key from Redis.
        
        Args:
            key: Cache key
        """
        try:
            if not self.client:
                await self.connect()
            
            await self.client.delete(key)
            logger.debug(f"Deleted Redis key: {key}")
        except Exception as e:
            logger.error(f"Failed to delete from Redis: {e}")
    
    async def get_json(self, key: str) -> Optional[Any]:
        """
        Get JSON value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized JSON value or None
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from Redis key: {key}")
        return None
    
    async def set_json(self, key: str, value: Any, expiry: int = 3600):
        """
        Set JSON value in Redis.
        
        Args:
            key: Cache key
            value: Value to serialize and cache
            expiry: Expiration time in seconds (default: 1 hour)
        """
        try:
            json_value = json.dumps(value)
            await self.set(key, json_value, expiry)
        except Exception as e:
            logger.error(f"Failed to serialize JSON for Redis: {e}")
    
    async def is_connected(self) -> bool:
        """Check if connected to Redis."""
        try:
            if self.client:
                await self.client.ping()
                return True
        except:
            pass
        return False


# Global Redis service instance
redis_service = RedisService()
