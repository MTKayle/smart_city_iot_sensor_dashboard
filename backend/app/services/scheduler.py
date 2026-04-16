"""
Scheduler module for Smart City IoT Dashboard.

This module provides scheduled background tasks for analytics processing,
including daily Clean Score calculation and telemetry summary generation.

Validates: Requirements 8.5
"""

import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from statistics import mean

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.analytics_service import get_analytics_service
from app.db.mongodb_client import get_mongodb_client
from app.db.oracle_client import get_oracle_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyticsScheduler:
    """
    Background scheduler for analytics tasks.
    
    Manages scheduled jobs for:
    - Daily Clean Score calculation at midnight
    - Telemetry summary aggregation by location
    """
    
    def __init__(self):
        """Initialize scheduler with background execution."""
        self.scheduler = BackgroundScheduler()
        self.analytics_service = get_analytics_service()
        self.mongodb_client = get_mongodb_client()
        self.oracle_client = get_oracle_client()
        
        # Configure scheduled jobs
        self._configure_jobs()
    
    def _configure_jobs(self):
        """
        Configure scheduled jobs with cron triggers.
        
        Jobs:
        - Daily Clean Score calculation: Runs at midnight (00:00) every day
        """
        # Daily Clean Score calculation at midnight
        self.scheduler.add_job(
            func=self.calculate_daily_clean_scores,
            trigger=CronTrigger(hour=0, minute=0),  # Midnight every day
            id='daily_clean_score_calculation',
            name='Calculate Clean Score for all locations',
            replace_existing=True,
            misfire_grace_time=3600  # Allow 1 hour grace period if job misses scheduled time
        )
        
        logger.info("Configured scheduled job: daily_clean_score_calculation at 00:00")
    
    def calculate_daily_clean_scores(self):
        """
        Calculate Clean Score for all locations for the previous day.
        
        This job:
        1. Gets all locations from Oracle
        2. For each location, aggregates telemetry data from MongoDB for previous day
        3. Calculates averages for CO2, Noise, and Temperature
        4. Calls store_daily_summary() to save results with Clean Score
        
        Validates: Requirements 8.5
        """
        try:
            logger.info("Starting daily Clean Score calculation job...")
            
            # Calculate date range for previous day
            yesterday = date.today() - timedelta(days=1)
            start_time = datetime.combine(yesterday, datetime.min.time())
            end_time = datetime.combine(yesterday, datetime.max.time())
            
            logger.info(f"Processing telemetry data for date: {yesterday}")
            
            # Get all locations from Oracle
            locations = self.oracle_client.get_location_hierarchy()
            
            if not locations:
                logger.warning("No locations found in database")
                return
            
            logger.info(f"Found {len(locations)} locations to process")
            
            # Process each location
            success_count = 0
            error_count = 0
            
            for location in locations:
                location_id = location.get('locationid')
                
                if not location_id:
                    logger.warning(f"Skipping location with missing ID: {location}")
                    continue
                
                try:
                    # Aggregate telemetry data for this location
                    summary_data = self._aggregate_location_telemetry(
                        location_id,
                        start_time,
                        end_time
                    )
                    
                    if summary_data:
                        # Store daily summary with Clean Score
                        success = self.analytics_service.store_daily_summary(
                            location_id=location_id,
                            summary_date=yesterday,
                            avg_co2=summary_data['avg_co2'],
                            avg_noise=summary_data['avg_noise'],
                            avg_temperature=summary_data['avg_temperature']
                        )
                        
                        if success:
                            success_count += 1
                            logger.debug(f"Processed location {location_id}: {summary_data}")
                        else:
                            error_count += 1
                            logger.error(f"Failed to store summary for location {location_id}")
                    else:
                        logger.debug(f"No telemetry data for location {location_id} on {yesterday}")
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing location {location_id}: {e}")
            
            logger.info(
                f"Daily Clean Score calculation completed: "
                f"{success_count} successful, {error_count} errors"
            )
        
        except Exception as e:
            logger.error(f"Daily Clean Score calculation job failed: {e}")
    
    def _aggregate_location_telemetry(
        self,
        location_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """
        Aggregate telemetry data for a location within a time range.
        
        Queries all sensors for the location and calculates average values
        for CO2, Noise, and Temperature metrics.
        
        Args:
            location_id: Location identifier
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
        
        Returns:
            Dictionary with avg_co2, avg_noise, avg_temperature, or None if no data
        """
        try:
            # Get all sensors for this location
            sensors = self.oracle_client.get_sensors(location_id=location_id)
            
            if not sensors:
                return None
            
            # Collect telemetry data from all sensors
            all_co2_values = []
            all_noise_values = []
            all_temperature_values = []
            
            for sensor in sensors:
                sensor_id = sensor.get('sensorid')
                
                if not sensor_id:
                    continue
                
                # Query telemetry data for this sensor in the time range
                telemetry_docs = self.mongodb_client.query_telemetry(
                    sensor_id=sensor_id,
                    start_time=start_time,
                    end_time=end_time,
                    limit=10000  # High limit to get all data for the day
                )
                
                # Extract values
                for doc in telemetry_docs:
                    all_co2_values.append(doc.get('co2'))
                    all_noise_values.append(doc.get('noise'))
                    all_temperature_values.append(doc.get('temperature'))
            
            # Check if we have any data
            if not all_co2_values:
                return None
            
            # Calculate averages
            avg_co2 = mean(all_co2_values)
            avg_noise = mean(all_noise_values)
            avg_temperature = mean(all_temperature_values)
            
            return {
                'avg_co2': round(avg_co2, 2),
                'avg_noise': round(avg_noise, 2),
                'avg_temperature': round(avg_temperature, 2)
            }
        
        except Exception as e:
            logger.error(f"Error aggregating telemetry for location {location_id}: {e}")
            return None
    
    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Analytics scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Analytics scheduler shutdown")


# Singleton instance
_analytics_scheduler: AnalyticsScheduler = None


def get_analytics_scheduler() -> AnalyticsScheduler:
    """
    Get singleton AnalyticsScheduler instance.
    
    Returns:
        AnalyticsScheduler: Shared scheduler instance
    """
    global _analytics_scheduler
    if _analytics_scheduler is None:
        _analytics_scheduler = AnalyticsScheduler()
    return _analytics_scheduler
