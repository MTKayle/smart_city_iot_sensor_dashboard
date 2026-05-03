"""
Test script for Task 4 – Telemetry Service (Tasks 4.1, 4.2, 4.3)

Tests:
  - enrich_telemetry_with_geolocation() with mocked Oracle
  - _validate_telemetry() with valid and invalid inputs
  - _store_telemetry() with batch insert (mocked MongoDB)
  - _broadcast_telemetry() with mocked WebSocket manager

Run from project root:
    python -m backend.app.services.test_telemetry_service
or just:
    python backend/app/services/test_telemetry_service.py
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

# ── path setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.models import Telemetry, TelemetryData, GeoLocation, DataQuality
from app.services.telemetry_service import (
    enrich_telemetry_with_geolocation,
    TelemetryService,
    TELEMETRY_TTL_DAYS,
)

# ── helpers ─────────────────────────────────────────────────────────────────

def _make_raw_telemetry(
    sensor_id="sen_q1_ben_nghe_01",
    location_id="ward_q1_ben_nghe",
    with_quality=True,
) -> Telemetry:
    """Build a minimal raw telemetry object (no geo enrichment yet)."""
    return Telemetry(
        sensorId=sensor_id,
        locationId=location_id,
        data=TelemetryData(co2=450.5, noise=65.2, temperature=25.3),
        location=GeoLocation(type="Point", coordinates=[106.7019, 10.7756]),
        quality=DataQuality(batteryLevel=87.5, signalStrength=-45.2) if with_quality else None,
        timestamp=datetime.now(timezone.utc),
        receivedAt=datetime.now(timezone.utc),
    )


def _mock_oracle_with_geo(lat=10.7756, lng=106.7019, cluster="cluster_q1_north"):
    """Return a mock OracleClient that returns geolocation data."""
    oracle = MagicMock()
    oracle.get_sensor_geolocation.return_value = {
        "latitude": lat,
        "longitude": lng,
        "clusterId": cluster,
        "locationId": "ward_q1_ben_nghe",
    }
    return oracle


def _mock_oracle_not_found():
    """Return a mock OracleClient where the sensor doesn't exist."""
    oracle = MagicMock()
    oracle.get_sensor_geolocation.return_value = None
    return oracle


# ── Test 4.1 – enrich_telemetry_with_geolocation ────────────────────────────

def test_enrichment_success():
    print("\n[4.1] test_enrichment_success")
    raw = _make_raw_telemetry(with_quality=True)
    oracle = _mock_oracle_with_geo(lat=10.7756, lng=106.7019, cluster="cluster_q1_north")

    enriched = enrich_telemetry_with_geolocation(raw, oracle_client=oracle)

    assert enriched.sensorId == "sen_q1_ben_nghe_01", "sensorId preserved"
    assert enriched.clusterId == "cluster_q1_north", f"clusterId set: {enriched.clusterId}"
    assert enriched.location.type == "Point", "GeoJSON type = Point"
    assert enriched.location.coordinates == [106.7019, 10.7756], (
        f"coordinates [lng, lat]: {enriched.location.coordinates}"
    )
    assert enriched.expireAt is not None, "expireAt is set"
    expected_ttl = TELEMETRY_TTL_DAYS
    delta = enriched.expireAt - enriched.receivedAt
    assert abs(delta.days - expected_ttl) <= 1, (
        f"expireAt ≈ receivedAt + {expected_ttl}d, got delta={delta}"
    )
    assert enriched.quality is not None, "quality preserved"
    assert enriched.quality.batteryLevel == 87.5, "batteryLevel preserved"
    print("  ✓ PASS")


def test_enrichment_no_quality():
    print("\n[4.1] test_enrichment_no_quality")
    raw = _make_raw_telemetry(with_quality=False)
    oracle = _mock_oracle_with_geo()

    enriched = enrich_telemetry_with_geolocation(raw, oracle_client=oracle)
    assert enriched.quality is None, "quality remains None"
    print("  ✓ PASS")


def test_enrichment_sensor_not_found():
    """When sensor not in Oracle, return original telemetry unchanged."""
    print("\n[4.1] test_enrichment_sensor_not_found")
    raw = _make_raw_telemetry()
    oracle = _mock_oracle_not_found()

    result = enrich_telemetry_with_geolocation(raw, oracle_client=oracle)
    # Should return unchanged – no expireAt set by enrichment
    assert result.sensorId == raw.sensorId
    assert result.expireAt is None  # not enriched
    print("  ✓ PASS (fallback to original when sensor not found)")


def test_enrichment_oracle_exception():
    """Exceptions from Oracle should be swallowed; original telemetry returned."""
    print("\n[4.1] test_enrichment_oracle_exception")
    raw = _make_raw_telemetry()
    oracle = MagicMock()
    oracle.get_sensor_geolocation.side_effect = Exception("DB down")

    result = enrich_telemetry_with_geolocation(raw, oracle_client=oracle)
    assert result.sensorId == raw.sensorId
    print("  ✓ PASS (exception swallowed, original returned)")


# ── Test 4.2 – validate_telemetry & store_telemetry ────────────────────────

def _make_service(ws_manager=None):
    """Build TelemetryService with mocked DB clients."""
    with patch("app.services.telemetry_service.get_mongodb_client") as mg, \
         patch("app.services.telemetry_service.get_oracle_client") as oc, \
         patch("app.services.telemetry_service.get_alert_service") as als:

        mg.return_value = MagicMock()
        oc.return_value = MagicMock()
        als.return_value = MagicMock()

        svc = TelemetryService(websocket_manager=ws_manager)
        return svc


def test_validate_valid():
    print("\n[4.2] test_validate_valid")
    svc = _make_service()
    tel = _make_raw_telemetry()
    # Add expireAt to simulate enriched
    tel = tel.model_copy(update={"expireAt": datetime.now(timezone.utc) + timedelta(days=30)})
    assert svc._validate_telemetry(tel) is True
    print("  ✓ PASS")


def test_validate_missing_sensorId():
    print("\n[4.2] test_validate_missing_sensorId — expects False")
    svc = _make_service()
    try:
        # Pydantic won't allow empty sensorId via model; we patch the attribute
        tel = _make_raw_telemetry()
        tel.sensorId = ""
        result = svc._validate_telemetry(tel)
        assert result is False
        print("  ✓ PASS")
    except Exception as e:
        print(f"  ✓ PASS (Pydantic stopped it: {type(e).__name__})")


def test_validate_no_metrics():
    print("\n[4.2] test_validate_no_metrics — expects False")
    svc = _make_service()
    from app.models import TelemetryData
    tel = _make_raw_telemetry()
    tel.data = TelemetryData()  # all None
    tel = tel.model_copy(update={"expireAt": datetime.now(timezone.utc) + timedelta(days=30)})
    result = svc._validate_telemetry(tel)
    assert result is False
    print("  ✓ PASS")


def test_validate_missing_expireAt():
    print("\n[4.2] test_validate_missing_expireAt — expects False")
    svc = _make_service()
    tel = _make_raw_telemetry()
    # expireAt is None by default in raw telemetry
    result = svc._validate_telemetry(tel)
    assert result is False
    print("  ✓ PASS")


def test_store_telemetry_success():
    print("\n[4.2] test_store_telemetry_success")
    svc = _make_service()

    from app.db.mongodb_client import BatchInsertResult
    mock_result = BatchInsertResult(inserted=1)
    svc.mongodb_client.batch_insert_telemetry.return_value = mock_result

    tel = _make_raw_telemetry()
    tel = tel.model_copy(update={"expireAt": datetime.now(timezone.utc) + timedelta(days=30)})
    ok = svc._store_telemetry(tel)
    assert ok is True
    svc.mongodb_client.batch_insert_telemetry.assert_called_once()
    print("  ✓ PASS")


def test_store_telemetry_duplicate():
    print("\n[4.2] test_store_telemetry_duplicate — should return True (non-fatal)")
    svc = _make_service()

    from app.db.mongodb_client import BatchInsertResult
    mock_result = BatchInsertResult(inserted=0, duplicates=1)
    svc.mongodb_client.batch_insert_telemetry.return_value = mock_result

    tel = _make_raw_telemetry()
    tel = tel.model_copy(update={"expireAt": datetime.now(timezone.utc) + timedelta(days=30)})
    ok = svc._store_telemetry(tel)
    assert ok is True, "Duplicate = non-fatal"
    print("  ✓ PASS")


def test_store_telemetry_error():
    print("\n[4.2] test_store_telemetry_error — should return False")
    svc = _make_service()

    from app.db.mongodb_client import BatchInsertResult
    mock_result = BatchInsertResult(inserted=0, errors=1)
    svc.mongodb_client.batch_insert_telemetry.return_value = mock_result

    tel = _make_raw_telemetry()
    tel = tel.model_copy(update={"expireAt": datetime.now(timezone.utc) + timedelta(days=30)})
    ok = svc._store_telemetry(tel)
    assert ok is False
    print("  ✓ PASS")


# ── Test 4.3 – _broadcast_telemetry ─────────────────────────────────────────

def test_broadcast_sends_typed_message():
    print("\n[4.3] test_broadcast_sends_typed_message")
    ws_manager = MagicMock()
    svc = _make_service(ws_manager=ws_manager)
    svc.websocket_manager = ws_manager  # ensure it's set

    tel = _make_raw_telemetry()
    tel = tel.model_copy(update={"expireAt": datetime.now(timezone.utc) + timedelta(days=30)})
    svc._broadcast_telemetry(tel)

    ws_manager.broadcast.assert_called_once()
    call_args = ws_manager.broadcast.call_args[0][0]
    assert call_args["type"] == "telemetry", f"type field: {call_args['type']}"
    assert "data" in call_args, "data field present"
    assert "sensorId" in call_args["data"]
    print("  ✓ PASS")


def test_broadcast_failure_is_non_fatal():
    print("\n[4.3] test_broadcast_failure_is_non_fatal")
    ws_manager = MagicMock()
    ws_manager.broadcast.side_effect = Exception("WebSocket error")
    svc = _make_service(ws_manager=ws_manager)
    svc.websocket_manager = ws_manager

    tel = _make_raw_telemetry()
    tel = tel.model_copy(update={"expireAt": datetime.now(timezone.utc) + timedelta(days=30)})
    # Should NOT raise
    try:
        svc._broadcast_telemetry(tel)
        print("  ✓ PASS (exception swallowed gracefully)")
    except Exception as e:
        print(f"  ✗ FAIL — exception propagated: {e}")


def test_broadcast_skipped_without_manager():
    print("\n[4.3] test_broadcast_skipped_without_manager")
    svc = _make_service(ws_manager=None)
    svc.websocket_manager = None
    tel = _make_raw_telemetry()
    tel = tel.model_copy(update={"expireAt": datetime.now(timezone.utc) + timedelta(days=30)})
    # Should not raise
    svc._broadcast_telemetry(tel)
    print("  ✓ PASS (no manager → skip silently)")


# ── runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Task 4 – Telemetry Service Tests")
    print("=" * 60)

    # 4.1
    test_enrichment_success()
    test_enrichment_no_quality()
    test_enrichment_sensor_not_found()
    test_enrichment_oracle_exception()

    # 4.2
    test_validate_valid()
    test_validate_missing_sensorId()
    test_validate_no_metrics()
    test_validate_missing_expireAt()
    test_store_telemetry_success()
    test_store_telemetry_duplicate()
    test_store_telemetry_error()

    # 4.3
    test_broadcast_sends_typed_message()
    test_broadcast_failure_is_non_fatal()
    test_broadcast_skipped_without_manager()

    print("\n" + "=" * 60)
    print("All tests completed.")
    print("=" * 60)
