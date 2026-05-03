"""
Alert Service for Smart City IoT Dashboard.

Enhanced alert engine providing:
1. Threshold-based alert generation (CO2, Noise, PM2.5, Humidity) with configurable
   thresholds and severity based on exceedance percentage.           (FR5.1, FR10.1, FR10.2)
2. Alert deduplication — 5-minute sliding window using an in-memory
   cache with Oracle fallback.                                       (FR5.4)
3. Predictive alerts — linear regression on last 20 readings to
   forecast 1 hour ahead; fires when confidence > 0.7 and predicted
   value exceeds threshold.                                          (FR5.2, FR3.5)
4. Anomaly detection — Z-score on last 100 readings (24 h window);
   fires when |Z| > 3.                                               (FR5.3, FR3.5)
5. Alert lifecycle management — acknowledge / resolve.               (FR5.5)
6. Oracle database storage.
7. WebSocket broadcasting.

Validates: FR5.1–FR5.5, FR3.5, FR10.1, FR10.2
"""

import logging
import uuid
import math
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from app.models import Alert, AlertType, AlertSeverity
from app.db.oracle_client import get_oracle_client
from app.db.mongodb_client import get_mongodb_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# 6.1 — Configurable Thresholds
# =============================================================================

ALERT_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "CO2": {
        "threshold": 1000.0,   # ppm
        "unit": "ppm",
        "ranges": {            # exceedance %  →  severity
            0:   AlertSeverity.LOW,
            25:  AlertSeverity.MEDIUM,
            50:  AlertSeverity.HIGH,
            100: AlertSeverity.CRITICAL,
        },
    },
    "Noise": {
        "threshold": 85.0,     # dB
        "unit": "dB",
        "ranges": {
            0:   AlertSeverity.LOW,
            15:  AlertSeverity.MEDIUM,
            30:  AlertSeverity.HIGH,
            60:  AlertSeverity.CRITICAL,
        },
    },
    "PM25": {
        "threshold": 55.0,     # µg/m³  (WHO 24h guideline ~15; VN standard ~50)
        "unit": "µg/m³",
        "ranges": {
            0:   AlertSeverity.LOW,
            30:  AlertSeverity.MEDIUM,
            80:  AlertSeverity.HIGH,
            150: AlertSeverity.CRITICAL,
        },
    },
    "Humidity": {
        "threshold": 90.0,     # %
        "unit": "%",
        "ranges": {
            0:   AlertSeverity.LOW,
            5:   AlertSeverity.MEDIUM,
            10:  AlertSeverity.HIGH,
            15:  AlertSeverity.CRITICAL,
        },
    },
}

# Alert deduplication window (5 minutes)
ALERT_DEDUPLICATION_WINDOW = timedelta(minutes=5)

# Predictive alert config
PREDICTIVE_READINGS_COUNT = 20       # last N readings for regression
PREDICTIVE_HORIZON_SECONDS = 3600    # predict 1 hour ahead
PREDICTIVE_CONFIDENCE_MIN = 0.7      # minimum R² to fire alert

# Anomaly detection config
ANOMALY_READINGS_COUNT = 100         # ~24 hours window
ANOMALY_ZSCORE_THRESHOLD = 3.0       # |Z| > 3 triggers alert


# =============================================================================
# Helpers
# =============================================================================

def _calc_exceedance_pct(value: float, threshold: float) -> float:
    """Return how far *value* exceeds *threshold* as a percentage of threshold."""
    if threshold == 0:
        return 100.0
    return max(0.0, ((value - threshold) / threshold) * 100)


def _severity_from_exceedance(pct: float, ranges: Dict[int, AlertSeverity]) -> AlertSeverity:
    """Map exceedance percentage to severity using the configured ranges."""
    severity = AlertSeverity.LOW
    for cutoff in sorted(ranges.keys()):
        if pct >= cutoff:
            severity = ranges[cutoff]
    return severity


# =============================================================================
# AlertService
# =============================================================================

class AlertService:
    """
    Alert service for threshold / predictive / anomaly alert generation,
    deduplication, lifecycle management, and broadcasting.
    """

    def __init__(self, websocket_manager=None):
        """
        Initialize alert service.

        Args:
            websocket_manager: Optional WebSocket manager for broadcasting alerts
        """
        self.oracle_client = get_oracle_client()
        self.mongodb_client = get_mongodb_client()
        self.websocket_manager = websocket_manager

        # In-memory deduplication cache: "sensorId:metricType:alertType" → last alert time
        self._recent_alerts_cache: Dict[str, datetime] = {}

        logger.info("Alert service initialized")

    # --------------------------------------------------------------------- #
    #  6.1 — Threshold Alert Checking                                        #
    # --------------------------------------------------------------------- #

    def check_threshold_alerts(
        self,
        sensor_id: str,
        location_id: str,
        metric_type: str,
        value: float,
        cluster_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Alert]:
        """
        Evaluate *value* against the configured threshold for *metric_type*.

        Steps:
        1. Look up threshold config
        2. Check if value exceeds threshold
        3. Calculate exceedance percentage and derive severity
        4. Check deduplication
        5. Persist alert in Oracle and broadcast

        Returns the created Alert or None.

        Validates: FR5.1, FR10.1, FR10.2
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        config = ALERT_THRESHOLDS.get(metric_type)
        if config is None:
            return None

        threshold = config["threshold"]
        if value <= threshold:
            return None

        # Severity from exceedance %
        pct = _calc_exceedance_pct(value, threshold)
        severity = _severity_from_exceedance(pct, config["ranges"])

        # Deduplication
        if self._is_duplicate_alert(sensor_id, metric_type, "THRESHOLD", timestamp):
            logger.debug(
                f"Threshold alert suppressed (duplicate) — "
                f"sensor={sensor_id}, metric={metric_type}"
            )
            return None

        message = (
            f"{metric_type} = {value:.1f} {config['unit']} exceeds threshold "
            f"{threshold:.1f} {config['unit']} by {pct:.0f}%"
        )

        alert = self._build_and_persist_alert(
            sensor_id=sensor_id,
            location_id=location_id,
            cluster_id=cluster_id,
            alert_type=AlertType.THRESHOLD,
            metric_type=metric_type,
            value=value,
            threshold=threshold,
            severity=severity,
            message=message,
            timestamp=timestamp,
        )
        return alert

    # --------------------------------------------------------------------- #
    #  6.2 — Alert Deduplication (5-minute window)                           #
    # --------------------------------------------------------------------- #

    def _is_duplicate_alert(
        self,
        sensor_id: str,
        metric_type: str,
        alert_type: str,
        current_time: datetime,
    ) -> bool:
        """
        Two-tier deduplication:
        1. In-memory cache — O(1) lookup
        2. Oracle query fallback — when cache misses (e.g. after restart)

        Validates: FR5.4
        """
        cache_key = f"{sensor_id}:{metric_type}:{alert_type}"

        # Tier 1 — memory cache
        if cache_key in self._recent_alerts_cache:
            last_time = self._recent_alerts_cache[cache_key]
            # Ensure both datetimes are comparable (handle naive vs aware)
            if _timedelta_aware_safe(current_time, last_time) < ALERT_DEDUPLICATION_WINDOW:
                return True

        # Tier 2 — database query
        return self._check_database_for_duplicate(
            sensor_id, metric_type, alert_type, current_time
        )

    def _check_database_for_duplicate(
        self,
        sensor_id: str,
        metric_type: str,
        alert_type: str,
        current_time: datetime,
    ) -> bool:
        """
        Query ALERTS table for recent alerts matching sensor + metric + type
        within the deduplication window.

        Validates: FR5.4
        """
        try:
            recent = self.oracle_client.get_recent_alerts_for_sensor(
                sensor_id=sensor_id,
                metric_type=metric_type,
                alert_type=alert_type,
                window_minutes=int(ALERT_DEDUPLICATION_WINDOW.total_seconds() / 60),
            )
            if recent:
                # Update cache
                cache_key = f"{sensor_id}:{metric_type}:{alert_type}"
                latest_time = recent[0].get("createdat") or recent[0].get("CREATEDAT")
                if isinstance(latest_time, datetime):
                    self._recent_alerts_cache[cache_key] = latest_time
                return True
            return False
        except Exception as e:
            logger.error(f"Dedup DB check failed: {e}")
            # Fail-open — prefer to create alert rather than miss one
            return False

    # --------------------------------------------------------------------- #
    #  6.3 — Predictive Alerts (Linear Regression)                           #
    # --------------------------------------------------------------------- #

    def check_predictive_alerts(
        self,
        sensor_id: str,
        location_id: str,
        metric_type: str,
        cluster_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Alert]:
        """
        Query last *PREDICTIVE_READINGS_COUNT* telemetry readings, fit a linear
        regression, and predict the value 1 hour ahead.

        Generates an alert when:
        - predicted value exceeds the configured threshold AND
        - R² confidence score > *PREDICTIVE_CONFIDENCE_MIN* (0.7)

        Validates: FR5.2, FR3.5
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        config = ALERT_THRESHOLDS.get(metric_type)
        if config is None:
            return None

        threshold = config["threshold"]

        # --- Query recent readings from MongoDB ---
        readings = self._get_recent_readings(
            sensor_id, metric_type, limit=PREDICTIVE_READINGS_COUNT
        )
        if len(readings) < 5:
            # Not enough data for meaningful regression
            return None

        # --- Linear regression ---
        try:
            from sklearn.linear_model import LinearRegression
            import numpy as np

            # Build X (seconds from first reading) and y (metric values)
            timestamps_epoch = []
            values = []
            for r in readings:
                ts = r.get("timestamp")
                val = r.get("value")
                if ts is not None and val is not None:
                    if isinstance(ts, datetime):
                        timestamps_epoch.append(ts.timestamp())
                    else:
                        timestamps_epoch.append(float(ts))
                    values.append(float(val))

            if len(values) < 5:
                return None

            base_epoch = timestamps_epoch[0]
            X = np.array([t - base_epoch for t in timestamps_epoch]).reshape(-1, 1)
            y = np.array(values)

            model = LinearRegression()
            model.fit(X, y)

            # Confidence — R²
            r2 = model.score(X, y)
            if r2 < PREDICTIVE_CONFIDENCE_MIN:
                logger.debug(
                    f"Predictive alert skipped — R²={r2:.3f} < {PREDICTIVE_CONFIDENCE_MIN} "
                    f"for sensor={sensor_id}, metric={metric_type}"
                )
                return None

            # Predict 1 hour ahead from last reading
            last_epoch = timestamps_epoch[-1]
            future_epoch = last_epoch + PREDICTIVE_HORIZON_SECONDS - base_epoch
            predicted_value = float(model.predict(np.array([[future_epoch]]))[0])

        except ImportError:
            logger.warning(
                "scikit-learn not installed — predictive alerts disabled. "
                "Install with: pip install scikit-learn numpy"
            )
            return None
        except Exception as e:
            logger.error(f"Predictive regression failed for sensor={sensor_id}: {e}")
            return None

        if predicted_value <= threshold:
            return None

        # Deduplication
        if self._is_duplicate_alert(sensor_id, metric_type, "PREDICTIVE", timestamp):
            return None

        message = (
            f"Predicted {metric_type} = {predicted_value:.1f} {config['unit']} "
            f"in 1 hour (threshold {threshold:.1f} {config['unit']}). "
            f"Confidence R²={r2:.2f}"
        )

        alert = self._build_and_persist_alert(
            sensor_id=sensor_id,
            location_id=location_id,
            cluster_id=cluster_id,
            alert_type=AlertType.PREDICTIVE,
            metric_type=metric_type,
            value=float(values[-1]),   # current value
            threshold=threshold,
            predicted_value=predicted_value,
            confidence_score=round(r2, 4),
            severity=AlertSeverity.MEDIUM,
            message=message,
            timestamp=timestamp,
        )
        return alert

    # --------------------------------------------------------------------- #
    #  6.4 — Anomaly Detection (Z-Score)                                     #
    # --------------------------------------------------------------------- #

    def detect_anomalies(
        self,
        sensor_id: str,
        location_id: str,
        metric_type: str,
        current_value: float,
        cluster_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Alert]:
        """
        Query last *ANOMALY_READINGS_COUNT* readings (~24 h), compute mean and
        std-dev, then calculate Z-score for *current_value*.

        Generates an alert when |Z-score| > *ANOMALY_ZSCORE_THRESHOLD* (3).

        Confidence is derived from Z-score: 1 - 1/(z²).

        Validates: FR5.3, FR3.5
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        config = ALERT_THRESHOLDS.get(metric_type)
        if config is None:
            return None

        readings = self._get_recent_readings(
            sensor_id, metric_type, limit=ANOMALY_READINGS_COUNT
        )

        if len(readings) < 10:
            return None  # insufficient data

        values = [float(r["value"]) for r in readings if r.get("value") is not None]
        if len(values) < 10:
            return None

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance) if variance > 0 else 0.0

        if std_dev == 0:
            return None  # all identical → no anomaly possible

        z_score = (current_value - mean) / std_dev

        if abs(z_score) <= ANOMALY_ZSCORE_THRESHOLD:
            return None

        # Confidence from Z-score: 1 - 1/z²  (ranges from 0 to ~1)
        confidence = max(0.0, min(1.0, 1.0 - 1.0 / (z_score ** 2)))

        # Deduplication
        if self._is_duplicate_alert(sensor_id, metric_type, "ANOMALY", timestamp):
            return None

        direction = "above" if z_score > 0 else "below"
        message = (
            f"Anomaly detected: {metric_type} = {current_value:.1f} {config['unit']} "
            f"is {abs(z_score):.1f}σ {direction} mean ({mean:.1f}). "
            f"Confidence={confidence:.2f}"
        )

        # Severity based on Z-score magnitude
        if abs(z_score) > 5:
            severity = AlertSeverity.CRITICAL
        elif abs(z_score) > 4:
            severity = AlertSeverity.HIGH
        else:
            severity = AlertSeverity.MEDIUM

        alert = self._build_and_persist_alert(
            sensor_id=sensor_id,
            location_id=location_id,
            cluster_id=cluster_id,
            alert_type=AlertType.ANOMALY,
            metric_type=metric_type,
            value=current_value,
            threshold=config["threshold"],
            confidence_score=round(confidence, 4),
            severity=severity,
            message=message,
            timestamp=timestamp,
        )
        return alert

    # --------------------------------------------------------------------- #
    #  6.5 — Alert Lifecycle Management                                      #
    # --------------------------------------------------------------------- #

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Transition alert status from OPEN → ACKNOWLEDGED.

        Updates AcknowledgedAt timestamp in Oracle.

        Validates: FR5.5
        """
        try:
            success = self.oracle_client.update_alert_status(
                alert_id=alert_id,
                new_status="ACKNOWLEDGED",
                acknowledged_at=datetime.now(timezone.utc),
            )
            if success:
                logger.info(f"Alert acknowledged: {alert_id}")
                self._broadcast_alert_update(alert_id, "ACKNOWLEDGED")
            else:
                logger.warning(f"Failed to acknowledge alert: {alert_id}")
            return success
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Transition alert status → RESOLVED.

        Updates ResolvedAt timestamp in Oracle.

        Validates: FR5.5
        """
        try:
            success = self.oracle_client.update_alert_status(
                alert_id=alert_id,
                new_status="RESOLVED",
                resolved_at=datetime.now(timezone.utc),
            )
            if success:
                logger.info(f"Alert resolved: {alert_id}")
                self._broadcast_alert_update(alert_id, "RESOLVED")
            else:
                logger.warning(f"Failed to resolve alert: {alert_id}")
            return success
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False

    # --------------------------------------------------------------------- #
    #  Internal helpers                                                       #
    # --------------------------------------------------------------------- #

    def _get_recent_readings(
        self,
        sensor_id: str,
        metric_type: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Query MongoDB for the last *limit* telemetry documents for a sensor,
        and extract the specified metric as {timestamp, value} dicts.
        """
        try:
            docs = self.mongodb_client.query_telemetry(
                sensor_id=sensor_id,
                limit=limit,
            )
            # Map the nested data.{metric} field to flat {timestamp, value}
            metric_key = metric_type.lower()
            # Metric key mapping
            key_map = {
                "co2": "co2",
                "noise": "noise",
                "temperature": "temperature",
                "pm25": "pm25",
                "humidity": "humidity",
            }
            field = key_map.get(metric_key, metric_key)

            results = []
            for doc in docs:
                ts = doc.get("timestamp")
                data = doc.get("data", {})
                val = data.get(field)
                if val is not None and ts is not None:
                    results.append({"timestamp": ts, "value": val})

            # Ensure chronological order (oldest first) for regression
            results.sort(
                key=lambda r: r["timestamp"]
                if isinstance(r["timestamp"], datetime)
                else datetime.min
            )
            return results

        except Exception as e:
            logger.error(
                f"Failed to query recent readings for sensor={sensor_id}, "
                f"metric={metric_type}: {e}"
            )
            return []

    def _build_and_persist_alert(
        self,
        sensor_id: str,
        location_id: str,
        alert_type: AlertType,
        metric_type: str,
        value: float,
        severity: AlertSeverity,
        message: str,
        timestamp: datetime,
        cluster_id: Optional[str] = None,
        threshold: Optional[float] = None,
        predicted_value: Optional[float] = None,
        confidence_score: Optional[float] = None,
    ) -> Optional[Alert]:
        """Build Alert object, persist to Oracle, broadcast, and return."""
        alert_id = str(uuid.uuid4())

        alert = Alert(
            alertId=alert_id,
            sensorId=sensor_id,
            locationId=location_id,
            clusterId=cluster_id,
            alertType=alert_type,
            metricType=metric_type,
            value=value,
            threshold=threshold,
            predictedValue=predicted_value,
            confidenceScore=confidence_score,
            severity=severity,
            status="OPEN",
            message=message,
            createdAt=timestamp,
        )

        # Persist to Oracle
        success = self.oracle_client.insert_alert_v2(alert)
        if not success:
            logger.error(
                f"Failed to persist alert to Oracle — "
                f"sensor={sensor_id}, metric={metric_type}, type={alert_type.value}"
            )
            return None

        logger.info(
            f"Alert created — id={alert_id}, type={alert_type.value}, "
            f"sensor={sensor_id}, metric={metric_type}, severity={severity.value}"
        )

        # Update dedup cache
        cache_key = f"{sensor_id}:{metric_type}:{alert_type.value}"
        self._recent_alerts_cache[cache_key] = timestamp

        # Broadcast
        self._broadcast_alert(alert)

        return alert

    def _broadcast_alert(self, alert: Alert):
        """Broadcast alert to WebSocket clients."""
        if self.websocket_manager:
            try:
                message = {
                    "type": "alert",
                    "data": alert.model_dump(mode='json'),
                }
                self.websocket_manager.broadcast(message)
                logger.debug(f"Alert broadcast — id={alert.alertId}")
            except Exception as e:
                logger.error(f"Error broadcasting alert: {e}", exc_info=True)

    def _broadcast_alert_update(self, alert_id: str, new_status: str):
        """Broadcast alert status change to WebSocket clients."""
        if self.websocket_manager:
            try:
                message = {
                    "type": "alert_update",
                    "data": {
                        "alertId": alert_id,
                        "status": new_status,
                        "updatedAt": datetime.now(timezone.utc).isoformat(),
                    },
                }
                self.websocket_manager.broadcast(message)
            except Exception as e:
                logger.error(f"Error broadcasting alert update: {e}", exc_info=True)

    # --------------------------------------------------------------------- #
    #  Public utilities                                                       #
    # --------------------------------------------------------------------- #

    def set_websocket_manager(self, websocket_manager):
        """Set or update the WebSocket manager for broadcasting."""
        self.websocket_manager = websocket_manager
        logger.info("WebSocket manager configured for alert service")

    def clear_cache(self):
        """Clear the in-memory alert deduplication cache."""
        self._recent_alerts_cache.clear()
        logger.info("Alert dedup cache cleared")


# =============================================================================
# Utility
# =============================================================================

def _timedelta_aware_safe(dt1: datetime, dt2: datetime) -> timedelta:
    """Compute dt1 - dt2 handling naive / aware mismatch gracefully."""
    # If one is aware and the other naive, strip tzinfo for comparison
    if dt1.tzinfo is not None and dt2.tzinfo is None:
        dt1 = dt1.replace(tzinfo=None)
    elif dt1.tzinfo is None and dt2.tzinfo is not None:
        dt2 = dt2.replace(tzinfo=None)
    return abs(dt1 - dt2)


# =============================================================================
# Singleton
# =============================================================================

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
