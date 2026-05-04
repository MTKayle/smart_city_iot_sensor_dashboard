"""
Tests for Task 9 — Spatial Query Utilities.

Covers:
- 9.1  haversine_distance() — known coordinates, edge cases
- 9.2  find_nearby_sensors() — geo query + Oracle enrichment + distance sort
- 9.3  identify_hotspots()  — grid aggregation, threshold filter, sort order
"""

import math
import pytest
from unittest.mock import MagicMock, Mock


# ===========================================================================
# 9.1 — Haversine distance
# ===========================================================================

class TestHaversineDistance:
    """Task 9.1: Haversine distance calculation."""

    def test_same_point_zero(self):
        from app.utils.spatial import haversine_distance
        assert haversine_distance(10.0, 106.0, 10.0, 106.0) == 0.0

    def test_north_pole_to_equator(self):
        """Quarter of Earth circumference ≈ 10 007 km."""
        from app.utils.spatial import haversine_distance
        dist = haversine_distance(90.0, 0.0, 0.0, 0.0)
        assert abs(dist - 10007.5) < 10   # ± 10 km tolerance

    def test_equatorial_one_degree_longitude(self):
        """1° longitude at equator ≈ 111.32 km."""
        from app.utils.spatial import haversine_distance
        dist = haversine_distance(0.0, 0.0, 0.0, 1.0)
        assert abs(dist - 111.32) < 0.5

    def test_known_hcmc_points(self):
        """Two well-known HCM City locations separated by ~8.6 km."""
        from app.utils.spatial import haversine_distance
        # Ben Thanh Market  → Tan Son Nhat Airport
        dist = haversine_distance(10.7726, 106.6980, 10.8185, 106.6546)
        assert 5.0 < dist < 12.0

    def test_symmetry(self):
        """Distance A→B == distance B→A."""
        from app.utils.spatial import haversine_distance
        d1 = haversine_distance(10.5, 106.5, 10.8, 106.9)
        d2 = haversine_distance(10.8, 106.9, 10.5, 106.5)
        assert abs(d1 - d2) < 1e-9

    def test_meters_wrapper(self):
        from app.utils.spatial import haversine_distance, haversine_distance_meters
        km  = haversine_distance(10.0, 106.0, 10.1, 106.0)
        m   = haversine_distance_meters(10.0, 106.0, 10.1, 106.0)
        assert abs(m - km * 1000) < 1e-6

    def test_invalid_latitude_raises(self):
        from app.utils.spatial import haversine_distance
        with pytest.raises(ValueError, match="Latitude"):
            haversine_distance(91.0, 0.0, 0.0, 0.0)

    def test_invalid_longitude_raises(self):
        from app.utils.spatial import haversine_distance
        with pytest.raises(ValueError, match="Longitude"):
            haversine_distance(0.0, 181.0, 0.0, 0.0)

    def test_negative_coordinates(self):
        """Southern hemisphere coordinates work correctly."""
        from app.utils.spatial import haversine_distance
        dist = haversine_distance(-33.8688, 151.2093, -37.8136, 144.9631)  # SYD→MEL
        assert 700 < dist < 800

    def test_result_always_non_negative(self):
        from app.utils.spatial import haversine_distance
        assert haversine_distance(-10.0, -50.0, 10.0, 50.0) >= 0.0

    def test_distance_in_km_not_meters(self):
        """1 degree lat ≈ 111 km — not 111 000."""
        from app.utils.spatial import haversine_distance
        dist = haversine_distance(0.0, 0.0, 1.0, 0.0)
        assert 110 < dist < 113


# ===========================================================================
# 9.2 — find_nearby_sensors
# ===========================================================================

def _geo_doc(sensor_id, lat, lng, co2=400.0, pm25=20.0):
    """Build a MongoDB geo telemetry document."""
    return {
        "sensorId": sensor_id,
        "locationId": "ward_test",
        "clusterId": "cluster_01",
        "location": {"type": "Point", "coordinates": [lng, lat]},
        "timestamp": "2026-05-03T10:00:00Z",
        "data": {"co2": co2, "pm25": pm25},
    }


class FakeMongo:
    def __init__(self, docs):
        self._docs = docs

    def find_nearby_sensors(self, longitude, latitude, max_distance_meters, limit=50):
        return self._docs[:limit]


class FakeOracle:
    def __init__(self, sensors=None):
        self._sensors = sensors or {}

    def get_sensor(self, sensor_id):
        return self._sensors.get(sensor_id)

    def get_sensors(self, location_id=None):
        return list(self._sensors.values())


class TestFindNearbySensors:
    """Task 9.2: find_nearby_sensors()."""

    def test_empty_result_when_no_docs(self):
        from app.utils.spatial import find_nearby_sensors
        result = find_nearby_sensors(
            10.77, 106.70, radius_km=1.0,
            mongodb_client=FakeMongo([]),
            oracle_client=FakeOracle(),
        )
        assert result == []

    def test_returns_sensor_entries(self):
        from app.utils.spatial import find_nearby_sensors
        docs = [_geo_doc("s1", 10.77, 106.70)]
        result = find_nearby_sensors(
            10.77, 106.70, radius_km=5.0,
            mongodb_client=FakeMongo(docs),
            oracle_client=FakeOracle(),
        )
        assert len(result) == 1
        assert result[0]["sensorId"] == "s1"

    def test_distance_km_computed(self):
        from app.utils.spatial import find_nearby_sensors
        docs = [_geo_doc("s2", 10.78, 106.70)]
        result = find_nearby_sensors(
            10.77, 106.70, radius_km=5.0,
            mongodb_client=FakeMongo(docs),
            oracle_client=FakeOracle(),
        )
        assert result[0]["distance_km"] is not None
        assert result[0]["distance_km"] > 0

    def test_deduplicates_by_sensor_id(self):
        """Multiple docs for same sensor → only first kept."""
        from app.utils.spatial import find_nearby_sensors
        docs = [
            _geo_doc("s3", 10.77, 106.70),
            _geo_doc("s3", 10.77, 106.70),
        ]
        result = find_nearby_sensors(
            10.77, 106.70, radius_km=5.0,
            mongodb_client=FakeMongo(docs),
            oracle_client=FakeOracle(),
        )
        assert len(result) == 1

    def test_sorted_by_distance_ascending(self):
        """Closest sensor appears first."""
        from app.utils.spatial import find_nearby_sensors
        docs = [
            _geo_doc("far",  10.80, 106.70),   # farther
            _geo_doc("near", 10.771, 106.70),  # closer
        ]
        result = find_nearby_sensors(
            10.77, 106.70, radius_km=50.0,
            mongodb_client=FakeMongo(docs),
            oracle_client=FakeOracle(),
        )
        assert result[0]["sensorId"] == "near"
        assert result[0]["distance_km"] < result[1]["distance_km"]

    def test_oracle_enrichment_included(self):
        """Oracle sensor data is merged into result."""
        from app.utils.spatial import find_nearby_sensors
        docs = [_geo_doc("s4", 10.77, 106.70)]
        oracle_sensors = {"s4": {"sensorid": "s4", "sensormodel": "IoT-v2",
                                  "locationname": "Ward 1", "status": "Active",
                                  "locationid": "ward_01", "clusterid": "c1"}}
        result = find_nearby_sensors(
            10.77, 106.70, radius_km=5.0,
            mongodb_client=FakeMongo(docs),
            oracle_client=FakeOracle(oracle_sensors),
        )
        assert result[0]["sensorModel"] == "IoT-v2"
        assert result[0]["locationName"] == "Ward 1"
        assert result[0]["status"] == "Active"

    def test_mongo_error_returns_empty(self):
        """MongoDB failure → return [] gracefully."""
        from app.utils.spatial import find_nearby_sensors
        bad_mongo = Mock()
        bad_mongo.find_nearby_sensors.side_effect = RuntimeError("conn refused")
        result = find_nearby_sensors(
            10.77, 106.70, radius_km=5.0,
            mongodb_client=bad_mongo,
            oracle_client=FakeOracle(),
        )
        assert result == []

    def test_latest_telemetry_nested(self):
        """latest_telemetry field contains timestamp and data."""
        from app.utils.spatial import find_nearby_sensors
        docs = [_geo_doc("s5", 10.77, 106.70, co2=555.0)]
        result = find_nearby_sensors(
            10.77, 106.70, radius_km=5.0,
            mongodb_client=FakeMongo(docs),
            oracle_client=FakeOracle(),
        )
        lt = result[0]["latest_telemetry"]
        assert "data" in lt
        assert lt["data"]["co2"] == 555.0


# ===========================================================================
# 9.3 — Hotspot detection
# ===========================================================================

def _geo_doc_for_hotspot(sensor_id, lat, lng, metric, value):
    """Build a minimal telemetry document for hotspot tests."""
    return {
        "sensorId": sensor_id,
        "location": {"type": "Point", "coordinates": [lng, lat]},
        "data": {metric: value},
    }


class FakeMongoHotspot:
    def __init__(self, docs_by_sensor):
        self._docs = docs_by_sensor

    def query_telemetry(self, sensor_id, limit=100, **kw):
        return self._docs.get(sensor_id, [])


class FakeOracleHotspot:
    def __init__(self, sensor_ids):
        self._sensors = [{"sensorid": sid} for sid in sensor_ids]

    def get_sensors(self, location_id=None):
        return self._sensors


class TestIdentifyHotspots:
    """Task 9.3: identify_hotspots()."""

    def _run(self, metric, docs_by_sensor, sensor_ids, threshold=None, resolution=0.1):
        from app.utils.spatial import identify_hotspots
        return identify_hotspots(
            metric_type=metric,
            threshold=threshold,
            grid_resolution_km=resolution,
            mongodb_client=FakeMongoHotspot(docs_by_sensor),
            oracle_client=FakeOracleHotspot(sensor_ids),
        )

    def test_empty_returns_empty_list(self):
        result = self._run("co2", {}, [])
        assert result == []

    def test_single_cell_returned(self):
        docs = {
            "s1": [_geo_doc_for_hotspot("s1", 10.77, 106.70, "co2", 800.0)]
        }
        result = self._run("co2", docs, ["s1"])
        assert len(result) == 1
        assert result[0]["avg_value"] == 800.0
        assert result[0]["metric_type"] == "co2"

    def test_sorted_by_avg_value_descending(self):
        docs = {
            "s1": [_geo_doc_for_hotspot("s1", 10.77, 106.70, "co2", 300.0)],
            "s2": [_geo_doc_for_hotspot("s2", 10.90, 106.90, "co2", 900.0)],
        }
        result = self._run("co2", docs, ["s1", "s2"])
        # Highest-pollution cell first
        assert result[0]["avg_value"] >= result[-1]["avg_value"]

    def test_threshold_filter_applied(self):
        """Cells with avg ≤ threshold are excluded."""
        docs = {
            "s1": [_geo_doc_for_hotspot("s1", 10.77, 106.70, "co2", 500.0)],
            "s2": [_geo_doc_for_hotspot("s2", 10.90, 106.90, "co2", 1500.0)],
        }
        result = self._run("co2", docs, ["s1", "s2"], threshold=1000.0)
        assert all(h["avg_value"] > 1000.0 for h in result)
        assert len(result) == 1

    def test_multiple_sensors_same_cell_aggregated(self):
        """Two sensors in the same 1-km cell → one cell with pooled average."""
        # Both at essentially the same location
        docs = {
            "s1": [_geo_doc_for_hotspot("s1", 10.7701, 106.7001, "pm25", 40.0)],
            "s2": [_geo_doc_for_hotspot("s2", 10.7702, 106.7002, "pm25", 60.0)],
        }
        result = self._run("pm25", docs, ["s1", "s2"], resolution=1.0)
        # They should land in the same cell
        assert len(result) == 1
        assert result[0]["avg_value"] == 50.0
        assert set(result[0]["sensor_ids"]) == {"s1", "s2"}

    def test_missing_metric_docs_excluded(self):
        """Docs without the requested metric field are silently skipped."""
        docs = {
            "s1": [
                {"sensorId": "s1", "location": {"type": "Point", "coordinates": [106.70, 10.77]}, "data": {"noise": 80.0}},
            ]
        }
        result = self._run("co2", docs, ["s1"])
        assert result == []

    def test_result_has_required_keys(self):
        docs = {
            "s1": [_geo_doc_for_hotspot("s1", 10.77, 106.70, "humidity", 92.0)]
        }
        result = self._run("humidity", docs, ["s1"])
        assert len(result) == 1
        h = result[0]
        for key in ("cell_id", "center_lat", "center_lng", "avg_value",
                    "reading_count", "sensor_ids", "metric_type"):
            assert key in h, f"Missing key: {key}"

    def test_reading_count_correct(self):
        docs = {
            "s1": [
                _geo_doc_for_hotspot("s1", 10.77, 106.70, "noise", 70.0),
                _geo_doc_for_hotspot("s1", 10.77, 106.70, "noise", 80.0),
                _geo_doc_for_hotspot("s1", 10.77, 106.70, "noise", 90.0),
            ]
        }
        result = self._run("noise", docs, ["s1"])
        assert result[0]["reading_count"] == 3

    def test_oracle_error_returns_empty(self):
        from app.utils.spatial import identify_hotspots
        bad_oracle = Mock()
        bad_oracle.get_sensors.side_effect = RuntimeError("DB down")
        result = identify_hotspots(
            metric_type="co2",
            mongodb_client=FakeMongoHotspot({}),
            oracle_client=bad_oracle,
        )
        assert result == []
