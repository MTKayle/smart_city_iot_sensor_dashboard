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
        assert "data" in telemetry
        assert "location" in telemetry
        assert "quality" in telemetry
        assert "timestamp" in telemetry
        
        # Verify nested data fields
        data = telemetry["data"]
        assert "co2" in data
        assert "noise" in data
        assert "temperature" in data
        assert "pm25" in data
        assert "humidity" in data
        
        # Verify quality fields
        assert "batteryLevel" in telemetry["quality"]
        assert "signalStrength" in telemetry["quality"]
        
        # Verify field types
        assert isinstance(telemetry["sensorId"], str)
        assert isinstance(telemetry["locationId"], str)
        assert isinstance(data["co2"], (int, float))
        assert isinstance(data["noise"], (int, float))
        assert isinstance(data["temperature"], (int, float))
        assert isinstance(data["pm25"], (int, float))
        assert isinstance(telemetry["timestamp"], str)
    
    def test_generate_telemetry_value_ranges(self):
        """
        Generated telemetry must stay inside the simulator's physical clamps.

        The simulator can drive metrics into the CRITICAL alert band during a
        typed anomaly event (TRAFFIC_JAM, INDUSTRIAL_FIRE, EQUIPMENT_MALFUNCTION,
        STORM_INCOMING, HEAT_WAVE, CO2_TREND), so the assertions match the
        widened clamps in `step_state` rather than a "normal-day" range.
        """
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=["sensor_001"]
        )

        for _ in range(100):
            telemetry = simulator.generate_telemetry("sensor_001")
            data = telemetry["data"]
            quality = telemetry["quality"]

            # Physical clamps from simulator.step_state
            assert 250 <= data["co2"] <= 3000, f"CO2 {data['co2']} out of range"
            assert 30 <= data["noise"] <= 125, f"Noise {data['noise']} out of range"
            assert 15 <= data["temperature"] <= 42, f"Temperature {data['temperature']} out of range"
            assert 5 <= data["pm25"] <= 300, f"PM2.5 {data['pm25']} out of range"
            assert 20 <= data["humidity"] <= 99, f"Humidity {data['humidity']} out of range"

            # Quality clamps
            assert 0 <= quality["batteryLevel"] <= 100, f"Battery {quality['batteryLevel']} out of range"
            assert -90 <= quality["signalStrength"] <= -30, f"Signal {quality['signalStrength']} out of range"
    
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
        assert parsed["data"]["co2"] == telemetry["data"]["co2"]
    
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
        sensor_ids = ["sen_q1_ben_nghe_01", "sen_q1_ben_nghe_02"]
        simulator = SensorSimulator(
            broker_host="localhost",
            broker_port=1883,
            sensor_ids=sensor_ids
        )
        
        # Generate telemetry for each sensor
        for sensor_id in sensor_ids:
            telemetry = simulator.generate_telemetry(sensor_id)
            assert telemetry["sensorId"] == sensor_id
            assert telemetry["locationId"] == "ward_q1_ben_nghe"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
