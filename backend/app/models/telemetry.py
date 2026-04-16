"""
Telemetry data models for Smart City IoT Dashboard.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class Telemetry(BaseModel):
    """
    Telemetry data model representing sensor measurements.
    
    Validates:
    - co2: Non-negative values (>= 0)
    - noise: Values between 0-120 dB
    - temperature: Values between -50°C and 60°C
    """
    sensorId: str = Field(..., min_length=1, description="Unique sensor identifier")
    locationId: str = Field(..., min_length=1, description="Location identifier where sensor is deployed")
    co2: float = Field(..., ge=0, le=5000, description="CO2 concentration in ppm (parts per million)")
    noise: float = Field(..., ge=0, le=120, description="Noise level in decibels (dB)")
    temperature: float = Field(..., ge=-50, le=60, description="Temperature in degrees Celsius")
    timestamp: datetime = Field(..., description="Timestamp of the measurement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensorId": "sensor_001",
                "locationId": "ward_001",
                "co2": 450.5,
                "noise": 65.2,
                "temperature": 25.3,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
