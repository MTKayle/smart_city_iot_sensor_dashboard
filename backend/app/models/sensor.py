"""
Sensor models for the redesigned database schema.
Includes Location, SensorCluster, SensorRegistry, and SensorCapability.
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class Location(BaseModel):
    """Location model (City/District/Ward hierarchy)"""
    locationId: str = Field(..., alias="LocationID")
    name: str = Field(..., alias="Name")
    parentId: Optional[str] = Field(None, alias="ParentID")
    type: str = Field(..., alias="Type")  # City, District, Ward
    
    centerLat: Optional[float] = Field(None, alias="CenterLat")
    centerLng: Optional[float] = Field(None, alias="CenterLng")
    geometry: Optional[str] = Field(None, alias="Geometry")  # GeoJSON
    area: Optional[float] = Field(None, alias="Area")  # km²
    population: Optional[int] = Field(None, alias="Population")
    
    createdAt: Optional[datetime] = Field(None, alias="CreatedAt")
    updatedAt: Optional[datetime] = Field(None, alias="UpdatedAt")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "locationId": "ward_q1_01",
                "name": "Ward 1",
                "parentId": "district_q1",
                "type": "Ward",
                "centerLat": 10.7756,
                "centerLng": 106.7019,
                "area": 0.89,
                "population": 18500
            }
        }


class SensorCluster(BaseModel):
    """Sensor cluster for spatial analysis"""
    clusterId: str = Field(..., alias="ClusterID")
    locationId: str = Field(..., alias="LocationID")
    
    clusterName: Optional[str] = Field(None, alias="ClusterName")
    centerLat: float = Field(..., alias="CenterLat")
    centerLng: float = Field(..., alias="CenterLng")
    radius: float = Field(..., alias="Radius")  # meters
    
    sensorCount: int = Field(0, alias="SensorCount")
    algorithm: Optional[str] = Field(None, alias="Algorithm")  # GRID, DBSCAN, KMEANS
    
    createdAt: Optional[datetime] = Field(None, alias="CreatedAt")
    updatedAt: Optional[datetime] = Field(None, alias="UpdatedAt")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "clusterId": "cluster_q1_north",
                "locationId": "district_q1",
                "clusterName": "District 1 North Cluster",
                "centerLat": 10.7780,
                "centerLng": 106.7030,
                "radius": 300,
                "sensorCount": 5,
                "algorithm": "GRID"
            }
        }


class SensorRegistry(BaseModel):
    """Enhanced sensor registry with geolocation"""
    sensorId: str = Field(..., alias="SensorID")
    locationId: str = Field(..., alias="LocationID")
    clusterId: Optional[str] = Field(None, alias="ClusterID")
    
    latitude: float = Field(..., alias="Latitude")
    longitude: float = Field(..., alias="Longitude")
    altitude: Optional[float] = Field(None, alias="Altitude")
    
    sensorModel: Optional[str] = Field(None, alias="SensorModel")
    firmwareVersion: Optional[str] = Field(None, alias="FirmwareVersion")
    
    status: str = Field("Active", alias="Status")  # Active, Offline, Maintenance, Decommissioned
    
    installDate: date = Field(..., alias="InstallDate")
    lastMaintenance: Optional[date] = Field(None, alias="LastMaintenance")
    nextMaintenance: Optional[date] = Field(None, alias="NextMaintenance")
    
    registeredAt: Optional[datetime] = Field(None, alias="RegisteredAt")
    updatedAt: Optional[datetime] = Field(None, alias="UpdatedAt")
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "sensorId": "sen_q1_ben_nghe_01",
                "locationId": "ward_q1_ben_nghe",
                "clusterId": "cluster_q1_north",
                "latitude": 10.7756,
                "longitude": 106.7019,
                "altitude": 5.0,
                "sensorModel": "EnviroSense Pro X1",
                "firmwareVersion": "v2.3.1",
                "status": "Active",
                "installDate": "2025-01-15"
            }
        }


class SensorCapability(BaseModel):
    """Sensor capability (what metrics it can measure)"""
    capabilityId: str = Field(..., alias="CapabilityID")
    sensorId: str = Field(..., alias="SensorID")
    
    metricType: str = Field(..., alias="MetricType")  # CO2, Noise, Temperature, PM2.5, Humidity
    unit: str = Field(..., alias="Unit")  # ppm, dB, °C, μg/m³, %
    
    minRange: Optional[float] = Field(None, alias="MinRange")
    maxRange: Optional[float] = Field(None, alias="MaxRange")
    accuracy: Optional[float] = Field(None, alias="Accuracy")  # percentage
    
    calibrationDate: Optional[date] = Field(None, alias="CalibrationDate")
    nextCalibration: Optional[date] = Field(None, alias="NextCalibration")
    
    isActive: bool = Field(True, alias="IsActive")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "capabilityId": "cap_001",
                "sensorId": "sen_q1_ben_nghe_01",
                "metricType": "CO2",
                "unit": "ppm",
                "minRange": 0,
                "maxRange": 5000,
                "accuracy": 2.0,
                "isActive": True
            }
        }


class SensorHealthLog(BaseModel):
    """Sensor health monitoring log"""
    logId: str = Field(..., alias="LogID")
    sensorId: str = Field(..., alias="SensorID")
    timestamp: datetime = Field(..., alias="Timestamp")
    
    status: Optional[str] = Field(None, alias="Status")  # HEALTHY, DEGRADED, OFFLINE, ERROR
    batteryLevel: Optional[float] = Field(None, alias="BatteryLevel")  # percentage
    signalStrength: Optional[float] = Field(None, alias="SignalStrength")  # dBm
    dataCompleteness: Optional[float] = Field(None, alias="DataCompleteness")  # percentage
    lastReadingAt: Optional[datetime] = Field(None, alias="LastReadingAt")
    
    errorCode: Optional[str] = Field(None, alias="ErrorCode")
    errorMessage: Optional[str] = Field(None, alias="ErrorMessage")
    metadata: Optional[str] = Field(None, alias="Metadata")  # JSON
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "logId": "log_001",
                "sensorId": "sen_q1_ben_nghe_01",
                "timestamp": "2026-05-02T10:30:00Z",
                "status": "HEALTHY",
                "batteryLevel": 87.5,
                "signalStrength": -45.2,
                "dataCompleteness": 98.5
            }
        }


class SensorWithCapabilities(SensorRegistry):
    """Sensor with its capabilities"""
    capabilities: List[SensorCapability] = []
    
    class Config:
        populate_by_name = True


class SensorWithLocation(SensorRegistry):
    """Sensor with location details"""
    location: Optional[Location] = None
    cluster: Optional[SensorCluster] = None
    
    class Config:
        populate_by_name = True
