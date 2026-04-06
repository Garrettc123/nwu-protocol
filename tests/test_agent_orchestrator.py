"""
Tests for the Agent Orchestration System.

Tests cover:
- Agent spawning
- Task assignment
- Health monitoring
- Auto-scaling
- Hierarchical structures
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime

from backend.app.services.agent_orchestrator import (
    AgentOrchestrator,
    AgentType,
    AgentStatus,
    AgentCapability,
    AgentMetrics,
    AgentInstance
)
from backend.app.services.base_agent import (
    BaseAgent,
    MasterAgent,
    VerifierAgent,
    AnalyzerAgent,
    CoordinatorAgent
)


@pytest_asyncio.fixture
async def orchestrator():
    """Create a test orchestrator."""
    orch = AgentOrchestrator()
    await orch.initialize()
    yield orch
    await orch.shutdown()


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    orch = AgentOrchestrator()
    assert not orch.running
    assert orch.master_agent_id is None

    await orch.initialize()

    assert orch.running
    assert orch.master_agent_id is not None
    assert orch.master_agent_id in orch.agents
    assert orch.agents[orch.master_agent_id].agent_type == AgentType.MASTER

    await orch.shutdown()


@pytest.mark.asyncio
async def test_spawn_agent(orchestrator):
    """Test spawning different agent types."""
    # Spawn a verifier agent
    verifier_id = await orchestrator.spawn_agent(AgentType.VERIFIER)
    assert verifier_id is not None
    assert verifier_id in orchestrator.agents
    assert orchestrator.agents[verifier_id].agent_type == AgentType.VERIFIER
    assert orchestrator.agents[verifier_id].status == AgentStatus.ACTIVE

    # Spawn an analyzer agent
    analyzer_id = await orchestrator.spawn_agent(AgentType.ANALYZER)
    assert analyzer_id is not None
    assert analyzer_id in orchestrator.agents
    assert orchestrator.agents[analyzer_id].agent_type == AgentType.ANALYZER


@pytest.mark.asyncio
async def test_agent_registry(orchestrator):
    """Test agent registry tracking."""
    initial_count = len(orchestrator.agent_registry[AgentType.VERIFIER])

    # Spawn 3 verifier agents
    agent_ids = []
    for _ in range(3):
        agent_id = await orchestrator.spawn_agent(AgentType.VERIFIER)
        agent_ids.append(agent_id)

    # Check registry
    assert len(orchestrator.agent_registry[AgentType.VERIFIER]) == initial_count + 3
    for agent_id in agent_ids:
        assert agent_id in orchestrator.agent_registry[AgentType.VERIFIER]


@pytest.mark.asyncio
async def test_stop_agent(orchestrator):
    """Test stopping an agent."""
    # Spawn an agent
    agent_id = await orchestrator.spawn_agent(AgentType.SPECIALIST)
    assert agent_id in orchestrator.agents

    # Stop the agent
    await orchestrator.stop_agent(agent_id)

    # Verify it's stopped
    assert orchestrator.agents[agent_id].status == AgentStatus.STOPPED
    assert agent_id not in orchestrator.agent_registry[AgentType.SPECIALIST]


@pytest.mark.asyncio
async def test_hierarchical_spawning(orchestrator):
    """Test hierarchical agent spawning."""
    # Spawn a coordinator (can spawn children)
    coordinator_id = await orchestrator.spawn_agent(
        AgentType.COORDINATOR,
        config={'can_spawn_agents': True}
    )

    # Spawn a child agent
    child_id = await orchestrator.spawn_agent(
        AgentType.SPECIALIST,
        parent_agent_id=coordinator_id
    )

    # Verify parent-child relationship
    coordinator = orchestrator.agents[coordinator_id]
    child = orchestrator.agents[child_id]

    assert child.parent_agent_id == coordinator_id
    assert child_id in coordinator.child_agent_ids


@pytest.mark.asyncio
async def test_task_assignment(orchestrator):
    """Test task assignment to agents."""
    # Spawn a verifier agent
    verifier_id = await orchestrator.spawn_agent(AgentType.VERIFIER)

    # Assign a verification task
    assigned_id = await orchestrator.assign_task(
        task_type='verify_code',
        task_data={'contribution_id': 123},
        preferred_agent_type=AgentType.VERIFIER
    )

    assert assigned_id is not None
    agent = orchestrator.agents[assigned_id]
    assert len(agent.current_tasks) > 0
    assert agent.status == AgentStatus.BUSY


@pytest.mark.asyncio
async def test_agent_capabilities():
    """Test agent capability definitions."""
    orch = AgentOrchestrator()

    # Test verifier capabilities
    verifier_caps = orch._get_agent_capabilities(AgentType.VERIFIER)
    assert len(verifier_caps) > 0
    assert any('verif' in cap.name for cap in verifier_caps)
    assert any('verify_code' in cap.task_types for cap in verifier_caps)

    # Test master capabilities
    master_caps = orch._get_agent_capabilities(AgentType.MASTER)
    assert len(master_caps) > 0
    assert any('orchestration' in cap.name for cap in master_caps)


@pytest.mark.asyncio
async def test_agent_metrics():
    """Test agent metrics tracking."""
    orch = AgentOrchestrator()
    await orch.initialize()

    # Spawn an agent
    agent_id = await orch.spawn_agent(AgentType.VERIFIER)
    agent = orch.agents[agent_id]

    # Initial metrics should be zero
    assert agent.metrics.tasks_completed == 0
    assert agent.metrics.tasks_failed == 0
    assert agent.metrics.error_count == 0

    await orch.shutdown()


@pytest.mark.asyncio
async def test_get_agent_status(orchestrator):
    """Test getting agent status."""
    # Spawn an agent
    agent_id = await orchestrator.spawn_agent(AgentType.ANALYZER)

    # Get status
    status = orchestrator.get_agent_status(agent_id)

    assert status is not None
    assert status['agent_id'] == agent_id
    assert status['agent_type'] == AgentType.ANALYZER.value
    assert 'metrics' in status
    assert 'current_tasks' in status
    assert 'uptime' in status


@pytest.mark.asyncio
async def test_get_all_agents_status(orchestrator):
    """Test getting status for all agents."""
    # Spawn multiple agents
    await orchestrator.spawn_agent(AgentType.VERIFIER)
    await orchestrator.spawn_agent(AgentType.ANALYZER)
    await orchestrator.spawn_agent(AgentType.COORDINATOR)

    # Get all statuses
    all_status = orchestrator.get_all_agents_status()

    assert len(all_status) >= 4  # At least master + 3 spawned
    assert all(isinstance(s, dict) for s in all_status)


@pytest.mark.asyncio
async def test_max_agents_limit(orchestrator):
    """Test max agents per type limit."""
    orchestrator.max_agents_per_type = 2

    # Spawn agents up to limit
    agent1 = await orchestrator.spawn_agent(AgentType.SPECIALIST)
    agent2 = await orchestrator.spawn_agent(AgentType.SPECIALIST)

    assert agent1 is not None
    assert agent2 is not None

    # Try to spawn beyond limit
    agent3 = await orchestrator.spawn_agent(AgentType.SPECIALIST)
    assert agent3 is None


@pytest.mark.asyncio
async def test_master_agent():
    """Test MasterAgent functionality."""
    master = MasterAgent(
        agent_id="test-master",
        config={'initial_verifiers': 0}
    )

    assert master.can_spawn_agents
    assert master.agent_type == AgentType.MASTER

    await master.start()
    assert master.running
    assert master.status == AgentStatus.ACTIVE

    await master.stop()
    assert not master.running
    assert master.status == AgentStatus.STOPPED


@pytest.mark.asyncio
async def test_verifier_agent():
    """Test VerifierAgent functionality."""
    verifier = VerifierAgent(
        agent_id="test-verifier",
        config={'name': 'Test Verifier'}
    )

    assert not verifier.can_spawn_agents
    assert verifier.agent_type == AgentType.VERIFIER

    await verifier.start()
    assert verifier.running

    # Test task execution
    result = await verifier.execute_task(
        task_type='verify_code',
        task_data={'contribution_id': 123, 'ipfs_hash': 'QmTest'}
    )

    assert result['success']
    assert 'quality_score' in result

    await verifier.stop()


@pytest.mark.asyncio
async def test_analyzer_agent():
    """Test AnalyzerAgent functionality."""
    analyzer = AnalyzerAgent(
        agent_id="test-analyzer",
        config={'name': 'Test Analyzer'}
    )

    assert analyzer.agent_type == AgentType.ANALYZER

    await analyzer.start()

    # Test analysis tasks
    result = await analyzer.execute_task(
        task_type='analyze_trends',
        task_data={'dataset_id': 456}
    )

    assert result['success']

    await analyzer.stop()


@pytest.mark.asyncio
async def test_coordinator_agent():
    """Test CoordinatorAgent functionality."""
    coordinator = CoordinatorAgent(
        agent_id="test-coordinator",
        config={'name': 'Test Coordinator'}
    )

    assert coordinator.can_spawn_agents
    assert coordinator.agent_type == AgentType.COORDINATOR

    await coordinator.start()

    # Test coordination tasks
    result = await coordinator.execute_task(
        task_type='coordinate',
        task_data={'tasks': [{'name': 'Task1'}]}
    )

    assert result['success']

    await coordinator.stop()


@pytest.mark.asyncio
async def test_agent_pause_resume():
    """Test pausing and resuming agents."""
    agent = VerifierAgent("test-pause", {})
    await agent.start()

    assert agent.status == AgentStatus.ACTIVE

    await agent.pause()
    assert agent.status == AgentStatus.PAUSED

    await agent.resume()
    assert agent.status == AgentStatus.ACTIVE

    await agent.stop()


@pytest.mark.asyncio
async def test_task_routing():
    """Test task routing to appropriate agents."""
    orch = AgentOrchestrator()
    await orch.initialize()

    # Spawn different types of agents
    await orch.spawn_agent(AgentType.VERIFIER)
    await orch.spawn_agent(AgentType.ANALYZER)

    # Submit tasks and verify routing
    verifier_task = await orch.assign_task(
        task_type='verify_code',
        task_data={},
        preferred_agent_type=AgentType.VERIFIER
    )
    assert verifier_task is not None
    assert orch.agents[verifier_task].agent_type == AgentType.VERIFIER

    analyzer_task = await orch.assign_task(
        task_type='analyze_trends',
        task_data={},
        preferred_agent_type=AgentType.ANALYZER
    )
    assert analyzer_task is not None
    assert orch.agents[analyzer_task].agent_type == AgentType.ANALYZER

    await orch.shutdown()


@pytest.mark.asyncio
async def test_orchestrator_shutdown(orchestrator):
    """Test graceful orchestrator shutdown."""
    # Spawn several agents
    await orchestrator.spawn_agent(AgentType.VERIFIER)
    await orchestrator.spawn_agent(AgentType.ANALYZER)

    initial_count = len(orchestrator.agents)
    assert initial_count > 1

    # Shutdown
    await orchestrator.shutdown()

    # Verify all agents are stopped
    assert not orchestrator.running
    for agent in orchestrator.agents.values():
        assert agent.status == AgentStatus.STOPPED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
