"""
Unit tests for MQTT Consumer module.

Tests cover:
- Message parsing with valid payloads
- Rejection of malformed JSON
- Handling of missing required fields
- Validation error handling
- Telemetry handler invocation
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.messaging.mqtt_consumer import MQTTConsumer
from app.models import Telemetry
from pydantic import ValidationError


class TestMQTTConsumer:
    """Test suite for MQTTConsumer class."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        self.handler_mock = Mock()
        self.consumer = MQTTConsumer(
            broker_host="test_broker",
            broker_port=1883,
            telemetry_handler=self.handler_mock
        )
    
    def test_initialization(self):
        """Test MQTT consumer initialization with custom parameters."""
        assert self.consumer.broker_host == "test_broker"
        assert self.consumer.broker_port == 1883
        assert self.consumer.telemetry_handler == self.handler_mock
        assert self.consumer.topic_pattern == "sensors/+/telemetry"
        assert self.consumer.reconnect_delay == 1
        assert self.consumer.max_reconnect_delay == 60
    
    def test_initialization_with_env_defaults(self):
        """Test MQTT consumer initialization using environment variables."""
        with patch.dict('os.environ', {
            'MQTT_BROKER_HOST': 'env_broker',
            'MQTT_BROKER_PORT': '1234'
        }):
            consumer = MQTTConsumer()
            assert consumer.broker_host == "env_broker"
            assert consumer.broker_port == 1234
    
    def test_on_message_valid_telemetry(self):
        """Test processing of valid telemetry message."""
        # Create valid telemetry payload
        payload = {
            "sensorId": "sensor_001",
            "locationId": "ward_001",
            "co2": 450.5,
            "noise": 65.2,
            "temperature": 25.3,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        # Create mock MQTT message
        msg = Mock()
        msg.topic = "sensors/sensor_001/telemetry"
        msg.payload = json.dumps(payload).encode('utf-8')
        
        # Process message
        self.consumer._on_message(None, None, msg)
        
        # Verify handler was called with Telemetry object
        assert self.handler_mock.call_count == 1
        telemetry = self.handler_mock.call_args[0][0]
        assert isinstance(telemetry, Telemetry)
        assert telemetry.sensorId == "sensor_001"
        assert telemetry.locationId == "ward_001"
        assert telemetry.co2 == 450.5
        assert telemetry.noise == 65.2
        assert telemetry.temperature == 25.3
    
    def test_on_message_invalid_json(self):
        """Test handling of malformed JSON message."""
        # Create message with invalid JSON
        msg = Mock()
        msg.topic = "sensors/sensor_001/telemetry"
        msg.payload = b"{ invalid json }"
        
        # Process message - should not crash
        self.consumer._on_message(None, None, msg)
        
        # Verify handler was NOT called
        assert self.handler_mock.call_count == 0
    
    def test_on_message_missing_required_field(self):
        """Test handling of message with missing required field."""
        # Create payload missing 'sensorId' field
        payload = {
            "locationId": "ward_001",
            "co2": 450.5,
            "noise": 65.2,
            "temperature": 25.3,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        msg = Mock()
        msg.topic = "sensors/sensor_001/telemetry"
        msg.payload = json.dumps(payload).encode('utf-8')
        
        # Process message - should not crash
        self.consumer._on_message(None, None, msg)
        
        # Verify handler was NOT called
        assert self.handler_mock.call_count == 0
    
    def test_on_message_invalid_co2_value(self):
        """Test handling of message with invalid CO2 value (negative)."""
        # Create payload with negative CO2 (violates validation)
        payload = {
            "sensorId": "sensor_001",
            "locationId": "ward_001",
            "co2": -100.0,  # Invalid: must be >= 0
            "noise": 65.2,
            "temperature": 25.3,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        msg = Mock()
        msg.topic = "sensors/sensor_001/telemetry"
        msg.payload = json.dumps(payload).encode('utf-8')
        
        # Process message - should not crash
        self.consumer._on_message(None, None, msg)
        
        # Verify handler was NOT called
        assert self.handler_mock.call_count == 0
    
    def test_on_message_invalid_noise_value(self):
        """Test handling of message with out-of-range noise value."""
        # Create payload with noise > 120 dB (violates validation)
        payload = {
            "sensorId": "sensor_001",
            "locationId": "ward_001",
            "co2": 450.5,
            "noise": 150.0,  # Invalid: must be <= 120
            "temperature": 25.3,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        msg = Mock()
        msg.topic = "sensors/sensor_001/telemetry"
        msg.payload = json.dumps(payload).encode('utf-8')
        
        # Process message - should not crash
        self.consumer._on_message(None, None, msg)
        
        # Verify handler was NOT called
        assert self.handler_mock.call_count == 0
    
    def test_on_message_invalid_temperature_value(self):
        """Test handling of message with out-of-range temperature value."""
        # Create payload with temperature > 60°C (violates validation)
        payload = {
            "sensorId": "sensor_001",
            "locationId": "ward_001",
            "co2": 450.5,
            "noise": 65.2,
            "temperature": 100.0,  # Invalid: must be <= 60
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        msg = Mock()
        msg.topic = "sensors/sensor_001/telemetry"
        msg.payload = json.dumps(payload).encode('utf-8')
        
        # Process message - should not crash
        self.consumer._on_message(None, None, msg)
        
        # Verify handler was NOT called
        assert self.handler_mock.call_count == 0
    
    def test_on_message_no_handler_configured(self):
        """Test processing message when no handler is configured."""
        # Create consumer without handler
        consumer = MQTTConsumer(broker_host="test", broker_port=1883)
        
        payload = {
            "sensorId": "sensor_001",
            "locationId": "ward_001",
            "co2": 450.5,
            "noise": 65.2,
            "temperature": 25.3,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        msg = Mock()
        msg.topic = "sensors/sensor_001/telemetry"
        msg.payload = json.dumps(payload).encode('utf-8')
        
        # Process message - should not crash even without handler
        consumer._on_message(None, None, msg)
    
    def test_set_telemetry_handler(self):
        """Test updating telemetry handler after initialization."""
        new_handler = Mock()
        self.consumer.set_telemetry_handler(new_handler)
        
        assert self.consumer.telemetry_handler == new_handler
        
        # Verify new handler is used
        payload = {
            "sensorId": "sensor_001",
            "locationId": "ward_001",
            "co2": 450.5,
            "noise": 65.2,
            "temperature": 25.3,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        msg = Mock()
        msg.topic = "sensors/sensor_001/telemetry"
        msg.payload = json.dumps(payload).encode('utf-8')
        
        self.consumer._on_message(None, None, msg)
        
        # New handler should be called, old handler should not
        assert new_handler.call_count == 1
        assert self.handler_mock.call_count == 0
    
    def test_on_connect_success(self):
        """Test successful connection callback."""
        client_mock = Mock()
        
        # Simulate successful connection (rc=0)
        self.consumer._on_connect(client_mock, None, None, 0)
        
        # Verify subscription was made
        client_mock.subscribe.assert_called_once_with("sensors/+/telemetry")
        
        # Verify reconnection parameters were reset
        assert self.consumer.reconnect_delay == 1
        assert self.consumer.reconnect_attempts == 0
    
    def test_on_connect_failure(self):
        """Test failed connection callback."""
        client_mock = Mock()
        
        # Simulate failed connection (rc != 0)
        self.consumer._on_connect(client_mock, None, None, 5)
        
        # Verify subscription was NOT made
        client_mock.subscribe.assert_not_called()
    
    def test_on_disconnect_unexpected(self):
        """Test unexpected disconnection callback."""
        client_mock = Mock()
        
        # Mock reconnect method to avoid actual reconnection
        with patch.object(self.consumer, '_reconnect_with_backoff') as reconnect_mock:
            # Simulate unexpected disconnection (rc != 0)
            self.consumer._on_disconnect(client_mock, None, 1)
            
            # Verify reconnection was attempted
            reconnect_mock.assert_called_once()
    
    def test_on_disconnect_expected(self):
        """Test expected disconnection callback."""
        client_mock = Mock()
        
        # Mock reconnect method
        with patch.object(self.consumer, '_reconnect_with_backoff') as reconnect_mock:
            # Simulate expected disconnection (rc = 0)
            self.consumer._on_disconnect(client_mock, None, 0)
            
            # Verify reconnection was NOT attempted
            reconnect_mock.assert_not_called()
    
    def test_reconnect_with_backoff_exponential_delay(self):
        """Test exponential backoff in reconnection logic."""
        # Mock time.sleep and client.reconnect
        with patch('time.sleep') as sleep_mock, \
             patch.object(self.consumer.client, 'reconnect') as reconnect_mock:
            
            # First reconnection attempt
            self.consumer._reconnect_with_backoff()
            sleep_mock.assert_called_with(1)
            assert self.consumer.reconnect_delay == 2
            assert self.consumer.reconnect_attempts == 1
            
            # Second reconnection attempt
            self.consumer._reconnect_with_backoff()
            sleep_mock.assert_called_with(2)
            assert self.consumer.reconnect_delay == 4
            assert self.consumer.reconnect_attempts == 2
            
            # Third reconnection attempt
            self.consumer._reconnect_with_backoff()
            sleep_mock.assert_called_with(4)
            assert self.consumer.reconnect_delay == 8
            assert self.consumer.reconnect_attempts == 3
    
    def test_reconnect_with_backoff_max_delay(self):
        """Test that reconnection delay caps at maximum value."""
        # Set delay close to maximum
        self.consumer.reconnect_delay = 40
        
        with patch('time.sleep') as sleep_mock, \
             patch.object(self.consumer.client, 'reconnect') as reconnect_mock:
            
            # Reconnection attempt should cap at max_reconnect_delay (60)
            self.consumer._reconnect_with_backoff()
            assert self.consumer.reconnect_delay == 60
            
            # Next attempt should stay at max
            self.consumer._reconnect_with_backoff()
            assert self.consumer.reconnect_delay == 60
    
    def test_reconnect_with_backoff_failure(self):
        """Test handling of failed reconnection attempt."""
        with patch('time.sleep') as sleep_mock, \
             patch.object(self.consumer.client, 'reconnect', side_effect=Exception("Connection failed")):
            
            # Should not raise exception
            self.consumer._reconnect_with_backoff()
            
            # Delay should still increase
            assert self.consumer.reconnect_delay == 2
            assert self.consumer.reconnect_attempts == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
