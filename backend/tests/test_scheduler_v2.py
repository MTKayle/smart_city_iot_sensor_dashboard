"""
Tests for Task 8 — Updated Scheduler Service.

Covers:
- 8.1  Updated daily aggregation with PM2.5 / Humidity fields
- 8.2  New hourly cluster aggregation job
- 8.3  SLA timing guard (_sla_guard emits WARNING when > 5 min)
"""

import time
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock, call, patch


# ---------------------------------------------------------------------------
# Helpers / stubs
# ---------------------------------------------------------------------------

def _make_scheduler(
    locations=None,
    sensors_by_location=None,
    telemetry_by_sensor=None,
    clusters=None,
    cluster_analytics=None,
    summary_ok=True,
):
    """
    Build an AnalyticsScheduler whose dependencies are fully mocked.

    All arguments default to empty / success so each test only sets
    what it cares about.
    """
    from app.services.scheduler import AnalyticsScheduler

    svc = AnalyticsScheduler.__new__(AnalyticsScheduler)

    # ── APScheduler (keep real so job registration works) ─────────────────
    from apscheduler.schedulers.background import BackgroundScheduler
    svc.scheduler = BackgroundScheduler()
    svc._configure_jobs()

    # ── Oracle stub ───────────────────────────────────────────────────────
    oracle = Mock()
    oracle.get_location_hierarchy.return_value = locations or []
    oracle.get_all_clusters.return_value = clusters or []

    def _get_sensors(location_id=None):
        if sensors_by_location is None:
            return []
        return sensors_by_location.get(location_id, [])

    oracle.get_sensors.side_effect = _get_sensors
    oracle.insert_or_update_telemetry_summary.return_value = summary_ok
    svc.oracle_client = oracle

    # ── MongoDB stub ──────────────────────────────────────────────────────
    mongo = Mock()

    def _query(sensor_id, start_time=None, end_time=None, limit=100):
        if telemetry_by_sensor is None:
            return []
        return telemetry_by_sensor.get(sensor_id, [])

    mongo.query_telemetry.side_effect = _query
    svc.mongodb_client = mongo

    # ── AnalyticsService stub ─────────────────────────────────────────────
    analytics = Mock()
    analytics.store_daily_summary.return_value = True
    if cluster_analytics is not None:
        analytics.calculate_cluster_analytics.side_effect = cluster_analytics
    else:
        analytics.calculate_cluster_analytics.return_value = None
    svc.analytics_service = analytics

    return svc


def _nested_doc(co2=None, noise=None, temperature=None, pm25=None, humidity=None):
    """Build a telemetry doc in the v2 nested-data format."""
    data = {}
    if co2 is not None:         data["co2"]         = co2
    if noise is not None:       data["noise"]        = noise
    if temperature is not None: data["temperature"]  = temperature
    if pm25 is not None:        data["pm25"]         = pm25
    if humidity is not None:    data["humidity"]     = humidity
    return {"data": data}


def _flat_doc(co2=None, noise=None, temperature=None, pm25=None, humidity=None):
    """Build a telemetry doc in the legacy flat format."""
    doc = {}
    if co2 is not None:         doc["co2"]         = co2
    if noise is not None:       doc["noise"]        = noise
    if temperature is not None: doc["temperature"]  = temperature
    if pm25 is not None:        doc["pm25"]         = pm25
    if humidity is not None:    doc["humidity"]     = humidity
    return doc


# ===========================================================================
# 8.1 — Updated daily aggregation
# ===========================================================================

class TestDailyAggregation:
    """Task 8.1: PM2.5 and Humidity included in aggregation & summary."""

    def test_no_locations_skips_gracefully(self):
        svc = _make_scheduler(locations=[])
        svc.calculate_daily_clean_scores()  # should not raise
        svc.oracle_client.get_location_hierarchy.assert_called_once()
        svc.analytics_service.store_daily_summary.assert_not_called()

    def test_pm25_and_humidity_extracted_from_nested_doc(self):
        """Daily summary is called with avg_pm25 and avg_humidity when present."""
        docs = [
            _nested_doc(co2=400, noise=60, temperature=26, pm25=20, humidity=70),
            _nested_doc(co2=500, noise=70, temperature=28, pm25=40, humidity=80),
        ]
        svc = _make_scheduler(
            locations=[{"locationid": "loc_01"}],
            sensors_by_location={"loc_01": [{"sensorid": "s1"}]},
            telemetry_by_sensor={"s1": docs},
        )
        svc.calculate_daily_clean_scores()

        call_kwargs = svc.analytics_service.store_daily_summary.call_args.kwargs
        assert call_kwargs["avg_pm25"] == 30.0
        assert call_kwargs["avg_humidity"] == 75.0
        assert call_kwargs["avg_co2"] == 450.0
        assert call_kwargs["avg_noise"] == 65.0

    def test_pm25_and_humidity_extracted_from_flat_doc(self):
        """Backward-compat: legacy flat document layout still works."""
        docs = [
            _flat_doc(co2=400, noise=60, temperature=26, pm25=20, humidity=70),
        ]
        svc = _make_scheduler(
            locations=[{"locationid": "loc_02"}],
            sensors_by_location={"loc_02": [{"sensorid": "s2"}]},
            telemetry_by_sensor={"s2": docs},
        )
        svc.calculate_daily_clean_scores()

        call_kwargs = svc.analytics_service.store_daily_summary.call_args.kwargs
        assert call_kwargs["avg_pm25"] == 20.0
        assert call_kwargs["avg_humidity"] == 70.0

    def test_no_pm25_passes_none_to_summary(self):
        """If no PM2.5 readings exist, avg_pm25=None is forwarded."""
        docs = [_nested_doc(co2=400, noise=60, temperature=26)]
        svc = _make_scheduler(
            locations=[{"locationid": "loc_03"}],
            sensors_by_location={"loc_03": [{"sensorid": "s3"}]},
            telemetry_by_sensor={"s3": docs},
        )
        svc.calculate_daily_clean_scores()

        call_kwargs = svc.analytics_service.store_daily_summary.call_args.kwargs
        assert call_kwargs.get("avg_pm25") is None
        assert call_kwargs.get("avg_humidity") is None

    def test_multiple_sensors_pooled(self):
        """Values from multiple sensors in the same location are pooled."""
        svc = _make_scheduler(
            locations=[{"locationid": "loc_04"}],
            sensors_by_location={
                "loc_04": [{"sensorid": "s4a"}, {"sensorid": "s4b"}]
            },
            telemetry_by_sensor={
                "s4a": [_nested_doc(co2=400, noise=60, temperature=26, pm25=10)],
                "s4b": [_nested_doc(co2=600, noise=80, temperature=28, pm25=30)],
            },
        )
        svc.calculate_daily_clean_scores()

        kw = svc.analytics_service.store_daily_summary.call_args.kwargs
        assert kw["avg_co2"] == 500.0
        assert kw["avg_pm25"] == 20.0

    def test_no_telemetry_skips_store(self):
        """Location with no telemetry data → store_daily_summary not called."""
        svc = _make_scheduler(
            locations=[{"locationid": "loc_05"}],
            sensors_by_location={"loc_05": [{"sensorid": "s5"}]},
            telemetry_by_sensor={"s5": []},
        )
        svc.calculate_daily_clean_scores()
        svc.analytics_service.store_daily_summary.assert_not_called()

    def test_exception_in_one_location_continues_others(self):
        """An error for one location must not abort processing of remaining ones."""
        call_count = 0

        def bad_store(**kwargs):
            nonlocal call_count
            call_count += 1
            if kwargs.get("location_id") == "loc_bad":
                raise RuntimeError("simulated Oracle failure")
            return True

        svc = _make_scheduler(
            locations=[
                {"locationid": "loc_bad"},
                {"locationid": "loc_good"},
            ],
            sensors_by_location={
                "loc_bad":  [{"sensorid": "s_bad"}],
                "loc_good": [{"sensorid": "s_good"}],
            },
            telemetry_by_sensor={
                "s_bad":  [_nested_doc(co2=400, noise=60, temperature=26)],
                "s_good": [_nested_doc(co2=400, noise=60, temperature=26)],
            },
        )
        svc.analytics_service.store_daily_summary.side_effect = bad_store
        # Should not raise
        svc.calculate_daily_clean_scores()
        # loc_good was still processed
        assert call_count == 2


# ===========================================================================
# 8.2 — Hourly cluster aggregation
# ===========================================================================

class TestClusterAggregationJob:
    """Task 8.2: hourly cluster aggregation job."""

    def _make_cluster_analytics(self, cluster_id, avg_co2=400.0, avg_pm25=20.0,
                                 clean_score=70.0):
        from app.models.analytics import ClusterAnalytics
        return ClusterAnalytics(
            clusterId=cluster_id,
            clusterName=f"Cluster {cluster_id}",
            locationId="ward_test",
            sensorCount=2,
            readingCount=10,
            avgCO2=avg_co2,
            avgNoise=60.0,
            avgTemperature=26.0,
            avgPM25=avg_pm25,
            avgHumidity=70.0,
            aqi=71,
            aqi_category="Moderate",
            cleanScore=clean_score,
        )

    def test_no_clusters_skips_gracefully(self):
        svc = _make_scheduler(clusters=[])
        svc.calculate_cluster_summaries()
        svc.oracle_client.insert_or_update_telemetry_summary.assert_not_called()

    def test_cluster_summary_stored_for_each_cluster(self):
        clusters = [{"clusterid": "c1"}, {"clusterid": "c2"}]
        analytics_results = {
            "c1": self._make_cluster_analytics("c1"),
            "c2": self._make_cluster_analytics("c2"),
        }

        def _calc(cid, **kw):
            return analytics_results.get(cid)

        svc = _make_scheduler(
            clusters=clusters,
            cluster_analytics=_calc,
        )
        svc.calculate_cluster_summaries()

        assert svc.oracle_client.insert_or_update_telemetry_summary.call_count == 2

    def test_cluster_with_zero_readings_skipped(self):
        from app.models.analytics import ClusterAnalytics
        empty = ClusterAnalytics(
            clusterId="c_empty",
            sensorCount=1,
            readingCount=0,
        )
        svc = _make_scheduler(
            clusters=[{"clusterid": "c_empty"}],
            cluster_analytics=lambda cid, **kw: empty,
        )
        svc.calculate_cluster_summaries()
        svc.oracle_client.insert_or_update_telemetry_summary.assert_not_called()

    def test_cluster_analytics_failure_continues(self):
        """Failure for one cluster must not abort others."""
        call_count = 0

        def _bad_calc(cid, **kw):
            nonlocal call_count
            call_count += 1
            if cid == "c_bad":
                raise RuntimeError("crash!")
            return self._make_cluster_analytics(cid)

        svc = _make_scheduler(
            clusters=[{"clusterid": "c_bad"}, {"clusterid": "c_good"}],
            cluster_analytics=_bad_calc,
        )
        svc.calculate_cluster_summaries()  # must not raise
        # c_good was processed and stored
        svc.oracle_client.insert_or_update_telemetry_summary.assert_called_once()

    def test_two_jobs_registered(self):
        """Scheduler must now have exactly 2 jobs configured."""
        svc = _make_scheduler()
        jobs = svc.scheduler.get_jobs()
        job_ids = {j.id for j in jobs}
        assert "daily_clean_score_calculation" in job_ids
        assert "hourly_cluster_aggregation" in job_ids
        assert len(jobs) == 2


# ===========================================================================
# 8.3 — SLA timing guard
# ===========================================================================

class TestSLAGuard:
    """Task 8.3: Jobs log a WARNING when they exceed 5 minutes."""

    def test_fast_job_logs_info(self, caplog):
        from app.services.scheduler import _sla_guard
        import logging

        with caplog.at_level(logging.INFO, logger="app.services.scheduler"):
            _sla_guard("test_job", time.perf_counter())

        assert "test_job" in caplog.text
        assert "EXCEEDED" not in caplog.text

    def test_slow_job_logs_warning(self, caplog):
        from app.services.scheduler import _sla_guard
        import logging

        # Simulate a start time 310 seconds ago
        fake_start = time.perf_counter() - 310
        with caplog.at_level(logging.WARNING, logger="app.services.scheduler"):
            _sla_guard("slow_job", fake_start)

        assert "EXCEEDED" in caplog.text
        assert "slow_job" in caplog.text

    def test_daily_job_measures_duration(self):
        """calculate_daily_clean_scores must call _sla_guard (no exception)."""
        svc = _make_scheduler(locations=[])
        # Should complete without raising (timing guard inside finally block)
        svc.calculate_daily_clean_scores()

    def test_cluster_job_measures_duration(self):
        svc = _make_scheduler(clusters=[])
        svc.calculate_cluster_summaries()


# ===========================================================================
# Scheduler lifecycle
# ===========================================================================

class TestSchedulerLifecycle:
    def test_start_and_shutdown(self):
        svc = _make_scheduler()
        svc.start()
        assert svc.scheduler.running
        svc.shutdown()
        assert not svc.scheduler.running
