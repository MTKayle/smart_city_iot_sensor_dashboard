"""
Tests for Enhanced Alert Service (Task 6).

Tests cover:
- 6.1: Threshold alert checking with configurable thresholds and severity
- 6.2: Alert deduplication (5-minute window)
- 6.3: Predictive alerts (linear regression)
- 6.4: Anomaly detection (Z-score)
- 6.5: Alert lifecycle management (acknowledge, resolve)
"""

import math
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, PropertyMock

# ---------------------------------------------------------------------------
# We patch heavy dependencies so the tests run without Oracle/MongoDB/sklearn
# ---------------------------------------------------------------------------


class FakeOracleClient:
    """In-memory Oracle stub."""

    def __init__(self):
        self.alerts = {}  # alert_id -> alert dict
        self._insert_calls = []

    def insert_alert_v2(self, alert):
        self._insert_calls.append(alert)
        self.alerts[alert.alertId] = {
            "alertid": alert.alertId,
            "sensorid": alert.sensorId,
            "metrictype": alert.metricType,
            "alerttype": alert.alertType.value,
            "value": alert.value,
            "severity": alert.severity.value,
            "status": alert.status,
            "createdat": alert.createdAt,
        }
        return True

    def get_recent_alerts_for_sensor(self, sensor_id, metric_type, alert_type, window_minutes=5):
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=window_minutes)
        results = []
        for a in self.alerts.values():
            if (
                a["sensorid"] == sensor_id
                and a["metrictype"] == metric_type
                and a["alerttype"] == alert_type
            ):
                ts = a["createdat"]
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    results.append(a)
        results.sort(key=lambda x: x["createdat"], reverse=True)
        return results

    def update_alert_status(self, alert_id, new_status, acknowledged_at=None, resolved_at=None):
        if alert_id not in self.alerts:
            return False
        alert = self.alerts[alert_id]
        if new_status == "ACKNOWLEDGED" and alert["status"] != "OPEN":
            return False
        if new_status == "RESOLVED" and alert["status"] not in ("OPEN", "ACKNOWLEDGED"):
            return False
        alert["status"] = new_status
        return True

    def get_alert_by_id(self, alert_id):
        return self.alerts.get(alert_id)


class FakeMongoDBClient:
    """In-memory MongoDB stub."""

    def __init__(self, docs=None):
        self.docs = docs or []

    def query_telemetry(self, sensor_id, start_time=None, end_time=None, limit=100):
        filtered = [d for d in self.docs if d.get("sensorId") == sensor_id]
        filtered.sort(key=lambda d: d.get("timestamp", datetime.min), reverse=True)
        return filtered[:limit]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_service(oracle=None, mongo=None, ws=None):
    """Construct AlertService with fake backends."""
    from app.services.alert_service import AlertService

    svc = AlertService.__new__(AlertService)
    svc.oracle_client = oracle or FakeOracleClient()
    svc.mongodb_client = mongo or FakeMongoDBClient()
    svc.websocket_manager = ws
    svc._recent_alerts_cache = {}
    return svc


# ========================================================================== #
#  6.1 — Threshold Alert Checking                                            #
# ========================================================================== #


class TestThresholdAlerts:
    """Task 6.1: Configurable threshold alerts with severity calculation."""

    def test_co2_above_threshold_creates_alert(self):
        svc = _make_service()
        alert = svc.check_threshold_alerts(
            sensor_id="sen_01",
            location_id="ward_01",
            metric_type="CO2",
            value=1500.0,
        )
        assert alert is not None
        assert alert.alertType.value == "THRESHOLD"
        assert alert.metricType == "CO2"
        assert alert.value == 1500.0
        assert alert.threshold == 1000.0

    def test_co2_below_threshold_no_alert(self):
        svc = _make_service()
        alert = svc.check_threshold_alerts(
            sensor_id="sen_01",
            location_id="ward_01",
            metric_type="CO2",
            value=800.0,
        )
        assert alert is None

    def test_pm25_above_threshold_creates_alert(self):
        svc = _make_service()
        alert = svc.check_threshold_alerts(
            sensor_id="sen_01",
            location_id="ward_01",
            metric_type="PM25",
            value=80.0,
        )
        assert alert is not None
        assert alert.metricType == "PM25"
        assert alert.threshold == 55.0

    def test_humidity_above_threshold_creates_alert(self):
        svc = _make_service()
        alert = svc.check_threshold_alerts(
            sensor_id="sen_01",
            location_id="ward_01",
            metric_type="Humidity",
            value=95.0,
        )
        assert alert is not None
        assert alert.metricType == "Humidity"

    def test_noise_above_threshold_creates_alert(self):
        svc = _make_service()
        alert = svc.check_threshold_alerts(
            sensor_id="sen_01",
            location_id="ward_01",
            metric_type="Noise",
            value=100.0,
        )
        assert alert is not None
        assert alert.metricType == "Noise"

    def test_unknown_metric_no_alert(self):
        svc = _make_service()
        alert = svc.check_threshold_alerts(
            sensor_id="sen_01",
            location_id="ward_01",
            metric_type="UnknownMetric",
            value=9999.0,
        )
        assert alert is None

    def test_severity_scales_with_exceedance(self):
        """
        CO2 ranges: 0% → LOW, 25% → MEDIUM, 50% → HIGH, 100% → CRITICAL
        Threshold = 1000
        value = 2100 → exceedance = 110% → should be CRITICAL
        """
        svc = _make_service()
        alert = svc.check_threshold_alerts(
            sensor_id="sen_01",
            location_id="ward_01",
            metric_type="CO2",
            value=2100.0,
        )
        assert alert is not None
        assert alert.severity.value == "CRITICAL"

    def test_severity_low_for_small_exceedance(self):
        """value = 1050 → exceedance = 5% → LOW"""
        svc = _make_service()
        alert = svc.check_threshold_alerts(
            sensor_id="sen_01",
            location_id="ward_01",
            metric_type="CO2",
            value=1050.0,
        )
        assert alert is not None
        assert alert.severity.value == "LOW"

    def test_severity_medium_for_moderate_exceedance(self):
        """value = 1300 → exceedance = 30% → MEDIUM"""
        svc = _make_service()
        alert = svc.check_threshold_alerts(
            sensor_id="sen_01",
            location_id="ward_01",
            metric_type="CO2",
            value=1300.0,
        )
        assert alert is not None
        assert alert.severity.value == "MEDIUM"


# ========================================================================== #
#  6.2 — Alert Deduplication                                                 #
# ========================================================================== #


class TestDeduplication:
    """Task 6.2: Alert deduplication within 5-minute window."""

    def test_first_alert_passes(self):
        svc = _make_service()
        alert = svc.check_threshold_alerts(
            sensor_id="sen_dup",
            location_id="ward_01",
            metric_type="CO2",
            value=1500.0,
            timestamp=datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc),
        )
        assert alert is not None

    def test_second_alert_within_5min_suppressed(self):
        svc = _make_service()
        # First alert
        svc.check_threshold_alerts(
            sensor_id="sen_dup",
            location_id="ward_01",
            metric_type="CO2",
            value=1500.0,
            timestamp=datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc),
        )
        # Second alert 2 minutes later — should be suppressed
        alert2 = svc.check_threshold_alerts(
            sensor_id="sen_dup",
            location_id="ward_01",
            metric_type="CO2",
            value=1600.0,
            timestamp=datetime(2026, 5, 3, 10, 2, 0, tzinfo=timezone.utc),
        )
        assert alert2 is None

    def test_alert_after_5min_window_passes(self):
        svc = _make_service()
        # First alert
        svc.check_threshold_alerts(
            sensor_id="sen_dup",
            location_id="ward_01",
            metric_type="CO2",
            value=1500.0,
            timestamp=datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc),
        )
        # Second alert 6 minutes later — should pass
        alert2 = svc.check_threshold_alerts(
            sensor_id="sen_dup",
            location_id="ward_01",
            metric_type="CO2",
            value=1600.0,
            timestamp=datetime(2026, 5, 3, 10, 6, 0, tzinfo=timezone.utc),
        )
        assert alert2 is not None

    def test_different_metric_not_deduplicated(self):
        svc = _make_service()
        svc.check_threshold_alerts(
            sensor_id="sen_dup",
            location_id="ward_01",
            metric_type="CO2",
            value=1500.0,
            timestamp=datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc),
        )
        # Different metric — should still fire
        alert2 = svc.check_threshold_alerts(
            sensor_id="sen_dup",
            location_id="ward_01",
            metric_type="Noise",
            value=100.0,
            timestamp=datetime(2026, 5, 3, 10, 1, 0, tzinfo=timezone.utc),
        )
        assert alert2 is not None

    def test_different_sensor_not_deduplicated(self):
        svc = _make_service()
        svc.check_threshold_alerts(
            sensor_id="sen_A",
            location_id="ward_01",
            metric_type="CO2",
            value=1500.0,
            timestamp=datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc),
        )
        alert2 = svc.check_threshold_alerts(
            sensor_id="sen_B",
            location_id="ward_01",
            metric_type="CO2",
            value=1500.0,
            timestamp=datetime(2026, 5, 3, 10, 1, 0, tzinfo=timezone.utc),
        )
        assert alert2 is not None


# ========================================================================== #
#  6.3 — Predictive Alerts                                                   #
# ========================================================================== #


class TestPredictiveAlerts:
    """Task 6.3: Predictive alerts via linear regression."""

    def _build_trending_docs(self, sensor_id, metric_key, start_val, slope, count=20):
        """Create MongoDB docs with a clear upward trend."""
        base_time = datetime(2026, 5, 3, 9, 0, 0, tzinfo=timezone.utc)
        docs = []
        for i in range(count):
            ts = base_time + timedelta(minutes=i * 3)  # every 3 minutes
            val = start_val + slope * i
            docs.append({
                "sensorId": sensor_id,
                "timestamp": ts,
                "data": {metric_key: val},
            })
        return docs

    def test_predictive_alert_fires_on_uptrend(self):
        """
        CO2 trending from 800 → ~1370 over ~1 hour.
        1 hour beyond last reading should predict ~1940 (well above 1000).
        R² should be ~1.0 (perfect linear data).
        """
        docs = self._build_trending_docs("sen_pred", "co2", 800, 30, count=20)
        mongo = FakeMongoDBClient(docs)
        svc = _make_service(mongo=mongo)

        alert = svc.check_predictive_alerts(
            sensor_id="sen_pred",
            location_id="ward_01",
            metric_type="CO2",
        )
        assert alert is not None
        assert alert.alertType.value == "PREDICTIVE"
        assert alert.predictedValue is not None
        assert alert.predictedValue > 1000.0
        assert alert.confidenceScore is not None
        assert alert.confidenceScore >= 0.7

    def test_predictive_alert_no_fire_stable(self):
        """Stable CO2 around 400 → predicted value stays below threshold."""
        docs = self._build_trending_docs("sen_stable", "co2", 400, 0.5, count=20)
        mongo = FakeMongoDBClient(docs)
        svc = _make_service(mongo=mongo)

        alert = svc.check_predictive_alerts(
            sensor_id="sen_stable",
            location_id="ward_01",
            metric_type="CO2",
        )
        assert alert is None

    def test_predictive_alert_insufficient_data(self):
        """Less than 5 readings → no alert."""
        docs = self._build_trending_docs("sen_few", "co2", 800, 30, count=3)
        mongo = FakeMongoDBClient(docs)
        svc = _make_service(mongo=mongo)

        alert = svc.check_predictive_alerts(
            sensor_id="sen_few",
            location_id="ward_01",
            metric_type="CO2",
        )
        assert alert is None


# ========================================================================== #
#  6.4 — Anomaly Detection                                                   #
# ========================================================================== #


class TestAnomalyDetection:
    """Task 6.4: Anomaly detection via Z-score."""

    def _build_normal_docs(self, sensor_id, metric_key, mean, std, count=100):
        """Create docs clustered around a mean with specified std deviation."""
        import random
        random.seed(42)
        base_time = datetime(2026, 5, 2, 0, 0, 0, tzinfo=timezone.utc)
        docs = []
        for i in range(count):
            ts = base_time + timedelta(minutes=i * 15)  # every 15 min
            val = mean + random.gauss(0, std)
            docs.append({
                "sensorId": sensor_id,
                "timestamp": ts,
                "data": {metric_key: round(val, 2)},
            })
        return docs

    def test_anomaly_fires_on_extreme_value(self):
        """
        Normal CO2 around 450 ± 30.
        A current value of 600 → Z = (600-450)/30 = 5.0 → should fire.
        """
        docs = self._build_normal_docs("sen_anom", "co2", 450, 30, count=100)
        mongo = FakeMongoDBClient(docs)
        svc = _make_service(mongo=mongo)

        alert = svc.detect_anomalies(
            sensor_id="sen_anom",
            location_id="ward_01",
            metric_type="CO2",
            current_value=600.0,
        )
        assert alert is not None
        assert alert.alertType.value == "ANOMALY"
        assert alert.confidenceScore is not None
        assert alert.confidenceScore > 0.5

    def test_anomaly_no_fire_on_normal_value(self):
        """Current value 460 is within normal range — no alert."""
        docs = self._build_normal_docs("sen_norm", "co2", 450, 30, count=100)
        mongo = FakeMongoDBClient(docs)
        svc = _make_service(mongo=mongo)

        alert = svc.detect_anomalies(
            sensor_id="sen_norm",
            location_id="ward_01",
            metric_type="CO2",
            current_value=460.0,
        )
        assert alert is None

    def test_anomaly_insufficient_data(self):
        """Less than 10 readings → no anomaly check."""
        docs = self._build_normal_docs("sen_few_a", "co2", 450, 30, count=5)
        mongo = FakeMongoDBClient(docs)
        svc = _make_service(mongo=mongo)

        alert = svc.detect_anomalies(
            sensor_id="sen_few_a",
            location_id="ward_01",
            metric_type="CO2",
            current_value=600.0,
        )
        assert alert is None


# ========================================================================== #
#  6.5 — Alert Lifecycle Management                                          #
# ========================================================================== #


class TestAlertLifecycle:
    """Task 6.5: Acknowledge and resolve alerts."""

    def _create_open_alert(self, svc):
        """Helper — create a threshold alert to use in lifecycle tests."""
        alert = svc.check_threshold_alerts(
            sensor_id="sen_life",
            location_id="ward_01",
            metric_type="CO2",
            value=1500.0,
            timestamp=datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc),
        )
        assert alert is not None
        return alert

    def test_acknowledge_open_alert(self):
        svc = _make_service()
        alert = self._create_open_alert(svc)

        result = svc.acknowledge_alert(alert.alertId)
        assert result is True

        # Verify status changed
        stored = svc.oracle_client.get_alert_by_id(alert.alertId)
        assert stored["status"] == "ACKNOWLEDGED"

    def test_resolve_acknowledged_alert(self):
        svc = _make_service()
        alert = self._create_open_alert(svc)

        svc.acknowledge_alert(alert.alertId)
        result = svc.resolve_alert(alert.alertId)
        assert result is True

        stored = svc.oracle_client.get_alert_by_id(alert.alertId)
        assert stored["status"] == "RESOLVED"

    def test_resolve_open_alert_directly(self):
        svc = _make_service()
        alert = self._create_open_alert(svc)

        result = svc.resolve_alert(alert.alertId)
        assert result is True

        stored = svc.oracle_client.get_alert_by_id(alert.alertId)
        assert stored["status"] == "RESOLVED"

    def test_acknowledge_nonexistent_alert(self):
        svc = _make_service()
        result = svc.acknowledge_alert("nonexistent_id")
        assert result is False

    def test_resolve_already_resolved_alert(self):
        svc = _make_service()
        alert = self._create_open_alert(svc)
        svc.resolve_alert(alert.alertId)

        # Second resolve should fail
        result = svc.resolve_alert(alert.alertId)
        assert result is False


# ========================================================================== #
#  WebSocket broadcast tests                                                  #
# ========================================================================== #


class TestWebSocketBroadcast:
    """Verify alerts are broadcast to WebSocket clients."""

    def test_threshold_alert_broadcasts(self):
        ws = MagicMock()
        svc = _make_service(ws=ws)

        svc.check_threshold_alerts(
            sensor_id="sen_ws",
            location_id="ward_01",
            metric_type="CO2",
            value=1500.0,
        )
        ws.broadcast.assert_called_once()
        call_args = ws.broadcast.call_args[0][0]
        assert call_args["type"] == "alert"

    def test_lifecycle_broadcasts_update(self):
        ws = MagicMock()
        svc = _make_service(ws=ws)

        alert = svc.check_threshold_alerts(
            sensor_id="sen_ws2",
            location_id="ward_01",
            metric_type="CO2",
            value=1500.0,
        )
        ws.reset_mock()

        svc.acknowledge_alert(alert.alertId)
        ws.broadcast.assert_called_once()
        call_args = ws.broadcast.call_args[0][0]
        assert call_args["type"] == "alert_update"
        assert call_args["data"]["status"] == "ACKNOWLEDGED"


# ========================================================================== #
#  Helper function tests                                                      #
# ========================================================================== #


class TestHelpers:
    """Test internal utility functions."""

    def test_exceedance_pct_calculation(self):
        from app.services.alert_service import _calc_exceedance_pct
        assert _calc_exceedance_pct(1500, 1000) == 50.0
        assert _calc_exceedance_pct(1000, 1000) == 0.0
        assert _calc_exceedance_pct(800, 1000) == 0.0  # below threshold

    def test_severity_from_exceedance(self):
        from app.services.alert_service import (
            _severity_from_exceedance,
            ALERT_THRESHOLDS,
            AlertSeverity,
        )
        ranges = ALERT_THRESHOLDS["CO2"]["ranges"]
        assert _severity_from_exceedance(0, ranges) == AlertSeverity.LOW
        assert _severity_from_exceedance(30, ranges) == AlertSeverity.MEDIUM
        assert _severity_from_exceedance(60, ranges) == AlertSeverity.HIGH
        assert _severity_from_exceedance(110, ranges) == AlertSeverity.CRITICAL

    def test_timedelta_aware_safe(self):
        from app.services.alert_service import _timedelta_aware_safe
        dt_aware = datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc)
        dt_naive = datetime(2026, 5, 3, 10, 0, 30)
        result = _timedelta_aware_safe(dt_aware, dt_naive)
        assert result == timedelta(seconds=30)
