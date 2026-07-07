"""Tests for systematic runtime module separation and task-state flow."""

import asyncio

import pytest

from backend.app.services.agent_orchestrator import AgentOrchestrator, AgentType
from backend.app.services.agent_runtime import (
    LifecycleManager,
    ObservabilityService,
    ProducerService,
    SharedTaskStateModel,
    TaskEnvelope,
    TaskState,
    WorkerService,
)


@pytest.mark.asyncio
async def test_producer_enqueues_only_and_sets_queued_state():
    state_model = SharedTaskStateModel()
    producer = ProducerService(state_model)

    envelope = await producer.submit(task_type="verify_code", task_data={"contribution_id": 1})
    dequeued = await producer.dequeue(timeout=0.1)

    assert dequeued is not None
    assert dequeued.task_id == envelope.task_id
    assert state_model.get_state(envelope.task_id) == TaskState.QUEUED


@pytest.mark.asyncio
async def test_worker_executes_single_unit_and_records_success():
    state_model = SharedTaskStateModel()
    observability = ObservabilityService()

    async def execute_unit(agent_id: str, task: TaskEnvelope):
        return {"agent_id": agent_id, "task": task.task_type}

    worker = WorkerService(
        state_model=state_model,
        observability=observability,
        execute_unit=execute_unit,
        max_retries=1,
    )

    task = TaskEnvelope(task_id="task-unit-success", task_type="verify_code", task_data={})
    state_model.transition(task.task_id, TaskState.QUEUED)
    result = await worker.execute_one(agent_id="verifier-1", task=task)

    assert result.state == TaskState.SUCCEEDED
    assert state_model.get_history(task.task_id) == [TaskState.QUEUED, TaskState.RUNNING, TaskState.SUCCEEDED]


@pytest.mark.asyncio
async def test_lifecycle_manager_controls_provisioning():
    lifecycle = LifecycleManager(max_agents_per_type=5)

    async def find_existing(task_type: str, preferred_agent_type):
        return "existing-agent"

    async def spawn_new(agent_type):
        raise AssertionError("spawn should not be called when an existing agent is available")

    selected = await lifecycle.select_or_provision(
        task_type="verify_code",
        preferred_agent_type=AgentType.VERIFIER,
        find_agent=find_existing,
        spawn_agent=spawn_new,
        default_agent_type=AgentType.SPECIALIST,
    )

    assert selected == "existing-agent"


@pytest.mark.asyncio
async def test_observability_is_passive_recorder():
    observability = ObservabilityService()
    observability.record_task_state("task-1", TaskState.QUEUED)
    observability.record_task_state("task-1", TaskState.RUNNING)
    observability.record_agent_health("agent-1", "busy")

    snapshot = observability.snapshot()
    assert snapshot["task_state_counts"]["queued"] == 1
    assert snapshot["task_state_counts"]["running"] == 1
    assert snapshot["agent_health"]["agent-1"] == "busy"


@pytest.mark.asyncio
async def test_end_to_end_fault_injection_dead_letters_after_retry():
    orchestrator = AgentOrchestrator()
    await orchestrator.initialize()

    try:
        task = await orchestrator.producer.submit(
            task_type="verify_code",
            task_data={"force_error": True, "error_message": "fault-injection"},
            preferred_agent_type=AgentType.VERIFIER,
        )

        # Wait for processing + retry + dead-lettering
        await asyncio.sleep(3.5)

        assert orchestrator.get_task_state(task.task_id) == TaskState.DEAD_LETTERED.value
        assert orchestrator.get_task_state_history(task.task_id) == [
            TaskState.QUEUED.value,
            TaskState.RUNNING.value,
            TaskState.FAILED.value,
            TaskState.RETRIED.value,
            TaskState.QUEUED.value,
            TaskState.RUNNING.value,
            TaskState.FAILED.value,
            TaskState.DEAD_LETTERED.value,
        ]
    finally:
        await orchestrator.shutdown()
