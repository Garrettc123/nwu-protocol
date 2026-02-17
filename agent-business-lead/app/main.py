"""Business Cooperation Lead Agent - Autonomous business management."""

import asyncio
import json
import logging
import signal
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

import aio_pika
import httpx

from .config import config
from .agent_factory import AgentFactory, AgentType, AgentStatus
from .task_coordinator import TaskCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BusinessCooperationLeadAgent:
    """
    Business Cooperation Lead Agent - Manages business operations autonomously.

    This agent:
    - Continues business operations autonomously when the owner is not around
    - Creates specialized agents for specific tasks
    - Delegates tasks to appropriate agents
    - Monitors and coordinates all business activities
    - Makes intelligent decisions based on priorities and business rules
    """

    def __init__(self):
        """Initialize the Business Cooperation Lead Agent."""
        self.agent_id = config.AGENT_ID
        self.connection = None
        self.channel = None
        self.running = False

        # Initialize agent factory and coordinator
        self.agent_factory = AgentFactory(max_agents=config.MAX_CONCURRENT_AGENTS)
        self.task_coordinator = TaskCoordinator(self.agent_factory)

        # Business state
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: List[Dict[str, Any]] = []
        self.business_metrics = {
            "tasks_processed": 0,
            "agents_created": 0,
            "decisions_made": 0,
            "uptime": 0
        }
        self.start_time = None

    async def start(self):
        """Start the Business Cooperation Lead Agent."""
        logger.info("=" * 80)
        logger.info("STARTING BUSINESS COOPERATION LEAD AGENT")
        logger.info("=" * 80)
        logger.info(f"Agent ID: {self.agent_id}")
        logger.info(f"Max Concurrent Agents: {config.MAX_CONCURRENT_AGENTS}")
        logger.info(f"Auto-Delegation: {config.AUTO_DELEGATE}")
        logger.info(f"Agent Creation: {config.AGENT_CREATION_ENABLED}")
        logger.info("=" * 80)

        self.start_time = datetime.utcnow()

        # Initialize default agents for common business operations
        await self._initialize_core_agents()

        # Connect to RabbitMQ for task queue
        try:
            self.connection = await aio_pika.connect_robust(config.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=5)

            # Declare business tasks queue
            queue = await self.channel.declare_queue(
                "business.tasks",
                durable=True
            )

            logger.info("Connected to RabbitMQ, ready to manage business operations...")

            # Start consuming tasks
            self.running = True
            await queue.consume(self.on_message)

            # Start background monitoring
            asyncio.create_task(self._monitor_operations())

            # Keep running
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in Business Lead Agent: {e}", exc_info=True)
            raise

    async def _initialize_core_agents(self):
        """Initialize core agents for essential business functions."""
        logger.info("Initializing core business agents...")

        core_agents = [
            (AgentType.OPERATIONS, "Operations-Core"),
            (AgentType.CUSTOMER_SERVICE, "CustomerService-Core"),
            (AgentType.FINANCE, "Finance-Core")
        ]

        for agent_type, agent_name in core_agents:
            agent = self.agent_factory.create_agent(agent_type, name=agent_name)
            if agent:
                logger.info(f"  ✓ Created {agent_name}")
                self.business_metrics["agents_created"] += 1
            else:
                logger.warning(f"  ✗ Failed to create {agent_name}")

    async def on_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming business tasks."""
        async with message.process():
            try:
                task = json.loads(message.body.decode())
                logger.info(f"Received business task: {task.get('task_id', 'unknown')}")

                # Process the business task
                await self.process_business_task(task)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode message: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

    async def process_business_task(self, task: Dict[str, Any]):
        """
        Process a business task intelligently.

        This method:
        1. Analyzes the task
        2. Determines the best agent type to handle it
        3. Creates a new agent if needed
        4. Delegates the task
        5. Monitors execution
        """
        task_id = task.get("task_id", str(uuid.uuid4()))
        task_type = task.get("task_type", "general")
        task_data = task.get("data", {})
        priority = task.get("priority", 5)

        logger.info(f"Processing business task {task_id} [Type: {task_type}, Priority: {priority}]")

        # Track the task
        self.active_tasks[task_id] = {
            "task": task,
            "started_at": datetime.utcnow(),
            "status": "analyzing"
        }

        try:
            # Analyze and determine the appropriate agent type
            required_agent_type = await self._determine_agent_type(task)
            logger.info(f"Task {task_id} requires: {required_agent_type.value}")

            # Find or create appropriate agent
            agent = await self._get_or_create_agent(required_agent_type)

            if not agent:
                logger.error(f"Could not obtain agent for task {task_id}")
                self.active_tasks[task_id]["status"] = "failed"
                self.active_tasks[task_id]["error"] = "No agent available"
                return

            # Delegate task to agent
            self.active_tasks[task_id]["status"] = "executing"
            self.active_tasks[task_id]["agent_id"] = agent.agent_id

            result = await agent.execute_task(task)

            # Mark as completed
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["completed_at"] = datetime.utcnow()
            self.active_tasks[task_id]["result"] = result

            # Move to completed tasks
            self.completed_tasks.append(self.active_tasks[task_id])
            del self.active_tasks[task_id]

            # Update metrics
            self.business_metrics["tasks_processed"] += 1

            logger.info(f"✓ Task {task_id} completed successfully")

            # Report result back to backend
            await self._report_task_result(task_id, result)

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
            self.active_tasks[task_id]["status"] = "error"
            self.active_tasks[task_id]["error"] = str(e)

    async def _determine_agent_type(self, task: Dict[str, Any]) -> AgentType:
        """Determine which type of agent is best suited for the task."""
        task_type = task.get("task_type", "").lower()
        category = task.get("category", "").lower()

        # Intelligent mapping of tasks to agent types
        mappings = {
            "sales": AgentType.SALES,
            "lead": AgentType.SALES,
            "client": AgentType.SALES,
            "marketing": AgentType.MARKETING,
            "campaign": AgentType.MARKETING,
            "content": AgentType.MARKETING,
            "operations": AgentType.OPERATIONS,
            "process": AgentType.OPERATIONS,
            "workflow": AgentType.OPERATIONS,
            "finance": AgentType.FINANCE,
            "budget": AgentType.FINANCE,
            "invoice": AgentType.FINANCE,
            "customer": AgentType.CUSTOMER_SERVICE,
            "support": AgentType.CUSTOMER_SERVICE,
            "ticket": AgentType.CUSTOMER_SERVICE,
            "research": AgentType.RESEARCH,
            "analysis": AgentType.RESEARCH,
            "development": AgentType.DEVELOPMENT,
            "code": AgentType.DEVELOPMENT,
            "qa": AgentType.QUALITY_ASSURANCE,
            "test": AgentType.QUALITY_ASSURANCE,
            "hr": AgentType.HUMAN_RESOURCES,
            "recruitment": AgentType.HUMAN_RESOURCES,
            "legal": AgentType.LEGAL,
            "contract": AgentType.LEGAL,
            "strategy": AgentType.STRATEGY,
            "planning": AgentType.STRATEGY,
            "project": AgentType.PROJECT_MANAGEMENT,
            "coordination": AgentType.PROJECT_MANAGEMENT
        }

        # Check task type and category
        for keyword, agent_type in mappings.items():
            if keyword in task_type or keyword in category:
                self.business_metrics["decisions_made"] += 1
                return agent_type

        # Default to operations for general tasks
        return AgentType.OPERATIONS

    async def _get_or_create_agent(self, agent_type: AgentType) -> Optional[object]:
        """Get an available agent or create a new one if needed."""
        # Try to find an idle agent of the required type
        agents = self.agent_factory.get_agents_by_type(agent_type)
        for agent in agents:
            if agent.status == AgentStatus.IDLE:
                logger.info(f"Using existing agent: {agent.name}")
                return agent

        # No idle agent found, create a new one if enabled
        if config.AGENT_CREATION_ENABLED:
            logger.info(f"Creating new {agent_type.value} agent...")
            agent = self.agent_factory.create_agent(agent_type)
            if agent:
                self.business_metrics["agents_created"] += 1
                logger.info(f"✓ Created new agent: {agent.name}")
            return agent

        # Use the first available agent even if busy (will queue)
        if agents:
            logger.warning(f"All {agent_type.value} agents busy, using first available")
            return agents[0]

        return None

    async def _report_task_result(self, task_id: str, result: Dict[str, Any]):
        """Report task result back to the backend API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.BACKEND_URL}/api/v1/business-tasks/results",
                    json={
                        "task_id": task_id,
                        "agent_id": self.agent_id,
                        "result": result,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    timeout=30.0
                )

                if response.status_code in [200, 201]:
                    logger.info(f"Task result reported for {task_id}")
                else:
                    logger.warning(f"Failed to report result: {response.status_code}")

        except Exception as e:
            logger.error(f"Error reporting task result: {e}")

    async def _monitor_operations(self):
        """Monitor business operations and agent health."""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Update uptime
                if self.start_time:
                    uptime = (datetime.utcnow() - self.start_time).total_seconds()
                    self.business_metrics["uptime"] = int(uptime)

                # Get factory status
                factory_status = self.agent_factory.get_factory_status()

                # Log status
                logger.info("=" * 80)
                logger.info("BUSINESS OPERATIONS STATUS")
                logger.info(f"Active Tasks: {len(self.active_tasks)}")
                logger.info(f"Completed Tasks: {len(self.completed_tasks)}")
                logger.info(f"Total Agents: {factory_status['total_agents']}")
                logger.info(f"Available Capacity: {factory_status['available_capacity']}")
                logger.info(f"Tasks Processed: {self.business_metrics['tasks_processed']}")
                logger.info(f"Agents Created: {self.business_metrics['agents_created']}")
                logger.info(f"Uptime: {self.business_metrics['uptime']}s")
                logger.info("=" * 80)

            except Exception as e:
                logger.error(f"Error in monitoring: {e}")

    async def stop(self):
        """Stop the Business Cooperation Lead Agent gracefully."""
        logger.info("Stopping Business Cooperation Lead Agent...")
        self.running = False

        # Terminate all agents
        for agent in self.agent_factory.get_all_agents():
            agent.terminate()

        if self.connection:
            await self.connection.close()

        logger.info("Business Cooperation Lead Agent stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the business operations."""
        return {
            "agent_id": self.agent_id,
            "status": "running" if self.running else "stopped",
            "uptime": self.business_metrics["uptime"],
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "metrics": self.business_metrics,
            "factory_status": self.agent_factory.get_factory_status(),
            "agents": [agent.get_status() for agent in self.agent_factory.get_all_agents()]
        }


# Global agent instance
business_lead_agent = BusinessCooperationLeadAgent()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    asyncio.create_task(business_lead_agent.stop())


async def main():
    """Main entry point."""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await business_lead_agent.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await business_lead_agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
