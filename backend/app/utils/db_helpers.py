"""Database helper utilities for common query patterns."""
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.app.models import User, Contribution


def get_user_by_address_or_404(db: Session, address: str) -> User:
    """
    Get user by Ethereum address or raise 404.

    Args:
        db: Database session
        address: Ethereum address (will be normalized to lowercase)

    Returns:
        User object

    Raises:
        HTTPException: 404 if user not found
    """
    normalized_address = address.lower()
    user = db.query(User).filter(User.address == normalized_address).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_contribution_by_id_or_404(db: Session, contribution_id: int) -> Contribution:
    """
    Get contribution by ID or raise 404.

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


def get_or_create_user(db: Session, address: str) -> tuple[User, bool]:
    """
    Get existing user or create new one.

    Args:
        db: Database session
        address: Ethereum address (will be normalized to lowercase)

    Returns:
        Tuple of (User object, created boolean)
    """
    normalized_address = address.lower()
    user = db.query(User).filter(User.address == normalized_address).first()
    if user:
        return user, False

    # Create new user
    user = User(address=normalized_address)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True
