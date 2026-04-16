"""
Unit tests for IoT Simulator

Tests core functionality of the sensor simulator including:
- Telemetry data generation
- Data validation
- MQTT message formatting
"""

import json
import pytest
from datetime import datetime
from simulator import SensorSimulator


class TestSensorSimulator:
    """Test suite for SensorSimulator class."""
    
    def test_initialization(self):
        """Test simulator initialization with valid parameters."""
        sensor_ids = ["sensor_001", "sensor_002"]
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=sensor_ids,
            publish_interval=5
        )
        
        assert simulator.broker_host == "localhost"
        assert simulator.broker_port == 1883
        assert simulator.sensor_ids == sensor_ids
        assert simulator.publish_interval == 5
        assert simulator.connected is False
    
    def test_sensor_location_mapping(self):
        """Test that sensors are mapped to locations correctly."""
        sensor_ids = ["sensor_001", "sensor_002", "sensor_003"]
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=sensor_ids
        )
        
        # Verify all sensors have location mappings
        for sensor_id in sensor_ids:
            assert sensor_id in simulator.sensor_locations
            assert simulator.sensor_locations[sensor_id].startswith("ward_")
    
    def test_generate_telemetry_structure(self):
        """Test that generated telemetry has correct structure."""
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=["sensor_001"]
        )
        
        telemetry = simulator.generate_telemetry("sensor_001")
        
        # Verify all required fields are present
        assert "sensorId" in telemetry
        assert "locationId" in telemetry
        assert "co2" in telemetry
        assert "noise" in telemetry
        assert "temperature" in telemetry
        assert "timestamp" in telemetry
        
        # Verify field types
        assert isinstance(telemetry["sensorId"], str)
        assert isinstance(telemetry["locationId"], str)
        assert isinstance(telemetry["co2"], (int, float))
        assert isinstance(telemetry["noise"], (int, float))
        assert isinstance(telemetry["temperature"], (int, float))
        assert isinstance(telemetry["timestamp"], str)
    
    def test_generate_telemetry_value_ranges(self):
        """Test that generated telemetry values are within expected ranges."""
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=["sensor_001"]
        )
        
        # Generate multiple samples to test ranges
        for _ in range(100):
            telemetry = simulator.generate_telemetry("sensor_001")
            
            # Verify CO2 range (300-2000 ppm)
            assert 300 <= telemetry["co2"] <= 2000, f"CO2 {telemetry['co2']} out of range"
            
            # Verify Noise range (30-100 dB)
            assert 30 <= telemetry["noise"] <= 100, f"Noise {telemetry['noise']} out of range"
            
            # Verify Temperature range (15-35°C)
            assert 15 <= telemetry["temperature"] <= 35, f"Temperature {telemetry['temperature']} out of range"
    
    def test_generate_telemetry_sensor_id(self):
        """Test that generated telemetry contains correct sensor ID."""
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=["sensor_001", "sensor_002"]
        )
        
        telemetry1 = simulator.generate_telemetry("sensor_001")
        assert telemetry1["sensorId"] == "sensor_001"
        
        telemetry2 = simulator.generate_telemetry("sensor_002")
        assert telemetry2["sensorId"] == "sensor_002"
    
    def test_generate_telemetry_timestamp_format(self):
        """Test that timestamp is in ISO 8601 format with UTC timezone."""
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=["sensor_001"]
        )
        
        telemetry = simulator.generate_telemetry("sensor_001")
        timestamp = telemetry["timestamp"]
        
        # Verify timestamp ends with 'Z' (UTC indicator)
        assert timestamp.endswith("Z"), "Timestamp should end with 'Z' for UTC"
        
        # Verify timestamp can be parsed as ISO 8601
        try:
            # Remove 'Z' and parse
            datetime.fromisoformat(timestamp[:-1])
        except ValueError:
            pytest.fail("Timestamp is not valid ISO 8601 format")
    
    def test_telemetry_json_serialization(self):
        """Test that telemetry can be serialized to JSON."""
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=["sensor_001"]
        )
        
        telemetry = simulator.generate_telemetry("sensor_001")
        
        # Should not raise exception
        json_str = json.dumps(telemetry)
        assert isinstance(json_str, str)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["sensorId"] == telemetry["sensorId"]
        assert parsed["co2"] == telemetry["co2"]
    
    def test_retry_delay_initialization(self):
        """Test that retry delay is initialized correctly."""
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=["sensor_001"]
        )
        
        assert simulator.retry_delay == 1
        assert simulator.max_retry_delay == 60
    
    def test_multiple_sensors(self):
        """Test simulator with multiple sensors."""
        sensor_ids = ["sensor_001", "sensor_002", "sensor_003", "sensor_004", "sensor_005"]
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=sensor_ids
        )
        
        # Generate telemetry for each sensor
        for sensor_id in sensor_ids:
            telemetry = simulator.generate_telemetry(sensor_id)
            assert telemetry["sensorId"] == sensor_id
            assert telemetry["locationId"] in [f"ward_{i:03d}" for i in range(1, 6)]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
