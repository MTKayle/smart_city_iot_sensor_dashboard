from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional
from enum import Enum

class AlertType(str, Enum):
    THRESHOLD = "THRESHOLD"
    PREDICTIVE = "PREDICTIVE"
    ANOMALY = "ANOMALY"
    CLUSTER = "CLUSTER"

class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Alert(BaseModel):
    """
    Alert data model for MongoDB and Oracle.
    """
    alertId: str = Field(..., description="Unique alert identifier")
    sensorId: Optional[str] = Field(None, description="Sensor that triggered the alert")
    clusterId: Optional[str] = Field(None, description="Cluster that triggered the alert")
    locationId: str = Field(..., description="Location of the alert")
    
    alertType: AlertType = Field(..., description="Type of alert")
    metricType: str = Field(..., description="Metric that triggered the alert (e.g. CO2, Noise)")
    
    value: float = Field(..., description="Measured value that triggered the alert")
    threshold: Optional[float] = Field(None, description="Threshold that was violated")
    predictedValue: Optional[float] = Field(None, description="Predicted value for PREDICTIVE alerts")
    confidenceScore: Optional[float] = Field(None, ge=0, le=1, description="Confidence score for ML models")
    
    severity: AlertSeverity = Field(..., description="Alert severity level")
    status: str = Field("OPEN", description="Status of the alert (OPEN, ACKNOWLEDGED, RESOLVED)")
    
    message: Optional[str] = Field(None, description="Human readable alert message")
    
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when alert was created")
    acknowledgedAt: Optional[datetime] = Field(None, description="Timestamp when alert was acknowledged")
    resolvedAt: Optional[datetime] = Field(None, description="Timestamp when alert was resolved")
    
    class Config:
        json_schema_extra = {
            "example": {
                "alertId": "alert_001",
                "sensorId": "sen_q1_ben_nghe_01",
                "locationId": "ward_q1_ben_nghe",
                "alertType": "THRESHOLD",
                "metricType": "CO2",
                "value": 1250.0,
                "threshold": 1000.0,
                "severity": "HIGH",
                "createdAt": "2026-05-02T10:30:05Z"
            }
        }
