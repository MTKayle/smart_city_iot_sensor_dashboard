"""
Analytics data models for Smart City IoT Dashboard.

Extended in Task 7.2 to include PM2.5, Humidity, AQI, and
updated Clean Score (now weighted across 4 metrics).

Extended in Task 7.3 to include ClusterAnalytics for cluster-level aggregation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class MovingAverage(BaseModel):
    """
    Moving average data model for a single metric.

    Calculates the average of the last N readings (N = min(10, total_readings)).
    """
    metric: str = Field(..., description="Metric name (CO2, Noise, Temperature, PM25, Humidity)")
    values: List[float] = Field(..., description="List of values used in calculation")
    average: float = Field(..., description="Calculated moving average")
    window_size: int = Field(..., description="Number of readings used (max 10)")

    class Config:
        json_schema_extra = {
            "example": {
                "metric": "CO2",
                "values": [450.5, 460.2, 455.8, 470.1, 465.3, 458.9, 462.4, 467.2, 461.5, 459.7],
                "average": 461.16,
                "window_size": 10
            }
        }


class Analytics(BaseModel):
    """
    Analytics data model containing moving averages for all 5 metrics
    plus AQI derived from PM2.5.

    Task 7.2: added pm25_moving_avg, humidity_moving_avg, aqi.
    """
    sensorId: str = Field(..., description="Sensor identifier")
    co2_moving_avg: MovingAverage = Field(..., description="CO2 moving average data")
    noise_moving_avg: MovingAverage = Field(..., description="Noise moving average data")
    temperature_moving_avg: MovingAverage = Field(..., description="Temperature moving average data")
    # New in Task 7.2
    pm25_moving_avg: Optional[MovingAverage] = Field(None, description="PM2.5 moving average data")
    humidity_moving_avg: Optional[MovingAverage] = Field(None, description="Humidity moving average data")
    aqi: Optional[int] = Field(None, description="Air Quality Index derived from PM2.5 average")
    aqi_category: Optional[str] = Field(None, description="AQI category label (e.g. 'Moderate')")

    class Config:
        json_schema_extra = {
            "example": {
                "sensorId": "sensor_001",
                "co2_moving_avg": {"metric": "CO2", "values": [450.5, 460.2], "average": 455.35, "window_size": 2},
                "noise_moving_avg": {"metric": "Noise", "values": [65.2, 67.1], "average": 66.15, "window_size": 2},
                "temperature_moving_avg": {"metric": "Temperature", "values": [25.3, 25.8], "average": 25.55, "window_size": 2},
                "pm25_moving_avg": {"metric": "PM25", "values": [20.0, 22.5], "average": 21.25, "window_size": 2},
                "humidity_moving_avg": {"metric": "Humidity", "values": [70.0, 72.0], "average": 71.0, "window_size": 2},
                "aqi": 71,
                "aqi_category": "Moderate"
            }
        }


class LeaderboardEntry(BaseModel):
    """
    Leaderboard entry data model for location environmental quality ranking.

    Updated Clean Score in Task 7.2 now incorporates PM2.5 (40 % weight)
    alongside CO2 (30 %) and Noise (30 %) for a more comprehensive score.

    cleanScore = 100 - (
        normalized_CO2   * 0.30 +
        normalized_Noise * 0.30 +
        normalized_PM25  * 0.40
    )
    """
    locationId: str = Field(..., description="Location identifier")
    locationName: str = Field(..., description="Human-readable location name")
    avgCO2: float = Field(..., description="Average CO2 level in ppm")
    avgNoise: float = Field(..., description="Average noise level in dB")
    avgTemperature: float = Field(..., description="Average temperature in °C")
    avgPM25: Optional[float] = Field(None, description="Average PM2.5 in µg/m³")
    avgHumidity: Optional[float] = Field(None, description="Average humidity in %")
    aqi: Optional[int] = Field(None, description="Air Quality Index derived from PM2.5")
    aqi_category: Optional[str] = Field(None, description="AQI category label")
    cleanScore: float = Field(..., description="Calculated environmental quality score (0-100)")
    rank: int = Field(..., description="Ranking position (1 = best)")

    class Config:
        json_schema_extra = {
            "example": {
                "locationId": "ward_001",
                "locationName": "Ward 1",
                "avgCO2": 420.5,
                "avgNoise": 55.2,
                "avgTemperature": 26.3,
                "avgPM25": 18.4,
                "avgHumidity": 72.0,
                "aqi": 64,
                "aqi_category": "Moderate",
                "cleanScore": 85.5,
                "rank": 1
            }
        }


class ClusterAnalytics(BaseModel):
    """
    Cluster-level aggregated analytics model.

    Task 7.3: Aggregates telemetry across all sensors in a spatial cluster.
    """
    clusterId: str = Field(..., description="Cluster identifier")
    clusterName: Optional[str] = Field(None, description="Human-readable cluster name")
    locationId: Optional[str] = Field(None, description="Parent location of the cluster")
    sensorCount: int = Field(..., description="Number of sensors contributing data")
    readingCount: int = Field(..., description="Total telemetry readings aggregated")
    avgCO2: Optional[float] = Field(None, description="Cluster-wide average CO2 (ppm)")
    avgNoise: Optional[float] = Field(None, description="Cluster-wide average noise (dB)")
    avgTemperature: Optional[float] = Field(None, description="Cluster-wide average temperature (°C)")
    avgPM25: Optional[float] = Field(None, description="Cluster-wide average PM2.5 (µg/m³)")
    avgHumidity: Optional[float] = Field(None, description="Cluster-wide average humidity (%)")
    aqi: Optional[int] = Field(None, description="Cluster AQI derived from avgPM25")
    aqi_category: Optional[str] = Field(None, description="Cluster AQI category label")
    cleanScore: Optional[float] = Field(None, description="Cluster environmental quality score (0–100)")

    class Config:
        json_schema_extra = {
            "example": {
                "clusterId": "cluster_q1",
                "clusterName": "District 1 Cluster",
                "locationId": "district_q1",
                "sensorCount": 4,
                "readingCount": 240,
                "avgCO2": 510.3,
                "avgNoise": 72.1,
                "avgTemperature": 28.4,
                "avgPM25": 38.7,
                "avgHumidity": 76.2,
                "aqi": 108,
                "aqi_category": "Unhealthy for Sensitive Groups",
                "cleanScore": 63.4
            }
        }
