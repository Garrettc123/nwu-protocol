"""Verification API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from nwu_protocol.models.verification import Verification, VerificationCreate
from nwu_protocol.services.verification_engine import VerificationEngine
from nwu_protocol.services.contribution_manager import ContributionManager
from nwu_protocol.core.dependencies import get_verification_engine, get_contribution_manager

router = APIRouter(prefix="/api/v1/verifications", tags=["verifications"])


@router.post("", response_model=Verification, status_code=201)
async def submit_verification(
    verification_data: VerificationCreate,
    engine: VerificationEngine = Depends(get_verification_engine),
    manager: ContributionManager = Depends(get_contribution_manager)
) -> Verification:
    """
    Submit a new verification for a contribution.

    Args:
        verification_data: Verification data
        engine: Verification engine instance
        manager: Contribution manager instance

    Returns:
        Created verification
    """
    try:
        # Check if contribution exists
        contribution = manager.get_contribution(verification_data.contribution_id)
        if not contribution:
            raise HTTPException(status_code=404, detail="Contribution not found")

        verification = engine.submit_verification(verification_data)
        return verification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit verification: {str(e)}")


@router.get("/{verification_id}", response_model=Verification)
async def get_verification(
    verification_id: str,
    engine: VerificationEngine = Depends(get_verification_engine)
) -> Verification:
    """
    Get a verification by ID.

    Args:
        verification_id: ID of the verification
        engine: Verification engine instance

    Returns:
        Verification details
    """
    verification = engine.get_verification(verification_id)
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    return verification


@router.get("/contribution/{contribution_id}", response_model=List[Verification])
async def get_contribution_verifications(
    contribution_id: str,
    engine: VerificationEngine = Depends(get_verification_engine),
    manager: ContributionManager = Depends(get_contribution_manager)
) -> List[Verification]:
    """
    Get all verifications for a contribution.

    Args:
        contribution_id: ID of the contribution
        engine: Verification engine instance
        manager: Contribution manager instance

    Returns:
        List of verifications
    """
    # Check if contribution exists
    contribution = manager.get_contribution(contribution_id)
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")

    return engine.get_verifications_for_contribution(contribution_id)


@router.get("/contribution/{contribution_id}/consensus")
async def get_contribution_consensus(
    contribution_id: str,
    engine: VerificationEngine = Depends(get_verification_engine),
    manager: ContributionManager = Depends(get_contribution_manager)
):
    """
    Get the consensus status for a contribution.

    Args:
        contribution_id: ID of the contribution
        engine: Verification engine instance
        manager: Contribution manager instance

    Returns:
        Consensus information
    """
    # Check if contribution exists
    contribution = manager.get_contribution(contribution_id)
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")

    consensus = engine.calculate_consensus(contribution_id)
    return {
        "contribution_id": contribution_id,
        **consensus
    }
