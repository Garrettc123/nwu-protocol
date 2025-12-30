"""Main Agent-Alpha application - RabbitMQ consumer."""

import asyncio
import json
import logging
import signal
import sys
from typing import Dict, Any

import aio_pika
import httpx
import ipfshttpclient

from .config import config
from .verifier import verifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentAlpha:
    """Agent-Alpha: AI Verification Agent."""
    
    def __init__(self):
        """Initialize the agent."""
        self.connection = None
        self.channel = None
        self.running = False
        self.ipfs_client = None
    
    async def connect_ipfs(self):
        """Connect to IPFS."""
        try:
            self.ipfs_client = ipfshttpclient.connect(
                f'/dns/{config.IPFS_HOST}/tcp/{config.IPFS_PORT}/http'
            )
            logger.info("Connected to IPFS")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS: {e}")
            self.ipfs_client = None
    
    async def get_file_from_ipfs(self, ipfs_hash: str) -> bytes:
        """Retrieve file content from IPFS."""
        try:
            if not self.ipfs_client:
                await self.connect_ipfs()
            
            if self.ipfs_client:
                content = self.ipfs_client.cat(ipfs_hash)
                return content
        except Exception as e:
            logger.error(f"Failed to retrieve file from IPFS: {e}")
        return b""
    
    async def submit_verification(self, result: Dict[str, Any]) -> bool:
        """Submit verification result to backend API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.BACKEND_URL}/api/v1/verifications/",
                    json=result,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    logger.info(f"Verification submitted successfully for contribution {result['contribution_id']}")
                    return True
                else:
                    logger.error(f"Failed to submit verification: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error submitting verification: {e}")
            return False
    
    async def process_verification_task(self, task: Dict[str, Any]):
        """Process a verification task."""
        contribution_id = task.get('contribution_id')
        ipfs_hash = task.get('ipfs_hash')
        file_type = task.get('file_type')
        
        logger.info(f"Processing verification task for contribution {contribution_id}")
        
        # Get file content from IPFS
        file_content = await self.get_file_from_ipfs(ipfs_hash)
        if not file_content:
            logger.error(f"Could not retrieve file {ipfs_hash} from IPFS")
            return
        
        # Decode content
        try:
            content_str = file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to decode file content: {e}")
            return
        
        # Perform verification based on file type
        try:
            if file_type == "code":
                result = await verifier.verify_code(content_str, task)
            elif file_type == "dataset":
                result = await verifier.verify_dataset(content_str[:1000], task)  # Sample for datasets
            elif file_type == "document":
                result = await verifier.verify_document(content_str, task)
            else:
                logger.error(f"Unknown file type: {file_type}")
                return
            
            # Prepare verification submission
            verification_data = {
                'contribution_id': contribution_id,
                'agent_id': config.AGENT_ID,
                'agent_type': config.AGENT_TYPE,
                'vote_score': result['vote_score'],
                'quality_score': result.get('quality_score'),
                'originality_score': result.get('originality_score'),
                'security_score': result.get('security_score'),
                'documentation_score': result.get('documentation_score'),
                'reasoning': result.get('reasoning'),
                'details': result.get('details')
            }
            
            # Submit to backend
            await self.submit_verification(verification_data)
            
        except Exception as e:
            logger.error(f"Error during verification: {e}", exc_info=True)
    
    async def on_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming message from RabbitMQ."""
        async with message.process():
            try:
                task = json.loads(message.body.decode())
                logger.info(f"Received task: {task}")
                await self.process_verification_task(task)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode message: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    
    async def start(self):
        """Start the agent and begin consuming messages."""
        logger.info("Starting Agent-Alpha...")
        
        # Connect to IPFS
        await self.connect_ipfs()
        
        # Connect to RabbitMQ
        try:
            self.connection = await aio_pika.connect_robust(config.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare queue
            queue = await self.channel.declare_queue(
                "verifications.pending",
                durable=True
            )
            
            logger.info("Connected to RabbitMQ, waiting for messages...")
            
            # Start consuming
            self.running = True
            await queue.consume(self.on_message)
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in agent: {e}", exc_info=True)
            raise
    
    async def stop(self):
        """Stop the agent gracefully."""
        logger.info("Stopping Agent-Alpha...")
        self.running = False
        
        if self.connection:
            await self.connection.close()
        
        logger.info("Agent-Alpha stopped")


# Create global agent instance
agent = AgentAlpha()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    asyncio.create_task(agent.stop())


async def main():
    """Main entry point."""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
