"""
Tests for Task 7 — Analytics Service Enhancements.

Covers:
- 7.1  AQI calculation utility (all 6 EPA ranges)
- 7.2  Updated calculate_moving_average() — PM2.5, Humidity, AQI, Clean Score
- 7.3  calculate_cluster_analytics() — cluster-level aggregation
"""

import math
import pytest
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from unittest.mock import MagicMock


# ===========================================================================
# Stubs / helpers
# ===========================================================================

def _make_doc(sensor_id: str, ts: datetime, **metrics) -> dict:
    """Build a minimal telemetry MongoDB document (nested 'data' layout)."""
    return {
        "sensorId": sensor_id,
        "timestamp": ts,
        "data": {k: v for k, v in metrics.items() if v is not None},
    }


BASE_TS = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)


class FakeMongoDBClient:
    """In-memory MongoDB stub (returns docs per sensor_id)."""

    def __init__(self, docs: List[dict] = None):
        self._docs = docs or []

    def query_telemetry(self, sensor_id, start_time=None, end_time=None, limit=100):
        filtered = [d for d in self._docs if d.get("sensorId") == sensor_id]
        filtered.sort(key=lambda d: d.get("timestamp", datetime.min), reverse=True)
        return filtered[:limit]


class FakeOracleClient:
    """Minimal Oracle stub for analytics tests."""

    def __init__(self, sensors_by_cluster=None):
        # sensors_by_cluster: dict cluster_id -> list of sensor dicts
        self._sensors_by_cluster = sensors_by_cluster or {}
        self._summary_calls = []

    def get_cluster(self, cluster_id):
        return {
            "clusterid": cluster_id,
            "clustername": f"Test Cluster {cluster_id}",
            "locationid": "ward_test",
        }

    def get_sensors_by_cluster(self, cluster_id, status=None):
        return self._sensors_by_cluster.get(cluster_id, [])

    def insert_or_update_telemetry_summary(self, **kwargs):
        self._summary_calls.append(kwargs)
        return True


def _make_analytics_service(docs=None, sensors_by_cluster=None):
    """Construct an AnalyticsService with fake dependencies (no DB needed)."""
    from app.services.analytics_service import AnalyticsService

    svc = AnalyticsService.__new__(AnalyticsService)
    svc.mongodb_client = FakeMongoDBClient(docs)
    svc.oracle_client  = FakeOracleClient(sensors_by_cluster)
    return svc


# ===========================================================================
# 7.1 — AQI Calculation Utility
# ===========================================================================

class TestAQICalculation:
    """Task 7.1: EPA AQI calculation from PM2.5 breakpoints."""

    def test_good_range_low(self):
        """PM2.5 = 0 → AQI = 0, category Good."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(0.0)
        assert r is not None
        assert r.aqi == 0
        assert r.category == "Good"
        assert r.color == "#00E400"

    def test_good_range_mid(self):
        """PM2.5 = 6.0 → AQI ≈ 25."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(6.0)
        assert r is not None
        assert 20 <= r.aqi <= 30
        assert r.category == "Good"

    def test_good_range_upper_boundary(self):
        """PM2.5 = 12.0 → AQI = 50 (exact top of Good band)."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(12.0)
        assert r is not None
        assert r.aqi == 50
        assert r.category == "Good"

    def test_moderate_range(self):
        """PM2.5 = 35.4 → AQI = 100 (top of Moderate)."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(35.4)
        assert r is not None
        assert r.aqi == 100
        assert r.category == "Moderate"

    def test_moderate_lower_boundary(self):
        """PM2.5 = 12.1 → starts Moderate."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(12.1)
        assert r is not None
        assert r.aqi == 51
        assert r.category == "Moderate"

    def test_unhealthy_sensitive_range(self):
        """PM2.5 = 45.0 → Unhealthy for Sensitive Groups."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(45.0)
        assert r is not None
        assert 101 <= r.aqi <= 150
        assert r.category == "Unhealthy for Sensitive Groups"

    def test_unhealthy_range(self):
        """PM2.5 = 100.0 → Unhealthy (AQI 151-200)."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(100.0)
        assert r is not None
        assert 151 <= r.aqi <= 200
        assert r.category == "Unhealthy"

    def test_very_unhealthy_range(self):
        """PM2.5 = 200.0 → Very Unhealthy."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(200.0)
        assert r is not None
        assert 201 <= r.aqi <= 300
        assert r.category == "Very Unhealthy"

    def test_hazardous_range(self):
        """PM2.5 = 300.0 → Hazardous."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(300.0)
        assert r is not None
        assert r.aqi >= 301
        assert r.category == "Hazardous"

    def test_negative_pm25_returns_none(self):
        """Negative PM2.5 is invalid → None."""
        from app.utils.aqi import calculate_aqi
        assert calculate_aqi(-1.0) is None

    def test_none_pm25_returns_none(self):
        from app.utils.aqi import calculate_aqi
        assert calculate_aqi(None) is None

    def test_above_max_clamped_to_hazardous(self):
        """PM2.5 > 500.4 → clamped, still returns Hazardous AQI = 500."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(999.0)
        assert r is not None
        assert r.aqi == 500
        assert r.category == "Hazardous"

    def test_result_has_pm25_stored(self):
        """AQIResult.pm25 stores the original value."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(25.0)
        assert r.pm25 == 25.0

    def test_to_dict(self):
        """AQIResult.to_dict() returns expected keys."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(10.0)
        d = r.to_dict()
        assert {"aqi", "category", "color", "pm25"} == set(d.keys())

    def test_get_aqi_category_all_bands(self):
        from app.utils.aqi import get_aqi_category
        assert get_aqi_category(25)[0] == "Good"
        assert get_aqi_category(75)[0] == "Moderate"
        assert get_aqi_category(125)[0] == "Unhealthy for Sensitive Groups"
        assert get_aqi_category(175)[0] == "Unhealthy"
        assert get_aqi_category(250)[0] == "Very Unhealthy"
        assert get_aqi_category(400)[0] == "Hazardous"

    def test_epa_verification_35_4(self):
        """EPA standard: PM2.5 = 35.4 → AQI = 100 exactly."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(35.4)
        assert r.aqi == 100

    def test_epa_verification_55_5(self):
        """EPA standard: PM2.5 = 55.5 → AQI = 151 (start of Unhealthy)."""
        from app.utils.aqi import calculate_aqi
        r = calculate_aqi(55.5)
        assert r.aqi == 151
        assert r.category == "Unhealthy"


# ===========================================================================
# 7.2 — Updated calculate_moving_average (PM2.5, Humidity, AQI)
# ===========================================================================

def _build_docs(sensor_id: str, count: int, **fixed_metrics) -> List[dict]:
    """Build *count* telemetry docs with fixed metric values."""
    docs = []
    for i in range(count):
        ts = BASE_TS - timedelta(minutes=i * 5)
        docs.append(_make_doc(sensor_id, ts, **fixed_metrics))
    return docs


class TestCalculateMovingAverage:
    """Task 7.2: Moving averages now include PM2.5, Humidity, AQI."""

    def test_returns_none_with_no_data(self):
        svc = _make_analytics_service(docs=[])
        assert svc.calculate_moving_average("sen_x") is None

    def test_co2_noise_temperature_averages(self):
        docs = _build_docs(
            "sen_01", 5,
            co2=500.0, noise=60.0, temperature=26.0,
            pm25=20.0, humidity=70.0,
        )
        svc = _make_analytics_service(docs=docs)
        result = svc.calculate_moving_average("sen_01")

        assert result is not None
        assert result.sensorId == "sen_01"
        assert result.co2_moving_avg.average == 500.0
        assert result.noise_moving_avg.average == 60.0
        assert result.temperature_moving_avg.average == 26.0

    def test_pm25_moving_average_populated(self):
        docs = _build_docs(
            "sen_02", 5,
            co2=500.0, noise=60.0, temperature=26.0,
            pm25=30.0, humidity=75.0,
        )
        svc = _make_analytics_service(docs=docs)
        result = svc.calculate_moving_average("sen_02")

        assert result.pm25_moving_avg is not None
        assert result.pm25_moving_avg.metric == "PM25"
        assert result.pm25_moving_avg.average == 30.0

    def test_humidity_moving_average_populated(self):
        docs = _build_docs(
            "sen_03", 5,
            co2=500.0, noise=60.0, temperature=26.0,
            pm25=20.0, humidity=80.0,
        )
        svc = _make_analytics_service(docs=docs)
        result = svc.calculate_moving_average("sen_03")

        assert result.humidity_moving_avg is not None
        assert result.humidity_moving_avg.average == 80.0

    def test_aqi_derived_from_pm25_average(self):
        """PM2.5 avg = 6.0 → Good range AQI."""
        docs = _build_docs(
            "sen_04", 5,
            co2=400.0, noise=50.0, temperature=25.0,
            pm25=6.0,
        )
        svc = _make_analytics_service(docs=docs)
        result = svc.calculate_moving_average("sen_04")

        assert result.aqi is not None
        assert result.aqi_category == "Good"
        assert result.aqi <= 50

    def test_aqi_none_without_pm25_data(self):
        docs = _build_docs(
            "sen_05", 5,
            co2=400.0, noise=50.0, temperature=25.0,
        )
        svc = _make_analytics_service(docs=docs)
        result = svc.calculate_moving_average("sen_05")

        assert result is not None
        assert result.pm25_moving_avg is None
        assert result.aqi is None

    def test_window_size_capped_at_10(self):
        docs = _build_docs(
            "sen_06", 15,
            co2=400.0, noise=50.0, temperature=25.0,
            pm25=20.0, humidity=70.0,
        )
        svc = _make_analytics_service(docs=docs)
        result = svc.calculate_moving_average("sen_06")

        assert result is not None
        # Query limit is 10, so window_size ≤ 10
        assert result.co2_moving_avg.window_size <= 10

    def test_varying_pm25_values(self):
        """PM2.5 readings 10, 20, 30 → average 20."""
        docs = []
        for i, pm25_val in enumerate([10.0, 20.0, 30.0]):
            ts = BASE_TS - timedelta(minutes=i * 5)
            docs.append(_make_doc("sen_07", ts,
                                  co2=400.0, noise=50.0, temperature=25.0,
                                  pm25=pm25_val))
        svc = _make_analytics_service(docs=docs)
        result = svc.calculate_moving_average("sen_07")

        assert result.pm25_moving_avg is not None
        assert result.pm25_moving_avg.average == 20.0


# ===========================================================================
# 7.2 — Updated Clean Score
# ===========================================================================

class TestCleanScore:
    """Task 7.2: Three-metric Clean Score (CO2 + Noise + PM2.5)."""

    def test_clean_score_with_pm25(self):
        """Formula: 100 - (norm_co2*0.3 + norm_noise*0.3 + norm_pm25*0.4)"""
        from app.services.analytics_service import calculate_clean_score
        # norm_co2   = (400/2000)*100 = 20
        # norm_noise = (50/100)*100   = 50
        # norm_pm25  = (10/250)*100   =  4
        # raw = 20*0.3 + 50*0.3 + 4*0.4 = 6 + 15 + 1.6 = 22.6
        # score = 100 - 22.6 = 77.4
        score = calculate_clean_score(400.0, 50.0, 10.0)
        assert abs(score - 77.4) < 0.1

    def test_clean_score_without_pm25_legacy(self):
        """Legacy two-metric formula when pm25=None: 100 - (0.5*co2 + 0.5*noise)."""
        from app.services.analytics_service import calculate_clean_score
        # norm_co2   = (400/2000)*100 = 20
        # norm_noise = (50/100)*100   = 50
        # raw = 20*0.5 + 50*0.5 = 35
        # score = 65.0
        score = calculate_clean_score(400.0, 50.0, None)
        assert abs(score - 65.0) < 0.01

    def test_clean_score_clamped_to_zero(self):
        """Extreme pollution → score never goes below 0."""
        from app.services.analytics_service import calculate_clean_score
        score = calculate_clean_score(2000.0, 100.0, 250.0)
        assert score == 0.0

    def test_clean_score_clamped_to_100(self):
        """Zero pollution → score = 100."""
        from app.services.analytics_service import calculate_clean_score
        score = calculate_clean_score(0.0, 0.0, 0.0)
        assert score == 100.0

    def test_high_pm25_lowers_score(self):
        """Same CO2/Noise but high PM2.5 → lower score than without PM2.5."""
        from app.services.analytics_service import calculate_clean_score
        base = calculate_clean_score(400.0, 50.0)
        with_pm25 = calculate_clean_score(400.0, 50.0, 200.0)
        assert with_pm25 < base


# ===========================================================================
# 7.3 — Cluster-Level Analytics
# ===========================================================================

class TestClusterAnalytics:
    """Task 7.3: calculate_cluster_analytics()."""

    def _sensors(self, *sensor_ids):
        return [{"sensorid": sid} for sid in sensor_ids]

    def test_returns_none_on_exception(self):
        """If oracle throws, function returns None."""
        from app.services.analytics_service import AnalyticsService
        svc = AnalyticsService.__new__(AnalyticsService)
        svc.oracle_client  = MagicMock(side_effect=Exception("DB down"))
        svc.mongodb_client = FakeMongoDBClient([])
        result = svc.calculate_cluster_analytics("bad_cluster")
        assert result is None

    def test_empty_cluster_returns_zero_counts(self):
        """Cluster with no sensors → ClusterAnalytics with sensorCount=0."""
        svc = _make_analytics_service(docs=[], sensors_by_cluster={"c1": []})
        result = svc.calculate_cluster_analytics("c1")
        assert result is not None
        assert result.clusterId == "c1"
        assert result.sensorCount == 0
        assert result.readingCount == 0
        assert result.avgCO2 is None

    def test_basic_aggregation_across_sensors(self):
        """Two sensors × 5 readings each → aggregated averages."""
        docs = (
            _build_docs("s1", 5, co2=400.0, noise=60.0, temperature=26.0,
                        pm25=20.0, humidity=70.0)
            + _build_docs("s2", 5, co2=600.0, noise=80.0, temperature=28.0,
                          pm25=40.0, humidity=80.0)
        )
        svc = _make_analytics_service(
            docs=docs,
            sensors_by_cluster={"c2": self._sensors("s1", "s2")},
        )
        result = svc.calculate_cluster_analytics("c2")

        assert result is not None
        assert result.sensorCount == 2
        assert result.readingCount == 10
        assert result.avgCO2 == 500.0
        assert result.avgNoise == 70.0
        assert result.avgTemperature == 27.0
        assert result.avgPM25 == 30.0
        assert result.avgHumidity == 75.0

    def test_cluster_aqi_derived_from_avg_pm25(self):
        """avgPM25 = 6.0 → Good AQI."""
        docs = _build_docs("s3", 5, co2=400.0, noise=50.0, temperature=25.0,
                           pm25=6.0)
        svc = _make_analytics_service(
            docs=docs,
            sensors_by_cluster={"c3": self._sensors("s3")},
        )
        result = svc.calculate_cluster_analytics("c3")

        assert result.aqi is not None
        assert result.aqi <= 50
        assert result.aqi_category == "Good"

    def test_cluster_clean_score_present(self):
        """Clean Score is non-None when CO2 + Noise data exists."""
        docs = _build_docs("s4", 5, co2=400.0, noise=60.0, temperature=26.0,
                           pm25=20.0)
        svc = _make_analytics_service(
            docs=docs,
            sensors_by_cluster={"c4": self._sensors("s4")},
        )
        result = svc.calculate_cluster_analytics("c4")

        assert result.cleanScore is not None
        assert 0.0 <= result.cleanScore <= 100.0

    def test_cluster_metadata_populated(self):
        """Cluster name and location come from Oracle stub."""
        docs = _build_docs("s5", 3, co2=400.0, noise=50.0, temperature=25.0)
        svc = _make_analytics_service(
            docs=docs,
            sensors_by_cluster={"c5": self._sensors("s5")},
        )
        result = svc.calculate_cluster_analytics("c5")

        assert result.clusterName == "Test Cluster c5"
        assert result.locationId == "ward_test"

    def test_cluster_no_telemetry_returns_zero_readings(self):
        """Sensors exist but have no MongoDB docs → readingCount=0."""
        svc = _make_analytics_service(
            docs=[],
            sensors_by_cluster={"c6": self._sensors("s_empty")},
        )
        result = svc.calculate_cluster_analytics("c6")

        assert result is not None
        assert result.sensorCount == 1
        assert result.readingCount == 0
        assert result.avgCO2 is None

    def test_partial_metrics_in_cluster(self):
        """Docs without PM2.5 → avgPM25=None, AQI=None."""
        docs = _build_docs("s6", 5, co2=400.0, noise=60.0, temperature=26.0)
        svc = _make_analytics_service(
            docs=docs,
            sensors_by_cluster={"c7": self._sensors("s6")},
        )
        result = svc.calculate_cluster_analytics("c7")

        assert result.avgPM25 is None
        assert result.aqi is None

    def test_high_pm25_cluster_shows_unhealthy(self):
        """Cluster with avgPM25 ~ 100 → Unhealthy AQI band."""
        docs = _build_docs("s7", 5, co2=800.0, noise=75.0, temperature=30.0,
                           pm25=100.0)
        svc = _make_analytics_service(
            docs=docs,
            sensors_by_cluster={"c8": self._sensors("s7")},
        )
        result = svc.calculate_cluster_analytics("c8")

        assert result.aqi is not None
        assert 151 <= result.aqi <= 200
        assert result.aqi_category == "Unhealthy"
