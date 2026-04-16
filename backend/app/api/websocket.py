"""
WebSocket endpoint for Smart City IoT Dashboard.

This module provides the WebSocket endpoint for real-time updates.
"""

import logging
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core import get_websocket_manager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create WebSocket router
router = APIRouter(tags=["websocket"])

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 30


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry and alert updates.
    
    Clients connect to this endpoint to receive:
    - Real-time telemetry data
    - Alert notifications
    - Periodic heartbeat messages to keep connection alive
    
    Message format:
    {
        "type": "telemetry" | "alert" | "heartbeat" | "connection_ack",
        "data": { ... }
    }
    
    Args:
        websocket: WebSocket connection
    """
    manager = get_websocket_manager()
    
    # Accept connection and register with manager
    await manager.connect(websocket)
    logger.info("Client connected to WebSocket")
    
    try:
        # Keep connection alive with periodic heartbeat
        while True:
            try:
                # Wait for client message with timeout for heartbeat
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=HEARTBEAT_INTERVAL
                )
                logger.debug(f"Received message from client: {data}")
                
                # Handle client messages (ping/pong, etc.)
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        # Respond to client ping with pong
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    logger.debug(f"Non-JSON message from client: {data}")
                
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                try:
                    heartbeat_message = {
                        "type": "heartbeat",
                        "message": "Connection alive"
                    }
                    await websocket.send_text(json.dumps(heartbeat_message))
                    logger.debug("Heartbeat sent to client")
                except Exception as e:
                    logger.warning(f"Failed to send heartbeat: {e}")
                    # Connection likely dead, will be caught in outer exception handler
                    raise
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)
