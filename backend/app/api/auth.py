"""API endpoints for authentication."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import secrets
import logging
from typing import Optional

from ..database import get_db
from ..models import User
from ..services import auth_service, redis_service
from ..utils.db_helpers import get_or_create_user
from ..utils.validators import validate_ethereum_address, normalize_ethereum_address

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


class ConnectRequest(BaseModel):
    """Request model for wallet connection."""
    address: str
    

class VerifyRequest(BaseModel):
    """Request model for signature verification."""
    address: str
    signature: str
    nonce: str


class AuthResponse(BaseModel):
    """Response model for authentication."""
    access_token: str
    token_type: str = "bearer"
    address: str
    expires_in: int


@router.post("/connect")
async def connect_wallet(request: ConnectRequest, db: Session = Depends(get_db)):
    """
    Initiate Web3 wallet connection.

    Returns a nonce that must be signed by the wallet.

    - **address**: Ethereum wallet address
    """
    address = normalize_ethereum_address(request.address)

    # Validate Ethereum address format
    if not validate_ethereum_address(address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Ethereum address format"
        )

    # Generate nonce
    nonce = secrets.token_urlsafe(32)

    # Store nonce in Redis with 5-minute expiration
    await redis_service.set(f"auth:nonce:{address}", nonce, expiry=300)

    # Generate message to sign
    message = auth_service.generate_nonce_message(address, nonce)

    # Get or create user
    user, created = get_or_create_user(db, address)
    
    logger.info(f"Nonce generated for address: {address}")
    
    return {
        "nonce": nonce,
        "message": message,
        "address": address
    }


@router.post("/verify", response_model=AuthResponse)
async def verify_signature(request: VerifyRequest, db: Session = Depends(get_db)):
    """
    Verify wallet signature and return JWT token.

    - **address**: Ethereum wallet address
    - **signature**: Signature from wallet
    - **nonce**: Nonce from connect endpoint
    """
    address = normalize_ethereum_address(request.address)
    
    # Get stored nonce from Redis
    stored_nonce = await redis_service.get(f"auth:nonce:{address}")
    
    if not stored_nonce:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nonce expired or not found. Please reconnect."
        )
    
    # Verify nonce matches
    if stored_nonce != request.nonce:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid nonce"
        )
    
    # Generate the same message that was signed
    message = auth_service.generate_nonce_message(address, request.nonce)
    
    # Verify signature
    is_valid = auth_service.verify_signature(address, message, request.signature)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # Delete used nonce
    await redis_service.delete(f"auth:nonce:{address}")

    # Get or create user
    user, created = get_or_create_user(db, address)
    
    # Create JWT token
    token_data = {
        "sub": address,
        "user_id": user.id,
        "type": "access"
    }
    access_token = auth_service.create_access_token(token_data)
    
    # Store session in Redis
    await redis_service.set_json(
        f"auth:session:{address}",
        {"user_id": user.id, "address": address},
        expiry=86400  # 24 hours
    )
    
    logger.info(f"Authentication successful for address: {address}")
    
    return AuthResponse(
        access_token=access_token,
        address=address,
        expires_in=auth_service.access_token_expire_minutes * 60
    )


@router.post("/logout")
async def logout(address: str):
    """
    Logout user and invalidate session.

    - **address**: Ethereum wallet address
    """
    address = normalize_ethereum_address(address)
    
    # Delete session from Redis
    await redis_service.delete(f"auth:session:{address}")
    await redis_service.delete(f"auth:nonce:{address}")
    
    logger.info(f"User logged out: {address}")
    
    return {"message": "Logged out successfully"}


@router.get("/status")
async def auth_status(address: str):
    """
    Check authentication status.

    - **address**: Ethereum wallet address
    """
    address = normalize_ethereum_address(address)
    
    # Check if session exists in Redis
    session = await redis_service.get_json(f"auth:session:{address}")
    
    return {
        "authenticated": session is not None,
        "address": address
    }
