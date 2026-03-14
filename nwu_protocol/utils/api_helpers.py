"""API helper utilities for common API patterns."""
import json
from typing import Any, Dict, Optional, List
from fastapi import HTTPException, status


def parse_json_or_400(json_string: str, field_name: str = "data") -> Dict[str, Any]:
    """
    Parse JSON string or raise 400 error.

    Args:
        json_string: JSON string to parse
        field_name: Name of field for error message

    Returns:
        Parsed JSON as dictionary

    Raises:
        HTTPException: 400 if JSON is invalid
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON in {field_name}"
        )


def create_pagination_params(
    skip: int = 0,
    limit: int = 50,
    max_limit: int = 100
) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters.

    Args:
        skip: Number of records to skip
        limit: Number of records to return
        max_limit: Maximum allowed limit

    Returns:
        Tuple of (skip, limit)

    Raises:
        HTTPException: 400 if parameters are invalid
    """
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skip parameter must be non-negative"
        )

    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit parameter must be positive"
        )

    if limit > max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limit parameter cannot exceed {max_limit}"
        )

    return skip, limit


def handle_value_error(detail: str):
    """
    Raise HTTPException for ValueError cases.

    Args:
        detail: Error detail message

    Raises:
        HTTPException: 409 Conflict
    """
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail
    )


def handle_not_found(resource: str, identifier: Any):
    """
    Raise HTTPException for resource not found.

    Args:
        resource: Name of resource
        identifier: Resource identifier

    Raises:
        HTTPException: 404 Not Found
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} not found: {identifier}"
    )


def handle_generic_error(detail: str = "Internal server error"):
    """
    Raise HTTPException for generic errors.

    Args:
        detail: Error detail message

    Raises:
        HTTPException: 500 Internal Server Error
    """
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail
    )
