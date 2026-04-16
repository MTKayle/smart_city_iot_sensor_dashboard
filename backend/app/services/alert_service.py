"""
Alert Service for Smart City IoT Dashboard.

This module provides alert creation functionality with:
1. Threshold-based alert generation (CO2 > 1000 ppm, Noise > 85 dB)
2. Alert deduplication (5-minute window)
3. Oracle database storage
4. WebSocket broadcasting

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.models import Alert
from app.db.oracle_client import get_oracle_client


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Alert thresholds
CO2_THRESHOLD = 1000  # ppm
NOISE_THRESHOLD = 85  # dB

# Alert deduplication window (5 minutes)
ALERT_DEDUPLICATION_WINDOW = timedelta(minutes=5)


class AlertService:
    """
    Alert service for threshold-based alert generation and management.
    
    Features:
    - Threshold evaluation (CO2 > 1000, Noise > 85)
    - Alert deduplication (5-minute window)
    - Oracle database storage
    - WebSocket broadcasting support
    """
    
    def __init__(self, websocket_manager=None):
        """
        Initialize alert service.
        
        Args:
            websocket_manager: Optional WebSocket manager for broadcasting alerts
        """
        self.oracle_client = get_oracle_client()
        self.websocket_manager = websocket_manager
        
        # Cache for recent alerts (sensor_id:metric_type -> last_alert_time)
        # Used for fast deduplication without database queries
        self._recent_alerts_cache = {}
        
        logger.info("Alert service initialized")
    
    def create_alert(
        self,
        sensor_id: str,
        metric_type: str,
        value: float,
        timestamp: Optional[datetime] = None
    ) -> Optional[Alert]:
        """
        Create alert if thresholds are exceeded and no duplicate exists.
        
        Steps:
        1. Validate that metric exceeds threshold
        2. Check for duplicate alerts within 5-minute window
        3. Generate unique AlertID using UUID
        4. Determine alert level (HIGH for CO2 > 1000, Noise > 85)
        5. Insert alert into Oracle ALERTS table
        6. Broadcast alert to WebSocket clients
        
        Args:
            sensor_id: Sensor identifier
            metric_type: Metric type (CO2, Noise, Temperature)
            value: Measured value
            timestamp: Optional timestamp (defaults to current time)
        
        Returns:
            Alert: Created alert object if successful, None if duplicate or failed
        
        Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Step 1: Validate threshold
        if not self._exceeds_threshold(metric_type, value):
            logger.debug(
                f"Value does not exceed threshold - Sensor: {sensor_id}, "
                f"Metric: {metric_type}, Value: {value}"
            )
            return None
        
        # Step 2: Check for duplicate alerts
        if self._is_duplicate_alert(sensor_id, metric_type, timestamp):
            logger.debug(
                f"Alert suppressed (duplicate) - Sensor: {sensor_id}, "
                f"Metric: {metric_type}"
            )
            return None
        
        # Step 3: Generate unique AlertID
        alert_id = str(uuid.uuid4())
        
        # Step 4: Determine alert level
        level = self._determine_alert_level(metric_type, value)
        
        # Create Alert object
        alert = Alert(
            alertId=alert_id,
            sensorId=sensor_id,
            metricType=metric_type,
            value=value,
            level=level,
            createdAt=timestamp
        )
        
        # Step 5: Insert into Oracle ALERTS table
        success = self.oracle_client.insert_alert(alert)
        
        if not success:
            logger.error(
                f"Failed to insert alert into database - Sensor: {sensor_id}, "
                f"Metric: {metric_type}"
            )
            return None
        
        logger.info(
            f"Alert created - ID: {alert_id}, Sensor: {sensor_id}, "
            f"Metric: {metric_type}, Value: {value}, Level: {level}"
        )
        
        # Update cache
        cache_key = f"{sensor_id}:{metric_type}"
        self._recent_alerts_cache[cache_key] = timestamp
        
        # Step 6: Broadcast alert to WebSocket clients
        self._broadcast_alert(alert)
        
        return alert
    
    def _exceeds_threshold(self, metric_type: str, value: float) -> bool:
        """
        Check if metric value exceeds alert threshold.
        
        Thresholds:
        - CO2 > 1000 ppm → Alert
        - Noise > 85 dB → Alert
        - Temperature → No threshold (not monitored for alerts)
        
        Args:
            metric_type: Metric type (CO2, Noise, Temperature)
            value: Measured value
        
        Returns:
            bool: True if threshold exceeded, False otherwise
        
        Validates: Requirements 6.1, 6.2
        """
        if metric_type == "CO2":
            return value > CO2_THRESHOLD
        elif metric_type == "Noise":
            return value > NOISE_THRESHOLD
        else:
            # Temperature and other metrics don't have alert thresholds
            return False
    
    def _determine_alert_level(self, metric_type: str, value: float) -> str:
        """
        Determine alert severity level based on metric and value.
        
        Current implementation:
        - CO2 > 1000 ppm → HIGH
        - Noise > 85 dB → HIGH
        
        Args:
            metric_type: Metric type
            value: Measured value
        
        Returns:
            str: Alert level (LOW, MEDIUM, HIGH)
        
        Validates: Requirement 6.4
        """
        # For now, all threshold-exceeding values are HIGH
        # Future enhancement: Add MEDIUM and LOW thresholds
        if metric_type == "CO2" and value > CO2_THRESHOLD:
            return "HIGH"
        elif metric_type == "Noise" and value > NOISE_THRESHOLD:
            return "HIGH"
        else:
            return "MEDIUM"
    
    def _is_duplicate_alert(
        self,
        sensor_id: str,
        metric_type: str,
        current_time: datetime
    ) -> bool:
        """
        Check if alert already exists for sensor within 5-minute window.
        
        Uses two-tier approach:
        1. Check in-memory cache for fast lookup
        2. Fall back to database query if cache miss
        
        Args:
            sensor_id: Sensor identifier
            metric_type: Metric type
            current_time: Current timestamp
        
        Returns:
            bool: True if duplicate exists, False otherwise
        
        Validates: Requirement 6.5
        """
        cache_key = f"{sensor_id}:{metric_type}"
        
        # Check in-memory cache first
        if cache_key in self._recent_alerts_cache:
            last_alert_time = self._recent_alerts_cache[cache_key]
            time_since_last_alert = current_time - last_alert_time
            
            if time_since_last_alert < ALERT_DEDUPLICATION_WINDOW:
                logger.debug(
                    f"Duplicate found in cache - Sensor: {sensor_id}, "
                    f"Metric: {metric_type}, Time since last: {time_since_last_alert}"
                )
                return True
        
        # Check database for recent alerts (fallback)
        return self._check_database_for_duplicate(sensor_id, metric_type, current_time)
    
    def _check_database_for_duplicate(
        self,
        sensor_id: str,
        metric_type: str,
        current_time: datetime
    ) -> bool:
        """
        Query database for duplicate alerts within deduplication window.
        
        Args:
            sensor_id: Sensor identifier
            metric_type: Metric type
            current_time: Current timestamp
        
        Returns:
            bool: True if duplicate exists, False otherwise
        """
        try:
            # Query recent alerts for this sensor
            recent_alerts = self.oracle_client.get_alerts(limit=100)
            
            # Calculate window start time
            window_start = current_time - ALERT_DEDUPLICATION_WINDOW
            
            # Filter for matching sensor and metric within time window
            for alert_dict in recent_alerts:
                if (alert_dict.get('sensorid') == sensor_id and
                    alert_dict.get('metrictype') == metric_type):
                    
                    alert_time = alert_dict.get('createdat')
                    if isinstance(alert_time, datetime):
                        if alert_time >= window_start:
                            logger.debug(
                                f"Duplicate found in database - Sensor: {sensor_id}, "
                                f"Metric: {metric_type}, Alert time: {alert_time}"
                            )
                            # Update cache for future lookups
                            cache_key = f"{sensor_id}:{metric_type}"
                            self._recent_alerts_cache[cache_key] = alert_time
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking database for duplicates: {e}")
            # On error, assume no duplicate to avoid missing critical alerts
            return False
    
    def _broadcast_alert(self, alert: Alert):
        """
        Broadcast alert to all connected WebSocket clients.
        
        Args:
            alert: Alert object to broadcast
        
        Validates: Requirement 6.4
        """
        if self.websocket_manager:
            try:
                message = {
                    "type": "alert",
                    "data": alert.model_dump(mode='json')
                }
                self.websocket_manager.broadcast(message)
                logger.info(
                    f"Alert broadcast - ID: {alert.alertId}, Sensor: {alert.sensorId}, "
                    f"Metric: {alert.metricType}, Level: {alert.level}"
                )
            except Exception as e:
                logger.error(f"Error broadcasting alert: {e}", exc_info=True)
        else:
            logger.debug("WebSocket manager not configured - skipping broadcast")
    
    def set_websocket_manager(self, websocket_manager):
        """
        Set or update the WebSocket manager for broadcasting.
        
        Args:
            websocket_manager: WebSocket manager instance
        """
        self.websocket_manager = websocket_manager
        logger.info("WebSocket manager configured for alert service")
    
    def clear_cache(self):
        """
        Clear the in-memory alert cache.
        
        Useful for testing or when cache becomes stale.
        """
        self._recent_alerts_cache.clear()
        logger.info("Alert cache cleared")


# Singleton instance
_alert_service: Optional[AlertService] = None


def get_alert_service(websocket_manager=None) -> AlertService:
    """
    Get singleton alert service instance.
    
    Args:
        websocket_manager: Optional WebSocket manager for broadcasting
    
    Returns:
        AlertService: Shared alert service instance
    """
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService(websocket_manager)
    elif websocket_manager and not _alert_service.websocket_manager:
        _alert_service.set_websocket_manager(websocket_manager)
    return _alert_service
