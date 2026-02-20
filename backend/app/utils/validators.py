"""Validation utilities to reduce code duplication."""

from fastapi import HTTPException, status
from typing import Literal

from ..schemas import FileType


def validate_ethereum_address(address: str) -> str:
    """
    Validate Ethereum address format.

    Args:
        address: Ethereum address to validate

    Returns:
        Normalized (lowercase) address

    Raises:
        HTTPException: 400 if address format is invalid
    """
    if not address.startswith("0x") or len(address) != 42:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Ethereum address format"
        )
    return address.lower()


def validate_file_type(file_type: str) -> str:
    """
    Validate file type against allowed types.

    Args:
        file_type: File type to validate

    Returns:
        Validated file type

    Raises:
        HTTPException: 400 if file type is invalid
    """
    allowed_types = [ft.value for ft in FileType]
    if file_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Must be one of: {', '.join(allowed_types)}"
        )
    return file_type
