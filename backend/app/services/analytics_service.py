"""
Analytics service module for Smart City IoT Dashboard.

This module provides analytics calculations including moving averages
and Clean Score computation for environmental quality assessment.

Validates: Requirements 7.1, 7.3, 8.1, 8.2, 8.3
"""

import logging
from typing import Optional, Dict
from statistics import mean
from datetime import date
import uuid

from app.models.analytics import Analytics, MovingAverage
from app.db.mongodb_client import get_mongodb_client
from app.db.oracle_client import get_oracle_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Moving average window size
MOVING_AVERAGE_WINDOW = 10


class AnalyticsService:
    """
    Service class for analytics operations.
    
    Provides methods for calculating moving averages and Clean Score metrics.
    """
    
    def __init__(self):
        """Initialize analytics service."""
        self.mongodb_client = get_mongodb_client()
        self.oracle_client = get_oracle_client()
    
    def calculate_moving_average(self, sensor_id: str) -> Optional[Analytics]:
        """
        Calculate moving averages for the last N telemetry readings of a sensor.
        
        Queries the last 10 telemetry readings from MongoDB for the given sensor
        and calculates the arithmetic mean for CO2, Noise, and Temperature metrics.
        Handles cases where fewer than 10 readings exist by using all available data.
        
        Args:
            sensor_id: Sensor identifier to calculate analytics for
        
        Returns:
            Analytics object containing moving averages for all metrics,
            or None if no telemetry data exists for the sensor
        
        Algorithm:
            1. Query last N readings from MongoDB (N = MOVING_AVERAGE_WINDOW = 10)
            2. Extract values for each metric (CO2, Noise, Temperature)
            3. Calculate arithmetic mean: sum(values) / len(values)
            4. Handle edge case: if fewer than N readings exist, use all available
            5. Return Analytics object with MovingAverage data for each metric
        
        Validates: Requirements 7.1, 7.3
        
        Example:
            >>> analytics = calculate_moving_average("sensor_001")
            >>> print(analytics.co2_moving_avg.average)
            461.16
            >>> print(analytics.co2_moving_avg.window_size)
            10
        """
        try:
            # Query last N telemetry readings for the sensor
            # Results are sorted by timestamp descending (most recent first)
            telemetry_docs = self.mongodb_client.query_telemetry(
                sensor_id=sensor_id,
                limit=MOVING_AVERAGE_WINDOW
            )
            
            # Check if any data exists
            if not telemetry_docs:
                logger.warning(f"No telemetry data found for sensor {sensor_id}")
                return None
            
            # Extract values for each metric
            co2_values = [doc["co2"] for doc in telemetry_docs]
            noise_values = [doc["noise"] for doc in telemetry_docs]
            temperature_values = [doc["temperature"] for doc in telemetry_docs]
            
            # Calculate arithmetic mean for each metric
            # Using statistics.mean() for precision
            co2_avg = mean(co2_values)
            noise_avg = mean(noise_values)
            temperature_avg = mean(temperature_values)
            
            # Determine actual window size (may be less than 10 if fewer readings exist)
            window_size = len(telemetry_docs)
            
            # Create MovingAverage objects for each metric
            co2_moving_avg = MovingAverage(
                metric="CO2",
                values=co2_values,
                average=round(co2_avg, 2),
                window_size=window_size
            )
            
            noise_moving_avg = MovingAverage(
                metric="Noise",
                values=noise_values,
                average=round(noise_avg, 2),
                window_size=window_size
            )
            
            temperature_moving_avg = MovingAverage(
                metric="Temperature",
                values=temperature_values,
                average=round(temperature_avg, 2),
                window_size=window_size
            )
            
            # Create and return Analytics object
            analytics = Analytics(
                sensorId=sensor_id,
                co2_moving_avg=co2_moving_avg,
                noise_moving_avg=noise_moving_avg,
                temperature_moving_avg=temperature_moving_avg
            )
            
            logger.info(
                f"Calculated moving averages for sensor {sensor_id}: "
                f"CO2={co2_avg:.2f}, Noise={noise_avg:.2f}, Temp={temperature_avg:.2f} "
                f"(window_size={window_size})"
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error calculating moving average for sensor {sensor_id}: {e}")
            return None
    
    def calculate_clean_score(self, avg_co2: float, avg_noise: float) -> float:
        """
        Calculate Clean Score for environmental quality assessment.
        
        Clean Score is a composite metric that ranks location environmental quality
        based on normalized CO2 and Noise levels. Higher scores indicate better
        environmental quality.
        
        Args:
            avg_co2: Average CO2 level in ppm
            avg_noise: Average noise level in dB
        
        Returns:
            float: Clean Score value between 0-100 (higher is better)
        
        Algorithm:
            1. Normalize CO2: normalized_CO2 = (avgCO2 / 2000) * 100
               - Range: 0-2000 ppm maps to 0-100
            2. Normalize Noise: normalized_Noise = (avgNoise / 100) * 100
               - Range: 0-100 dB maps to 0-100
            3. Calculate Clean Score: 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)
               - Equal weighting (50%) for CO2 and Noise
               - Inverted scale: lower pollution = higher score
        
        Validates: Requirements 8.1, 8.2
        
        Example:
            >>> calculate_clean_score(420.5, 55.2)
            68.09
            >>> # normalized_CO2 = (420.5 / 2000) * 100 = 21.025
            >>> # normalized_Noise = (55.2 / 100) * 100 = 55.2
            >>> # clean_score = 100 - (21.025 * 0.5 + 55.2 * 0.5) = 100 - 38.1125 = 61.8875
        """
        # Normalize CO2 using range 0-2000 ppm
        normalized_co2 = (avg_co2 / 2000.0) * 100.0
        
        # Normalize Noise using range 0-100 dB
        normalized_noise = (avg_noise / 100.0) * 100.0
        
        # Calculate Clean Score with equal weighting (0.5 each)
        clean_score = 100.0 - (normalized_co2 * 0.5 + normalized_noise * 0.5)
        
        # Round to 2 decimal places for consistency
        return round(clean_score, 2)
    
    def store_daily_summary(
        self,
        location_id: str,
        summary_date: date,
        avg_co2: float,
        avg_noise: float,
        avg_temperature: float
    ) -> bool:
        """
        Store daily telemetry summary with Clean Score in Oracle TELEMETRY_SUMMARY table.
        
        Calculates Clean Score and stores aggregated daily metrics for a location.
        Uses MERGE operation to insert new records or update existing ones.
        
        Args:
            location_id: Location identifier
            summary_date: Date for the summary
            avg_co2: Average CO2 level in ppm
            avg_noise: Average noise level in dB
            avg_temperature: Average temperature in °C
        
        Returns:
            bool: True if storage successful, False otherwise
        
        Validates: Requirements 8.3
        
        Example:
            >>> store_daily_summary(
            ...     "ward_001",
            ...     date(2024, 1, 15),
            ...     420.5,
            ...     55.2,
            ...     26.3
            ... )
            True
        """
        try:
            # Calculate Clean Score
            clean_score = self.calculate_clean_score(avg_co2, avg_noise)
            
            # Generate unique summary ID
            summary_id = str(uuid.uuid4())
            
            # Store in Oracle
            success = self.oracle_client.insert_or_update_telemetry_summary(
                summary_id=summary_id,
                location_id=location_id,
                summary_date=summary_date,
                avg_co2=avg_co2,
                avg_noise=avg_noise,
                avg_temperature=avg_temperature,
                clean_score=clean_score
            )
            
            if success:
                logger.info(
                    f"Stored daily summary for location {location_id} on {summary_date}: "
                    f"CO2={avg_co2:.2f}, Noise={avg_noise:.2f}, Temp={avg_temperature:.2f}, "
                    f"CleanScore={clean_score:.2f}"
                )
            else:
                logger.error(f"Failed to store daily summary for location {location_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing daily summary for location {location_id}: {e}")
            return False


# Singleton instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """
    Get singleton AnalyticsService instance.
    
    Returns:
        AnalyticsService: Shared service instance
    """
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
