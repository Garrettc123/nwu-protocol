"""Task Coordinator - Manages task delegation and coordination."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .agent_factory import AgentFactory, AgentType, AgentStatus

logger = logging.getLogger(__name__)


class TaskPriority:
    """Task priority levels."""
    CRITICAL = 10
    HIGH = 7
    MEDIUM = 5
    LOW = 3
    MINIMAL = 1


class TaskCoordinator:
    """
    Coordinates task delegation and execution across multiple agents.

    Responsibilities:
    - Task prioritization
    - Load balancing across agents
    - Task queue management
    - Concurrent task execution
    - Result aggregation
    """

    def __init__(self, agent_factory: AgentFactory):
        """Initialize the task coordinator."""
        self.agent_factory = agent_factory
        self.task_queue: List[Dict[str, Any]] = []
        self.executing_tasks: Dict[str, Dict[str, Any]] = {}

    async def submit_task(
        self,
        task: Dict[str, Any],
        agent_type: Optional[AgentType] = None,
        priority: int = TaskPriority.MEDIUM
    ) -> str:
        """
        Submit a task for execution.

        Args:
            task: Task definition
            agent_type: Specific agent type to use (optional)
            priority: Task priority

        Returns:
            Task ID
        """
        task_id = task.get("task_id", f"task-{len(self.task_queue) + 1}")
        task["task_id"] = task_id
        task["priority"] = priority
        task["submitted_at"] = datetime.utcnow()
        task["agent_type"] = agent_type

        # Add to queue (sorted by priority)
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.get("priority", 0), reverse=True)

        logger.info(f"Task {task_id} submitted with priority {priority}")
        return task_id

    async def process_queue(self):
        """Process tasks from the queue."""
        while self.task_queue:
            task = self.task_queue.pop(0)
            await self._execute_task(task)

    async def _execute_task(self, task: Dict[str, Any]):
        """Execute a single task."""
        task_id = task["task_id"]
        agent_type = task.get("agent_type")

        logger.info(f"Executing task {task_id}")

        # Get appropriate agent
        agent = None
        if agent_type:
            agents = self.agent_factory.get_agents_by_type(agent_type)
            agent = next((a for a in agents if a.status == AgentStatus.IDLE), None)

        if not agent:
            # Get any available agent
            available = self.agent_factory.get_available_agents()
            agent = available[0] if available else None

        if not agent:
            logger.warning(f"No agent available for task {task_id}, requeueing...")
            self.task_queue.append(task)
            await asyncio.sleep(1)
            return

        # Track execution
        self.executing_tasks[task_id] = {
            "task": task,
            "agent_id": agent.agent_id,
            "started_at": datetime.utcnow()
        }

        try:
            # Execute
            result = await agent.execute_task(task)

            # Complete
            self.executing_tasks[task_id]["completed_at"] = datetime.utcnow()
            self.executing_tasks[task_id]["result"] = result
            self.executing_tasks[task_id]["status"] = "completed"

            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            self.executing_tasks[task_id]["status"] = "failed"
            self.executing_tasks[task_id]["error"] = str(e)

    async def delegate_to_multiple_agents(
        self,
        tasks: List[Dict[str, Any]],
        agent_types: Optional[List[AgentType]] = None
    ) -> List[Dict[str, Any]]:
        """
        Delegate multiple tasks to different agents concurrently.

        Args:
            tasks: List of tasks to execute
            agent_types: Optional list of specific agent types for each task

        Returns:
            List of results
        """
        logger.info(f"Delegating {len(tasks)} tasks concurrently")

        # Submit all tasks
        task_ids = []
        for i, task in enumerate(tasks):
            agent_type = agent_types[i] if agent_types and i < len(agent_types) else None
            task_id = await self.submit_task(task, agent_type=agent_type)
            task_ids.append(task_id)

        # Execute all tasks concurrently
        await self.process_queue()

        # Collect results
        results = []
        for task_id in task_ids:
            if task_id in self.executing_tasks:
                results.append(self.executing_tasks[task_id].get("result", {}))

        return results

    def get_queue_status(self) -> Dict[str, Any]:
        """Get task queue status."""
        return {
            "queued_tasks": len(self.task_queue),
            "executing_tasks": len(self.executing_tasks),
            "queue": [
                {
                    "task_id": t["task_id"],
                    "priority": t.get("priority"),
                    "submitted_at": t.get("submitted_at").isoformat() if t.get("submitted_at") else None
                }
                for t in self.task_queue
            ]
        }

    def clear_completed_tasks(self, max_age_seconds: int = 3600):
        """Clear completed tasks older than specified age."""
        now = datetime.utcnow()
        to_remove = []

        for task_id, task_info in self.executing_tasks.items():
            if task_info.get("status") == "completed":
                completed_at = task_info.get("completed_at")
                if completed_at:
                    age = (now - completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(task_id)

        for task_id in to_remove:
            del self.executing_tasks[task_id]

        if to_remove:
            logger.info(f"Cleared {len(to_remove)} completed tasks")
