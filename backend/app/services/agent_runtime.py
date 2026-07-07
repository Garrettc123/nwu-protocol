"""Systematic runtime modules for producer/worker/lifecycle/observability."""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)


class TaskState(Enum):
    """Shared task lifecycle states."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRIED = "retried"
    DEAD_LETTERED = "dead_lettered"


@dataclass
class TaskErrorContract:
    """Strict error contract for task failures."""

    code: str
    message: str
    retryable: bool = True


@dataclass
class TaskEnvelope:
    """Strict input contract for task execution."""

    task_id: str
    task_type: str
    task_data: Dict[str, Any]
    preferred_agent_type: Any = None
    retry_count: int = 0


@dataclass
class TaskResult:
    """Strict output contract for task execution."""

    task_id: str
    state: TaskState
    agent_id: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[TaskErrorContract] = None


class TaskProducerContract(Protocol):
    """Producer contract: enqueue/dequeue only."""

    async def submit(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        preferred_agent_type: Any = None,
        task_id: Optional[str] = None,
        retry_count: int = 0,
    ) -> TaskEnvelope: ...

    async def dequeue(self, timeout: float = 1.0) -> Optional[TaskEnvelope]: ...


class TaskWorkerContract(Protocol):
    """Worker contract: execute one task unit only."""

    async def execute_one(self, agent_id: str, task: TaskEnvelope) -> TaskResult: ...


class LifecycleManagerContract(Protocol):
    """Lifecycle contract: select/scale/recover workers."""

    async def select_or_provision(
        self,
        task_type: str,
        preferred_agent_type: Any,
        find_agent: Callable[[str, Any], Awaitable[Optional[str]]],
        spawn_agent: Callable[[Any], Awaitable[Optional[str]]],
        default_agent_type: Any,
    ) -> Optional[str]: ...


class ObservabilityContract(Protocol):
    """Observability contract: passively record events."""

    def record_task_state(self, task_id: str, state: TaskState, details: Optional[Dict[str, Any]] = None) -> None: ...


class SharedTaskStateModel:
    """Centralized task state transitions used by all modules."""

    _allowed_transitions = {
        TaskState.QUEUED: {TaskState.RUNNING, TaskState.DEAD_LETTERED},
        TaskState.RUNNING: {TaskState.SUCCEEDED, TaskState.FAILED},
        TaskState.FAILED: {TaskState.RETRIED, TaskState.DEAD_LETTERED},
        TaskState.RETRIED: {TaskState.QUEUED, TaskState.DEAD_LETTERED},
    }

    def __init__(self):
        self._state: Dict[str, TaskState] = {}
        self._history: Dict[str, List[TaskState]] = {}

    def transition(self, task_id: str, state: TaskState) -> None:
        current = self._state.get(task_id)
        if current is not None and current != state:
            allowed = self._allowed_transitions.get(current, set())
            if state not in allowed:
                raise ValueError(f"Invalid transition {current.value} -> {state.value} for {task_id}")

        self._state[task_id] = state
        self._history.setdefault(task_id, []).append(state)

    def get_state(self, task_id: str) -> Optional[TaskState]:
        return self._state.get(task_id)

    def get_history(self, task_id: str) -> List[TaskState]:
        return list(self._history.get(task_id, []))


class ProducerService(TaskProducerContract):
    """Producer-only service for queueing work."""

    def __init__(self, state_model: SharedTaskStateModel):
        self._queue: asyncio.Queue[TaskEnvelope] = asyncio.Queue()
        self._state_model = state_model

    async def submit(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        preferred_agent_type: Any = None,
        task_id: Optional[str] = None,
        retry_count: int = 0,
    ) -> TaskEnvelope:
        envelope = TaskEnvelope(
            task_id=task_id or f"task-{uuid.uuid4().hex[:8]}",
            task_type=task_type,
            task_data=task_data,
            preferred_agent_type=preferred_agent_type,
            retry_count=retry_count,
        )
        self._state_model.transition(envelope.task_id, TaskState.QUEUED)
        await self._queue.put(envelope)
        return envelope

    async def dequeue(self, timeout: float = 1.0) -> Optional[TaskEnvelope]:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None


class WorkerService(TaskWorkerContract):
    """Worker service that executes a single task unit per invocation."""

    def __init__(
        self,
        state_model: SharedTaskStateModel,
        observability: ObservabilityContract,
        execute_unit: Callable[[str, TaskEnvelope], Awaitable[Dict[str, Any]]],
        max_retries: int = 1,
    ):
        self._state_model = state_model
        self._observability = observability
        self._execute_unit = execute_unit
        self.max_retries = max_retries

    async def execute_one(self, agent_id: str, task: TaskEnvelope) -> TaskResult:
        self._state_model.transition(task.task_id, TaskState.RUNNING)
        self._observability.record_task_state(task.task_id, TaskState.RUNNING, {"agent_id": agent_id})

        try:
            output = await self._execute_unit(agent_id, task)
            self._state_model.transition(task.task_id, TaskState.SUCCEEDED)
            self._observability.record_task_state(task.task_id, TaskState.SUCCEEDED, {"agent_id": agent_id})
            return TaskResult(
                task_id=task.task_id,
                state=TaskState.SUCCEEDED,
                agent_id=agent_id,
                output=output,
            )
        except Exception as exc:
            self._state_model.transition(task.task_id, TaskState.FAILED)
            self._observability.record_task_state(
                task.task_id,
                TaskState.FAILED,
                {"agent_id": agent_id, "error": str(exc)},
            )

            if task.retry_count < self.max_retries:
                self._state_model.transition(task.task_id, TaskState.RETRIED)
                self._observability.record_task_state(task.task_id, TaskState.RETRIED, {"agent_id": agent_id})
                return TaskResult(
                    task_id=task.task_id,
                    state=TaskState.RETRIED,
                    agent_id=agent_id,
                    error=TaskErrorContract(code="task_execution_failed", message=str(exc), retryable=True),
                )

            self._state_model.transition(task.task_id, TaskState.DEAD_LETTERED)
            self._observability.record_task_state(task.task_id, TaskState.DEAD_LETTERED, {"agent_id": agent_id})
            return TaskResult(
                task_id=task.task_id,
                state=TaskState.DEAD_LETTERED,
                agent_id=agent_id,
                error=TaskErrorContract(code="task_execution_failed", message=str(exc), retryable=False),
            )


@dataclass
class LifecycleManager(LifecycleManagerContract):
    """Lifecycle manager for worker selection, scaling, and recovery policies."""

    max_agents_per_type: int = 10
    restart_failed_agents: bool = True
    desired_workers: Dict[str, int] = field(default_factory=dict)

    async def select_or_provision(
        self,
        task_type: str,
        preferred_agent_type: Any,
        find_agent: Callable[[str, Any], Awaitable[Optional[str]]],
        spawn_agent: Callable[[Any], Awaitable[Optional[str]]],
        default_agent_type: Any,
    ) -> Optional[str]:
        agent_id = await find_agent(task_type, preferred_agent_type)
        if agent_id:
            return agent_id

        target_type = preferred_agent_type or default_agent_type
        return await spawn_agent(target_type)

    async def recover_if_enabled(
        self,
        agent_id: str,
        recover_callable: Callable[[str], Awaitable[None]],
    ) -> None:
        if not self.restart_failed_agents:
            return
        await recover_callable(agent_id)


class ObservabilityService(ObservabilityContract):
    """Passive observability module for logs/metrics/health snapshots."""

    def __init__(self):
        self.task_state_counts: Dict[str, int] = {state.value: 0 for state in TaskState}
        self.task_events: List[Dict[str, Any]] = []
        self.agent_health: Dict[str, str] = {}

    def record_task_state(self, task_id: str, state: TaskState, details: Optional[Dict[str, Any]] = None) -> None:
        self.task_state_counts[state.value] += 1
        self.task_events.append(
            {
                "task_id": task_id,
                "state": state.value,
                "details": details or {},
            }
        )

    def record_agent_health(self, agent_id: str, state: str) -> None:
        self.agent_health[agent_id] = state

    def snapshot(self) -> Dict[str, Any]:
        return {
            "task_state_counts": dict(self.task_state_counts),
            "task_events": list(self.task_events),
            "agent_health": dict(self.agent_health),
        }
