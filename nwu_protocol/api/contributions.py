"""Contribution API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from nwu_protocol.models.contribution import (
    Contribution,
    ContributionCreate,
    ContributionStatus,
)
from nwu_protocol.services.contribution_manager import ContributionManager
from nwu_protocol.core.dependencies import get_contribution_manager

router = APIRouter(prefix="/api/v1/contributions", tags=["contributions"])


@router.post("", response_model=Contribution, status_code=201)
async def create_contribution(
    contribution_data: ContributionCreate,
    submitter: str,
    manager: ContributionManager = Depends(get_contribution_manager)
) -> Contribution:
    """
    Create a new contribution.

    Args:
        contribution_data: Contribution data
        submitter: Ethereum address of submitter (from auth)
        manager: Contribution manager instance

    Returns:
        Created contribution
    """
    try:
        contribution = manager.create_contribution(submitter, contribution_data)
        return contribution
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create contribution: {str(e)}")


@router.get("/{contribution_id}", response_model=Contribution)
async def get_contribution(
    contribution_id: str,
    manager: ContributionManager = Depends(get_contribution_manager)
) -> Contribution:
    """
    Get a contribution by ID.

    Args:
        contribution_id: ID of the contribution
        manager: Contribution manager instance

    Returns:
        Contribution details
    """
    contribution = manager.get_contribution(contribution_id)
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return contribution


@router.get("/{contribution_id}/status")
async def get_contribution_status(
    contribution_id: str,
    manager: ContributionManager = Depends(get_contribution_manager)
):
    """
    Get the verification status of a contribution.

    Args:
        contribution_id: ID of the contribution
        manager: Contribution manager instance

    Returns:
        Status information
    """
    contribution = manager.get_contribution(contribution_id)
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")

    return {
        "contribution_id": contribution_id,
        "status": contribution.status,
        "quality_score": contribution.quality_score,
        "verification_count": contribution.verification_count,
        "reward_amount": contribution.reward_amount,
        "updated_at": contribution.updated_at
    }


@router.get("", response_model=List[Contribution])
async def list_contributions(
    submitter: Optional[str] = None,
    status: Optional[ContributionStatus] = None,
    limit: int = 100,
    manager: ContributionManager = Depends(get_contribution_manager)
) -> List[Contribution]:
    """
    List contributions with optional filters.

    Args:
        submitter: Filter by submitter address
        status: Filter by status
        limit: Maximum number of results (default 100)
        manager: Contribution manager instance

    Returns:
        List of contributions
    """
    return manager.list_contributions(submitter=submitter, status=status, limit=limit)
