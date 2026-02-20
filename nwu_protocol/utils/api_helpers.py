"""API helper utilities to reduce code duplication in nwu_protocol."""

from typing import Optional, TypeVar
from fastapi import HTTPException

T = TypeVar('T')


def get_or_404(
    item: Optional[T],
    error_message: str = "Resource not found"
) -> T:
    """
    Return the item if it exists, otherwise raise 404 error.

    Args:
        item: The item to check (can be None)
        error_message: Custom error message

    Returns:
        The item if it's not None

    Raises:
        HTTPException: 404 if item is None
    """
    if item is None:
        raise HTTPException(status_code=404, detail=error_message)
    return item


def handle_value_error(error: ValueError, default_message: str = "Invalid request") -> None:
    """
    Convert ValueError to 409 Conflict HTTPException.

    Args:
        error: The ValueError to handle
        default_message: Default message if error message is empty

    Raises:
        HTTPException: 409 with the error message
    """
    message = str(error) if str(error) else default_message
    raise HTTPException(status_code=409, detail=message)


def handle_generic_error(error: Exception, action: str = "process request") -> None:
    """
    Convert generic Exception to 500 Internal Server Error HTTPException.

    Args:
        error: The Exception to handle
        action: Description of the action that failed

    Raises:
        HTTPException: 500 with the error message
    """
    raise HTTPException(status_code=500, detail=f"Failed to {action}: {str(error)}")
