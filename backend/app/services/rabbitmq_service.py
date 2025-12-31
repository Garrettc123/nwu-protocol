"""RabbitMQ service for message queue management."""

import aio_pika
import json
import logging
from typing import Dict, Any, Optional
from ..config import settings

logger = logging.getLogger(__name__)


class RabbitMQService:
    """RabbitMQ service for message queue operations."""
    
    def __init__(self):
        """Initialize RabbitMQ service."""
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
    
    async def connect(self):
        """Connect to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            self.channel = await self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
    
    async def publish_message(self, queue_name: str, message: Dict[str, Any]):
        """
        Publish message to queue.
        
        Args:
            queue_name: Name of the queue
            message: Message data as dictionary
        """
        try:
            if not self.channel:
                await self.connect()
            
            queue = await self.channel.declare_queue(queue_name, durable=True)
            
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=queue_name
            )
            logger.info(f"Published message to queue {queue_name}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise
    
    async def publish_verification_task(self, contribution_id: int, ipfs_hash: str, file_type: str):
        """
        Publish verification task for agents.
        
        Args:
            contribution_id: ID of the contribution
            ipfs_hash: IPFS hash of the file
            file_type: Type of file (code, dataset, document)
        """
        message = {
            "task_type": "verification",
            "contribution_id": contribution_id,
            "ipfs_hash": ipfs_hash,
            "file_type": file_type
        }
        await self.publish_message("verifications.pending", message)
    
    async def is_connected(self) -> bool:
        """Check if connected to RabbitMQ."""
        return self.connection is not None and not self.connection.is_closed


# Global RabbitMQ service instance
rabbitmq_service = RabbitMQService()
