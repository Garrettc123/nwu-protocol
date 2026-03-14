"""Task coordinator for the Business Cooperation Lead Agent system.

Provides a priority-based task queue (levels 1–10), load balancing,
and concurrent task execution using asyncio.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .agent_factory import AgentFactory, BusinessAgentInstance, AGENT_STATUS_TERMINATED

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Priority constants (1 = highest, 10 = lowest)
# ---------------------------------------------------------------------------

PRIORITY_CRITICAL = 1
PRIORITY_HIGH = 2
PRIORITY_ELEVATED = 3
PRIORITY_ABOVE_NORMAL = 4
PRIORITY_NORMAL = 5
PRIORITY_BELOW_NORMAL = 6
PRIORITY_LOW = 7
PRIORITY_BACKGROUND = 8
PRIORITY_DEFERRED = 9
PRIORITY_IDLE = 10

PRIORITY_MIN = PRIORITY_CRITICAL
PRIORITY_MAX = PRIORITY_IDLE

# ---------------------------------------------------------------------------
# Task dataclass
# ---------------------------------------------------------------------------


@dataclass(order=True)
class CoordinatorTask:
    """A task queued for execution by the coordinator."""

    priority: int = field(compare=True)
    created_at: datetime = field(compare=True, default_factory=datetime.utcnow)

    # Non-comparable fields
    task_id: str = field(compare=False, default_factory=lambda: f"task-{uuid.uuid4().hex}")
    title: str = field(compare=False, default="Untitled Task")
    task_type: str = field(compare=False, default="generic")
    required_agent_type: Optional[str] = field(compare=False, default=None)
    task_data: Dict[str, Any] = field(compare=False, default_factory=dict)
    max_retries: int = field(compare=False, default=3)
    retry_count: int = field(compare=False, default=0)
    callback: Optional[Callable[[str, Dict[str, Any]], None]] = field(compare=False, default=None)

    # Runtime-populated fields
    result: Optional[Dict[str, Any]] = field(compare=False, default=None)
    error: Optional[str] = field(compare=False, default=None)
    started_at: Optional[datetime] = field(compare=False, default=None)
    completed_at: Optional[datetime] = field(compare=False, default=None)
    assigned_agent_id: Optional[str] = field(compare=False, default=None)
    status: str = field(compare=False, default="queued")


# ---------------------------------------------------------------------------
# TaskCoordinator
# ---------------------------------------------------------------------------


class TaskCoordinator:
    """
    Priority-based task coordinator with load balancing and concurrent execution.

    Features:
    - 10-level priority queue (1 = highest)
    - Load-balanced agent assignment (least-loaded agent first)
    - Configurable max concurrent task execution
    - Automatic retries with configurable max_retries
    - Callback support for task completion/failure events
    """

    def __init__(
        self,
        agent_factory: AgentFactory,
        max_concurrent_tasks: int = 10,
        auto_delegate: bool = True,
    ) -> None:
        self.agent_factory: AgentFactory = agent_factory
        self.max_concurrent_tasks: int = max_concurrent_tasks
        self.auto_delegate: bool = auto_delegate

        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._active_tasks: Dict[str, CoordinatorTask] = {}
        self._completed_tasks: List[CoordinatorTask] = []
        self._failed_tasks: List[CoordinatorTask] = []
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._running: bool = False
        self._worker_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background dispatcher loop."""
        if self._running:
            logger.warning("TaskCoordinator is already running.")
            return
        self._semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        self._running = True
        self._worker_task = asyncio.create_task(self._dispatch_loop())
        logger.info(
            "TaskCoordinator started (max_concurrent=%d, auto_delegate=%s)",
            self.max_concurrent_tasks,
            self.auto_delegate,
        )

    async def stop(self) -> None:
        """Stop the dispatcher loop gracefully."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("TaskCoordinator stopped.")

    # ------------------------------------------------------------------
    # Task submission
    # ------------------------------------------------------------------

    async def submit_task(
        self,
        task_type: str,
        title: str = "Untitled Task",
        task_data: Optional[Dict[str, Any]] = None,
        priority: int = PRIORITY_NORMAL,
        required_agent_type: Optional[str] = None,
        max_retries: int = 3,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> str:
        """
        Enqueue a task for execution.

        Args:
            task_type: Identifies the nature of the task.
            title: Human-readable task title.
            task_data: Arbitrary payload forwarded to the agent handler.
            priority: 1 (highest) to 10 (lowest).
            required_agent_type: If set, only agents of this type may handle it.
            max_retries: Maximum automatic retries on failure.
            callback: Optional callable(task_id, result_or_error) invoked on completion.

        Returns:
            The generated task_id string.
        """
        if not (PRIORITY_MIN <= priority <= PRIORITY_MAX):
            raise ValueError(f"Priority must be between {PRIORITY_MIN} and {PRIORITY_MAX}.")

        task = CoordinatorTask(
            priority=priority,
            task_type=task_type,
            title=title,
            task_data=task_data or {},
            required_agent_type=required_agent_type,
            max_retries=max_retries,
            callback=callback,
        )

        await self._queue.put(task)
        logger.info(
            "Task %s enqueued (type=%s, priority=%d)", task.task_id, task_type, priority
        )
        return task.task_id

    # ------------------------------------------------------------------
    # Dispatcher loop
    # ------------------------------------------------------------------

    async def _dispatch_loop(self) -> None:
        """Continuously pull tasks from the priority queue and dispatch them."""
        while self._running:
            try:
                task: CoordinatorTask = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            if self.auto_delegate:
                asyncio.create_task(self._execute_task(task))
            else:
                logger.debug("Auto-delegate disabled; task %s left unprocessed.", task.task_id)
                self._queue.task_done()

    # ------------------------------------------------------------------
    # Task execution
    # ------------------------------------------------------------------

    async def _execute_task(self, task: CoordinatorTask) -> None:
        """Execute a single task inside the concurrency semaphore."""
        assert self._semaphore is not None, "Semaphore not initialised — call start() first."

        async with self._semaphore:
            agent = self._select_agent(task.required_agent_type)

            if agent is None:
                logger.warning(
                    "No available agent for task %s (type=%s). Re-queuing.",
                    task.task_id,
                    task.required_agent_type or "any",
                )
                await asyncio.sleep(2)
                await self._queue.put(task)
                self._queue.task_done()
                return

            task.assigned_agent_id = agent.agent_id
            task.started_at = datetime.utcnow()
            task.status = "in_progress"
            self._active_tasks[task.task_id] = task

            try:
                # Run the potentially blocking handler in the default executor
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, agent.execute_task, task.task_data
                )
                task.result = result
                task.completed_at = datetime.utcnow()
                task.status = "completed"
                self._completed_tasks.append(task)
                logger.info("Task %s completed by agent %s", task.task_id, agent.agent_id)

                if task.callback:
                    try:
                        task.callback(task.task_id, result)
                    except Exception as callback_exc:
                        logger.error(
                            "Task %s callback raised an error: %s", task.task_id, callback_exc
                        )

            except Exception as exc:
                task.error = str(exc)
                task.retry_count += 1

                if task.retry_count <= task.max_retries:
                    logger.warning(
                        "Task %s failed (attempt %d/%d), retrying: %s",
                        task.task_id,
                        task.retry_count,
                        task.max_retries,
                        exc,
                    )
                    task.status = "queued"
                    await self._queue.put(task)
                else:
                    task.completed_at = datetime.utcnow()
                    task.status = "failed"
                    self._failed_tasks.append(task)
                    logger.error(
                        "Task %s permanently failed after %d retries: %s",
                        task.task_id,
                        task.retry_count,
                        exc,
                    )

            finally:
                self._active_tasks.pop(task.task_id, None)
                self._queue.task_done()

    # ------------------------------------------------------------------
    # Load balancing
    # ------------------------------------------------------------------

    def _select_agent(self, required_agent_type: Optional[str]) -> Optional[BusinessAgentInstance]:
        """
        Select the least-loaded available agent.

        Prefers agents of the required type if specified, otherwise picks
        from all non-terminated, non-busy agents and returns the one with
        the fewest completed tasks (as a proxy for workload recency).
        """
        if required_agent_type:
            candidates = [
                a
                for a in self.agent_factory.get_agents_by_type(required_agent_type)
                if a.status not in (AGENT_STATUS_TERMINATED, "busy")
            ]
        else:
            candidates = [
                a
                for a in self.agent_factory.all_agents
                if a.status not in (AGENT_STATUS_TERMINATED, "busy")
            ]

        if not candidates:
            return None

        # Least-loaded = fewest tasks_completed (most capacity remaining)
        return min(candidates, key=lambda a: a.tasks_completed)

    # ------------------------------------------------------------------
    # Status / reporting
    # ------------------------------------------------------------------

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    @property
    def active_task_count(self) -> int:
        return len(self._active_tasks)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Return status information for a task by ID."""
        # Check active
        task = self._active_tasks.get(task_id)
        if task:
            return _task_to_dict(task)
        # Check completed
        for completed_task in self._completed_tasks:
            if completed_task.task_id == task_id:
                return _task_to_dict(completed_task)
        # Check failed
        for failed_task in self._failed_tasks:
            if failed_task.task_id == task_id:
                return _task_to_dict(failed_task)
        return None

    def summary(self) -> Dict[str, Any]:
        """Return coordinator performance summary."""
        return {
            "running": self._running,
            "queue_size": self.queue_size,
            "active_tasks": self.active_task_count,
            "completed_tasks": len(self._completed_tasks),
            "failed_tasks": len(self._failed_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "auto_delegate": self.auto_delegate,
        }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _task_to_dict(task: CoordinatorTask) -> Dict[str, Any]:
    return {
        "task_id": task.task_id,
        "title": task.title,
        "task_type": task.task_type,
        "required_agent_type": task.required_agent_type,
        "priority": task.priority,
        "status": task.status,
        "retry_count": task.retry_count,
        "max_retries": task.max_retries,
        "assigned_agent_id": task.assigned_agent_id,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
