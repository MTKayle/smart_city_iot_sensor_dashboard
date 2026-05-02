"""
Pydantic models for Smart City IoT Dashboard.

This package exports all data models used throughout the application.
"""

from app.models.telemetry import Telemetry, TelemetryData, GeoLocation, DataQuality, TelemetryLegacy
from app.models.sensor import Location, SensorCluster, SensorRegistry, SensorCapability, SensorHealthLog, SensorWithCapabilities, SensorWithLocation
from app.models.alert import Alert, AlertType, AlertSeverity
from app.models.analytics import MovingAverage, Analytics, LeaderboardEntry

# Backward compatibility alias
Sensor = SensorRegistry

__all__ = [
    "Telemetry",
    "TelemetryData",
    "GeoLocation",
    "DataQuality",
    "TelemetryLegacy",
    "Location",
    "SensorCluster",
    "SensorRegistry",
    "SensorCapability",
    "SensorHealthLog",
    "SensorWithCapabilities",
    "SensorWithLocation",
    "Alert",
    "AlertType",
    "AlertSeverity",
    "MovingAverage",
    "Analytics",
    "LeaderboardEntry",
]
