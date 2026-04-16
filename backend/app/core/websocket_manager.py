"""
WebSocket Manager for Smart City IoT Dashboard.

This module manages WebSocket connections and broadcasts real-time updates
to connected clients.
"""

import logging
import json
from typing import Set, Dict, Any
from fastapi import WebSocket


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manager for WebSocket connections and broadcasting.
    
    Features:
    - Connection management (connect/disconnect)
    - Broadcast messages to all connected clients
    - Automatic cleanup of disconnected clients
    """
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Set[WebSocket] = set()
        self.loop = None
        logger.info("WebSocket manager initialized")
    
    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.
        Sends connection acknowledgment message to the client.
        
        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected - Total connections: {len(self.active_connections)}")
        
        # Send connection acknowledgment message
        try:
            ack_message = {
                "type": "connection_ack",
                "message": "Connected successfully"
            }
            await websocket.send_text(json.dumps(ack_message))
            logger.debug("Connection acknowledgment sent to client")
        except Exception as e:
            logger.error(f"Failed to send connection acknowledgment: {e}")
            # Remove from active connections if acknowledgment fails
            self.active_connections.discard(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from active connections.
        
        Args:
            websocket: WebSocket connection to remove
        """
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected - Total connections: {len(self.active_connections)}")
    
    def broadcast(self, message: Dict[str, Any]):
        """
        Synchronous wrapper to broadcast message to all connected WebSocket clients.
        Schedules the async broadcast on the main event loop.
        """
        if not self.active_connections:
            return
            
        import asyncio
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._async_broadcast(message), self.loop)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._async_broadcast(message))
            except RuntimeError:
                logger.error("No event loop available for broadcasting")

    async def _async_broadcast(self, message: Dict[str, Any]):
        """
        Internal async method to broadcast message.
        """
        # Convert message to JSON
        try:
            message_json = json.dumps(message)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize message to JSON: {e}")
            return
        
        # Track disconnected clients for cleanup
        disconnected = set()
        
        # Broadcast to all active connections
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
        
        logger.debug(
            f"Broadcast complete - Message type: {message.get('type')}, "
            f"Clients: {len(self.active_connections)}"
        )
    
    def get_connection_count(self) -> int:
        """
        Get the number of active WebSocket connections.
        
        Returns:
            int: Number of active connections
        """
        return len(self.active_connections)


# Singleton instance
_websocket_manager: WebSocketManager = None


def get_websocket_manager() -> WebSocketManager:
    """
    Get singleton WebSocket manager instance.
    
    Returns:
        WebSocketManager: Shared manager instance
    """
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager
