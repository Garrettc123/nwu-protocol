"""User API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from nwu_protocol.models.user import User, UserCreate, UserStats
from nwu_protocol.services.user_manager import UserManager
from nwu_protocol.services.contribution_manager import ContributionManager
from nwu_protocol.core.dependencies import get_user_manager, get_contribution_manager

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("", response_model=User, status_code=201)
async def create_user(
    user_data: UserCreate,
    manager: UserManager = Depends(get_user_manager),
) -> User:
    """
    Register a new user by Ethereum address.

    Args:
        user_data: User creation data
        manager: User manager instance

    Returns:
        Created user
    """
    try:
        return manager.create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("", response_model=List[User])
async def list_users(
    limit: int = 100,
    manager: UserManager = Depends(get_user_manager),
) -> List[User]:
    """
    List all registered users.

    Args:
        limit: Maximum number of results (default 100)
        manager: User manager instance

    Returns:
        List of users
    """
    return manager.list_users(limit=limit)


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    manager: UserManager = Depends(get_user_manager),
) -> User:
    """
    Get a user by ID.

    Args:
        user_id: ID of the user
        manager: User manager instance

    Returns:
        User details
    """
    user = manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/address/{address}", response_model=User)
async def get_user_by_address(
    address: str,
    manager: UserManager = Depends(get_user_manager),
) -> User:
    """
    Get a user by Ethereum address.

    Args:
        address: Ethereum wallet address
        manager: User manager instance

    Returns:
        User details
    """
    user = manager.get_user_by_address(address)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: str,
    user_manager: UserManager = Depends(get_user_manager),
    contribution_manager: ContributionManager = Depends(get_contribution_manager),
) -> UserStats:
    """
    Get statistics for a user.

    Args:
        user_id: ID of the user
        user_manager: User manager instance
        contribution_manager: Contribution manager instance

    Returns:
        User statistics
    """
    user = user_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    contributions = contribution_manager.list_contributions(submitter=user.address)
    stats = user_manager.get_user_stats(user_id, contributions)
    if stats is None:
        raise HTTPException(status_code=404, detail="User not found")
    return stats
