"""
Scheduler module for Smart City IoT Dashboard.

Background jobs:
- Daily location-level Clean Score aggregation (midnight)   (FR6.2, FR6.4)
- Hourly cluster-level aggregation                         (FR6.5)

Task 8.1 — Updated aggregation pipeline now extracts PM2.5 and Humidity from
            the nested ``data`` sub-document and passes them through to
            store_daily_summary() / insert_or_update_telemetry_summary().

Task 8.2 — New hourly job: ``calculate_cluster_summaries()`` uses
            AnalyticsService.calculate_cluster_analytics() for every active
            cluster and stores results to TELEMETRY_SUMMARY.

Task 8.3 — Every job records wall-clock duration via ``time.perf_counter()``
            and emits a WARN log if it exceeds the 5-minute SLA.

Validates: FR6.2, FR6.4, FR6.5, NFR1.4
"""

import logging
import time
import uuid as _uuid
from datetime import date, datetime, timedelta
from statistics import mean
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.db.mongodb_client import get_mongodb_client
from app.db.oracle_client import get_oracle_client
from app.db.aggregate_summary import aggregate as aggregate_summary
from app.services.analytics_service import get_analytics_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 8.3 — SLA guard: warn if any job takes longer than this
_JOB_SLA_SECONDS = 300  # 5 minutes


def _sla_guard(job_name: str, start: float) -> None:
    """Log a warning when a job exceeds the 5-minute SLA."""
    elapsed = time.perf_counter() - start
    level = logging.WARNING if elapsed > _JOB_SLA_SECONDS else logging.INFO
    logger.log(
        level,
        f"[scheduler] {job_name} finished in {elapsed:.1f}s"
        + (" ⚠ EXCEEDED 5-min SLA" if elapsed > _JOB_SLA_SECONDS else ""),
    )


def _extract_metric(doc: dict, field: str) -> Optional[float]:
    """
    Extract a metric value from a telemetry document.

    Supports both the new nested layout ``{"data": {"co2": ...}}``
    and the legacy flat layout ``{"co2": ...}``.
    """
    value = doc.get("data", {}).get(field)
    if value is None:
        value = doc.get(field)
    return float(value) if value is not None else None


class AnalyticsScheduler:
    """
    Background scheduler for analytics tasks.

    Jobs
    ----
    daily_clean_score_calculation   (00:00 every day)
        Aggregates yesterday's telemetry per location, stores daily summary
        with Clean Score in Oracle TELEMETRY_SUMMARY.          (FR6.2, FR6.4)

    hourly_cluster_aggregation      (every hour, on the hour)
        Calls calculate_cluster_analytics() for every active cluster,
        stores cluster summaries in Oracle TELEMETRY_SUMMARY.  (FR6.5)
    """

    def __init__(self):
        """Initialize scheduler with lazy-loaded dependencies."""
        self.scheduler        = BackgroundScheduler()
        self.analytics_service = get_analytics_service()
        self.mongodb_client   = get_mongodb_client()
        self.oracle_client    = get_oracle_client()
        self._configure_jobs()

    # ------------------------------------------------------------------ #
    # Job registration                                                     #
    # ------------------------------------------------------------------ #

    def _configure_jobs(self) -> None:
        """Register all cron-triggered jobs."""
        # 8.1 — Daily location summary at midnight
        self.scheduler.add_job(
            func=self.calculate_daily_clean_scores,
            trigger=CronTrigger(hour=0, minute=0),
            id="daily_clean_score_calculation",
            name="Calculate Clean Score for all locations",
            replace_existing=True,
            misfire_grace_time=3600,
        )
        logger.info("Configured job: daily_clean_score_calculation at 00:00")

        # 8.2 — Hourly cluster aggregation
        self.scheduler.add_job(
            func=self.calculate_cluster_summaries,
            trigger=CronTrigger(minute=0),   # every hour on the hour
            id="hourly_cluster_aggregation",
            name="Hourly cluster-level analytics aggregation",
            replace_existing=True,
            misfire_grace_time=600,
        )
        logger.info("Configured job: hourly_cluster_aggregation (every hour)")

        # ─── DEMO INTERVALS (rút ngắn để dễ thấy trong demo) ───
        # MongoDB raw → Oracle TELEMETRY_SUMMARY pipeline.
        # Trong production các interval này nên tăng lên (10 phút / 2 giờ / 1 ngày)
        # vì re-aggregating quá thường xuyên là phí compute.

        # Job: HOURLY granularity — chạy mỗi 1 phút, aggregate 2 ngày gần nhất.
        self.scheduler.add_job(
            func=lambda: self._run_summary_aggregator("HOURLY", days=2),
            trigger=IntervalTrigger(minutes=1),
            id="summary_hourly_aggregation",
            name="Aggregate raw MongoDB telemetry → Oracle TELEMETRY_SUMMARY (HOURLY)",
            replace_existing=True,
            misfire_grace_time=120,
            next_run_time=datetime.utcnow() + timedelta(seconds=30),
        )
        logger.info("Configured job: summary_hourly_aggregation (every 1 minute, demo)")

        # Job: DAILY granularity — chạy mỗi 2 phút, aggregate 7 ngày gần nhất.
        self.scheduler.add_job(
            func=lambda: self._run_summary_aggregator("DAILY", days=7),
            trigger=IntervalTrigger(minutes=2),
            id="summary_daily_aggregation",
            name="Aggregate raw MongoDB telemetry → Oracle TELEMETRY_SUMMARY (DAILY)",
            replace_existing=True,
            misfire_grace_time=120,
            next_run_time=datetime.utcnow() + timedelta(seconds=60),
        )
        logger.info("Configured job: summary_daily_aggregation (every 2 minutes, demo)")

        # Job: WEEKLY granularity — chạy mỗi 5 phút, aggregate 90 ngày gần nhất.
        self.scheduler.add_job(
            func=lambda: self._run_summary_aggregator("WEEKLY", days=90),
            trigger=IntervalTrigger(minutes=5),
            id="summary_weekly_aggregation",
            name="Aggregate raw MongoDB telemetry → Oracle TELEMETRY_SUMMARY (WEEKLY)",
            replace_existing=True,
            misfire_grace_time=300,
            next_run_time=datetime.utcnow() + timedelta(seconds=120),
        )
        logger.info("Configured job: summary_weekly_aggregation (every 5 minutes, demo)")

    # ------------------------------------------------------------------ #
    # MongoDB raw → Oracle TELEMETRY_SUMMARY                              #
    # ------------------------------------------------------------------ #
    def _run_summary_aggregator(self, granularity: str, days: int) -> None:
        """Wrapper that wires the aggregator into the scheduler with telemetry."""
        t0 = time.perf_counter()
        logger.info(f"[scheduler] Starting summary_{granularity.lower()}_aggregation …")
        try:
            aggregate_summary(granularity, days)
            logger.info(
                f"[scheduler] summary_{granularity.lower()}_aggregation completed "
                f"in {time.perf_counter() - t0:.1f}s"
            )
        except Exception as e:
            logger.error(
                f"[scheduler] summary_{granularity.lower()}_aggregation failed: {e}",
                exc_info=True,
            )

    # ------------------------------------------------------------------ #
    # 8.1 — Daily location-level Clean Score job                          #
    # ------------------------------------------------------------------ #

    def calculate_daily_clean_scores(self) -> None:
        """
        Aggregate previous day's telemetry for every location.

        For each location:
        1. Fetches all sensors via Oracle.
        2. Queries MongoDB for yesterday's readings (per sensor).
        3. Computes averages for CO2, Noise, Temperature, PM2.5, Humidity.
        4. Stores the result with the updated Clean Score formula
           (CO2 30 % + Noise 30 % + PM2.5 40 % when PM2.5 is available).

        8.3 — Duration logged; SLA warning if > 5 minutes.

        Validates: FR6.2, FR6.4, NFR1.4
        """
        t0 = time.perf_counter()
        logger.info("[scheduler] Starting daily_clean_score_calculation …")

        try:
            yesterday  = date.today() - timedelta(days=1)
            start_time = datetime.combine(yesterday, datetime.min.time())
            end_time   = datetime.combine(yesterday, datetime.max.time())

            locations = self.oracle_client.get_location_hierarchy()
            if not locations:
                logger.warning("[scheduler] No locations found — job skipped")
                return

            logger.info(f"[scheduler] Processing {len(locations)} locations for {yesterday}")
            success_count = error_count = 0

            for location in locations:
                location_id = location.get("locationid")
                if not location_id:
                    continue

                try:
                    summary = self._aggregate_location_telemetry(
                        location_id, start_time, end_time
                    )
                    if summary is None:
                        continue

                    ok = self.analytics_service.store_daily_summary(
                        location_id=location_id,
                        summary_date=yesterday,
                        avg_co2=summary["avg_co2"],
                        avg_noise=summary["avg_noise"],
                        avg_temperature=summary["avg_temperature"],
                        avg_pm25=summary.get("avg_pm25"),
                        avg_humidity=summary.get("avg_humidity"),
                    )
                    if ok:
                        success_count += 1
                    else:
                        error_count += 1
                        logger.error(
                            f"[scheduler] Failed to store summary for {location_id}"
                        )

                except Exception as exc:
                    error_count += 1
                    logger.error(
                        f"[scheduler] Error processing location {location_id}: {exc}"
                    )

            logger.info(
                f"[scheduler] daily_clean_score_calculation done — "
                f"success={success_count}, errors={error_count}"
            )

        except Exception as exc:
            logger.error(f"[scheduler] daily_clean_score_calculation FAILED: {exc}")

        finally:
            _sla_guard("daily_clean_score_calculation", t0)

    # ------------------------------------------------------------------ #
    # 8.1 helper — _aggregate_location_telemetry                         #
    # ------------------------------------------------------------------ #

    def _aggregate_location_telemetry(
        self,
        location_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Optional[Dict[str, float]]:
        """
        Pool telemetry from all sensors in *location_id* for the given window.

        Task 8.1: now extracts PM2.5 and Humidity alongside CO2, Noise,
        Temperature.  Uses the nested ``data.*`` layout with flat fallback.

        Args:
            location_id: Location identifier.
            start_time:  Window start (inclusive).
            end_time:    Window end (inclusive).

        Returns:
            Dict with avg_* keys, or None if no data found.

        Validates: FR6.4
        """
        try:
            sensors = self.oracle_client.get_sensors(location_id=location_id)
            if not sensors:
                return None

            pools: Dict[str, List[float]] = {
                "co2": [], "noise": [], "temperature": [], "pm25": [], "humidity": []
            }

            for sensor in sensors:
                sensor_id = sensor.get("sensorid")
                if not sensor_id:
                    continue

                docs = self.mongodb_client.query_telemetry(
                    sensor_id=sensor_id,
                    start_time=start_time,
                    end_time=end_time,
                    limit=10_000,
                )
                for doc in docs:
                    for field in pools:
                        val = _extract_metric(doc, field)
                        if val is not None:
                            pools[field].append(val)

            if not pools["co2"]:
                return None

            result: Dict[str, float] = {
                "avg_co2":         round(mean(pools["co2"]),         2),
                "avg_noise":       round(mean(pools["noise"]),       2) if pools["noise"]       else None,
                "avg_temperature": round(mean(pools["temperature"]), 2) if pools["temperature"] else None,
                "avg_pm25":        round(mean(pools["pm25"]),        2) if pools["pm25"]        else None,
                "avg_humidity":    round(mean(pools["humidity"]),    2) if pools["humidity"]    else None,
            }
            return result

        except Exception as exc:
            logger.error(
                f"[scheduler] Error aggregating telemetry for {location_id}: {exc}"
            )
            return None

    # ------------------------------------------------------------------ #
    # 8.2 — Hourly cluster aggregation job                                #
    # ------------------------------------------------------------------ #

    def calculate_cluster_summaries(self) -> None:
        """
        Hourly job: aggregate telemetry for every active cluster.

        For each cluster:
        1. Calls ``AnalyticsService.calculate_cluster_analytics()``.
        2. Stores the result in Oracle TELEMETRY_SUMMARY using the cluster's
           LocationID as the grouping key so the leaderboard can reflect
           cluster-level quality.

        8.3 — Duration logged; SLA warning if > 5 minutes.

        Validates: FR6.5, NFR1.4
        """
        t0 = time.perf_counter()
        logger.info("[scheduler] Starting hourly_cluster_aggregation …")

        try:
            clusters = self.oracle_client.get_all_clusters()
            if not clusters:
                logger.info("[scheduler] No clusters found — job skipped")
                return

            logger.info(f"[scheduler] Processing {len(clusters)} clusters")
            success_count = error_count = 0

            today = date.today()

            for cluster in clusters:
                cluster_id = cluster.get("clusterid")
                if not cluster_id:
                    continue

                try:
                    analytics = self.analytics_service.calculate_cluster_analytics(
                        cluster_id
                    )
                    if analytics is None:
                        continue
                    if analytics.readingCount == 0:
                        logger.debug(
                            f"[scheduler] Cluster {cluster_id}: no readings — skipped"
                        )
                        continue

                    # Derive a location_id: prefer cluster's own locationId,
                    # fall back to cluster_id so the row is still stored.
                    loc_id = (
                        analytics.locationId
                        or cluster.get("locationid")
                        or cluster_id
                    )

                    ok = self.oracle_client.insert_or_update_telemetry_summary(
                        summary_id=str(_uuid.uuid4()),
                        location_id=loc_id,
                        summary_date=today,
                        avg_co2=analytics.avgCO2 or 0.0,
                        avg_noise=analytics.avgNoise or 0.0,
                        avg_temperature=analytics.avgTemperature or 0.0,
                        clean_score=analytics.cleanScore or 0.0,
                        avg_pm25=analytics.avgPM25,
                        avg_humidity=analytics.avgHumidity,
                        aqi=analytics.aqi,
                        data_points=analytics.readingCount,
                        granularity='HOURLY',
                    )
                    if ok:
                        success_count += 1
                        logger.debug(
                            f"[scheduler] Cluster {cluster_id}: "
                            f"PM25={analytics.avgPM25}, AQI={analytics.aqi}, "
                            f"CleanScore={analytics.cleanScore}"
                        )
                    else:
                        error_count += 1
                        logger.error(
                            f"[scheduler] Failed to store cluster summary for {cluster_id}"
                        )

                except Exception as exc:
                    error_count += 1
                    logger.error(
                        f"[scheduler] Error processing cluster {cluster_id}: {exc}"
                    )

            logger.info(
                f"[scheduler] hourly_cluster_aggregation done — "
                f"success={success_count}, errors={error_count}"
            )

        except Exception as exc:
            logger.error(f"[scheduler] hourly_cluster_aggregation FAILED: {exc}")

        finally:
            _sla_guard("hourly_cluster_aggregation", t0)

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Start the background scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("[scheduler] Started (2 jobs active)")

    def shutdown(self) -> None:
        """Shutdown the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("[scheduler] Shut down")


# =============================================================================
# Singleton
# =============================================================================

_analytics_scheduler: Optional[AnalyticsScheduler] = None


def get_analytics_scheduler() -> AnalyticsScheduler:
    """Get (or create) the singleton AnalyticsScheduler."""
    global _analytics_scheduler
    if _analytics_scheduler is None:
        _analytics_scheduler = AnalyticsScheduler()
    return _analytics_scheduler
