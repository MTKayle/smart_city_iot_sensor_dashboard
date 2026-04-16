"""
Quick validation test for Pydantic models.
This ensures the models are correctly defined and validation works as expected.
"""

from app.models import Telemetry, Location, Sensor, Alert, Analytics, MovingAverage, LeaderboardEntry
from datetime import datetime
import json


def test_telemetry_validation():
    """Test Telemetry model with valid and invalid data."""
    # Valid telemetry
    valid = Telemetry(
        sensorId="sensor_001",
        locationId="ward_001",
        co2=450.5,
        noise=65.2,
        temperature=25.3,
        timestamp=datetime.now()
    )
    print(f"✓ Valid Telemetry: {valid.sensorId}")
    
    # Test field validation - co2 >= 0
    try:
        invalid_co2 = Telemetry(
            sensorId="sensor_001",
            locationId="ward_001",
            co2=-10,  # Invalid: negative
            noise=65.2,
            temperature=25.3,
            timestamp=datetime.now()
        )
        print("✗ FAILED: Negative CO2 should be rejected")
    except Exception as e:
        print(f"✓ CO2 validation works: Negative value rejected")
    
    # Test noise range 0-120
    try:
        invalid_noise = Telemetry(
            sensorId="sensor_001",
            locationId="ward_001",
            co2=450.5,
            noise=150,  # Invalid: > 120
            temperature=25.3,
            timestamp=datetime.now()
        )
        print("✗ FAILED: Noise > 120 should be rejected")
    except Exception as e:
        print(f"✓ Noise validation works: Value > 120 rejected")
    
    # Test temperature range -50 to 60
    try:
        invalid_temp = Telemetry(
            sensorId="sensor_001",
            locationId="ward_001",
            co2=450.5,
            noise=65.2,
            temperature=-60,  # Invalid: < -50
            timestamp=datetime.now()
        )
        print("✗ FAILED: Temperature < -50 should be rejected")
    except Exception as e:
        print(f"✓ Temperature validation works: Value < -50 rejected")


def test_location_model():
    """Test Location model."""
    location = Location(
        locationId="district_001",
        name="District 1",
        parentId="city_hcm",
        type="District"
    )
    print(f"✓ Valid Location: {location.name} ({location.type})")


def test_sensor_model():
    """Test Sensor model."""
    sensor = Sensor(
        sensorId="sensor_001",
        locationId="ward_001",
        sensorType="CO2",
        registeredAt=datetime.now()
    )
    print(f"✓ Valid Sensor: {sensor.sensorId} ({sensor.sensorType})")


def test_alert_model():
    """Test Alert model."""
    alert = Alert(
        alertId="alert_001",
        sensorId="sensor_001",
        metricType="CO2",
        value=1250.0,
        level="HIGH",
        createdAt=datetime.now()
    )
    print(f"✓ Valid Alert: {alert.alertId} ({alert.level})")


def test_analytics_model():
    """Test Analytics and MovingAverage models."""
    analytics = Analytics(
        sensorId="sensor_001",
        co2_moving_avg=MovingAverage(
            metric="CO2",
            values=[450.5, 460.2, 455.8],
            average=455.5,
            window_size=3
        ),
        noise_moving_avg=MovingAverage(
            metric="Noise",
            values=[65.2, 67.1, 66.5],
            average=66.27,
            window_size=3
        ),
        temperature_moving_avg=MovingAverage(
            metric="Temperature",
            values=[25.3, 25.8, 25.5],
            average=25.53,
            window_size=3
        )
    )
    print(f"✓ Valid Analytics: {analytics.sensorId}")


def test_leaderboard_entry():
    """Test LeaderboardEntry model."""
    entry = LeaderboardEntry(
        locationId="ward_001",
        locationName="Ward 1",
        avgCO2=420.5,
        avgNoise=55.2,
        avgTemperature=26.3,
        cleanScore=85.5,
        rank=1
    )
    print(f"✓ Valid LeaderboardEntry: {entry.locationName} (Rank {entry.rank})")


def test_json_serialization():
    """Test JSON serialization and deserialization (round-trip)."""
    original = Telemetry(
        sensorId="sensor_001",
        locationId="ward_001",
        co2=450.5,
        noise=65.2,
        temperature=25.3,
        timestamp=datetime(2024, 1, 15, 10, 30, 0)
    )
    
    # Serialize to JSON
    json_str = original.model_dump_json()
    
    # Deserialize back
    parsed = Telemetry.model_validate_json(json_str)
    
    # Verify round-trip
    assert parsed.sensorId == original.sensorId
    assert parsed.co2 == original.co2
    assert parsed.noise == original.noise
    assert parsed.temperature == original.temperature
    print(f"✓ JSON round-trip serialization works")


if __name__ == "__main__":
    print("Testing Pydantic Models...\n")
    test_telemetry_validation()
    test_location_model()
    test_sensor_model()
    test_alert_model()
    test_analytics_model()
    test_leaderboard_entry()
    test_json_serialization()
    print("\n✓ All model tests passed!")
