"""Business Cooperation Lead Agent — Main entry point.

An autonomous business manager that:
- Analyzes incoming tasks via RabbitMQ
- Determines the required agent type
- Delegates tasks to specialized agents via TaskCoordinator
- Monitors agent operations and re-queues failed tasks
- Integrates with the NWU Protocol backend REST API for persistence

Environment variables
---------------------
RABBITMQ_URL              RabbitMQ AMQP URL (default: amqp://guest:guest@localhost:5672)
BACKEND_URL               NWU backend base URL (default: http://backend:8000)
MAX_CONCURRENT_AGENTS     Maximum concurrent agent instances (default: 20)
AGENT_CREATION_ENABLED    Whether new agents may be created (default: true)
AUTO_DELEGATE             Whether tasks are auto-dispatched to agents (default: true)
MAX_CONCURRENT_TASKS      Maximum tasks executing at once (default: 10)
LOG_LEVEL                 Python logging level (default: INFO)
"""

import asyncio
import json
import logging
import os
import signal
import sys
from typing import Any, Dict, Optional

import aio_pika
import httpx

from .agent_factory import AgentFactory, ALL_AGENT_TYPES, AGENT_TYPE_SALES
from .task_coordinator import TaskCoordinator, PRIORITY_NORMAL

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------

RABBITMQ_URL: str = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://backend:8000").rstrip("/")
MAX_CONCURRENT_AGENTS: int = int(os.environ.get("MAX_CONCURRENT_AGENTS", "20"))
AGENT_CREATION_ENABLED: bool = os.environ.get("AGENT_CREATION_ENABLED", "true").lower() == "true"
AUTO_DELEGATE: bool = os.environ.get("AUTO_DELEGATE", "true").lower() == "true"
MAX_CONCURRENT_TASKS: int = int(os.environ.get("MAX_CONCURRENT_TASKS", "10"))
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()

# RabbitMQ queue names
TASK_QUEUE = "business_tasks"
RESULT_QUEUE = "business_results"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("business-lead")

# ---------------------------------------------------------------------------
# BusinessLeadAgent
# ---------------------------------------------------------------------------


class BusinessLeadAgent:
    """
    Autonomous business manager agent.

    Responsibilities:
    1. Connect to RabbitMQ and consume incoming task messages.
    2. Parse each message to determine the appropriate agent type.
    3. Ensure at least one agent of that type is registered (via AgentFactory).
    4. Delegate the task via TaskCoordinator.
    5. Publish results back to the RESULT_QUEUE.
    6. Persist task state to the NWU backend REST API.
    """

    def __init__(self) -> None:
        self.factory = AgentFactory(
            max_concurrent_agents=MAX_CONCURRENT_AGENTS,
            creation_enabled=AGENT_CREATION_ENABLED,
        )
        self.coordinator = TaskCoordinator(
            agent_factory=self.factory,
            max_concurrent_tasks=MAX_CONCURRENT_TASKS,
            auto_delegate=AUTO_DELEGATE,
        )
        self._rabbitmq_connection: Optional[aio_pika.abc.AbstractConnection] = None
        self._rabbitmq_channel: Optional[aio_pika.abc.AbstractChannel] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._running: bool = False

    @property
    def is_running(self) -> bool:
        """Whether the lead agent is currently running."""
        return self._running

    # ------------------------------------------------------------------
    # Startup / shutdown
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Bootstrap all subsystems and begin consuming tasks."""
        logger.info("Business Lead Agent starting …")
        self._http_client = httpx.AsyncClient(base_url=BACKEND_URL, timeout=10.0)

        await self._connect_rabbitmq()
        await self.coordinator.start()

        # Pre-warm one agent of each type so no delay on first task
        if AGENT_CREATION_ENABLED:
            self._prewarm_agents()

        self._running = True
        logger.info("Business Lead Agent is operational.")

    async def stop(self) -> None:
        """Gracefully shut down all subsystems."""
        logger.info("Business Lead Agent shutting down …")
        self._running = False
        await self.coordinator.stop()

        if self._rabbitmq_connection and not self._rabbitmq_connection.is_closed:
            await self._rabbitmq_connection.close()

        if self._http_client:
            await self._http_client.aclose()

        logger.info("Business Lead Agent stopped.")

    # ------------------------------------------------------------------
    # RabbitMQ
    # ------------------------------------------------------------------

    async def _connect_rabbitmq(self) -> None:
        """Establish RabbitMQ connection and declare queues."""
        try:
            self._rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
            self._rabbitmq_channel = await self._rabbitmq_connection.channel()
            await self._rabbitmq_channel.set_qos(prefetch_count=MAX_CONCURRENT_TASKS)

            await self._rabbitmq_channel.declare_queue(TASK_QUEUE, durable=True)
            await self._rabbitmq_channel.declare_queue(RESULT_QUEUE, durable=True)

            task_queue = await self._rabbitmq_channel.get_queue(TASK_QUEUE)
            await task_queue.consume(self._on_task_message)

            logger.info("Connected to RabbitMQ at %s", RABBITMQ_URL)
        except Exception as exc:
            logger.error("Failed to connect to RabbitMQ: %s", exc)
            raise

    async def _publish_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """Publish a task result to the RESULT_QUEUE."""
        if self._rabbitmq_channel is None:
            return
        try:
            payload = json.dumps({"task_id": task_id, "result": result}).encode()
            await self._rabbitmq_channel.default_exchange.publish(
                aio_pika.Message(body=payload, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=RESULT_QUEUE,
            )
        except Exception as exc:
            logger.error("Failed to publish result for task %s: %s", task_id, exc)

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    async def _on_task_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        """Process a single incoming task message."""
        async with message.process():
            try:
                body = json.loads(message.body.decode())
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                logger.error("Invalid message body: %s", exc)
                return

            task_type: str = body.get("task_type", "generic")
            task_data: Dict[str, Any] = body.get("task_data", {})
            priority: int = int(body.get("priority", PRIORITY_NORMAL))
            title: str = body.get("title", f"Task: {task_type}")
            required_agent_type: Optional[str] = body.get("required_agent_type") or self._infer_agent_type(task_type)

            logger.info(
                "Received task message: type=%s agent_type=%s priority=%d",
                task_type, required_agent_type, priority,
            )

            # Ensure an agent exists for the required type
            if required_agent_type and AGENT_CREATION_ENABLED:
                self._ensure_agent_available(required_agent_type)

            # Persist task creation to backend
            backend_task_id: Optional[str] = await self._create_backend_task(
                title=title,
                task_type=task_type,
                task_data=task_data,
                priority=priority,
                required_agent_type=required_agent_type,
            )

            # Submit to coordinator
            coordinator_task_id = await self.coordinator.submit_task(
                task_type=task_type,
                title=title,
                task_data=task_data,
                priority=priority,
                required_agent_type=required_agent_type,
                callback=self._make_completion_callback(backend_task_id),
            )

            logger.info(
                "Delegated message to coordinator as task %s (backend_id=%s)",
                coordinator_task_id, backend_task_id,
            )

    def _make_completion_callback(self, backend_task_id: Optional[str]):
        """Create an async-friendly completion callback."""
        def callback(task_id: str, result: Dict[str, Any]) -> None:
            asyncio.create_task(self._handle_task_completion(task_id, result, backend_task_id))
        return callback

    async def _handle_task_completion(
        self,
        coordinator_task_id: str,
        result: Dict[str, Any],
        backend_task_id: Optional[str],
    ) -> None:
        await self._publish_result(coordinator_task_id, result)
        if backend_task_id:
            await self._update_backend_task(
                backend_task_id, status="completed", result_data=result
            )

    # ------------------------------------------------------------------
    # Agent type inference
    # ------------------------------------------------------------------

    def _infer_agent_type(self, task_type: str) -> Optional[str]:
        """
        Heuristically map a task_type string to one of the 12 agent types.

        Falls back to None (any available agent) when no match is found.
        """
        task_type_lower = task_type.lower()
        keyword_map = {
            "sales": ["sales", "lead", "deal", "pipeline", "prospect", "revenue"],
            "marketing": ["marketing", "campaign", "content", "brand", "seo", "ad"],
            "operations": ["operation", "process", "logistics", "resource", "supply"],
            "finance": ["finance", "budget", "expense", "invoice", "payment", "forecast"],
            "customer_service": ["customer", "support", "ticket", "feedback", "service"],
            "research": ["research", "market", "competitor", "analysis", "trend", "data"],
            "development": ["develop", "code", "feature", "sprint", "engineering", "tech"],
            "qa": ["qa", "quality", "test", "bug", "regression", "defect"],
            "hr": ["hr", "recruit", "hire", "employee", "onboard", "performance"],
            "legal": ["legal", "contract", "compliance", "risk", "policy", "ip"],
            "strategy": ["strategy", "okr", "roadmap", "partnership", "vision", "growth"],
            "project_management": ["project", "pm", "milestone", "deadline", "stakeholder"],
        }
        for agent_type, keywords in keyword_map.items():
            if any(keyword in task_type_lower for keyword in keywords):
                return agent_type
        return None

    # ------------------------------------------------------------------
    # Agent pre-warming
    # ------------------------------------------------------------------

    def _prewarm_agents(self) -> None:
        """Create one idle agent of each type on startup."""
        for agent_type in ALL_AGENT_TYPES:
            try:
                agent = self.factory.create_agent(agent_type=agent_type)
                agent.activate()
                logger.debug("Pre-warmed agent %s (%s)", agent.agent_id, agent_type)
            except Exception as exc:
                logger.warning("Could not pre-warm agent type %s: %s", agent_type, exc)

    def _ensure_agent_available(self, agent_type: str) -> None:
        """Create an agent of the given type if none is currently available."""
        available = self.factory.get_available_agent(agent_type)
        if available is None:
            try:
                new_agent = self.factory.create_agent(agent_type=agent_type)
                new_agent.activate()
                logger.info(
                    "Auto-created agent %s for type '%s'", new_agent.agent_id, agent_type
                )
            except RuntimeError as exc:
                logger.warning("Cannot create agent of type %s: %s", agent_type, exc)

    # ------------------------------------------------------------------
    # Backend REST API integration
    # ------------------------------------------------------------------

    async def _create_backend_task(
        self,
        title: str,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int,
        required_agent_type: Optional[str],
    ) -> Optional[str]:
        """Persist a new task to the NWU backend and return its task_id."""
        if self._http_client is None:
            return None
        payload = {
            "title": title,
            "task_type": task_type,
            "task_data": task_data,
            "priority": priority,
            "required_agent_type": required_agent_type,
        }
        try:
            response = await self._http_client.post("/api/v1/business-tasks/", json=payload)
            response.raise_for_status()
            return response.json().get("task_id")
        except Exception as exc:
            logger.error("Failed to create backend task: %s", exc)
            return None

    async def _update_backend_task(
        self,
        task_id: str,
        status: str,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update an existing backend task record."""
        if self._http_client is None:
            return
        payload: Dict[str, Any] = {"status": status}
        if result_data is not None:
            payload["result_data"] = result_data
        if error_message is not None:
            payload["error_message"] = error_message
        try:
            response = await self._http_client.patch(
                f"/api/v1/business-tasks/{task_id}", json=payload
            )
            response.raise_for_status()
        except Exception as exc:
            logger.error("Failed to update backend task %s: %s", task_id, exc)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """Return a combined status snapshot."""
        return {
            "running": self._running,
            "factory": self.factory.summary(),
            "coordinator": self.coordinator.summary(),
        }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    agent = BusinessLeadAgent()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(agent.stop()))

    await agent.start()

    # Keep running until stopped
    while agent.is_running:
        await asyncio.sleep(5)
        logger.debug("Status: %s", json.dumps(agent.status()))

    logger.info("Business Lead Agent exited cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
