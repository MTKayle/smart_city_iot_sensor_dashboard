"""
Telemetry Processing Service for Smart City IoT Dashboard.

This module processes incoming telemetry data by:
1. Enriching raw telemetry with geolocation data from Oracle (FR4.1, FR4.2, FR4.3)
2. Computing TTL expireAt timestamp (current time + 30 days) (FR4.4)
3. Inserting enriched document into MongoDB using batch insert (FR4.4, NFR1.2, NFR3.3)
4. Checking alert thresholds (CO2 > 1000 ppm, Noise > 85 dB) (FR6.x)
5. Broadcasting enriched telemetry to WebSocket clients (FR4.5, IR2.1, NFR1.3)

Validates: FR4.1, FR4.2, FR4.3, FR4.4, FR4.5, NFR1.2, NFR1.3, NFR3.3
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from app.models import Telemetry, TelemetryData, GeoLocation, DataQuality
from app.db.mongodb_client import get_mongodb_client
from app.db.oracle_client import get_oracle_client
from app.services.alert_service import get_alert_service


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# TTL configuration
TELEMETRY_TTL_DAYS = 30


# ---------------------------------------------------------------------------
# Helper: enrich_telemetry_with_geolocation
# ---------------------------------------------------------------------------

def enrich_telemetry_with_geolocation(
    raw_telemetry: Telemetry,
    oracle_client=None,
) -> Telemetry:
    """
    Enrich a raw telemetry object with geolocation data from Oracle SENSOR_REGISTRY.

    Steps:
    1. Query Oracle SENSOR_REGISTRY for sensor's Latitude, Longitude, ClusterID, LocationID
    2. Assign ClusterID from registry if not already set
    3. Build GeoLocation object (GeoJSON Point) with coordinates [lng, lat]
    4. Calculate expireAt = receivedAt + 30 days (TTL for MongoDB)
    5. Preserve DataQuality fields if present in raw telemetry

    If the sensor is not found in Oracle the original telemetry is returned unchanged
    so the pipeline can still proceed (with whatever geo data was provided upstream).

    Args:
        raw_telemetry: Validated Telemetry object (may have partial location info)
        oracle_client:  Optional pre-acquired OracleClient (injection for testing)

    Returns:
        Telemetry: Enriched telemetry object ready for MongoDB storage

    Validates: FR4.1, FR4.2, FR4.3, FR4.4
    """
    if oracle_client is None:
        oracle_client = get_oracle_client()

    # --- 1. Query geolocation from Oracle ---
    geo_info: Optional[Dict[str, Any]] = None
    try:
        geo_info = oracle_client.get_sensor_geolocation(raw_telemetry.sensorId)
    except Exception as e:
        logger.error(
            f"[enrich] Oracle geolocation lookup failed for sensor "
            f"'{raw_telemetry.sensorId}': {e}"
        )

    if geo_info is None:
        logger.warning(
            f"[enrich] No geolocation found for sensor '{raw_telemetry.sensorId}'. "
            "Returning telemetry without enrichment."
        )
        return raw_telemetry

    latitude = geo_info["latitude"]
    longitude = geo_info["longitude"]
    cluster_id = geo_info.get("clusterId") or raw_telemetry.clusterId
    location_id = geo_info.get("locationId") or raw_telemetry.locationId

    logger.debug(
        f"[enrich] Sensor '{raw_telemetry.sensorId}' → "
        f"lat={latitude}, lng={longitude}, cluster={cluster_id}"
    )

    # --- 2 & 3. Build GeoLocation (GeoJSON Point) ---
    geo_location = GeoLocation(
        type="Point",
        coordinates=[longitude, latitude]  # GeoJSON: [lng, lat]
    )

    # --- 4. Calculate TTL expireAt (current server time + 30 days) ---
    received_at = raw_telemetry.receivedAt or datetime.now(timezone.utc)
    expire_at = received_at + timedelta(days=TELEMETRY_TTL_DAYS)

    # --- 5. Preserve or carry quality field ---
    quality = raw_telemetry.quality  # may be None – that's fine

    # Build enriched Telemetry object (copy all data fields, override geo/cluster/ttl)
    enriched = Telemetry(
        sensorId=raw_telemetry.sensorId,
        locationId=location_id,
        clusterId=cluster_id,
        data=raw_telemetry.data,
        location=geo_location,
        quality=quality,
        timestamp=raw_telemetry.timestamp,
        receivedAt=received_at,
        expireAt=expire_at,
    )

    logger.info(
        f"[enrich] Telemetry enriched — sensor='{enriched.sensorId}', "
        f"cluster='{enriched.clusterId}', "
        f"expireAt={enriched.expireAt.isoformat()}"
    )
    return enriched


# ---------------------------------------------------------------------------
# TelemetryService
# ---------------------------------------------------------------------------

class TelemetryService:
    """
    Service for processing telemetry data with enrichment, storage, alerting,
    and broadcasting.

    Features:
    - Geolocation enrichment via Oracle SENSOR_REGISTRY
    - MongoDB batch insert for time-series data
    - Pydantic validation before storage
    - Threshold-based alert generation via AlertService
    - WebSocket broadcasting with `type` field
    """

    def __init__(self, websocket_manager=None):
        """
        Initialize telemetry service.

        Args:
            websocket_manager: Optional WebSocket manager for broadcasting updates
        """
        self.mongodb_client = get_mongodb_client()
        self.oracle_client = get_oracle_client()
        self.alert_service = get_alert_service(websocket_manager)
        self.websocket_manager = websocket_manager

        logger.info("TelemetryService initialized")

    def process_telemetry(self, telemetry: Telemetry):
        """
        Full telemetry processing pipeline.

        Steps:
        1. Enrich telemetry with geolocation from Oracle
        2. Validate enriched telemetry
        3. Store enriched telemetry in MongoDB (batch insert)
        4. Check alert thresholds via AlertService
        5. Broadcast enriched telemetry to WebSocket clients

        Args:
            telemetry: Validated Telemetry object received from MQTT

        Validates: FR4.1–FR4.5, NFR1.2, NFR1.3, NFR3.3
        """
        try:
            # Step 1: Enrich with geolocation
            enriched = enrich_telemetry_with_geolocation(
                telemetry, oracle_client=self.oracle_client
            )

            # Step 2: Validate enriched telemetry
            if not self._validate_telemetry(enriched):
                logger.error(
                    f"[process] Enriched telemetry failed validation for "
                    f"sensor '{enriched.sensorId}' — skipping storage"
                )
                return

            # Step 3: Store in MongoDB using batch insert
            stored = self._store_telemetry(enriched)
            if not stored:
                logger.error(
                    f"[process] Failed to store telemetry for sensor "
                    f"'{enriched.sensorId}'"
                )
                return

            logger.debug(
                f"[process] Stored — sensor='{enriched.sensorId}', "
                f"ts={enriched.timestamp.isoformat()}"
            )

            # Step 4: Check thresholds and create alerts
            self._check_and_create_alerts(enriched)

            # Step 5: Broadcast enriched telemetry via WebSocket
            self._broadcast_telemetry(enriched)

        except Exception as e:
            logger.error(
                f"[process] Unexpected error for sensor "
                f"'{getattr(telemetry, 'sensorId', 'unknown')}': {e}",
                exc_info=True,
            )

    # -----------------------------------------------------------------------
    # 4.2 – Storage (batch insert + validation)
    # -----------------------------------------------------------------------

    def _validate_telemetry(self, telemetry: Telemetry) -> bool:
        """
        Validate telemetry before storage.

        Checks:
        - sensorId is non-empty
        - locationId is non-empty
        - location coordinates are present
        - at least one data metric is non-None
        - expireAt is set and is in the future

        Args:
            telemetry: Telemetry object to validate

        Returns:
            bool: True if valid, False otherwise

        Validates: FR4.4, NFR3.3
        """
        if not telemetry.sensorId:
            logger.warning("[validate] Missing sensorId")
            return False

        if not telemetry.locationId:
            logger.warning(
                f"[validate] Missing locationId for sensor '{telemetry.sensorId}'"
            )
            return False

        if not telemetry.location or len(telemetry.location.coordinates) != 2:
            logger.warning(
                f"[validate] Invalid location for sensor '{telemetry.sensorId}'"
            )
            return False

        data = telemetry.data
        has_metric = any(
            v is not None for v in [
                data.co2, data.noise, data.temperature,
                data.pm25, data.humidity
            ]
        )
        if not has_metric:
            logger.warning(
                f"[validate] No data metrics for sensor '{telemetry.sensorId}'"
            )
            return False

        if telemetry.expireAt is None:
            logger.warning(
                f"[validate] Missing expireAt for sensor '{telemetry.sensorId}'"
            )
            return False

        return True

    def _store_telemetry(self, telemetry: Telemetry) -> bool:
        """
        Store enriched telemetry in MongoDB using batch insert for performance.

        Uses batch_insert_telemetry([telemetry]) which leverages ordered=False
        bulk write — duplicates (E11000) are handled gracefully.

        Args:
            telemetry: Enriched Telemetry object

        Returns:
            bool: True if inserted successfully or duplicate (already present),
                  False on error

        Validates: FR4.4, NFR1.2, NFR3.3
        """
        try:
            result = self.mongodb_client.batch_insert_telemetry([telemetry])

            if result.errors > 0:
                logger.error(
                    f"[store] Batch insert error for sensor '{telemetry.sensorId}': "
                    f"{result.errors} error(s)"
                )
                return False

            if result.duplicates > 0:
                logger.warning(
                    f"[store] Duplicate telemetry skipped for sensor "
                    f"'{telemetry.sensorId}' at {telemetry.timestamp}"
                )
                # Treat duplicate as non-fatal — downstream alert/broadcast still useful
                return True

            if result.inserted > 0:
                logger.debug(
                    f"[store] Inserted telemetry for sensor '{telemetry.sensorId}'"
                )
                return True

            logger.warning(
                f"[store] No insert recorded for sensor '{telemetry.sensorId}'"
            )
            return False

        except Exception as e:
            logger.error(
                f"[store] Exception storing telemetry for sensor "
                f"'{telemetry.sensorId}': {e}",
                exc_info=True,
            )
            return False

    # -----------------------------------------------------------------------
    # 4.1 – Alert checking (delegates to AlertService using enriched data)
    # -----------------------------------------------------------------------

    def _check_and_create_alerts(self, telemetry: Telemetry):
        """
        Check telemetry values against thresholds, run predictive analysis
        and anomaly detection, then create alerts as needed.

        Checks:
        - CO2 threshold
        - Noise threshold
        - PM2.5 threshold
        - Humidity threshold
        - Predictive alerts (linear regression 1h ahead)
        - Anomaly detection (Z-score)

        Args:
            telemetry: Enriched Telemetry object

        Validates: FR5.1, FR5.2, FR5.3, FR5.4, FR10.1, FR10.2
        """
        data = telemetry.data
        sid = telemetry.sensorId
        lid = telemetry.locationId
        cid = telemetry.clusterId
        ts = telemetry.timestamp

        # Metric → value mapping for threshold + anomaly + predictive checks
        metrics = {
            "CO2": data.co2,
            "Noise": data.noise,
            "PM25": data.pm25,
            "Humidity": data.humidity,
        }

        for metric_type, value in metrics.items():
            if value is None:
                continue

            # 6.1 — Threshold check
            self.alert_service.check_threshold_alerts(
                sensor_id=sid,
                location_id=lid,
                metric_type=metric_type,
                value=value,
                cluster_id=cid,
                timestamp=ts,
            )

            # 6.3 — Predictive alert (linear regression)
            try:
                self.alert_service.check_predictive_alerts(
                    sensor_id=sid,
                    location_id=lid,
                    metric_type=metric_type,
                    cluster_id=cid,
                    timestamp=ts,
                )
            except Exception as e:
                logger.warning(f"[alerts] Predictive check failed for {metric_type}: {e}")

            # 6.4 — Anomaly detection (Z-score)
            try:
                self.alert_service.detect_anomalies(
                    sensor_id=sid,
                    location_id=lid,
                    metric_type=metric_type,
                    current_value=value,
                    cluster_id=cid,
                    timestamp=ts,
                )
            except Exception as e:
                logger.warning(f"[alerts] Anomaly check failed for {metric_type}: {e}")


    # -----------------------------------------------------------------------
    # 4.3 – WebSocket broadcast
    # -----------------------------------------------------------------------

    def _broadcast_telemetry(self, telemetry: Telemetry):
        """
        Broadcast enriched telemetry data to all connected WebSocket clients.

        Message format:
        {
            "type": "telemetry",
            "data": { ...enriched telemetry fields... }
        }

        Broadcast failures are caught and logged — they do NOT abort the pipeline.

        Args:
            telemetry: Enriched Telemetry object

        Validates: FR4.5, IR2.1, NFR1.3
        """
        if not self.websocket_manager:
            logger.debug(
                "[broadcast] WebSocket manager not configured — skipping broadcast"
            )
            return

        try:
            message = {
                "type": "telemetry",
                "data": telemetry.model_dump(mode="json"),
            }
            self.websocket_manager.broadcast(message)
            logger.debug(
                f"[broadcast] Telemetry broadcast — sensor='{telemetry.sensorId}'"
            )
        except Exception as e:
            # Non-fatal: log and continue
            logger.error(
                f"[broadcast] Failed to broadcast telemetry for sensor "
                f"'{telemetry.sensorId}': {e}",
                exc_info=True,
            )

    # -----------------------------------------------------------------------
    # Utility
    # -----------------------------------------------------------------------

    def set_websocket_manager(self, websocket_manager):
        """
        Set or update the WebSocket manager for broadcasting.

        Args:
            websocket_manager: WebSocket manager instance
        """
        self.websocket_manager = websocket_manager
        self.alert_service.set_websocket_manager(websocket_manager)
        logger.info("WebSocket manager configured for TelemetryService")


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_telemetry_service: Optional[TelemetryService] = None


def get_telemetry_service(websocket_manager=None) -> TelemetryService:
    """
    Get singleton TelemetryService instance.

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
