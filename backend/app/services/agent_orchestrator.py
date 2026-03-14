"""Agent Orchestrator Service - Dynamic multi-agent management and spawning."""

import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
import json

from ..config import settings

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents that can be spawned."""
    MASTER = "master"  # Orchestrates other agents
    VERIFIER = "verifier"  # Verifies contributions
    ANALYZER = "analyzer"  # Analyzes data patterns
    COORDINATOR = "coordinator"  # Coordinates multiple tasks
    SPECIALIST = "specialist"  # Domain-specific tasks


class AgentStatus(Enum):
    """Agent lifecycle status."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class AgentCapability:
    """Defines what an agent can do."""
    name: str
    description: str
    task_types: List[str]
    max_concurrent_tasks: int = 5
    requires_dependencies: List[str] = field(default_factory=list)


@dataclass
class AgentMetrics:
    """Agent performance metrics."""
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_task_duration: float = 0.0
    last_task_timestamp: Optional[datetime] = None
    uptime_seconds: float = 0.0
    error_count: int = 0


@dataclass
class AgentInstance:
    """Represents a running agent instance."""
    agent_id: str
    agent_type: AgentType
    status: AgentStatus
    capabilities: List[AgentCapability]
    metrics: AgentMetrics
    created_at: datetime
    last_heartbeat: datetime
    current_tasks: Set[str] = field(default_factory=set)
    config: Dict[str, Any] = field(default_factory=dict)
    parent_agent_id: Optional[str] = None
    child_agent_ids: List[str] = field(default_factory=list)


class AgentOrchestrator:
    """
    Master orchestrator for dynamic multi-agent system.

    This orchestrator can:
    - Spawn new agents dynamically based on workload
    - Manage agent lifecycle (start, stop, pause, resume)
    - Route tasks to appropriate agents
    - Monitor agent health and performance
    - Implement hierarchical agent structures
    - Auto-scale agents based on demand
    """

    def __init__(self):
        """Initialize the orchestrator."""
        self.agents: Dict[str, AgentInstance] = {}
        self.agent_registry: Dict[AgentType, List[str]] = {
            agent_type: [] for agent_type in AgentType
        }
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.master_agent_id: Optional[str] = None

        # Configuration
        self.max_agents_per_type = 10
        self.auto_scale_enabled = True
        self.health_check_interval = 30  # seconds
        self.task_timeout = 300  # seconds

    async def initialize(self):
        """Initialize the orchestrator and spawn master agent."""
        logger.info("Initializing Agent Orchestrator...")
        self.running = True

        # Spawn the master agent
        master_id = await self.spawn_agent(
            agent_type=AgentType.MASTER,
            config={
                "name": "Master Orchestrator",
                "can_spawn_agents": True,
                "max_child_agents": 50
            }
        )
        self.master_agent_id = master_id

        # Start background tasks
        asyncio.create_task(self._health_monitor())
        asyncio.create_task(self._auto_scaler())
        asyncio.create_task(self._task_processor())

        logger.info(f"Agent Orchestrator initialized with master agent {master_id}")

    async def spawn_agent(
        self,
        agent_type: AgentType,
        parent_agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Spawn a new agent instance.

        Args:
            agent_type: Type of agent to spawn
            parent_agent_id: ID of parent agent (for hierarchical structure)
            config: Agent-specific configuration

        Returns:
            agent_id: Unique identifier for the spawned agent
        """
        # Check capacity
        if len(self.agent_registry[agent_type]) >= self.max_agents_per_type:
            logger.warning(f"Maximum agents of type {agent_type} reached")
            return None

        # Generate unique agent ID
        agent_id = f"{agent_type.value}-{uuid.uuid4().hex[:8]}"

        # Define capabilities based on agent type
        capabilities = self._get_agent_capabilities(agent_type)

        # Create agent instance
        agent = AgentInstance(
            agent_id=agent_id,
            agent_type=agent_type,
            status=AgentStatus.INITIALIZING,
            capabilities=capabilities,
            metrics=AgentMetrics(),
            created_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            config=config or {},
            parent_agent_id=parent_agent_id
        )

        # Register agent
        self.agents[agent_id] = agent
        self.agent_registry[agent_type].append(agent_id)

        # Update parent if exists
        if parent_agent_id and parent_agent_id in self.agents:
            self.agents[parent_agent_id].child_agent_ids.append(agent_id)

        # Initialize the agent
        await self._initialize_agent(agent)

        logger.info(f"Spawned agent {agent_id} of type {agent_type}")
        return agent_id

    def _get_agent_capabilities(self, agent_type: AgentType) -> List[AgentCapability]:
        """Get capabilities for an agent type."""
        capabilities_map = {
            AgentType.MASTER: [
                AgentCapability(
                    name="orchestration",
                    description="Orchestrates and spawns other agents",
                    task_types=["orchestrate", "spawn", "coordinate"],
                    max_concurrent_tasks=100
                )
            ],
            AgentType.VERIFIER: [
                AgentCapability(
                    name="verification",
                    description="Verifies contributions using AI",
                    task_types=["verify_code", "verify_dataset", "verify_document"],
                    max_concurrent_tasks=5,
                    requires_dependencies=["openai", "ipfs"]
                )
            ],
            AgentType.ANALYZER: [
                AgentCapability(
                    name="analysis",
                    description="Analyzes patterns and trends",
                    task_types=["analyze_trends", "detect_patterns", "generate_insights"],
                    max_concurrent_tasks=10
                )
            ],
            AgentType.COORDINATOR: [
                AgentCapability(
                    name="coordination",
                    description="Coordinates multiple agents and tasks",
                    task_types=["coordinate", "aggregate_results", "manage_workflow"],
                    max_concurrent_tasks=20
                )
            ],
            AgentType.SPECIALIST: [
                AgentCapability(
                    name="specialized_task",
                    description="Handles domain-specific tasks",
                    task_types=["specialized"],
                    max_concurrent_tasks=3
                )
            ]
        }
        return capabilities_map.get(agent_type, [])

    async def _initialize_agent(self, agent: AgentInstance):
        """Initialize an agent and mark it as active."""
        try:
            # Perform initialization based on agent type
            logger.info(f"Initializing agent {agent.agent_id}...")

            # Simulate initialization (in real implementation, this would start the agent process)
            await asyncio.sleep(0.1)

            # Mark as active
            agent.status = AgentStatus.ACTIVE
            logger.info(f"Agent {agent.agent_id} is now active")

        except Exception as e:
            logger.error(f"Failed to initialize agent {agent.agent_id}: {e}")
            agent.status = AgentStatus.FAILED

    async def stop_agent(self, agent_id: str, graceful: bool = True):
        """
        Stop an agent.

        Args:
            agent_id: ID of agent to stop
            graceful: If True, wait for current tasks to complete
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found")
            return

        agent = self.agents[agent_id]
        agent.status = AgentStatus.STOPPING

        if graceful:
            # Wait for current tasks to complete
            while agent.current_tasks:
                await asyncio.sleep(1)

        # Stop child agents first
        for child_id in agent.child_agent_ids:
            await self.stop_agent(child_id, graceful=graceful)

        # Remove from registry
        self.agent_registry[agent.agent_type].remove(agent_id)
        agent.status = AgentStatus.STOPPED

        logger.info(f"Stopped agent {agent_id}")

    async def assign_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        preferred_agent_type: Optional[AgentType] = None
    ) -> Optional[str]:
        """
        Assign a task to an appropriate agent.

        Args:
            task_type: Type of task
            task_data: Task data
            preferred_agent_type: Preferred agent type (optional)

        Returns:
            agent_id: ID of agent assigned to task, or None if no agent available
        """
        task_id = f"task-{uuid.uuid4().hex[:8]}"

        # Find suitable agent
        agent_id = await self._find_suitable_agent(task_type, preferred_agent_type)

        if not agent_id:
            # No suitable agent found, try to spawn one
            if self.auto_scale_enabled:
                agent_type = preferred_agent_type or AgentType.SPECIALIST
                agent_id = await self.spawn_agent(agent_type)

        if agent_id:
            agent = self.agents[agent_id]
            agent.current_tasks.add(task_id)
            agent.status = AgentStatus.BUSY

            # Execute task asynchronously
            asyncio.create_task(self._execute_task(agent_id, task_id, task_type, task_data))

            logger.info(f"Assigned task {task_id} to agent {agent_id}")
            return agent_id

        logger.warning(f"No suitable agent found for task type {task_type}")
        return None

    async def _find_suitable_agent(
        self,
        task_type: str,
        preferred_agent_type: Optional[AgentType] = None
    ) -> Optional[str]:
        """Find a suitable agent for a task."""
        # Search in preferred type first
        if preferred_agent_type:
            agent_ids = self.agent_registry.get(preferred_agent_type, [])
            for agent_id in agent_ids:
                agent = self.agents[agent_id]
                if self._can_handle_task(agent, task_type):
                    return agent_id

        # Search all agents
        for agent_id, agent in self.agents.items():
            if self._can_handle_task(agent, task_type):
                return agent_id

        return None

    def _can_handle_task(self, agent: AgentInstance, task_type: str) -> bool:
        """Check if agent can handle a task."""
        if agent.status not in [AgentStatus.ACTIVE, AgentStatus.IDLE]:
            return False

        for capability in agent.capabilities:
            if task_type in capability.task_types:
                if len(agent.current_tasks) < capability.max_concurrent_tasks:
                    return True

        return False

    async def _execute_task(
        self,
        agent_id: str,
        task_id: str,
        task_type: str,
        task_data: Dict[str, Any]
    ):
        """Execute a task on an agent."""
        agent = self.agents[agent_id]
        start_time = datetime.utcnow()

        try:
            logger.info(f"Agent {agent_id} executing task {task_id} ({task_type})")

            # Task execution logic would go here
            # This is a placeholder for the actual task execution
            await asyncio.sleep(1)  # Simulate work

            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            agent.metrics.tasks_completed += 1
            agent.metrics.last_task_timestamp = datetime.utcnow()

            # Update average duration
            total_tasks = agent.metrics.tasks_completed + agent.metrics.tasks_failed
            if total_tasks > 1:
                agent.metrics.average_task_duration = (
                    (agent.metrics.average_task_duration * (total_tasks - 1) + duration) / total_tasks
                )
            else:
                agent.metrics.average_task_duration = duration

            logger.info(f"Agent {agent_id} completed task {task_id} in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Agent {agent_id} failed task {task_id}: {e}")
            agent.metrics.tasks_failed += 1
            agent.metrics.error_count += 1

        finally:
            # Remove task and update status
            agent.current_tasks.discard(task_id)
            if not agent.current_tasks:
                agent.status = AgentStatus.IDLE

    async def _health_monitor(self):
        """Monitor agent health and handle failures."""
        while self.running:
            try:
                current_time = datetime.utcnow()

                for agent_id, agent in list(self.agents.items()):
                    # Check heartbeat
                    time_since_heartbeat = (current_time - agent.last_heartbeat).total_seconds()

                    if time_since_heartbeat > 60:  # 60 seconds timeout
                        logger.warning(f"Agent {agent_id} appears unresponsive")
                        agent.status = AgentStatus.FAILED

                        # Attempt recovery
                        await self._recover_agent(agent_id)

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Error in health monitor: {e}")

    async def _recover_agent(self, agent_id: str):
        """Attempt to recover a failed agent."""
        logger.info(f"Attempting to recover agent {agent_id}")

        agent = self.agents[agent_id]
        old_config = agent.config
        old_type = agent.agent_type
        parent_id = agent.parent_agent_id

        # Stop the failed agent
        await self.stop_agent(agent_id, graceful=False)

        # Spawn a replacement
        new_agent_id = await self.spawn_agent(
            agent_type=old_type,
            parent_agent_id=parent_id,
            config=old_config
        )

        logger.info(f"Recovered agent {agent_id} as {new_agent_id}")

    async def _auto_scaler(self):
        """Automatically scale agents based on workload."""
        while self.running:
            try:
                if not self.auto_scale_enabled:
                    await asyncio.sleep(30)
                    continue

                # Check workload for each agent type
                for agent_type, agent_ids in self.agent_registry.items():
                    if agent_type == AgentType.MASTER:
                        continue  # Don't scale master agents

                    # Calculate utilization
                    if agent_ids:
                        busy_agents = sum(
                            1 for agent_id in agent_ids
                            if self.agents[agent_id].status == AgentStatus.BUSY
                        )
                        utilization = busy_agents / len(agent_ids)

                        # Scale up if utilization > 80%
                        if utilization > 0.8 and len(agent_ids) < self.max_agents_per_type:
                            logger.info(f"Scaling up {agent_type.value} agents (utilization: {utilization:.2%})")
                            await self.spawn_agent(
                                agent_type=agent_type,
                                parent_agent_id=self.master_agent_id
                            )

                        # Scale down if utilization < 20% and more than 1 agent
                        elif utilization < 0.2 and len(agent_ids) > 1:
                            # Find idle agent to stop
                            for agent_id in agent_ids:
                                if self.agents[agent_id].status == AgentStatus.IDLE:
                                    logger.info(f"Scaling down {agent_type.value} agents (utilization: {utilization:.2%})")
                                    await self.stop_agent(agent_id)
                                    break

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in auto-scaler: {e}")

    async def _task_processor(self):
        """Process tasks from the queue."""
        while self.running:
            try:
                # Get task from queue
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                # Assign to agent
                await self.assign_task(
                    task_type=task.get('task_type'),
                    task_data=task.get('task_data', {}),
                    preferred_agent_type=task.get('preferred_agent_type')
                )

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing task: {e}")

    async def submit_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        preferred_agent_type: Optional[AgentType] = None
    ):
        """Submit a task to the orchestrator."""
        await self.task_queue.put({
            'task_type': task_type,
            'task_data': task_data,
            'preferred_agent_type': preferred_agent_type
        })

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an agent."""
        if agent_id not in self.agents:
            return None

        agent = self.agents[agent_id]
        return {
            'agent_id': agent.agent_id,
            'agent_type': agent.agent_type.value,
            'status': agent.status.value,
            'metrics': {
                'tasks_completed': agent.metrics.tasks_completed,
                'tasks_failed': agent.metrics.tasks_failed,
                'average_duration': agent.metrics.average_task_duration,
                'error_count': agent.metrics.error_count
            },
            'current_tasks': len(agent.current_tasks),
            'child_agents': len(agent.child_agent_ids),
            'uptime': (datetime.utcnow() - agent.created_at).total_seconds()
        }

    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents."""
        return [
            self.get_agent_status(agent_id)
            for agent_id in self.agents.keys()
        ]

    async def shutdown(self):
        """Shutdown the orchestrator and all agents."""
        logger.info("Shutting down Agent Orchestrator...")
        self.running = False

        # Stop all agents
        for agent_id in list(self.agents.keys()):
            await self.stop_agent(agent_id, graceful=True)

        logger.info("Agent Orchestrator shutdown complete")


# Global orchestrator instance
orchestrator = AgentOrchestrator()
