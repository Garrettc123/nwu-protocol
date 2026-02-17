"""API endpoints for Business Agent management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from ..database import get_db
from ..models import BusinessAgent, BusinessTask
from ..schemas import (
    BusinessAgentCreate,
    BusinessAgentResponse,
    BusinessTaskCreate,
    BusinessTaskResponse,
    BusinessAgentStatus
)

router = APIRouter(prefix="/api/v1/business-agents", tags=["business-agents"])


@router.get("/", response_model=List[BusinessAgentResponse])
async def list_business_agents(
    status: str = None,
    agent_type: str = None,
    db: Session = Depends(get_db)
):
    """List all business agents with optional filters."""
    query = db.query(BusinessAgent)

    if status:
        query = query.filter(BusinessAgent.status == status)
    if agent_type:
        query = query.filter(BusinessAgent.agent_type == agent_type)

    agents = query.all()
    return agents


@router.get("/{agent_id}", response_model=BusinessAgentResponse)
async def get_business_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get a specific business agent by ID."""
    agent = db.query(BusinessAgent).filter(BusinessAgent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/", response_model=BusinessAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_business_agent(agent: BusinessAgentCreate, db: Session = Depends(get_db)):
    """Create a new business agent."""
    # Check if agent already exists
    existing = db.query(BusinessAgent).filter(BusinessAgent.agent_id == agent.agent_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Agent already exists")

    # Create new agent
    db_agent = BusinessAgent(
        agent_id=agent.agent_id,
        agent_type=agent.agent_type,
        name=agent.name,
        status=agent.status,
        capabilities=json.dumps(agent.capabilities) if agent.capabilities else None,
        config=json.dumps(agent.config) if agent.config else None
    )

    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)

    return db_agent


@router.put("/{agent_id}/status", response_model=BusinessAgentResponse)
async def update_agent_status(
    agent_id: str,
    status_update: BusinessAgentStatus,
    db: Session = Depends(get_db)
):
    """Update agent status."""
    agent = db.query(BusinessAgent).filter(BusinessAgent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = status_update.status
    db.commit()
    db.refresh(agent)

    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_agent(agent_id: str, db: Session = Depends(get_db)):
    """Terminate a business agent."""
    agent = db.query(BusinessAgent).filter(BusinessAgent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    from datetime import datetime
    agent.status = "terminated"
    agent.terminated_at = datetime.utcnow()
    db.commit()

    return None


@router.get("/{agent_id}/tasks", response_model=List[BusinessTaskResponse])
async def get_agent_tasks(agent_id: str, db: Session = Depends(get_db)):
    """Get all tasks for a specific agent."""
    tasks = db.query(BusinessTask).filter(BusinessTask.agent_id == agent_id).all()
    return tasks


# Business Task endpoints
task_router = APIRouter(prefix="/api/v1/business-tasks", tags=["business-tasks"])


@task_router.get("/", response_model=List[BusinessTaskResponse])
async def list_business_tasks(
    status: str = None,
    task_type: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List business tasks with optional filters."""
    query = db.query(BusinessTask)

    if status:
        query = query.filter(BusinessTask.status == status)
    if task_type:
        query = query.filter(BusinessTask.task_type == task_type)

    tasks = query.order_by(BusinessTask.created_at.desc()).limit(limit).all()
    return tasks


@task_router.get("/{task_id}", response_model=BusinessTaskResponse)
async def get_business_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific business task by ID."""
    task = db.query(BusinessTask).filter(BusinessTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@task_router.post("/", response_model=BusinessTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_business_task(task: BusinessTaskCreate, db: Session = Depends(get_db)):
    """Create a new business task."""
    db_task = BusinessTask(
        task_id=task.task_id,
        task_type=task.task_type,
        category=task.category,
        priority=task.priority,
        status="pending",
        task_data=json.dumps(task.task_data) if task.task_data else None
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


@task_router.post("/results", status_code=status.HTTP_201_CREATED)
async def submit_task_result(result_data: dict, db: Session = Depends(get_db)):
    """Submit task result from an agent."""
    task_id = result_data.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id required")

    task = db.query(BusinessTask).filter(BusinessTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    from datetime import datetime
    task.status = "completed"
    task.result = json.dumps(result_data.get("result", {}))
    task.completed_at = datetime.utcnow()

    db.commit()

    return {"message": "Task result submitted successfully"}
