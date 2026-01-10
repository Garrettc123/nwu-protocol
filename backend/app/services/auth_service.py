"""Authentication service with Web3 signature verification."""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from web3 import Web3
from eth_account.messages import encode_defunct
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for Web3 wallet verification."""
    
    def __init__(self):
        """Initialize auth service."""
        self.w3 = Web3()
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
    
    def verify_signature(self, address: str, message: str, signature: str) -> bool:
        """
        Verify Web3 signature.
        
        Args:
            address: Ethereum address
            message: Original message that was signed
            signature: Signature from wallet
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Create the message that was signed
            message_hash = encode_defunct(text=message)
            
            # Recover the address from signature
            recovered_address = self.w3.eth.account.recover_message(
                message_hash,
                signature=signature
            )
            
            # Compare addresses (case-insensitive)
            is_valid = recovered_address.lower() == address.lower()
            
            if is_valid:
                logger.info(f"Signature verified for address: {address}")
            else:
                logger.warning(f"Invalid signature for address: {address}")
            
            return is_valid
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Data to encode in token
            expires_delta: Optional custom expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            return None
    
    def generate_nonce_message(self, address: str, nonce: str) -> str:
        """
        Generate message for wallet signature.
        
        Args:
            address: Ethereum address
            nonce: Random nonce for this authentication attempt
            
        Returns:
            Message to be signed by wallet
        """
        return f"Sign this message to authenticate with NWU Protocol.\n\nAddress: {address}\nNonce: {nonce}\n\nThis request will not trigger a blockchain transaction or cost any gas fees."


# Global auth service instance
auth_service = AuthService()
