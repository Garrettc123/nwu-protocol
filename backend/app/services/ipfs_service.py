"""IPFS service for file storage."""

import ipfshttpclient
import logging
from typing import Optional, BinaryIO
from ..config import settings

logger = logging.getLogger(__name__)


class IPFSService:
    """IPFS service for decentralized file storage."""
    
    def __init__(self):
        """Initialize IPFS client."""
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to IPFS node."""
        try:
            self.client = ipfshttpclient.connect(
                f'/dns/{settings.ipfs_host}/tcp/{settings.ipfs_port}/http'
            )
            logger.info("Connected to IPFS node")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS: {e}")
            self.client = None
    
    def add_file(self, file_data: BinaryIO, file_name: str) -> Optional[str]:
        """
        Add file to IPFS.
        
        Args:
            file_data: File binary data
            file_name: Original file name
            
        Returns:
            IPFS hash (CID) or None if failed
        """
        try:
            if not self.client:
                self._connect()
            
            result = self.client.add(file_data)
            ipfs_hash = result['Hash']
            logger.info(f"File {file_name} added to IPFS: {ipfs_hash}")
            return ipfs_hash
        except Exception as e:
            logger.error(f"Failed to add file to IPFS: {e}")
            return None
    
    def get_file(self, ipfs_hash: str) -> Optional[bytes]:
        """
        Get file from IPFS.
        
        Args:
            ipfs_hash: IPFS hash (CID)
            
        Returns:
            File content as bytes or None if failed
        """
        try:
            if not self.client:
                self._connect()
            
            content = self.client.cat(ipfs_hash)
            return content
        except Exception as e:
            logger.error(f"Failed to get file from IPFS: {e}")
            return None
    
    def pin_file(self, ipfs_hash: str) -> bool:
        """
        Pin file to ensure persistence.
        
        Args:
            ipfs_hash: IPFS hash (CID)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                self._connect()
            
            self.client.pin.add(ipfs_hash)
            logger.info(f"File pinned: {ipfs_hash}")
            return True
        except Exception as e:
            logger.error(f"Failed to pin file: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to IPFS."""
        try:
            if self.client:
                self.client.id()
                return True
        except:
            pass
        return False


# Global IPFS service instance
ipfs_service = IPFSService()
