"""Agent Orchestrator API - Control and monitor the multi-agent system."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..services.agent_orchestrator import orchestrator, AgentType, AgentStatus

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class SpawnAgentRequest(BaseModel):
    """Request to spawn a new agent."""
    agent_type: str = Field(..., description="Type of agent to spawn")
    parent_agent_id: Optional[str] = Field(None, description="Parent agent ID for hierarchical structure")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Agent configuration")


class SpawnAgentResponse(BaseModel):
    """Response from spawning an agent."""
    success: bool
    agent_id: Optional[str]
    message: str


class TaskSubmissionRequest(BaseModel):
    """Request to submit a task."""
    task_type: str = Field(..., description="Type of task")
    task_data: Dict[str, Any] = Field(default_factory=dict, description="Task data")
    preferred_agent_type: Optional[str] = Field(None, description="Preferred agent type")


class TaskSubmissionResponse(BaseModel):
    """Response from task submission."""
    success: bool
    message: str


class AgentStatusResponse(BaseModel):
    """Agent status information."""
    agent_id: str
    agent_type: str
    status: str
    metrics: Dict[str, Any]
    current_tasks: int
    child_agents: int
    uptime: float


class OrchestratorStatusResponse(BaseModel):
    """Overall orchestrator status."""
    running: bool
    total_agents: int
    agents_by_type: Dict[str, int]
    auto_scaling_enabled: bool
    master_agent_id: Optional[str]


@router.post("/initialize", response_model=dict, status_code=status.HTTP_200_OK)
async def initialize_orchestrator():
    """
    Initialize the agent orchestrator.

    This creates the master agent and starts the orchestration system.
    """
    try:
        if orchestrator.running:
            return {
                "success": False,
                "message": "Orchestrator is already running",
                "master_agent_id": orchestrator.master_agent_id
            }

        await orchestrator.initialize()

        return {
            "success": True,
            "message": "Orchestrator initialized successfully",
            "master_agent_id": orchestrator.master_agent_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize orchestrator: {str(e)}"
        )


@router.post("/spawn", response_model=SpawnAgentResponse, status_code=status.HTTP_201_CREATED)
async def spawn_agent(request: SpawnAgentRequest):
    """
    Spawn a new agent.

    Args:
        request: Agent spawn request with type and configuration

    Returns:
        Information about the spawned agent
    """
    try:
        # Validate agent type
        try:
            agent_type = AgentType(request.agent_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent type: {request.agent_type}"
            )

        # Spawn the agent
        agent_id = await orchestrator.spawn_agent(
            agent_type=agent_type,
            parent_agent_id=request.parent_agent_id,
            config=request.config
        )

        if agent_id:
            return SpawnAgentResponse(
                success=True,
                agent_id=agent_id,
                message=f"Agent {agent_id} spawned successfully"
            )
        else:
            return SpawnAgentResponse(
                success=False,
                agent_id=None,
                message="Failed to spawn agent (capacity limit reached)"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error spawning agent: {str(e)}"
        )


@router.delete("/agents/{agent_id}", response_model=dict)
async def stop_agent(agent_id: str, graceful: bool = True):
    """
    Stop an agent.

    Args:
        agent_id: ID of the agent to stop
        graceful: If True, wait for current tasks to complete

    Returns:
        Confirmation of agent stop
    """
    try:
        if agent_id not in orchestrator.agents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )

        await orchestrator.stop_agent(agent_id, graceful=graceful)

        return {
            "success": True,
            "message": f"Agent {agent_id} stopped successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping agent: {str(e)}"
        )


@router.post("/tasks", response_model=TaskSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_task(request: TaskSubmissionRequest):
    """
    Submit a task to the orchestrator.

    The orchestrator will find an appropriate agent to handle the task.

    Args:
        request: Task submission request

    Returns:
        Confirmation of task submission
    """
    try:
        preferred_type = None
        if request.preferred_agent_type:
            try:
                preferred_type = AgentType(request.preferred_agent_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid agent type: {request.preferred_agent_type}"
                )

        await orchestrator.submit_task(
            task_type=request.task_type,
            task_data=request.task_data,
            preferred_agent_type=preferred_type
        )

        return TaskSubmissionResponse(
            success=True,
            message="Task submitted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting task: {str(e)}"
        )


@router.get("/agents/{agent_id}", response_model=AgentStatusResponse)
async def get_agent_status(agent_id: str):
    """
    Get status of a specific agent.

    Args:
        agent_id: ID of the agent

    Returns:
        Agent status information
    """
    status_data = orchestrator.get_agent_status(agent_id)

    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return AgentStatusResponse(**status_data)


@router.get("/agents", response_model=List[AgentStatusResponse])
async def get_all_agents():
    """
    Get status of all agents.

    Returns:
        List of agent status information
    """
    all_status = orchestrator.get_all_agents_status()
    return [AgentStatusResponse(**status) for status in all_status]


@router.get("/status", response_model=OrchestratorStatusResponse)
async def get_orchestrator_status():
    """
    Get overall orchestrator status.

    Returns:
        Orchestrator status including agent counts and configuration
    """
    agents_by_type = {}
    for agent_type, agent_ids in orchestrator.agent_registry.items():
        agents_by_type[agent_type.value] = len(agent_ids)

    return OrchestratorStatusResponse(
        running=orchestrator.running,
        total_agents=len(orchestrator.agents),
        agents_by_type=agents_by_type,
        auto_scaling_enabled=orchestrator.auto_scale_enabled,
        master_agent_id=orchestrator.master_agent_id
    )


@router.post("/shutdown", response_model=dict)
async def shutdown_orchestrator():
    """
    Shutdown the orchestrator and all agents.

    This is a graceful shutdown that stops all running agents.
    """
    try:
        await orchestrator.shutdown()

        return {
            "success": True,
            "message": "Orchestrator shutdown successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error shutting down orchestrator: {str(e)}"
        )


@router.put("/config/auto-scaling", response_model=dict)
async def configure_auto_scaling(enabled: bool):
    """
    Enable or disable auto-scaling.

    Args:
        enabled: Whether to enable auto-scaling

    Returns:
        Configuration confirmation
    """
    orchestrator.auto_scale_enabled = enabled

    return {
        "success": True,
        "auto_scaling_enabled": enabled,
        "message": f"Auto-scaling {'enabled' if enabled else 'disabled'}"
    }


@router.put("/config/max-agents", response_model=dict)
async def configure_max_agents(max_agents_per_type: int):
    """
    Set maximum agents per type.

    Args:
        max_agents_per_type: Maximum number of agents per type

    Returns:
        Configuration confirmation
    """
    if max_agents_per_type < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_agents_per_type must be at least 1"
        )

    orchestrator.max_agents_per_type = max_agents_per_type

    return {
        "success": True,
        "max_agents_per_type": max_agents_per_type,
        "message": f"Max agents per type set to {max_agents_per_type}"
    }
