from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

class TelemetryData(BaseModel):
    """Combo sensor data (multiple metrics)"""
    co2: Optional[float] = Field(None, ge=0, le=5000, description="CO2 in ppm")
    noise: Optional[float] = Field(None, ge=0, le=120, description="Noise in dB")
    temperature: Optional[float] = Field(None, ge=-50, le=60, description="Temperature in °C")
    pm25: Optional[float] = Field(None, ge=0, le=500, description="PM2.5 in μg/m³")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity in %")

class GeoLocation(BaseModel):
    """GeoJSON Point for geospatial queries"""
    type: str = "Point"
    coordinates: list[float]  # [longitude, latitude]
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if len(v) != 2:
            raise ValueError('Coordinates must be [longitude, latitude]')
        lng, lat = v
        if not -180 <= lng <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        if not -90 <= lat <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

class DataQuality(BaseModel):
    """Device health and data quality metrics"""
    batteryLevel: Optional[float] = Field(None, ge=0, le=100, description="Battery level in %")
    signalStrength: Optional[float] = Field(None, description="Signal strength in dBm")

class Telemetry(BaseModel):
    """
    Enhanced telemetry document model for MongoDB.
    
    Supports:
    - Multi-metric combo sensors (CO2, Noise, Temperature, PM2.5, Humidity)
    - Geolocation for spatial queries
    - Clustering for hotspot detection
    - Device health monitoring
    - TTL for automatic data expiration
    """
    sensorId: str = Field(..., min_length=1, description="Unique sensor identifier")
    locationId: str = Field(..., min_length=1, description="Location identifier (ward)")
    clusterId: Optional[str] = Field(None, description="Cluster identifier for spatial analysis")
    
    data: TelemetryData = Field(..., description="Sensor measurements")
    location: GeoLocation = Field(..., description="GeoJSON point for spatial queries")
    quality: Optional[DataQuality] = Field(None, description="Device health metrics")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Sensor reading time")
    receivedAt: datetime = Field(default_factory=datetime.utcnow, description="Server receive time")
    expireAt: Optional[datetime] = Field(None, description="TTL expiration (30 days)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensorId": "sen_q1_ben_nghe_01",
                "locationId": "ward_q1_ben_nghe",
                "clusterId": "cluster_q1_north",
                "data": {
                    "co2": 450.5,
                    "noise": 65.2,
                    "temperature": 25.3,
                    "pm25": 35.8,
                    "humidity": 68.5
                },
                "location": {
                    "type": "Point",
                    "coordinates": [106.7019, 10.7756]
                },
                "quality": {
                    "batteryLevel": 87.5,
                    "signalStrength": -45.2
                },
                "timestamp": "2026-05-02T10:30:00Z",
                "receivedAt": "2026-05-02T10:30:01Z"
            }
        }

# Backward compatibility: Legacy flat telemetry model
class TelemetryLegacy(BaseModel):
    """Legacy telemetry model for backward compatibility"""
    sensorId: str
    locationId: str
    co2: float
    noise: float
    temperature: float
    timestamp: datetime
    
    def to_enhanced(self, latitude: float, longitude: float, clusterId: Optional[str] = None) -> Telemetry:
        """Convert legacy model to enhanced model"""
        return Telemetry(
            sensorId=self.sensorId,
            locationId=self.locationId,
            clusterId=clusterId,
            data=TelemetryData(
                co2=self.co2,
                noise=self.noise,
                temperature=self.temperature
            ),
            location=GeoLocation(
                type="Point",
                coordinates=[longitude, latitude]
            ),
            timestamp=self.timestamp,
            receivedAt=datetime.utcnow()
        )