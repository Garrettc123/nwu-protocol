"""API endpoints for halt process management and engagement iteration."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from backend.app.database import get_db
from backend.app.services.halt_process_service import HaltProcessService
from backend.app.services.engagement_service import EngagementIterationService
from backend.app.services.workflow_engine import ProgressiveAutomationEngine

router = APIRouter(prefix="/api/v1/halt-process", tags=["halt-process"])


# Request/Response Models
class HaltRequest(BaseModel):
    """Request model for halting a contribution."""
    reason: str = Field(..., description="Reason for halting")
    user_id: Optional[int] = Field(None, description="User ID initiating halt")
    halt_data: Optional[Dict[str, Any]] = Field(None, description="Additional halt data")


class PauseRequest(BaseModel):
    """Request model for pausing a contribution."""
    reason: str = Field(..., description="Reason for pausing")
    user_id: Optional[int] = Field(None, description="User ID initiating pause")


class ResumeRequest(BaseModel):
    """Request model for resuming a contribution."""
    user_id: Optional[int] = Field(None, description="User ID initiating resume")
    resume_to_status: Optional[str] = Field(None, description="Status to resume to")


class ApprovalRequest(BaseModel):
    """Request model for approving halt engagement."""
    approval_reason: str = Field(..., description="Reason for approval")
    user_id: Optional[int] = Field(None, description="User ID approving")


class WorkflowExecutionRequest(BaseModel):
    """Request model for executing workflow."""
    workflow_name: str = Field(..., description="Name of workflow to execute")
    max_automation_level: Optional[int] = Field(None, ge=0, le=5, description="Maximum automation level")
    workflow_data: Optional[Dict[str, Any]] = Field(None, description="Workflow execution data")


class EngagementRequest(BaseModel):
    """Request model for recording engagement."""
    engagement_type: str = Field(..., description="Type of engagement")
    user_id: Optional[int] = Field(None, description="User ID")
    engagement_data: Optional[Dict[str, Any]] = Field(None, description="Engagement data")
    source: str = Field(default="api", description="Engagement source")


# Halt Process Endpoints
@router.post("/contributions/{contribution_id}/halt")
def halt_contribution(
    contribution_id: int,
    request: HaltRequest,
    db: Session = Depends(get_db)
):
    """Halt a contribution process.

    Args:
        contribution_id: ID of the contribution to halt
        request: Halt request data
        db: Database session

    Returns:
        Updated contribution data
    """
    service = HaltProcessService(db)
    try:
        contribution = service.halt_contribution(
            contribution_id=contribution_id,
            reason=request.reason,
            user_id=request.user_id,
            halt_data=request.halt_data
        )
        return {
            "success": True,
            "contribution_id": contribution.id,
            "status": contribution.status,
            "halt_status": contribution.halt_status,
            "halt_reason": contribution.halt_reason,
            "halted_at": contribution.halted_at.isoformat() if contribution.halted_at else None
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to halt contribution: {str(error)}"
        )


@router.post("/contributions/{contribution_id}/pause")
def pause_contribution(
    contribution_id: int,
    request: PauseRequest,
    db: Session = Depends(get_db)
):
    """Pause a contribution process temporarily.

    Args:
        contribution_id: ID of the contribution to pause
        request: Pause request data
        db: Database session

    Returns:
        Updated contribution data
    """
    service = HaltProcessService(db)
    try:
        contribution = service.pause_contribution(
            contribution_id=contribution_id,
            reason=request.reason,
            user_id=request.user_id
        )
        return {
            "success": True,
            "contribution_id": contribution.id,
            "status": contribution.status,
            "halt_status": contribution.halt_status,
            "halt_reason": contribution.halt_reason
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.post("/contributions/{contribution_id}/resume")
def resume_contribution(
    contribution_id: int,
    request: ResumeRequest,
    db: Session = Depends(get_db)
):
    """Resume a halted or paused contribution.

    Args:
        contribution_id: ID of the contribution to resume
        request: Resume request data
        db: Database session

    Returns:
        Updated contribution data
    """
    service = HaltProcessService(db)
    try:
        contribution = service.resume_contribution(
            contribution_id=contribution_id,
            user_id=request.user_id,
            resume_to_status=request.resume_to_status
        )
        return {
            "success": True,
            "contribution_id": contribution.id,
            "status": contribution.status,
            "halt_status": contribution.halt_status,
            "resumed_at": contribution.resumed_at.isoformat() if contribution.resumed_at else None
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get("/contributions/{contribution_id}/halt-status")
def get_halt_status(
    contribution_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed halt status information.

    Args:
        contribution_id: ID of the contribution
        db: Database session

    Returns:
        Halt status information
    """
    service = HaltProcessService(db)
    try:
        return service.get_halt_status(contribution_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.post("/contributions/{contribution_id}/approve-halt")
def approve_halt_engagement(
    contribution_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """Approve any halt process by engaging and iteration.

    This endpoint implements the core requirement: "Approve any halt process
    by engaging and iteration".

    Args:
        contribution_id: ID of the contribution
        request: Approval request data
        db: Database session

    Returns:
        Updated contribution data
    """
    service = HaltProcessService(db)
    try:
        contribution = service.approve_halt_engagement(
            contribution_id=contribution_id,
            approval_reason=request.approval_reason,
            user_id=request.user_id
        )
        return {
            "success": True,
            "contribution_id": contribution.id,
            "engagement_count": contribution.engagement_count,
            "engagement_score": contribution.engagement_score,
            "message": "Halt process approved successfully"
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


# Workflow Automation Endpoints
@router.post("/contributions/{contribution_id}/execute-workflow")
def execute_workflow(
    contribution_id: int,
    request: WorkflowExecutionRequest,
    db: Session = Depends(get_db)
):
    """Execute a progressive automation workflow.

    Args:
        contribution_id: ID of the contribution
        request: Workflow execution request
        db: Database session

    Returns:
        Workflow execution result
    """
    engine = ProgressiveAutomationEngine(db)
    try:
        execution = engine.execute_workflow(
            contribution_id=contribution_id,
            workflow_name=request.workflow_name,
            max_automation_level=request.max_automation_level,
            workflow_data=request.workflow_data
        )
        return {
            "success": True,
            "execution_id": execution.id,
            "workflow_name": execution.workflow_name,
            "workflow_stage": execution.workflow_stage,
            "automation_level": execution.automation_level,
            "status": execution.status,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(error)}"
        )


@router.get("/contributions/{contribution_id}/workflow-status")
def get_workflow_status(
    contribution_id: int,
    db: Session = Depends(get_db)
):
    """Get workflow execution status.

    Args:
        contribution_id: ID of the contribution
        db: Database session

    Returns:
        Workflow status information
    """
    engine = ProgressiveAutomationEngine(db)
    try:
        return engine.get_workflow_status(contribution_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.post("/contributions/{contribution_id}/advance-automation")
def advance_automation_level(
    contribution_id: int,
    target_level: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Advance contribution to higher automation level.

    Args:
        contribution_id: ID of the contribution
        target_level: Target automation level (0-5)
        db: Database session

    Returns:
        Updated contribution data
    """
    engine = ProgressiveAutomationEngine(db)
    try:
        contribution = engine.advance_automation_level(
            contribution_id=contribution_id,
            target_level=target_level
        )
        return {
            "success": True,
            "contribution_id": contribution.id,
            "automation_level": contribution.automation_level,
            "process_stage": contribution.process_stage
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


# Engagement Endpoints
@router.post("/contributions/{contribution_id}/engagement")
def record_engagement(
    contribution_id: int,
    request: EngagementRequest,
    db: Session = Depends(get_db)
):
    """Record an engagement event.

    Args:
        contribution_id: ID of the contribution
        request: Engagement request data
        db: Database session

    Returns:
        Engagement record data
    """
    service = EngagementIterationService(db)
    try:
        engagement = service.record_engagement(
            contribution_id=contribution_id,
            engagement_type=request.engagement_type,
            user_id=request.user_id,
            engagement_data=request.engagement_data,
            source=request.source
        )
        return {
            "success": True,
            "engagement_id": engagement.id,
            "engagement_type": engagement.engagement_type,
            "created_at": engagement.created_at.isoformat()
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get("/contributions/{contribution_id}/engagement-analytics")
def get_engagement_analytics(
    contribution_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get engagement analytics for a contribution.

    Args:
        contribution_id: ID of the contribution
        days: Number of days to analyze
        db: Database session

    Returns:
        Engagement analytics data
    """
    service = EngagementIterationService(db)
    try:
        return service.get_engagement_analytics(contribution_id, days)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.get("/contributions/{contribution_id}/iteration-history")
def get_iteration_history(
    contribution_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get iteration history for a contribution.

    Args:
        contribution_id: ID of the contribution
        limit: Maximum number of iterations to return
        db: Database session

    Returns:
        List of iterations
    """
    service = EngagementIterationService(db)
    return service.get_iteration_history(contribution_id, limit)


@router.get("/contributions/{contribution_id}/engagement-trends")
def get_engagement_trends(
    contribution_id: int,
    db: Session = Depends(get_db)
):
    """Calculate engagement trends and patterns.

    Args:
        contribution_id: ID of the contribution
        db: Database session

    Returns:
        Trend analysis data
    """
    service = EngagementIterationService(db)
    try:
        return service.calculate_engagement_trends(contribution_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.get("/users/{user_id}/engagement-summary")
def get_user_engagement_summary(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get engagement summary for a user.

    Args:
        user_id: ID of the user
        days: Number of days to analyze
        db: Database session

    Returns:
        User engagement summary
    """
    service = EngagementIterationService(db)
    return service.get_user_engagement_summary(user_id, days)
