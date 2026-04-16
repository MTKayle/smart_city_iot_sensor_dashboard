"""
Sensor and Location data models for Smart City IoT Dashboard.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


class Location(BaseModel):
    """
    Location data model representing geographic hierarchy.
    
    Supports three-level hierarchy: City > District > Ward
    """
    locationId: str = Field(..., description="Unique location identifier")
    name: str = Field(..., description="Human-readable location name")
    parentId: Optional[str] = Field(None, description="Parent location ID (NULL for root locations)")
    type: Literal["City", "District", "Ward"] = Field(..., description="Location type in hierarchy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "locationId": "district_001",
                "name": "District 1",
                "parentId": "city_hcm",
                "type": "District"
            }
        }


class Sensor(BaseModel):
    """
    Sensor registry data model representing IoT device registration.
    """
    sensorId: str = Field(..., description="Unique sensor identifier")
    locationId: str = Field(..., description="Location ID where sensor is deployed (must be Ward-level)")
    sensorType: Literal["CO2", "Noise", "Temperature"] = Field(..., description="Type of sensor")
    registeredAt: datetime = Field(..., description="Timestamp when sensor was registered")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensorId": "sensor_001",
                "locationId": "ward_001",
                "sensorType": "CO2",
                "registeredAt": "2024-01-01T00:00:00Z"
            }
        }
