"""Validation utilities for common validation patterns."""
import re
from typing import Optional
from fastapi import HTTPException, status
from backend.app.models import SubscriptionTier


# Pre-compiled regex patterns for performance
ETHEREUM_ADDRESS_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')


def normalize_ethereum_address(address: str) -> str:
    """
    Normalize Ethereum address to lowercase.

    Args:
        address: Ethereum address

    Returns:
        Normalized (lowercase) Ethereum address
    """
    return address.lower()


def validate_ethereum_address(address: str) -> bool:
    """
    Validate Ethereum address format.

    Args:
        address: Ethereum address to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(ETHEREUM_ADDRESS_PATTERN.match(address))


def validate_and_normalize_address(address: str) -> str:
    """
    Validate and normalize Ethereum address.

    Args:
        address: Ethereum address

    Returns:
        Normalized (lowercase) Ethereum address

    Raises:
        HTTPException: 400 if address is invalid
    """
    if not validate_ethereum_address(address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Ethereum address format"
        )
    return normalize_ethereum_address(address)


def validate_subscription_tier(tier: str) -> SubscriptionTier:
    """
    Validate and convert subscription tier string to enum.

    Args:
        tier: Tier string (case-insensitive)

    Returns:
        SubscriptionTier enum

    Raises:
        HTTPException: 400 if tier is invalid
    """
    try:
        return SubscriptionTier[tier.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {tier}. Must be one of: free, pro, enterprise"
        )


def validate_file_type(file_type: str) -> str:
    """
    Validate file type for contributions.

    Args:
        file_type: File type to validate

    Returns:
        Validated file type

    Raises:
        HTTPException: 400 if file type is invalid
    """
    valid_types = ["code", "dataset", "document"]
    if file_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Must be one of: {', '.join(valid_types)}"
        )
    return file_type
