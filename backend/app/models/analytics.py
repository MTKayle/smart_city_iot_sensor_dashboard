"""
Analytics data models for Smart City IoT Dashboard.
"""

from pydantic import BaseModel, Field
from typing import List


class MovingAverage(BaseModel):
    """
    Moving average data model for a single metric.
    
    Calculates the average of the last N readings (where N = min(10, total_readings)).
    """
    metric: str = Field(..., description="Metric name (CO2, Noise, or Temperature)")
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
    Analytics data model containing moving averages for all metrics.
    """
    sensorId: str = Field(..., description="Sensor identifier")
    co2_moving_avg: MovingAverage = Field(..., description="CO2 moving average data")
    noise_moving_avg: MovingAverage = Field(..., description="Noise moving average data")
    temperature_moving_avg: MovingAverage = Field(..., description="Temperature moving average data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensorId": "sensor_001",
                "co2_moving_avg": {
                    "metric": "CO2",
                    "values": [450.5, 460.2, 455.8],
                    "average": 455.5,
                    "window_size": 3
                },
                "noise_moving_avg": {
                    "metric": "Noise",
                    "values": [65.2, 67.1, 66.5],
                    "average": 66.27,
                    "window_size": 3
                },
                "temperature_moving_avg": {
                    "metric": "Temperature",
                    "values": [25.3, 25.8, 25.5],
                    "average": 25.53,
                    "window_size": 3
                }
            }
        }


class LeaderboardEntry(BaseModel):
    """
    Leaderboard entry data model for location environmental quality ranking.
    
    Clean Score calculation:
    - normalized_CO2 = (avgCO2 / 2000) * 100
    - normalized_Noise = (avgNoise / 100) * 100
    - cleanScore = 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)
    """
    locationId: str = Field(..., description="Location identifier")
    locationName: str = Field(..., description="Human-readable location name")
    avgCO2: float = Field(..., description="Average CO2 level in ppm")
    avgNoise: float = Field(..., description="Average noise level in dB")
    avgTemperature: float = Field(..., description="Average temperature in °C")
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
                "cleanScore": 85.5,
                "rank": 1
            }
        }
