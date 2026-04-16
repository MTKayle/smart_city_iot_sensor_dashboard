"""
Integration tests for WebSocket broadcast functionality in telemetry and alert services.

Tests verify that:
1. Telemetry data is broadcast with correct message format
2. Alerts are broadcast with correct message format
3. Message format matches requirements: {"type": "...", "data": {...}}
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models import Telemetry, Alert
from app.services.telemetry_service import TelemetryService
from app.services.alert_service import AlertService
from app.core.websocket_manager import WebSocketManager


@pytest.fixture
def mock_websocket_manager():
    """Create a mock WebSocket manager for testing."""
    manager = MagicMock(spec=WebSocketManager)
    manager.broadcast = MagicMock()
    return manager


@pytest.fixture
def sample_telemetry():
    """Create sample telemetry data."""
    return Telemetry(
        sensorId="sensor_001",
        locationId="ward_001",
        co2=450.5,
        noise=65.2,
        temperature=25.3,
        timestamp=datetime(2024, 1, 15, 10, 30, 0)
    )


@pytest.fixture
def sample_alert():
    """Create sample alert data."""
    return Alert(
        alertId="alert_001",
        sensorId="sensor_001",
        metricType="CO2",
        value=1250.0,
        level="HIGH",
        createdAt=datetime(2024, 1, 15, 10, 30, 5)
    )


def test_telemetry_broadcast_message_format(mock_websocket_manager, sample_telemetry):
    """
    Test that telemetry broadcasts use correct message format.
    
    Validates: Requirement 10.3
    Message format: {"type": "telemetry", "data": {...}}
    """
    # Create telemetry service with mock WebSocket manager
    with patch('app.services.telemetry_service.get_mongodb_client') as mock_mongo, \
         patch('app.services.telemetry_service.get_alert_service') as mock_alert_service:
        
        # Mock MongoDB client
        mock_mongo_instance = MagicMock()
        mock_mongo_instance.insert_telemetry.return_value = True
        mock_mongo.return_value = mock_mongo_instance
        
        # Mock alert service
        mock_alert_service_instance = MagicMock()
        mock_alert_service_instance.create_alert.return_value = None
        mock_alert_service.return_value = mock_alert_service_instance
        
        # Create service
        service = TelemetryService(websocket_manager=mock_websocket_manager)
        
        # Process telemetry
        service.process_telemetry(sample_telemetry)
        
        # Verify broadcast was called
        assert mock_websocket_manager.broadcast.called
        
        # Get the broadcast message
        call_args = mock_websocket_manager.broadcast.call_args
        message = call_args[0][0]
        
        # Verify message format
        assert "type" in message
        assert "data" in message
        assert message["type"] == "telemetry"
        
        # Verify data content
        data = message["data"]
        assert data["sensorId"] == "sensor_001"
        assert data["locationId"] == "ward_001"
        assert data["co2"] == 450.5
        assert data["noise"] == 65.2
        assert data["temperature"] == 25.3


def test_alert_broadcast_message_format(mock_websocket_manager, sample_alert):
    """
    Test that alert broadcasts use correct message format.
    
    Validates: Requirement 10.4
    Message format: {"type": "alert", "data": {...}}
    """
    # Create alert service with mock WebSocket manager
    with patch('app.services.alert_service.get_oracle_client') as mock_oracle:
        
        # Mock Oracle client
        mock_oracle_instance = MagicMock()
        mock_oracle_instance.insert_alert.return_value = True
        mock_oracle_instance.get_alerts.return_value = []
        mock_oracle.return_value = mock_oracle_instance
        
        # Create service
        service = AlertService(websocket_manager=mock_websocket_manager)
        
        # Manually call broadcast method (simulating alert creation)
        service._broadcast_alert(sample_alert)
        
        # Verify broadcast was called
        assert mock_websocket_manager.broadcast.called
        
        # Get the broadcast message
        call_args = mock_websocket_manager.broadcast.call_args
        message = call_args[0][0]
        
        # Verify message format
        assert "type" in message
        assert "data" in message
        assert message["type"] == "alert"
        
        # Verify data content
        data = message["data"]
        assert data["alertId"] == "alert_001"
        assert data["sensorId"] == "sensor_001"
        assert data["metricType"] == "CO2"
        assert data["value"] == 1250.0
        assert data["level"] == "HIGH"


def test_telemetry_broadcast_without_websocket_manager(sample_telemetry):
    """
    Test that telemetry processing works gracefully without WebSocket manager.
    
    Validates: Graceful degradation when WebSocket is not configured
    """
    with patch('app.services.telemetry_service.get_mongodb_client') as mock_mongo, \
         patch('app.services.telemetry_service.get_alert_service') as mock_alert_service:
        
        # Mock MongoDB client
        mock_mongo_instance = MagicMock()
        mock_mongo_instance.insert_telemetry.return_value = True
        mock_mongo.return_value = mock_mongo_instance
        
        # Mock alert service
        mock_alert_service_instance = MagicMock()
        mock_alert_service_instance.create_alert.return_value = None
        mock_alert_service.return_value = mock_alert_service_instance
        
        # Create service without WebSocket manager
        service = TelemetryService(websocket_manager=None)
        
        # Process telemetry - should not raise exception
        service.process_telemetry(sample_telemetry)
        
        # Verify MongoDB insertion still happened
        assert mock_mongo_instance.insert_telemetry.called


def test_alert_broadcast_without_websocket_manager():
    """
    Test that alert creation works gracefully without WebSocket manager.
    
    Validates: Graceful degradation when WebSocket is not configured
    """
    with patch('app.services.alert_service.get_oracle_client') as mock_oracle:
        
        # Mock Oracle client
        mock_oracle_instance = MagicMock()
        mock_oracle_instance.insert_alert.return_return_value = True
        mock_oracle_instance.get_alerts.return_value = []
        mock_oracle.return_value = mock_oracle_instance
        
        # Create service without WebSocket manager
        service = AlertService(websocket_manager=None)
        
        # Create alert with threshold-exceeding value
        alert = service.create_alert(
            sensor_id="sensor_001",
            metric_type="CO2",
            value=1250.0,
            timestamp=datetime(2024, 1, 15, 10, 30, 5)
        )
        
        # Alert should still be created even without WebSocket
        assert alert is not None


def test_high_threshold_telemetry_triggers_alert_broadcast(
    mock_websocket_manager,
    sample_telemetry
):
    """
    Test that telemetry exceeding thresholds triggers both telemetry and alert broadcasts.
    
    Validates: Requirements 6.1, 6.2, 10.3, 10.4
    """
    # Create telemetry with high CO2 value
    high_co2_telemetry = Telemetry(
        sensorId="sensor_001",
        locationId="ward_001",
        co2=1250.0,  # Exceeds threshold of 1000
        noise=65.2,
        temperature=25.3,
        timestamp=datetime(2024, 1, 15, 10, 30, 0)
    )
    
    with patch('app.services.telemetry_service.get_mongodb_client') as mock_mongo, \
         patch('app.services.alert_service.get_oracle_client') as mock_oracle:
        
        # Mock MongoDB client
        mock_mongo_instance = MagicMock()
        mock_mongo_instance.insert_telemetry.return_value = True
        mock_mongo.return_value = mock_mongo_instance
        
        # Mock Oracle client
        mock_oracle_instance = MagicMock()
        mock_oracle_instance.insert_alert.return_value = True
        mock_oracle_instance.get_alerts.return_value = []
        mock_oracle.return_value = mock_oracle_instance
        
        # Create services
        alert_service = AlertService(websocket_manager=mock_websocket_manager)
        telemetry_service = TelemetryService(websocket_manager=mock_websocket_manager)
        telemetry_service.alert_service = alert_service
        
        # Process telemetry
        telemetry_service.process_telemetry(high_co2_telemetry)
        
        # Verify broadcast was called at least twice (telemetry + alert)
        assert mock_websocket_manager.broadcast.call_count >= 2
        
        # Get all broadcast calls
        calls = mock_websocket_manager.broadcast.call_args_list
        
        # Verify telemetry broadcast
        telemetry_messages = [call[0][0] for call in calls if call[0][0].get("type") == "telemetry"]
        assert len(telemetry_messages) >= 1
        assert telemetry_messages[0]["data"]["co2"] == 1250.0
        
        # Verify alert broadcast
        alert_messages = [call[0][0] for call in calls if call[0][0].get("type") == "alert"]
        assert len(alert_messages) >= 1
        assert alert_messages[0]["data"]["metricType"] == "CO2"
        assert alert_messages[0]["data"]["value"] == 1250.0
        assert alert_messages[0]["data"]["level"] == "HIGH"
