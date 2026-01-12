"""WebSocket endpoint for real-time verification status updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, Set
import json
import logging
import asyncio

from ..database import get_db
from ..models import Contribution
from ..services import redis_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, contribution_id: int):
        """
        Connect a WebSocket for a specific contribution.
        
        Args:
            websocket: WebSocket connection
            contribution_id: Contribution ID to track
        """
        await websocket.accept()
        
        if contribution_id not in self.active_connections:
            self.active_connections[contribution_id] = set()
        
        self.active_connections[contribution_id].add(websocket)
        logger.info(f"WebSocket connected for contribution {contribution_id}")
    
    def disconnect(self, websocket: WebSocket, contribution_id: int):
        """
        Disconnect a WebSocket.
        
        Args:
            websocket: WebSocket connection
            contribution_id: Contribution ID being tracked
        """
        if contribution_id in self.active_connections:
            self.active_connections[contribution_id].discard(websocket)
            
            if not self.active_connections[contribution_id]:
                del self.active_connections[contribution_id]
        
        logger.info(f"WebSocket disconnected for contribution {contribution_id}")
    
    async def send_update(self, contribution_id: int, message: dict):
        """
        Send update to all connections tracking a contribution.
        
        Args:
            contribution_id: Contribution ID
            message: Message to send
        """
        if contribution_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[contribution_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection, contribution_id)
    
    async def broadcast(self, message: dict):
        """
        Broadcast message to all connections.
        
        Args:
            message: Message to broadcast
        """
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting WebSocket message: {e}")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/contributions/{contribution_id}")
async def websocket_contribution_status(
    websocket: WebSocket,
    contribution_id: int
):
    """
    WebSocket endpoint for real-time contribution verification status.
    
    Clients can connect to receive updates about:
    - Verification status changes
    - Quality score updates
    - Agent verification progress
    
    Args:
        contribution_id: ID of the contribution to track
    """
    await manager.connect(websocket, contribution_id)
    
    try:
        # Send initial status
        from ..database import SessionLocal
        db = SessionLocal()
        
        try:
            contribution = db.query(Contribution).filter(
                Contribution.id == contribution_id
            ).first()
            
            if contribution:
                await websocket.send_json({
                    "type": "status",
                    "contribution_id": contribution_id,
                    "status": contribution.status,
                    "quality_score": contribution.quality_score,
                    "verification_count": contribution.verification_count,
                    "updated_at": contribution.updated_at.isoformat() if contribution.updated_at else None
                })
        finally:
            db.close()
        
        # Keep connection alive and listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                
                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")
                
            except WebSocketDisconnect:
                break
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket, contribution_id)


async def notify_contribution_update(contribution_id: int, status: str, quality_score: float = None):
    """
    Notify connected clients about contribution updates.
    
    This function should be called when a contribution's status changes.
    
    Args:
        contribution_id: ID of the contribution
        status: New status
        quality_score: Optional quality score
    """
    message = {
        "type": "update",
        "contribution_id": contribution_id,
        "status": status,
        "quality_score": quality_score,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.send_update(contribution_id, message)
    
    # Also store in Redis for clients that reconnect
    await redis_service.set_json(
        f"ws:update:{contribution_id}",
        message,
        expiry=3600  # 1 hour
    )
