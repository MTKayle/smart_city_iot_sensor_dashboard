"""
REST API routes for Smart City IoT Dashboard.

This module defines all HTTP endpoints for the backend API.
Implements endpoints for locations, sensors, telemetry, alerts, analytics, and leaderboard.

Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.models import Location, Sensor, Alert, Analytics, LeaderboardEntry, Telemetry
from app.db import get_mongodb_client, get_oracle_client
from app.services import get_analytics_service


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    
    Validates: Requirement 9.6
    """
    return {"status": "healthy", "service": "smart-city-iot-backend"}


@router.get("/locations", response_model=List[Location])
async def get_locations():
    """
    Get all locations in the hierarchy.
    
    Queries the Oracle LOCATION_HIERARCHY view to retrieve the complete
    location hierarchy with parent-child relationships.
    
    Returns:
        List[Location]: All locations (City, District, Ward) with hierarchy information
    
    Validates: Requirements 9.1, 1.3
    """
    try:
        oracle_client = get_oracle_client()
        
        # Query location hierarchy from Oracle
        hierarchy_data = oracle_client.get_location_hierarchy()
        
        # Convert to Location model objects
        locations = []
        for row in hierarchy_data:
            location = Location(
                locationId=row['locationid'],
                name=row['name'],
                parentId=row['parentid'],
                type=row['type']
            )
            locations.append(location)
        
        logger.info(f"Retrieved {len(locations)} locations from hierarchy")
        return locations
        
    except Exception as e:
        logger.error(f"Error retrieving locations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve locations: {str(e)}")


@router.get("/sensors", response_model=List[Sensor])
async def get_sensors(location_id: Optional[str] = None):
    """
    Get all registered sensors with location information.
    
    Joins SENSOR_REGISTRY with LOCATIONS table to retrieve sensors
    with their location hierarchy information. Optionally filters by location.
    
    Args:
        location_id: Optional location filter
    
    Returns:
        List[Sensor]: Registered sensors with location hierarchy
    
    Validates: Requirements 9.2, 2.4
    """
    try:
        oracle_client = get_oracle_client()
        
        # Query sensors from Oracle (with optional location filter)
        sensor_data = oracle_client.get_sensors(location_id=location_id)
        
        # Convert to Sensor model objects
        sensors = []
        for row in sensor_data:
            sensor = Sensor(
                sensorId=row['sensorid'],
                locationId=row['locationid'],
                sensorType=row['sensortype'],
                registeredAt=row['registeredat']
            )
            sensors.append(sensor)
        
        logger.info(f"Retrieved {len(sensors)} sensors" + (f" for location {location_id}" if location_id else ""))
        return sensors
        
    except Exception as e:
        logger.error(f"Error retrieving sensors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sensors: {str(e)}")


@router.get("/telemetry/{sensor_id}", response_model=List[Telemetry])
async def get_telemetry(
    sensor_id: str,
    start_time: Optional[datetime] = Query(None, description="Start of time range (ISO 8601 format)"),
    end_time: Optional[datetime] = Query(None, description="End of time range (ISO 8601 format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    Get telemetry data for a sensor with optional time range filter.
    
    Queries MongoDB telemetry collection with time range filter.
    Defaults to last 24 hours if no time range specified.
    Validates that start_time < end_time.
    
    Args:
        sensor_id: Sensor identifier
        start_time: Optional start of time range (inclusive)
        end_time: Optional end of time range (inclusive)
        limit: Maximum number of records to return (default: 100, max: 1000)
    
    Returns:
        List[Telemetry]: Telemetry records ordered by timestamp descending
    
    Raises:
        HTTPException: 400 if start_time >= end_time
        HTTPException: 404 if sensor not found
        HTTPException: 500 if query fails
    
    Validates: Requirement 9.3
    """
    try:
        # Validate time range if both provided
        if start_time and end_time:
            if start_time >= end_time:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid time range: start_time must be less than end_time"
                )
        
        from datetime import timezone
        
        # Default to last 24 hours if no time range specified
        if not start_time and not end_time:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)
            logger.info(f"No time range specified, defaulting to last 24 hours")
        elif start_time and not end_time:
            # Match the tzinfo state of start_time
            if start_time.tzinfo is not None:
                end_time = datetime.now(timezone.utc)
            else:
                end_time = datetime.utcnow()
        
        mongodb_client = get_mongodb_client()
        
        # Calculate time delta if both start and end exist
        time_delta = end_time - start_time if (start_time and end_time) else None
        
        # Query telemetry data from MongoDB
        # If duration > 8 hours, bucket by 5 minutes
        # If duration > 2 hours, bucket by 1 minute
        if time_delta and time_delta.total_seconds() > 8 * 3600:
            telemetry_docs = mongodb_client.query_telemetry_aggregated(
                sensor_id=sensor_id,
                start_time=start_time,
                end_time=end_time,
                bucket_minutes=5
            )
        elif time_delta and time_delta.total_seconds() > 2 * 3600:
            telemetry_docs = mongodb_client.query_telemetry_aggregated(
                sensor_id=sensor_id,
                start_time=start_time,
                end_time=end_time,
                bucket_minutes=1
            )
        else:
            telemetry_docs = mongodb_client.query_telemetry(
                sensor_id=sensor_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
        
        # Convert to Telemetry model objects
        from datetime import timezone
        telemetry_list = []
        for doc in telemetry_docs:
            ts = doc['timestamp']
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            
            telemetry = Telemetry(
                sensorId=doc['sensorId'],
                locationId=doc['locationId'],
                co2=doc['co2'],
                noise=doc['noise'],
                temperature=doc['temperature'],
                timestamp=ts
            )
            telemetry_list.append(telemetry)
        
        logger.info(
            f"Retrieved {len(telemetry_list)} telemetry records for sensor {sensor_id} "
            f"(start={start_time}, end={end_time})"
        )
        return telemetry_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving telemetry for sensor {sensor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve telemetry: {str(e)}")


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    level: Optional[str] = Query(None, description="Alert level filter (LOW, MEDIUM, HIGH)"),
    location_id: Optional[str] = Query(None, description="Location ID filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts to return")
):
    """
    Get recent alerts with optional filters.
    
    Queries Oracle ALERTS table with optional filters for level and location.
    Returns alerts ordered by CreatedAt descending, limited to 100 by default.
    
    Args:
        level: Optional alert level filter (LOW, MEDIUM, HIGH)
        location_id: Optional location ID filter
        limit: Maximum number of alerts to return (default: 100, max: 1000)
    
    Returns:
        List[Alert]: Recent alerts ordered by creation time descending
    
    Raises:
        HTTPException: 400 if invalid level provided
        HTTPException: 500 if query fails
    
    Validates: Requirement 9.4
    """
    try:
        # Validate level if provided
        if level and level not in ["LOW", "MEDIUM", "HIGH"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid alert level: {level}. Must be one of: LOW, MEDIUM, HIGH"
            )
        
        oracle_client = get_oracle_client()
        
        # Query alerts from Oracle with filters
        alert_data = oracle_client.get_alerts(
            level=level,
            location_id=location_id,
            limit=limit
        )
        
        # Convert to Alert model objects
        alerts = []
        for row in alert_data:
            alert = Alert(
                alertId=row['alertid'],
                sensorId=row['sensorid'],
                metricType=row['metrictype'],
                value=row['value'],
                level=row['alertlevel'],
                createdAt=row['createdat']
            )
            alerts.append(alert)
        
        logger.info(
            f"Retrieved {len(alerts)} alerts "
            f"(level={level}, location_id={location_id}, limit={limit})"
        )
        return alerts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {str(e)}")


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(limit: int = Query(100, ge=1, le=1000, description="Maximum number of entries to return")):
    """
    Get leaderboard of locations ranked by environmental quality (Clean Score).
    
    Queries Oracle TELEMETRY_SUMMARY table to retrieve locations ordered by
    Clean Score descending (highest score = cleanest location).
    Returns leaderboard entries with rank numbers.
    
    Args:
        limit: Maximum number of entries to return (default: 100, max: 1000)
    
    Returns:
        List[LeaderboardEntry]: Locations ranked by Clean Score with rank numbers
    
    Raises:
        HTTPException: 500 if query fails
    
    Validates: Requirement 8.4
    """
    try:
        oracle_client = get_oracle_client()
        
        # Query leaderboard from Oracle
        leaderboard_data = oracle_client.get_leaderboard(limit=limit)
        
        # Convert to LeaderboardEntry model objects
        leaderboard = []
        for row in leaderboard_data:
            entry = LeaderboardEntry(
                locationId=row['locationid'],
                locationName=row['locationname'],
                avgCO2=row['avgco2'],
                avgNoise=row['avgnoise'],
                avgTemperature=row['avgtemperature'],
                cleanScore=row['cleanscore'],
                rank=row['rank']
            )
            leaderboard.append(entry)
        
        logger.info(f"Retrieved leaderboard with {len(leaderboard)} entries")
        return leaderboard
        
    except Exception as e:
        logger.error(f"Error retrieving leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leaderboard: {str(e)}")


@router.get("/sensors/{sensor_id}/analytics", response_model=Analytics)
async def get_sensor_analytics(sensor_id: str):
    """
    Get analytics (moving averages) for a sensor.
    
    Calls calculate_moving_average() from analytics module to compute
    moving averages for the last 10 telemetry readings.
    
    Args:
        sensor_id: Sensor identifier
    
    Returns:
        Analytics: Moving averages for CO2, Noise, and Temperature metrics
    
    Raises:
        HTTPException: 404 if sensor has no telemetry data
        HTTPException: 500 if calculation fails
    
    Validates: Requirement 7.4
    """
    try:
        analytics_service = get_analytics_service()
        
        # Calculate moving averages
        analytics = analytics_service.calculate_moving_average(sensor_id)
        
        if analytics is None:
            raise HTTPException(
                status_code=404,
                detail=f"No telemetry data found for sensor {sensor_id}"
            )
        
        logger.info(f"Retrieved analytics for sensor {sensor_id}")
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating analytics for sensor {sensor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate analytics: {str(e)}")
