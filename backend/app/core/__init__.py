"""
Core modules for Smart City IoT Dashboard.
"""

from app.core.config import Settings, get_settings
from app.core.websocket_manager import WebSocketManager, get_websocket_manager

__all__ = [
    "Settings",
    "get_settings",
    "WebSocketManager",
    "get_websocket_manager",
]
