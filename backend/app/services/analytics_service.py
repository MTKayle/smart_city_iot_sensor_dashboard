"""
Analytics service module for Smart City IoT Dashboard.

Provides analytics calculations:
- Moving averages for all 5 metrics (CO2, Noise, Temperature, PM2.5, Humidity)
- AQI calculation from PM2.5 averages                          (FR6.1)
- Updated Clean Score weighted across CO2, Noise, and PM2.5   (FR6.3)
- Daily summary persistence to Oracle TELEMETRY_SUMMARY        (FR6.2, FR6.4)
- Cluster-level analytics aggregation                          (FR6.5)

Validates: FR6.1, FR6.2, FR6.3, FR6.4, FR6.5
"""

import logging
import uuid
from datetime import date, datetime
from statistics import mean
from typing import Any, Dict, List, Optional

from app.db.mongodb_client import get_mongodb_client
from app.db.oracle_client import get_oracle_client
from app.models.analytics import Analytics, ClusterAnalytics, LeaderboardEntry, MovingAverage
from app.utils.aqi import calculate_aqi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Moving average window size
MOVING_AVERAGE_WINDOW = 10


# =============================================================================
# Clean Score helpers
# =============================================================================

# Normalisation reference ranges
_CO2_MAX = 2000.0    # ppm
_NOISE_MAX = 100.0   # dB
_PM25_MAX = 250.0    # µg/m³ (upper Hazardous band start)

# Weights: CO2 30 %, Noise 30 %, PM2.5 40 %
_W_CO2   = 0.30
_W_NOISE = 0.30
_W_PM25  = 0.40


def _normalize(value: float, max_val: float) -> float:
    """Clamp and normalise *value* to [0, 100] using *max_val* as the ceiling."""
    return min(100.0, max(0.0, (value / max_val) * 100.0))


def calculate_clean_score(
    avg_co2: float,
    avg_noise: float,
    avg_pm25: Optional[float] = None,
) -> float:
    """
    Calculate the Clean Score (0–100, higher = cleaner).

    If PM2.5 is available the score uses a three-metric formula:
        cleanScore = 100 - (
            norm(CO2)   * 0.30 +
            norm(Noise) * 0.30 +
            norm(PM2.5) * 0.40
        )

    Without PM2.5, falls back to the legacy two-metric formula:
        cleanScore = 100 - (norm(CO2) * 0.50 + norm(Noise) * 0.50)

    Args:
        avg_co2:   Average CO2 in ppm
        avg_noise: Average noise level in dB
        avg_pm25:  Average PM2.5 in µg/m³ (optional)

    Returns:
        Clean Score clamped to [0, 100].

    Validates: FR6.3
    """
    norm_co2   = _normalize(avg_co2,   _CO2_MAX)
    norm_noise = _normalize(avg_noise, _NOISE_MAX)

    if avg_pm25 is not None:
        norm_pm25 = _normalize(avg_pm25, _PM25_MAX)
        raw = norm_co2 * _W_CO2 + norm_noise * _W_NOISE + norm_pm25 * _W_PM25
    else:
        # Legacy equal-weight formula (backward compatible)
        raw = norm_co2 * 0.50 + norm_noise * 0.50

    return round(max(0.0, min(100.0, 100.0 - raw)), 2)


# =============================================================================
# AnalyticsService
# =============================================================================

class AnalyticsService:
    """
    Service class for analytics operations.

    Methods
    -------
    calculate_moving_average(sensor_id)
        Moving averages + AQI for all 5 metrics.                 (FR6.3)
    calculate_clean_score(avg_co2, avg_noise, avg_pm25)
        Composite environmental quality score.                   (FR6.3)
    store_daily_summary(...)
        Persist daily aggregated summary to Oracle.              (FR6.2, FR6.4)
    calculate_cluster_analytics(cluster_id)
        Cluster-wide aggregation across all member sensors.      (FR6.5)
    """

    def __init__(self):
        """Initialize analytics service with lazy-loaded clients."""
        self.mongodb_client = get_mongodb_client()
        self.oracle_client  = get_oracle_client()

    # --------------------------------------------------------------------- #
    # 7.2 — calculate_moving_average                                         #
    # --------------------------------------------------------------------- #

    def calculate_moving_average(self, sensor_id: str) -> Optional[Analytics]:
        """
        Calculate moving averages for the last N telemetry readings of a sensor.

        Queries MongoDB for the last ``MOVING_AVERAGE_WINDOW`` (10) readings
        and computes the arithmetic mean for all available metrics:
        CO2, Noise, Temperature, PM2.5, and Humidity.

        AQI is derived from the PM2.5 moving average using the EPA formula.

        Args:
            sensor_id: Sensor identifier.

        Returns:
            Analytics object, or None if no data exists.

        Validates: FR6.3, FR6.1
        """
        try:
            telemetry_docs = self.mongodb_client.query_telemetry(
                sensor_id=sensor_id,
                limit=MOVING_AVERAGE_WINDOW,
            )

            if not telemetry_docs:
                logger.warning(f"No telemetry data found for sensor {sensor_id}")
                return None

            # ----- Extract metric values from nested data.{field} -----
            def _vals(field: str) -> List[float]:
                result = []
                for doc in telemetry_docs:
                    data = doc.get("data", {})
                    v = data.get(field)
                    # Backward-compat: top-level field
                    if v is None:
                        v = doc.get(field)
                    if v is not None:
                        result.append(float(v))
                return result

            co2_values         = _vals("co2")
            noise_values       = _vals("noise")
            temperature_values = _vals("temperature")
            pm25_values        = _vals("pm25")
            humidity_values    = _vals("humidity")

            # At minimum, require CO2 / Noise / Temperature
            if not co2_values or not noise_values or not temperature_values:
                logger.warning(f"Insufficient core metrics for sensor {sensor_id}")
                return None

            window_size = len(telemetry_docs)

            def _ma(metric: str, values: List[float]) -> MovingAverage:
                return MovingAverage(
                    metric=metric,
                    values=[round(v, 2) for v in values],
                    average=round(mean(values), 2),
                    window_size=len(values),
                )

            co2_ma  = _ma("CO2",         co2_values)
            noise_ma = _ma("Noise",      noise_values)
            temp_ma  = _ma("Temperature", temperature_values)

            pm25_ma     = _ma("PM25",     pm25_values)     if pm25_values     else None
            humidity_ma = _ma("Humidity", humidity_values) if humidity_values else None

            # AQI from PM2.5 average
            aqi_val      = None
            aqi_category = None
            if pm25_ma:
                aqi_result = calculate_aqi(pm25_ma.average)
                if aqi_result:
                    aqi_val      = aqi_result.aqi
                    aqi_category = aqi_result.category

            analytics = Analytics(
                sensorId=sensor_id,
                co2_moving_avg=co2_ma,
                noise_moving_avg=noise_ma,
                temperature_moving_avg=temp_ma,
                pm25_moving_avg=pm25_ma,
                humidity_moving_avg=humidity_ma,
                aqi=aqi_val,
                aqi_category=aqi_category,
            )

            logger.info(
                f"Moving averages for sensor {sensor_id}: "
                f"CO2={co2_ma.average:.2f}, Noise={noise_ma.average:.2f}, "
                f"Temp={temp_ma.average:.2f}"
                + (f", PM25={pm25_ma.average:.2f}" if pm25_ma else "")
                + (f", AQI={aqi_val}" if aqi_val is not None else "")
                + f" (window={window_size})"
            )
            return analytics

        except Exception as exc:
            logger.error(
                f"Error calculating moving average for sensor {sensor_id}: {exc}"
            )
            return None

    # --------------------------------------------------------------------- #
    # 7.2 — Clean Score (module-level function wrapped as method)            #
    # --------------------------------------------------------------------- #

    def calculate_clean_score(
        self,
        avg_co2: float,
        avg_noise: float,
        avg_pm25: Optional[float] = None,
    ) -> float:
        """Delegate to the module-level calculate_clean_score() helper."""
        return calculate_clean_score(avg_co2, avg_noise, avg_pm25)

    # --------------------------------------------------------------------- #
    # 7.2 — store_daily_summary                                              #
    # --------------------------------------------------------------------- #

    def store_daily_summary(
        self,
        location_id: str,
        summary_date: date,
        avg_co2: float,
        avg_noise: float,
        avg_temperature: float,
        avg_pm25: Optional[float] = None,
        avg_humidity: Optional[float] = None,
    ) -> bool:
        """
        Store daily telemetry summary with Clean Score in Oracle TELEMETRY_SUMMARY.

        Args:
            location_id:     Location identifier.
            summary_date:    Date for the summary.
            avg_co2:         Average CO2 level in ppm.
            avg_noise:       Average noise level in dB.
            avg_temperature: Average temperature in °C.
            avg_pm25:        Average PM2.5 in µg/m³ (optional).
            avg_humidity:    Average humidity in % (optional).

        Returns:
            True if storage successful, False otherwise.

        Validates: FR6.2, FR6.4
        """
        try:
            clean_score = calculate_clean_score(avg_co2, avg_noise, avg_pm25)
            summary_id  = str(uuid.uuid4())

            # Derive AQI from PM2.5 if available
            aqi_value = None
            if avg_pm25 is not None:
                aqi_result = calculate_aqi(avg_pm25)
                aqi_value = aqi_result.aqi

            success = self.oracle_client.insert_or_update_telemetry_summary(
                summary_id=summary_id,
                location_id=location_id,
                summary_date=summary_date,
                avg_co2=avg_co2,
                avg_noise=avg_noise,
                avg_temperature=avg_temperature,
                clean_score=clean_score,
                avg_pm25=avg_pm25,
                avg_humidity=avg_humidity,
                aqi=aqi_value,
            )

            if success:
                logger.info(
                    f"Stored daily summary for location {location_id} on {summary_date}: "
                    f"CO2={avg_co2:.2f}, Noise={avg_noise:.2f}, Temp={avg_temperature:.2f}"
                    + (f", PM25={avg_pm25:.2f}" if avg_pm25 is not None else "")
                    + (f", Humidity={avg_humidity:.2f}" if avg_humidity is not None else "")
                    + (f", AQI={aqi_value}" if aqi_value is not None else "")
                    + f", CleanScore={clean_score:.2f}"
                )
            else:
                logger.error(
                    f"Failed to store daily summary for location {location_id}"
                )
            return success

        except Exception as exc:
            logger.error(
                f"Error storing daily summary for location {location_id}: {exc}"
            )
            return False

    # --------------------------------------------------------------------- #
    # 7.3 — calculate_cluster_analytics                                      #
    # --------------------------------------------------------------------- #

    def calculate_cluster_analytics(
        self,
        cluster_id: str,
        limit_per_sensor: int = 100,
    ) -> Optional[ClusterAnalytics]:
        """
        Aggregate telemetry for all sensors in a spatial cluster and compute
        cluster-wide averages, AQI, and Clean Score.

        Algorithm:
        1. Fetch cluster metadata from Oracle (SENSOR_CLUSTERS).
        2. Fetch all Active sensors belonging to the cluster.
        3. For each sensor, query the last *limit_per_sensor* readings from MongoDB.
        4. Pool all readings → calculate mean for each metric.
        5. Derive AQI from avg PM2.5; derive Clean Score.
        6. Return ClusterAnalytics object.

        Args:
            cluster_id:        Cluster identifier.
            limit_per_sensor:  Max readings fetched per sensor (default 100).

        Returns:
            ClusterAnalytics object, or None on failure / no data.

        Validates: FR6.5
        """
        try:
            # ── 1. Cluster metadata ──────────────────────────────────────
            cluster_info = self.oracle_client.get_cluster(cluster_id)
            cluster_name = None
            location_id  = None
            if cluster_info:
                cluster_name = cluster_info.get("clustername")
                location_id  = cluster_info.get("locationid")

            # ── 2. Active sensors in the cluster ─────────────────────────
            sensors = self.oracle_client.get_sensors_by_cluster(
                cluster_id, status="Active"
            )
            if not sensors:
                logger.warning(
                    f"No active sensors found for cluster '{cluster_id}'"
                )
                return ClusterAnalytics(
                    clusterId=cluster_id,
                    clusterName=cluster_name,
                    locationId=location_id,
                    sensorCount=0,
                    readingCount=0,
                )

            # ── 3 & 4. Pool readings across all sensors ───────────────────
            pool: Dict[str, List[float]] = {
                "co2": [], "noise": [], "temperature": [], "pm25": [], "humidity": []
            }
            sensors_with_data = 0
            total_readings    = 0

            for sensor in sensors:
                sensor_id = sensor.get("sensorid")
                if not sensor_id:
                    continue

                docs = self.mongodb_client.query_telemetry(
                    sensor_id=sensor_id,
                    limit=limit_per_sensor,
                )
                if not docs:
                    continue

                sensors_with_data += 1
                total_readings    += len(docs)

                for doc in docs:
                    data = doc.get("data", {})

                    def _extract(field: str) -> Optional[float]:
                        v = data.get(field)
                        if v is None:
                            v = doc.get(field)  # backward-compat
                        return float(v) if v is not None else None

                    for metric in ("co2", "noise", "temperature", "pm25", "humidity"):
                        val = _extract(metric)
                        if val is not None:
                            pool[metric].append(val)

            if sensors_with_data == 0 or total_readings == 0:
                logger.warning(
                    f"No telemetry data available for cluster '{cluster_id}'"
                )
                return ClusterAnalytics(
                    clusterId=cluster_id,
                    clusterName=cluster_name,
                    locationId=location_id,
                    sensorCount=len(sensors),
                    readingCount=0,
                )

            # ── 5. Compute aggregates ─────────────────────────────────────
            def _avg(lst: List[float]) -> Optional[float]:
                return round(mean(lst), 2) if lst else None

            avg_co2         = _avg(pool["co2"])
            avg_noise       = _avg(pool["noise"])
            avg_temperature = _avg(pool["temperature"])
            avg_pm25        = _avg(pool["pm25"])
            avg_humidity    = _avg(pool["humidity"])

            # AQI from cluster PM2.5 average
            aqi_val      = None
            aqi_category = None
            if avg_pm25 is not None:
                aqi_result = calculate_aqi(avg_pm25)
                if aqi_result:
                    aqi_val      = aqi_result.aqi
                    aqi_category = aqi_result.category

            # Clean Score (requires at least CO2 and Noise)
            clean_score = None
            if avg_co2 is not None and avg_noise is not None:
                clean_score = calculate_clean_score(avg_co2, avg_noise, avg_pm25)

            result = ClusterAnalytics(
                clusterId=cluster_id,
                clusterName=cluster_name,
                locationId=location_id,
                sensorCount=len(sensors),
                readingCount=total_readings,
                avgCO2=avg_co2,
                avgNoise=avg_noise,
                avgTemperature=avg_temperature,
                avgPM25=avg_pm25,
                avgHumidity=avg_humidity,
                aqi=aqi_val,
                aqi_category=aqi_category,
                cleanScore=clean_score,
            )

            logger.info(
                f"Cluster analytics for '{cluster_id}': "
                f"sensors={len(sensors)}, readings={total_readings}, "
                f"CO2={avg_co2}, Noise={avg_noise}, PM25={avg_pm25}, "
                f"AQI={aqi_val}, CleanScore={clean_score}"
            )
            return result

        except Exception as exc:
            logger.error(
                f"Error calculating cluster analytics for '{cluster_id}': {exc}",
                exc_info=True,
            )
            return None


# =============================================================================
# Singleton
# =============================================================================

_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """
    Get singleton AnalyticsService instance.

    Returns:
        AnalyticsService: Shared service instance.
    """
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
