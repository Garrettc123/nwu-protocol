"""Database helper utilities to reduce code duplication."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models import User, Contribution, Verification


def get_user_by_address_or_404(db: Session, address: str) -> User:
    """
    Get a user by Ethereum address or raise 404 error.

    Args:
        db: Database session
        address: Ethereum address

    Returns:
        User object

    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(User).filter(User.address == address).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_contribution_by_id_or_404(db: Session, contribution_id: int) -> Contribution:
    """
    Get a contribution by ID or raise 404 error.

    Args:
        db: Database session
        contribution_id: Contribution ID

    Returns:
        Contribution object

    Raises:
        HTTPException: 404 if contribution not found
    """
    contribution = db.query(Contribution).filter(Contribution.id == contribution_id).first()
    if not contribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contribution not found"
        )
    return contribution


def get_verification_by_id_or_404(db: Session, verification_id: int) -> Verification:
    """
    Get a verification by ID or raise 404 error.

    Args:
        db: Database session
        verification_id: Verification ID

    Returns:
        Verification object

    Raises:
        HTTPException: 404 if verification not found
    """
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found"
        )
    return verification


def get_or_create_user(db: Session, address: str) -> User:
    """
    Get existing user or create a new one if not exists.

    Args:
        db: Database session
        address: Ethereum address

    Returns:
        User object (existing or newly created)
    """
    user = db.query(User).filter(User.address == address).first()
    if not user:
        user = User(address=address)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
