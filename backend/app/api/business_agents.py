"""Business Agents API - Manage business cooperation lead agents and tasks."""

import json
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    BusinessAgent,
    BusinessAgentStatus,
    BusinessAgentType,
    BusinessTask,
    BusinessTaskStatus,
)

logger = logging.getLogger(__name__)

business_agents_router = APIRouter(prefix="/api/v1/business-agents", tags=["business-agents"])
business_tasks_router = APIRouter(prefix="/api/v1/business-tasks", tags=["business-tasks"])

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

VALID_AGENT_TYPES = [t.value for t in BusinessAgentType]
VALID_AGENT_STATUSES = [s.value for s in BusinessAgentStatus]
VALID_TASK_STATUSES = [s.value for s in BusinessTaskStatus]

TASK_PRIORITY_MIN = 1
TASK_PRIORITY_MAX = 10


class BusinessAgentCreate(BaseModel):
    """Request body for creating a business agent."""

    agent_type: str = Field(..., description=f"Agent type. One of: {VALID_AGENT_TYPES}")
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable agent name")
    description: Optional[str] = Field(None, description="Optional description")
    capabilities: Optional[List[str]] = Field(None, description="List of capability strings")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")


class BusinessAgentUpdate(BaseModel):
    """Request body for updating a business agent."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, description=f"One of: {VALID_AGENT_STATUSES}")
    capabilities: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class BusinessAgentResponse(BaseModel):
    """Business agent response schema."""

    id: int
    agent_id: str
    agent_type: str
    status: str
    name: str
    description: Optional[str]
    capabilities: Optional[List[str]]
    config: Optional[Dict[str, Any]]
    tasks_completed: int
    tasks_failed: int
    last_active_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    terminated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class BusinessTaskCreate(BaseModel):
    """Request body for creating a business task."""

    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    task_type: str = Field(..., min_length=1, max_length=100, description="Task type identifier")
    required_agent_type: Optional[str] = Field(
        None, description=f"Required agent type. One of: {VALID_AGENT_TYPES}"
    )
    priority: int = Field(
        5,
        ge=TASK_PRIORITY_MIN,
        le=TASK_PRIORITY_MAX,
        description="Priority 1 (highest) to 10 (lowest)",
    )
    task_data: Optional[Dict[str, Any]] = Field(None, description="Task payload")
    scheduled_at: Optional[datetime] = Field(None, description="Optional scheduled execution time")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")


class BusinessTaskUpdate(BaseModel):
    """Request body for updating a business task."""

    status: Optional[str] = Field(None, description=f"One of: {VALID_TASK_STATUSES}")
    priority: Optional[int] = Field(None, ge=TASK_PRIORITY_MIN, le=TASK_PRIORITY_MAX)
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class BusinessTaskResponse(BaseModel):
    """Business task response schema."""

    id: int
    task_id: str
    title: str
    description: Optional[str]
    task_type: str
    required_agent_type: Optional[str]
    agent_id: Optional[int]
    status: str
    priority: int
    task_data: Optional[Dict[str, Any]]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _serialize_json_field(value: Optional[Any]) -> Optional[str]:
    """Serialize a Python object to a JSON string (or None)."""
    if value is None:
        return None
    return json.dumps(value)


def _deserialize_json_field(raw: Optional[str]) -> Optional[Any]:
    """Deserialize a JSON string field to a Python object (or None)."""
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _agent_to_response(agent: BusinessAgent) -> BusinessAgentResponse:
    return BusinessAgentResponse(
        id=agent.id,
        agent_id=agent.agent_id,
        agent_type=agent.agent_type.value,
        status=agent.status.value,
        name=agent.name,
        description=agent.description,
        capabilities=_deserialize_json_field(agent.capabilities),
        config=_deserialize_json_field(agent.config),
        tasks_completed=agent.tasks_completed,
        tasks_failed=agent.tasks_failed,
        last_active_at=agent.last_active_at,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        terminated_at=agent.terminated_at,
    )


def _task_to_response(task: BusinessTask) -> BusinessTaskResponse:
    return BusinessTaskResponse(
        id=task.id,
        task_id=task.task_id,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        required_agent_type=task.required_agent_type.value if task.required_agent_type else None,
        agent_id=task.agent_id,
        status=task.status.value,
        priority=task.priority,
        task_data=_deserialize_json_field(task.task_data),
        result_data=_deserialize_json_field(task.result_data),
        error_message=task.error_message,
        retry_count=task.retry_count,
        max_retries=task.max_retries,
        scheduled_at=task.scheduled_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


# ---------------------------------------------------------------------------
# Business Agents endpoints
# ---------------------------------------------------------------------------


@business_agents_router.post(
    "/", response_model=BusinessAgentResponse, status_code=status.HTTP_201_CREATED
)
async def create_business_agent(
    request: BusinessAgentCreate, db: Session = Depends(get_db)
):
    """
    Create and register a new business agent.

    - **agent_type**: One of the 12 supported business agent types
    - **name**: Human-readable name for the agent
    - **capabilities**: Optional list of capability strings
    - **config**: Optional agent configuration dictionary
    """
    if request.agent_type not in VALID_AGENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent_type '{request.agent_type}'. Must be one of: {VALID_AGENT_TYPES}",
        )

    agent_type_enum = BusinessAgentType(request.agent_type)
    agent_id = f"business-{request.agent_type}-{uuid.uuid4().hex[:8]}"

    agent = BusinessAgent(
        agent_id=agent_id,
        agent_type=agent_type_enum,
        status=BusinessAgentStatus.IDLE,
        name=request.name,
        description=request.description,
        capabilities=_serialize_json_field(request.capabilities),
        config=_serialize_json_field(request.config),
    )

    try:
        db.add(agent)
        db.commit()
        db.refresh(agent)
    except Exception as e:
        db.rollback()
        logger.error("Failed to create business agent: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create business agent",
        )

    logger.info("Created business agent %s (type=%s)", agent_id, request.agent_type)
    return _agent_to_response(agent)


@business_agents_router.get("/", response_model=List[BusinessAgentResponse])
async def list_business_agents(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    agent_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
    db: Session = Depends(get_db),
):
    """List all registered business agents with optional filters."""
    query = db.query(BusinessAgent)

    if agent_type:
        if agent_type not in VALID_AGENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent_type '{agent_type}'. Must be one of: {VALID_AGENT_TYPES}",
            )
        query = query.filter(BusinessAgent.agent_type == BusinessAgentType(agent_type))

    if agent_status:
        if agent_status not in VALID_AGENT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{agent_status}'. Must be one of: {VALID_AGENT_STATUSES}",
            )
        query = query.filter(BusinessAgent.status == BusinessAgentStatus(agent_status))

    agents = query.order_by(BusinessAgent.created_at.desc()).offset(skip).limit(limit).all()
    return [_agent_to_response(agent) for agent in agents]


@business_agents_router.get("/{agent_id}", response_model=BusinessAgentResponse)
async def get_business_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get details of a specific business agent by its agent_id."""
    agent = db.query(BusinessAgent).filter(BusinessAgent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business agent '{agent_id}' not found",
        )
    return _agent_to_response(agent)


@business_agents_router.patch("/{agent_id}", response_model=BusinessAgentResponse)
async def update_business_agent(
    agent_id: str, request: BusinessAgentUpdate, db: Session = Depends(get_db)
):
    """Update fields on an existing business agent."""
    agent = db.query(BusinessAgent).filter(BusinessAgent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business agent '{agent_id}' not found",
        )

    if request.name is not None:
        agent.name = request.name
    if request.description is not None:
        agent.description = request.description
    if request.capabilities is not None:
        agent.capabilities = _serialize_json_field(request.capabilities)
    if request.config is not None:
        agent.config = _serialize_json_field(request.config)

    if request.status is not None:
        if request.status not in VALID_AGENT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{request.status}'. Must be one of: {VALID_AGENT_STATUSES}",
            )
        new_status = BusinessAgentStatus(request.status)
        agent.status = new_status
        if new_status == BusinessAgentStatus.TERMINATED:
            agent.terminated_at = datetime.utcnow()
        elif new_status in (BusinessAgentStatus.ACTIVE, BusinessAgentStatus.BUSY):
            agent.last_active_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(agent)
    except Exception as e:
        db.rollback()
        logger.error("Failed to update business agent %s: %s", agent_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update business agent",
        )

    return _agent_to_response(agent)


@business_agents_router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_business_agent(agent_id: str, db: Session = Depends(get_db)):
    """Terminate (soft-delete) a business agent by setting its status to TERMINATED."""
    agent = db.query(BusinessAgent).filter(BusinessAgent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business agent '{agent_id}' not found",
        )

    agent.status = BusinessAgentStatus.TERMINATED
    agent.terminated_at = datetime.utcnow()

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to terminate business agent %s: %s", agent_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate business agent",
        )


# ---------------------------------------------------------------------------
# Business Tasks endpoints
# ---------------------------------------------------------------------------


@business_tasks_router.post(
    "/", response_model=BusinessTaskResponse, status_code=status.HTTP_201_CREATED
)
async def create_business_task(
    request: BusinessTaskCreate, db: Session = Depends(get_db)
):
    """
    Create and enqueue a new business task.

    - **priority**: 1 = highest, 10 = lowest
    - **required_agent_type**: If specified, only agents of this type will be assigned
    - **task_data**: Arbitrary JSON payload forwarded to the handling agent
    """
    required_agent_type_enum: Optional[BusinessAgentType] = None
    if request.required_agent_type is not None:
        if request.required_agent_type not in VALID_AGENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid required_agent_type '{request.required_agent_type}'. "
                    f"Must be one of: {VALID_AGENT_TYPES}"
                ),
            )
        required_agent_type_enum = BusinessAgentType(request.required_agent_type)

    task_id = f"task-{uuid.uuid4().hex}"

    task = BusinessTask(
        task_id=task_id,
        title=request.title,
        description=request.description,
        task_type=request.task_type,
        required_agent_type=required_agent_type_enum,
        status=BusinessTaskStatus.QUEUED,
        priority=request.priority,
        task_data=_serialize_json_field(request.task_data),
        scheduled_at=request.scheduled_at,
        max_retries=request.max_retries,
    )

    try:
        db.add(task)
        db.commit()
        db.refresh(task)
    except Exception as e:
        db.rollback()
        logger.error("Failed to create business task: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create business task",
        )

    logger.info("Created business task %s (type=%s, priority=%d)", task_id, request.task_type, request.priority)
    return _task_to_response(task)


@business_tasks_router.get("/", response_model=List[BusinessTaskResponse])
async def list_business_tasks(
    task_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    required_agent_type: Optional[str] = Query(None, description="Filter by required agent type"),
    priority: Optional[int] = Query(None, ge=TASK_PRIORITY_MIN, le=TASK_PRIORITY_MAX, description="Filter by priority"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List business tasks with optional filters, ordered by priority then creation time."""
    query = db.query(BusinessTask)

    if task_status:
        if task_status not in VALID_TASK_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{task_status}'. Must be one of: {VALID_TASK_STATUSES}",
            )
        query = query.filter(BusinessTask.status == BusinessTaskStatus(task_status))

    if required_agent_type:
        if required_agent_type not in VALID_AGENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid required_agent_type. Must be one of: {VALID_AGENT_TYPES}",
            )
        query = query.filter(
            BusinessTask.required_agent_type == BusinessAgentType(required_agent_type)
        )

    if priority is not None:
        query = query.filter(BusinessTask.priority == priority)

    tasks = (
        query.order_by(BusinessTask.priority.asc(), BusinessTask.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_task_to_response(task) for task in tasks]


@business_tasks_router.get("/{task_id}", response_model=BusinessTaskResponse)
async def get_business_task(task_id: str, db: Session = Depends(get_db)):
    """Get details of a specific business task by its task_id."""
    task = db.query(BusinessTask).filter(BusinessTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business task '{task_id}' not found",
        )
    return _task_to_response(task)


@business_tasks_router.patch("/{task_id}", response_model=BusinessTaskResponse)
async def update_business_task(
    task_id: str, request: BusinessTaskUpdate, db: Session = Depends(get_db)
):
    """Update the status, priority, or result of a business task."""
    task = db.query(BusinessTask).filter(BusinessTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business task '{task_id}' not found",
        )

    if request.status is not None:
        if request.status not in VALID_TASK_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{request.status}'. Must be one of: {VALID_TASK_STATUSES}",
            )
        new_status = BusinessTaskStatus(request.status)
        task.status = new_status
        if new_status == BusinessTaskStatus.IN_PROGRESS and task.started_at is None:
            task.started_at = datetime.utcnow()
        elif new_status in (BusinessTaskStatus.COMPLETED, BusinessTaskStatus.FAILED, BusinessTaskStatus.CANCELLED):
            if task.completed_at is None:
                task.completed_at = datetime.utcnow()

    if request.priority is not None:
        task.priority = request.priority
    if request.result_data is not None:
        task.result_data = _serialize_json_field(request.result_data)
    if request.error_message is not None:
        task.error_message = request.error_message

    try:
        db.commit()
        db.refresh(task)
    except Exception as e:
        db.rollback()
        logger.error("Failed to update business task %s: %s", task_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update business task",
        )

    return _task_to_response(task)


@business_tasks_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_business_task(task_id: str, db: Session = Depends(get_db)):
    """Cancel a queued or delegated business task."""
    task = db.query(BusinessTask).filter(BusinessTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business task '{task_id}' not found",
        )

    non_cancellable = {BusinessTaskStatus.COMPLETED, BusinessTaskStatus.CANCELLED}
    if task.status in non_cancellable:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel a task with status '{task.status.value}'",
        )

    task.status = BusinessTaskStatus.CANCELLED
    task.completed_at = datetime.utcnow()

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to cancel business task %s: %s", task_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel business task",
        )


class DelegateTaskRequest(BaseModel):
    """Request body for delegating a task to a specific agent."""

    agent_id: str = Field(..., description="The agent_id of the target BusinessAgent")


@business_tasks_router.post("/{task_id}/delegate", response_model=BusinessTaskResponse)
async def delegate_business_task(
    task_id: str,
    request: DelegateTaskRequest,
    db: Session = Depends(get_db),
):
    """
    Delegate a queued task to a specific business agent.

    Request body:
    - **agent_id**: The `agent_id` string of the target BusinessAgent
    """
    agent_id: str = request.agent_id
    task = db.query(BusinessTask).filter(BusinessTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business task '{task_id}' not found",
        )

    if task.status not in (BusinessTaskStatus.QUEUED, BusinessTaskStatus.FAILED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Can only delegate tasks with status 'queued' or 'failed', not '{task.status.value}'",
        )

    agent = db.query(BusinessAgent).filter(BusinessAgent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business agent '{agent_id}' not found",
        )

    if agent.status == BusinessAgentStatus.TERMINATED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delegate to terminated agent '{agent_id}'",
        )

    if task.required_agent_type and task.required_agent_type != agent.agent_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Task requires agent type '{task.required_agent_type.value}', "
                f"but agent '{agent_id}' is of type '{agent.agent_type.value}'"
            ),
        )

    task.agent_id = agent.id
    task.status = BusinessTaskStatus.DELEGATED
    agent.status = BusinessAgentStatus.BUSY
    agent.last_active_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(task)
    except Exception as e:
        db.rollback()
        logger.error("Failed to delegate task %s to agent %s: %s", task_id, agent_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delegate task",
        )

    logger.info("Delegated task %s to agent %s", task_id, agent_id)
    return _task_to_response(task)
