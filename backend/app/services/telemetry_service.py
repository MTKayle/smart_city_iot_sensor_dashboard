"""
Telemetry Processing Service for Smart City IoT Dashboard.

This module processes incoming telemetry data by:
1. Inserting data into MongoDB for time-series storage
2. Checking alert thresholds (CO2 > 1000 ppm, Noise > 85 dB)
3. Creating alerts in Oracle when thresholds are exceeded
4. Broadcasting telemetry and alerts to WebSocket clients

Validates: Requirements 4.1, 6.1, 6.2, 10.3
"""

import logging
from typing import Optional

from app.models import Telemetry
from app.db.mongodb_client import get_mongodb_client
from app.services.alert_service import get_alert_service


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelemetryService:
    """
    Service for processing telemetry data with storage, alerting, and broadcasting.
    
    Features:
    - MongoDB insertion for time-series data
    - Threshold-based alert generation via AlertService
    - WebSocket broadcasting (when configured)
    """
    
    def __init__(self, websocket_manager=None):
        """
        Initialize telemetry service.
        
        Args:
            websocket_manager: Optional WebSocket manager for broadcasting updates
        """
        self.mongodb_client = get_mongodb_client()
        self.alert_service = get_alert_service(websocket_manager)
        self.websocket_manager = websocket_manager
        
        logger.info("Telemetry service initialized")
    
    def process_telemetry(self, telemetry: Telemetry):
        """
        Process incoming telemetry data.
        
        Steps:
        1. Insert telemetry into MongoDB
        2. Check alert thresholds via AlertService
        3. Broadcast telemetry to WebSocket clients
        
        Args:
            telemetry: Validated Telemetry object
        
        Validates: Requirements 4.1, 6.1, 6.2, 10.3
        """
        try:
            # Step 1: Insert telemetry into MongoDB
            success = self.mongodb_client.insert_telemetry(telemetry)
            
            if not success:
                logger.error(
                    f"Failed to insert telemetry for sensor {telemetry.sensorId}"
                )
                return
            
            logger.debug(
                f"Telemetry stored - Sensor: {telemetry.sensorId}, "
                f"CO2: {telemetry.co2}, Noise: {telemetry.noise}, "
                f"Temp: {telemetry.temperature}"
            )
            
            # Step 2: Check thresholds and create alerts via AlertService
            self._check_and_create_alerts(telemetry)
            
            # Step 3: Broadcast telemetry to WebSocket clients
            self._broadcast_telemetry(telemetry)
            
        except Exception as e:
            logger.error(
                f"Error processing telemetry for sensor {telemetry.sensorId}: {e}",
                exc_info=True
            )
    
    def _check_and_create_alerts(self, telemetry: Telemetry):
        """
        Check telemetry values against thresholds and create alerts.
        
        Delegates alert creation to AlertService which handles:
        - Threshold validation
        - Deduplication
        - Database storage
        - Broadcasting
        
        Args:
            telemetry: Telemetry object to check
        
        Validates: Requirements 6.1, 6.2
        """
        # Check CO2 threshold
        self.alert_service.create_alert(
            sensor_id=telemetry.sensorId,
            metric_type="CO2",
            value=telemetry.co2,
            timestamp=telemetry.timestamp
        )
        
        # Check Noise threshold
        self.alert_service.create_alert(
            sensor_id=telemetry.sensorId,
            metric_type="Noise",
            value=telemetry.noise,
            timestamp=telemetry.timestamp
        )
    
    def _broadcast_telemetry(self, telemetry: Telemetry):
        """
        Broadcast telemetry data to all connected WebSocket clients.
        
        Args:
            telemetry: Telemetry object to broadcast
        
        Validates: Requirement 10.3
        """
        if self.websocket_manager:
            try:
                message = {
                    "type": "telemetry",
                    "data": telemetry.model_dump(mode='json')
                }
                self.websocket_manager.broadcast(message)
                logger.debug(f"Telemetry broadcast - Sensor: {telemetry.sensorId}")
            except Exception as e:
                logger.error(f"Error broadcasting telemetry: {e}")
        else:
            logger.debug("WebSocket manager not configured - skipping broadcast")
    
    def set_websocket_manager(self, websocket_manager):
        """
        Set or update the WebSocket manager for broadcasting.
        
        Args:
            websocket_manager: WebSocket manager instance
        """
        self.websocket_manager = websocket_manager
        self.alert_service.set_websocket_manager(websocket_manager)
        logger.info("WebSocket manager configured for telemetry service")


# Singleton instance
_telemetry_service: Optional[TelemetryService] = None


def get_telemetry_service(websocket_manager=None) -> TelemetryService:
    """
    Get singleton telemetry service instance.
    
    Args:
        websocket_manager: Optional WebSocket manager for broadcasting
    
    Returns:
        TelemetryService: Shared service instance
    """
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService(websocket_manager)
    elif websocket_manager and not _telemetry_service.websocket_manager:
        _telemetry_service.set_websocket_manager(websocket_manager)
    return _telemetry_service
