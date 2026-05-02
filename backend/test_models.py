import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.telemetry import Telemetry, TelemetryData, GeoLocation, DataQuality, TelemetryLegacy
from app.models.alert import Alert, AlertType, AlertSeverity
from app.models.sensor import SensorRegistry, SensorCapability, SensorCluster, Location
from pydantic import ValidationError

def test_telemetry():
    print("--- Testing Telemetry Models ---")
    # Valid
    t = Telemetry(
        sensorId="s1",
        locationId="l1",
        data=TelemetryData(co2=400, temperature=25),
        location=GeoLocation(coordinates=[106.7, 10.7])
    )
    print("Valid Telemetry:", t.dict())

    # Invalid coordinates
    try:
        GeoLocation(coordinates=[200, 10])
        print("FAIL: Expected validation error for coordinates")
    except ValidationError as e:
        print("PASS: GeoLocation validation caught invalid longitude")

    # Invalid metric
    try:
        TelemetryData(co2=6000)
        print("FAIL: Expected validation error for co2")
    except ValidationError as e:
        print("PASS: TelemetryData validation caught invalid co2")

    # Legacy conversion
    legacy = TelemetryLegacy(sensorId="s1", locationId="l1", co2=450, noise=60, temperature=25, timestamp="2026-05-02T10:00:00Z")
    enhanced = legacy.to_enhanced(latitude=10.7, longitude=106.7)
    print("Legacy conversion successful:", enhanced.location.coordinates == [106.7, 10.7])

def test_alert():
    print("\n--- Testing Alert Models ---")
    a = Alert(
        alertId="a1",
        locationId="l1",
        alertType=AlertType.PREDICTIVE,
        metricType="CO2",
        value=1500,
        predictedValue=1600,
        confidenceScore=0.85,
        severity=AlertSeverity.CRITICAL
    )
    print("Valid Alert:", a.dict())

def test_sensor():
    print("\n--- Testing Sensor Models ---")
    s = SensorRegistry(
        SensorID="s1",
        LocationID="l1",
        Latitude=10.7,
        Longitude=106.7,
        InstallDate="2025-01-01"
    )
    print("Valid Sensor:", s.dict(by_alias=True))
    
    try:
        SensorRegistry(
            SensorID="s1",
            LocationID="l1",
            Latitude=100.0,
            Longitude=106.7,
            InstallDate="2025-01-01"
        )
        print("FAIL: Expected validation error for Latitude")
    except ValidationError as e:
        print("PASS: Sensor validation caught invalid Latitude")

if __name__ == "__main__":
    test_telemetry()
    test_alert()
    test_sensor()
    print("\nAll model tests complete!")
