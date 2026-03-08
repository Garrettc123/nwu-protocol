"""Base Agent Class - Foundation for all spawnable agents."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

from .agent_orchestrator import AgentStatus, AgentType

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the system.

    Agents spawned by the orchestrator inherit from this class
    and implement task-specific logic.
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type of agent
            config: Agent configuration
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}
        self.status = AgentStatus.INITIALIZING
        self.running = False
        self.last_heartbeat = datetime.utcnow()

        # Capabilities
        self.can_spawn_agents = config.get('can_spawn_agents', False)
        self.max_child_agents = config.get('max_child_agents', 10)
        self.child_agents: List[str] = []

        logger.info(f"Initialized {self.agent_type.value} agent: {self.agent_id}")

    @abstractmethod
    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task (must be implemented by subclasses).

        Args:
            task_type: Type of task to execute
            task_data: Task data

        Returns:
            result: Task execution result
        """
        pass

    @abstractmethod
    async def initialize(self):
        """Initialize the agent (must be implemented by subclasses)."""
        pass

    async def start(self):
        """Start the agent."""
        logger.info(f"Starting agent {self.agent_id}...")
        self.running = True
        self.status = AgentStatus.ACTIVE

        # Initialize agent-specific resources
        await self.initialize()

        # Start heartbeat
        asyncio.create_task(self._heartbeat_loop())

        logger.info(f"Agent {self.agent_id} started successfully")

    async def stop(self):
        """Stop the agent."""
        logger.info(f"Stopping agent {self.agent_id}...")
        self.running = False
        self.status = AgentStatus.STOPPED

        # Stop child agents if any
        await self._stop_child_agents()

        logger.info(f"Agent {self.agent_id} stopped")

    async def pause(self):
        """Pause the agent."""
        logger.info(f"Pausing agent {self.agent_id}")
        self.status = AgentStatus.PAUSED

    async def resume(self):
        """Resume the agent."""
        logger.info(f"Resuming agent {self.agent_id}")
        self.status = AgentStatus.ACTIVE

    async def spawn_child_agent(
        self,
        agent_type: AgentType,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Spawn a child agent (if this agent has spawning capability).

        Args:
            agent_type: Type of agent to spawn
            config: Configuration for child agent

        Returns:
            child_agent_id: ID of spawned child agent, or None if failed
        """
        if not self.can_spawn_agents:
            logger.warning(f"Agent {self.agent_id} does not have spawning capability")
            return None

        if len(self.child_agents) >= self.max_child_agents:
            logger.warning(f"Agent {self.agent_id} has reached max child agents limit")
            return None

        # Import here to avoid circular dependency
        from .agent_orchestrator import orchestrator

        child_id = await orchestrator.spawn_agent(
            agent_type=agent_type,
            parent_agent_id=self.agent_id,
            config=config
        )

        if child_id:
            self.child_agents.append(child_id)
            logger.info(f"Agent {self.agent_id} spawned child agent {child_id}")

        return child_id

    async def _stop_child_agents(self):
        """Stop all child agents."""
        from .agent_orchestrator import orchestrator

        for child_id in self.child_agents:
            await orchestrator.stop_agent(child_id)

        self.child_agents.clear()

    async def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self.running:
            self.last_heartbeat = datetime.utcnow()
            await asyncio.sleep(10)  # Heartbeat every 10 seconds

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'status': self.status.value,
            'child_agents': len(self.child_agents),
            'can_spawn_agents': self.can_spawn_agents,
            'last_heartbeat': self.last_heartbeat.isoformat()
        }


class MasterAgent(BaseAgent):
    """
    Master Agent - The top-level orchestrator that can spawn and manage other agents.

    This is the "god bot" that creates and coordinates all other agents.
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize master agent."""
        super().__init__(agent_id, AgentType.MASTER, config)
        self.can_spawn_agents = True

    async def initialize(self):
        """Initialize master agent."""
        logger.info(f"Master Agent {self.agent_id} initializing...")

        # Spawn initial set of worker agents
        initial_verifiers = self.config.get('initial_verifiers', 2)
        for i in range(initial_verifiers):
            await self.spawn_child_agent(
                agent_type=AgentType.VERIFIER,
                config={'name': f'Verifier-{i+1}'}
            )

        logger.info(f"Master Agent {self.agent_id} initialized with {len(self.child_agents)} agents")

    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute orchestration tasks.

        Master agent handles high-level orchestration and delegates to child agents.
        """
        if task_type == "orchestrate":
            return await self._orchestrate_workflow(task_data)
        elif task_type == "spawn":
            child_id = await self.spawn_child_agent(
                agent_type=AgentType(task_data.get('agent_type', 'specialist')),
                config=task_data.get('config', {})
            )
            return {'success': child_id is not None, 'child_id': child_id}
        elif task_type == "coordinate":
            return await self._coordinate_agents(task_data)
        else:
            logger.warning(f"Unknown task type for master agent: {task_type}")
            return {'success': False, 'error': 'Unknown task type'}

    async def _orchestrate_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate a complex workflow across multiple agents."""
        workflow_id = workflow_data.get('workflow_id')
        steps = workflow_data.get('steps', [])

        logger.info(f"Master Agent orchestrating workflow {workflow_id} with {len(steps)} steps")

        results = []
        for step in steps:
            # Determine which agent type should handle this step
            agent_type = self._determine_agent_type_for_step(step)

            # Spawn specialized agent if needed
            agent_id = await self.spawn_child_agent(agent_type, config=step.get('config'))

            if agent_id:
                results.append({
                    'step': step.get('name'),
                    'agent_id': agent_id,
                    'status': 'assigned'
                })
            else:
                results.append({
                    'step': step.get('name'),
                    'status': 'failed',
                    'error': 'Could not spawn agent'
                })

        return {
            'success': True,
            'workflow_id': workflow_id,
            'results': results
        }

    def _determine_agent_type_for_step(self, step: Dict[str, Any]) -> AgentType:
        """Determine which agent type should handle a workflow step."""
        step_type = step.get('type', 'specialized')

        type_mapping = {
            'verification': AgentType.VERIFIER,
            'analysis': AgentType.ANALYZER,
            'coordination': AgentType.COORDINATOR,
            'specialized': AgentType.SPECIALIST
        }

        return type_mapping.get(step_type, AgentType.SPECIALIST)

    async def _coordinate_agents(self, coordination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate multiple agents for a complex task."""
        logger.info(f"Master Agent coordinating {len(self.child_agents)} child agents")

        # Distribute work among child agents
        tasks = coordination_data.get('tasks', [])
        results = []

        from .agent_orchestrator import orchestrator

        for task in tasks:
            # Assign task through orchestrator
            agent_id = await orchestrator.assign_task(
                task_type=task.get('type'),
                task_data=task.get('data', {}),
                preferred_agent_type=task.get('preferred_type')
            )

            results.append({
                'task': task.get('name'),
                'assigned_to': agent_id,
                'status': 'assigned' if agent_id else 'failed'
            })

        return {
            'success': True,
            'coordinated_tasks': len(results),
            'results': results
        }


class VerifierAgent(BaseAgent):
    """
    Verifier Agent - Specialized agent for verifying contributions.

    Can be spawned dynamically by the master agent or orchestrator.
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize verifier agent."""
        super().__init__(agent_id, AgentType.VERIFIER, config)

    async def initialize(self):
        """Initialize verifier agent."""
        logger.info(f"Verifier Agent {self.agent_id} initializing...")
        # Initialize AI models, connections, etc.
        logger.info(f"Verifier Agent {self.agent_id} ready")

    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute verification tasks."""
        if task_type in ['verify_code', 'verify_dataset', 'verify_document']:
            return await self._verify_contribution(task_type, task_data)
        else:
            return {'success': False, 'error': f'Unknown task type: {task_type}'}

    async def _verify_contribution(
        self,
        verification_type: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify a contribution."""
        contribution_id = task_data.get('contribution_id')
        ipfs_hash = task_data.get('ipfs_hash')

        logger.info(f"Verifier {self.agent_id} verifying contribution {contribution_id}")

        # Verification logic would go here
        # This is a placeholder for the actual verification
        await asyncio.sleep(1)

        return {
            'success': True,
            'contribution_id': contribution_id,
            'verification_type': verification_type,
            'quality_score': 85.0,
            'verified_by': self.agent_id
        }


class AnalyzerAgent(BaseAgent):
    """
    Analyzer Agent - Specialized agent for analyzing patterns and trends.
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize analyzer agent."""
        super().__init__(agent_id, AgentType.ANALYZER, config)

    async def initialize(self):
        """Initialize analyzer agent."""
        logger.info(f"Analyzer Agent {self.agent_id} initializing...")
        logger.info(f"Analyzer Agent {self.agent_id} ready")

    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis tasks."""
        if task_type == 'analyze_trends':
            return await self._analyze_trends(task_data)
        elif task_type == 'detect_patterns':
            return await self._detect_patterns(task_data)
        elif task_type == 'generate_insights':
            return await self._generate_insights(task_data)
        else:
            return {'success': False, 'error': f'Unknown task type: {task_type}'}

    async def _analyze_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends in data."""
        logger.info(f"Analyzer {self.agent_id} analyzing trends")
        await asyncio.sleep(1)
        return {'success': True, 'trends': [], 'analyzed_by': self.agent_id}

    async def _detect_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect patterns in data."""
        logger.info(f"Analyzer {self.agent_id} detecting patterns")
        await asyncio.sleep(1)
        return {'success': True, 'patterns': [], 'analyzed_by': self.agent_id}

    async def _generate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from data."""
        logger.info(f"Analyzer {self.agent_id} generating insights")
        await asyncio.sleep(1)
        return {'success': True, 'insights': [], 'analyzed_by': self.agent_id}


class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent - Coordinates multiple agents and aggregates results.
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize coordinator agent."""
        super().__init__(agent_id, AgentType.COORDINATOR, config)
        self.can_spawn_agents = True  # Coordinators can spawn agents

    async def initialize(self):
        """Initialize coordinator agent."""
        logger.info(f"Coordinator Agent {self.agent_id} initializing...")
        logger.info(f"Coordinator Agent {self.agent_id} ready")

    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coordination tasks."""
        if task_type == 'coordinate':
            return await self._coordinate_tasks(task_data)
        elif task_type == 'aggregate_results':
            return await self._aggregate_results(task_data)
        elif task_type == 'manage_workflow':
            return await self._manage_workflow(task_data)
        else:
            return {'success': False, 'error': f'Unknown task type: {task_type}'}

    async def _coordinate_tasks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate multiple tasks."""
        tasks = data.get('tasks', [])
        logger.info(f"Coordinator {self.agent_id} coordinating {len(tasks)} tasks")

        results = []
        for task in tasks:
            # Spawn agent for each task if needed
            agent_type = AgentType(task.get('agent_type', 'specialist'))
            agent_id = await self.spawn_child_agent(agent_type)

            if agent_id:
                results.append({'task': task.get('name'), 'agent_id': agent_id})

        return {'success': True, 'coordinated': len(results), 'results': results}

    async def _aggregate_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from multiple agents."""
        logger.info(f"Coordinator {self.agent_id} aggregating results")
        await asyncio.sleep(1)
        return {'success': True, 'aggregated': True, 'coordinator': self.agent_id}

    async def _manage_workflow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage a workflow."""
        logger.info(f"Coordinator {self.agent_id} managing workflow")
        await asyncio.sleep(1)
        return {'success': True, 'workflow_managed': True, 'coordinator': self.agent_id}
