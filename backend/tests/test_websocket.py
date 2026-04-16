"""
Unit tests for WebSocket endpoint.

Tests WebSocket connection, heartbeat, and message handling.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient

from app.main import app
from app.core import get_websocket_manager


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def ws_manager():
    """Get WebSocket manager instance."""
    return get_websocket_manager()


def test_websocket_connection_acknowledgment(client):
    """
    Test that WebSocket connection sends acknowledgment message.
    
    Feature: smart-city-iot-dashboard, Requirement 10.2
    """
    with client.websocket_connect("/ws") as websocket:
        # Receive connection acknowledgment
        data = websocket.receive_text()
        message = json.loads(data)
        
        assert message["type"] == "connection_ack"
        assert message["message"] == "Connected successfully"


def test_websocket_ping_pong(client):
    """
    Test that WebSocket responds to ping with pong.
    """
    with client.websocket_connect("/ws") as websocket:
        # Receive connection acknowledgment
        ack = websocket.receive_text()
        assert json.loads(ack)["type"] == "connection_ack"
        
        # Send ping
        websocket.send_text(json.dumps({"type": "ping"}))
        
        # Receive pong
        data = websocket.receive_text()
        message = json.loads(data)
        
        assert message["type"] == "pong"


def test_websocket_connection_count(client, ws_manager):
    """
    Test that WebSocket manager tracks connection count correctly.
    """
    initial_count = ws_manager.get_connection_count()
    
    with client.websocket_connect("/ws") as websocket:
        # Receive connection acknowledgment
        ack = websocket.receive_text()
        assert json.loads(ack)["type"] == "connection_ack"
        
        # Connection count should increase
        assert ws_manager.get_connection_count() == initial_count + 1
    
    # Connection count should return to initial after disconnect
    # Note: There might be a small delay for cleanup
    assert ws_manager.get_connection_count() == initial_count


def test_websocket_multiple_connections(client):
    """
    Test that multiple WebSocket connections can be established.
    
    Feature: smart-city-iot-dashboard, Property 20: WebSocket Client Isolation
    """
    with client.websocket_connect("/ws") as ws1:
        # Receive connection acknowledgment for first client
        ack1 = ws1.receive_text()
        assert json.loads(ack1)["type"] == "connection_ack"
        
        with client.websocket_connect("/ws") as ws2:
            # Receive connection acknowledgment for second client
            ack2 = ws2.receive_text()
            assert json.loads(ack2)["type"] == "connection_ack"
            
            # Both connections should be active
            # Send ping to first client
            ws1.send_text(json.dumps({"type": "ping"}))
            pong1 = ws1.receive_text()
            assert json.loads(pong1)["type"] == "pong"
            
            # Send ping to second client
            ws2.send_text(json.dumps({"type": "ping"}))
            pong2 = ws2.receive_text()
            assert json.loads(pong2)["type"] == "pong"


def test_websocket_handles_invalid_json(client):
    """
    Test that WebSocket handles invalid JSON gracefully.
    """
    with client.websocket_connect("/ws") as websocket:
        # Receive connection acknowledgment
        ack = websocket.receive_text()
        assert json.loads(ack)["type"] == "connection_ack"
        
        # Send invalid JSON
        websocket.send_text("not valid json")
        
        # Connection should remain alive
        # Send valid ping to verify
        websocket.send_text(json.dumps({"type": "ping"}))
        pong = websocket.receive_text()
        assert json.loads(pong)["type"] == "pong"


def test_websocket_broadcast(ws_manager):
    """
    Test that WebSocket manager can broadcast messages.
    """
    # Create mock WebSocket connections
    from unittest.mock import AsyncMock
    import asyncio
    
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()
    
    # Add to active connections
    ws_manager.active_connections.add(mock_ws1)
    ws_manager.active_connections.add(mock_ws2)
    
    # Broadcast message
    test_message = {
        "type": "telemetry",
        "data": {"sensorId": "test_sensor", "value": 100}
    }
    
    # Run async broadcast in event loop
    asyncio.run(ws_manager.broadcast(test_message))
    
    # Verify both connections received the message
    expected_json = json.dumps(test_message)
    mock_ws1.send_text.assert_called_once_with(expected_json)
    mock_ws2.send_text.assert_called_once_with(expected_json)
    
    # Cleanup
    ws_manager.active_connections.discard(mock_ws1)
    ws_manager.active_connections.discard(mock_ws2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
