"""API endpoints for contributions."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging

from ..database import get_db
from ..models import Contribution, User
from ..schemas import (
    ContributionResponse,
    ContributionUpload,
    ContributionStatus
)
from ..services import ipfs_service, rabbitmq_service
from ..utils.db_helpers import get_or_create_user, get_contribution_by_id_or_404
from ..utils.validators import validate_file_type
from nwu_protocol.utils.api_helpers import parse_json_or_400

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contributions", tags=["contributions"])


@router.post("/", response_model=ContributionResponse, status_code=status.HTTP_201_CREATED)
async def create_contribution(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file_type: str = Form(...),
    user_address: str = Form(...),
    metadata: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a new contribution.
    
    - **file**: File to upload
    - **title**: Title of the contribution
    - **description**: Optional description
    - **file_type**: Type of file (code, dataset, document)
    - **user_address**: Ethereum address of the user
    - **metadata**: Optional metadata as JSON string
    """
    # Validate file type
    validate_file_type(file_type)

    # Get or create user
    user, created = get_or_create_user(db, user_address)
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Upload to IPFS asynchronously
    ipfs_hash = await ipfs_service.add_file_async(file_content, file.filename)
    if not ipfs_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to IPFS"
        )
    
    # Pin the file for persistence asynchronously
    await ipfs_service.pin_file_async(ipfs_hash)
    
    # Parse metadata
    metadata_dict = None
    if metadata:
        metadata_dict = parse_json_or_400(metadata, "metadata")
    
    # Create contribution record
    contribution = Contribution(
        user_id=user.id,
        ipfs_hash=ipfs_hash,
        file_name=file.filename,
        file_type=file_type,
        file_size=file_size,
        title=title,
        description=description,
        meta_data=json.dumps(metadata_dict) if metadata_dict else None,
        status="pending"
    )
    
    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    
    # Publish verification task to RabbitMQ
    try:
        await rabbitmq_service.publish_verification_task(
            contribution.id,
            ipfs_hash,
            file_type
        )
        contribution.status = "verifying"
        db.commit()
    except Exception as e:
        logger.error(f"Failed to publish verification task: {e}")
    
    # Update user stats
    user.total_contributions += 1
    db.commit()
    
    return contribution


@router.get("/{contribution_id}", response_model=ContributionResponse)
def get_contribution(contribution_id: int, db: Session = Depends(get_db)):
    """Get contribution by ID."""
    return get_contribution_by_id_or_404(db, contribution_id)


@router.get("/{contribution_id}/status")
def get_contribution_status(contribution_id: int, db: Session = Depends(get_db)):
    """Get verification status of a contribution."""
    contribution = get_contribution_by_id_or_404(db, contribution_id)
    
    return {
        "contribution_id": contribution.id,
        "status": contribution.status,
        "quality_score": contribution.quality_score,
        "verification_count": contribution.verification_count,
        "updated_at": contribution.updated_at
    }


@router.get("/", response_model=List[ContributionResponse])
def list_contributions(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    user_address: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List contributions with optional filters."""
    query = db.query(Contribution)
    
    if status:
        query = query.filter(Contribution.status == status)
    
    if user_address:
        user = db.query(User).filter(User.address == user_address).first()
        if user:
            query = query.filter(Contribution.user_id == user.id)
        else:
            return []
    
    contributions = query.offset(skip).limit(limit).all()
    return contributions


@router.get("/{contribution_id}/file")
async def get_contribution_file(contribution_id: int, db: Session = Depends(get_db)):
    """Download the original file from IPFS."""
    contribution = get_contribution_by_id_or_404(db, contribution_id)
    
    file_content = await ipfs_service.get_file_async(contribution.ipfs_hash)
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file from IPFS"
        )
    
    from fastapi.responses import Response
    return Response(
        content=file_content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={contribution.file_name}"
        }
    )
