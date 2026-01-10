"""API endpoints for verifications."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
import logging

from ..database import get_db
from ..models import Verification, Contribution
from ..schemas import VerificationCreate, VerificationResponse
from .websocket import notify_contribution_update

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/verifications", tags=["verifications"])


@router.post("/", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def submit_verification(verification_data: VerificationCreate, db: Session = Depends(get_db)):
    """
    Submit a verification result from an AI agent.
    
    This endpoint is called by AI agents after they complete verification.
    """
    # Check if contribution exists
    contribution = db.query(Contribution).filter(
        Contribution.id == verification_data.contribution_id
    ).first()
    if not contribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contribution not found"
        )
    
    # Create verification record
    verification_dict = verification_data.model_dump()
    details = verification_dict.pop('details', None)
    
    verification = Verification(
        **verification_dict,
        details=json.dumps(details) if details else None
    )
    
    db.add(verification)
    db.commit()
    db.refresh(verification)
    
    # Update contribution verification count and status
    contribution.verification_count += 1
    
    # Calculate average quality score
    all_verifications = db.query(Verification).filter(
        Verification.contribution_id == contribution.id
    ).all()
    
    total_score = sum(v.vote_score for v in all_verifications)
    avg_score = total_score / len(all_verifications)
    contribution.quality_score = round(avg_score, 2)
    
    # Update status based on verification count and score
    if contribution.verification_count >= 3:  # Require at least 3 verifications
        if avg_score >= 70:
            contribution.status = "verified"
        else:
            contribution.status = "rejected"
    
    db.commit()
    
    # Send WebSocket notification
    try:
        await notify_contribution_update(
            contribution.id,
            contribution.status,
            contribution.quality_score
        )
    except Exception as e:
        # Log error but don't fail the request
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send WebSocket notification: {e}")
    
    return verification


@router.get("/contribution/{contribution_id}", response_model=List[VerificationResponse])
def get_contribution_verifications(contribution_id: int, db: Session = Depends(get_db)):
    """Get all verifications for a contribution."""
    contribution = db.query(Contribution).filter(Contribution.id == contribution_id).first()
    if not contribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contribution not found"
        )
    
    verifications = db.query(Verification).filter(
        Verification.contribution_id == contribution_id
    ).all()
    
    return verifications


@router.get("/{verification_id}", response_model=VerificationResponse)
def get_verification(verification_id: int, db: Session = Depends(get_db)):
    """Get a specific verification by ID."""
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found"
        )
    return verification
