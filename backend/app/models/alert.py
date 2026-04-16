"""
Alert data models for Smart City IoT Dashboard.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class Alert(BaseModel):
    """
    Alert data model representing threshold violations.
    
    Alerts are generated when:
    - CO2 > 1000 ppm (HIGH)
    - Noise > 85 dB (HIGH)
    """
    alertId: str = Field(..., description="Unique alert identifier")
    sensorId: str = Field(..., description="Sensor that triggered the alert")
    metricType: Literal["CO2", "Noise", "Temperature"] = Field(..., description="Metric that exceeded threshold")
    value: float = Field(..., description="Measured value that triggered the alert")
    level: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Alert severity level")
    createdAt: datetime = Field(..., description="Timestamp when alert was created")
    
    class Config:
        json_schema_extra = {
            "example": {
                "alertId": "alert_001",
                "sensorId": "sensor_001",
                "metricType": "CO2",
                "value": 1250.0,
                "level": "HIGH",
                "createdAt": "2024-01-15T10:30:05Z"
            }
        }
