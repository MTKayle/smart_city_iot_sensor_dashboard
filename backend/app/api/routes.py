"""
REST API routes for Smart City IoT Dashboard — v2.

Task 10 additions:
  10.1 Location endpoints   (FR8.1)
  10.2 Cluster endpoints    (FR8.2)
  10.3 Sensor registry      (FR8.3-FR8.6)
  10.4 Updated telemetry    (FR3.1-FR3.4)

All pre-existing endpoints are preserved for backward compatibility.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.db import get_mongodb_client, get_oracle_client
from app.models import (
    Alert, Analytics, ClusterAnalytics, LeaderboardEntry,
    Location, MovingAverage, SensorCapability, SensorCluster,
    SensorHealthLog, SensorRegistry, SensorWithCapabilities,
    SensorWithLocation, Telemetry,
)
from app.services import get_analytics_service
from app.services.alert_service import get_alert_service
from app.utils.spatial import find_nearby_sensors, identify_hotspots

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_location(row: dict) -> Location:
    return Location(
        locationId=row["locationid"],
        name=row["name"],
        parentId=row.get("parentid"),
        type=row["type"],
        centerLat=row.get("centerlat"),
        centerLng=row.get("centerlng"),
        area=row.get("area"),
        population=row.get("population"),
    )


def _row_to_sensor(row: dict) -> SensorRegistry:
    return SensorRegistry(
        sensorId=row["sensorid"],
        locationId=row["locationid"],
        clusterId=row.get("clusterid"),
        latitude=row.get("latitude", 0.0),
        longitude=row.get("longitude", 0.0),
        altitude=row.get("altitude"),
        sensorModel=row.get("sensormodel"),
        firmwareVersion=row.get("firmwareversion"),
        status=row.get("status", "Active"),
        installDate=row.get("installdate") or row.get("registeredat", datetime.now().date()),
        lastMaintenance=row.get("lastmaintenance"),
        nextMaintenance=row.get("nextmaintenance"),
        registeredAt=row.get("registeredat"),
    )


def _row_to_cluster(row: dict) -> SensorCluster:
    return SensorCluster(
        clusterId=row["clusterid"],
        locationId=row["locationid"],
        clusterName=row.get("clustername"),
        centerLat=row.get("centerlat", 0.0),
        centerLng=row.get("centerlng", 0.0),
        radius=row.get("radius", 0.0),
        sensorCount=row.get("sensorcount", 0),
        algorithm=row.get("algorithm"),
    )


def _row_to_capability(row: dict) -> SensorCapability:
    return SensorCapability(
        capabilityId=row["capabilityid"],
        sensorId=row["sensorid"],
        metricType=row["metrictype"],
        unit=row["unit"],
        minRange=row.get("minrange"),
        maxRange=row.get("maxrange"),
        accuracy=row.get("accuracy"),
        calibrationDate=row.get("calibrationdate"),
        nextCalibration=row.get("nextcalibration"),
        isActive=row.get("isactive", True),
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "smart-city-iot-backend"}


# ===========================================================================
# 10.1 — Location endpoints                                      (FR8.1)
# ===========================================================================

@router.get("/locations", summary="List all locations")
async def get_locations():
    """Return the complete location hierarchy (City → District → Ward)."""
    try:
        oracle = get_oracle_client()
        rows = oracle.get_location_hierarchy()
        locations = [_row_to_location(r).model_dump(by_alias=False) for r in rows]
        logger.info(f"Retrieved {len(locations)} locations")
        return locations
    except Exception as exc:
        logger.error(f"get_locations error: {exc}")
        raise HTTPException(500, f"Failed to retrieve locations: {exc}")


@router.get("/locations/{location_id}", summary="Get location by ID")
async def get_location(location_id: str):
    """Return a single location by its ID."""
    try:
        oracle = get_oracle_client()
        row = oracle.get_location(location_id)
        if not row:
            raise HTTPException(404, f"Location '{location_id}' not found")
        return _row_to_location(row).model_dump(by_alias=False)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_location({location_id}) error: {exc}")
        raise HTTPException(500, f"Failed to retrieve location: {exc}")


@router.get("/locations/{location_id}/hierarchy", summary="Get full hierarchy for a location")
async def get_location_hierarchy(location_id: str):
    """Return the ancestor chain and immediate children for a location."""
    try:
        oracle = get_oracle_client()
        row = oracle.get_location(location_id)
        if not row:
            raise HTTPException(404, f"Location '{location_id}' not found")

        all_rows = oracle.get_location_hierarchy()
        # Build ancestor chain
        index = {r["locationid"]: r for r in all_rows}
        ancestors = []
        current = row
        while current.get("parentid"):
            parent = index.get(current["parentid"])
            if not parent:
                break
            ancestors.insert(0, _row_to_location(parent))
            current = parent

        # Immediate children
        children = [_row_to_location(r) for r in all_rows if r.get("parentid") == location_id]

        return {
            "location": _row_to_location(row),
            "ancestors": [loc.model_dump() for loc in ancestors],
            "children": [loc.model_dump() for loc in children],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_location_hierarchy({location_id}) error: {exc}")
        raise HTTPException(500, f"Failed to retrieve hierarchy: {exc}")


@router.get("/locations/{location_id}/sensors", summary="List sensors for a location")
async def get_location_sensors(
    location_id: str,
    status: Optional[str] = Query(None, description="Filter by status (Active/Offline/Maintenance)"),
):
    """Return all sensors registered to a given location."""
    try:
        oracle = get_oracle_client()
        rows = oracle.get_sensors(location_id=location_id)
        sensors = [_row_to_sensor(r) for r in rows]
        if status:
            sensors = [s for s in sensors if s.status == status]
        logger.info(f"get_location_sensors({location_id}): {len(sensors)} sensors")
        return [s.model_dump(by_alias=False) for s in sensors]
    except Exception as exc:
        logger.error(f"get_location_sensors error: {exc}")
        raise HTTPException(500, f"Failed to retrieve sensors: {exc}")


# ===========================================================================
# 10.2 — Cluster endpoints                                       (FR8.2)
# ===========================================================================

@router.get("/clusters", summary="List all clusters")
async def get_clusters(
    location_id: Optional[str] = Query(None, description="Filter clusters by location"),
):
    """Return all sensor clusters, optionally filtered by location."""
    try:
        oracle = get_oracle_client()
        rows = oracle.get_all_clusters()
        clusters = [_row_to_cluster(r) for r in rows]
        if location_id:
            clusters = [c for c in clusters if c.locationId == location_id]
        logger.info(f"get_clusters: {len(clusters)}")
        return [c.model_dump(by_alias=False) for c in clusters]
    except Exception as exc:
        logger.error(f"get_clusters error: {exc}")
        raise HTTPException(500, f"Failed to retrieve clusters: {exc}")


@router.get("/clusters/hotspots", summary="Detect pollution hotspots")
async def get_hotspots(
    metric: str = Query("co2", description="Metric to analyse: co2, noise, pm25, humidity, temperature"),
    threshold: Optional[float] = Query(None, description="Only return cells exceeding this value"),
    grid_km: float = Query(1.0, ge=0.1, le=10.0, description="Grid cell size in km"),
):
    """
    Return geographic grid cells ranked by average pollution level.
    Backed by `identify_hotspots()` from the spatial utils module.
    """
    valid_metrics = {"co2", "noise", "pm25", "humidity", "temperature"}
    if metric.lower() not in valid_metrics:
        raise HTTPException(400, f"Invalid metric '{metric}'. Choose from: {sorted(valid_metrics)}")
    try:
        hotspots = identify_hotspots(
            metric_type=metric.lower(),
            threshold=threshold,
            grid_resolution_km=grid_km,
        )
        return {"metric": metric, "threshold": threshold, "count": len(hotspots), "hotspots": hotspots}
    except Exception as exc:
        logger.error(f"get_hotspots error: {exc}")
        raise HTTPException(500, f"Failed to detect hotspots: {exc}")


@router.get("/clusters/{cluster_id}", summary="Get cluster by ID")
async def get_cluster(cluster_id: str):
    """Return metadata for a single cluster."""
    try:
        oracle = get_oracle_client()
        row = oracle.get_cluster(cluster_id)
        if not row:
            raise HTTPException(404, f"Cluster '{cluster_id}' not found")
        return _row_to_cluster(row).model_dump(by_alias=False)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_cluster({cluster_id}) error: {exc}")
        raise HTTPException(500, f"Failed to retrieve cluster: {exc}")


@router.get("/clusters/{cluster_id}/sensors", summary="List sensors in a cluster")
async def get_cluster_sensors(
    cluster_id: str,
    status: Optional[str] = Query(None, description="Filter by sensor status"),
):
    """Return all sensors belonging to a cluster."""
    try:
        oracle = get_oracle_client()
        rows = oracle.get_sensors_by_cluster(cluster_id, status=status)
        sensors = [_row_to_sensor(r) for r in rows]
        logger.info(f"get_cluster_sensors({cluster_id}): {len(sensors)}")
        return [s.model_dump(by_alias=False) for s in sensors]
    except Exception as exc:
        logger.error(f"get_cluster_sensors error: {exc}")
        raise HTTPException(500, f"Failed to retrieve cluster sensors: {exc}")


@router.get("/clusters/{cluster_id}/telemetry", summary="Cluster-level analytics")
async def get_cluster_telemetry(cluster_id: str):
    """Return aggregated analytics (AQI, Clean Score, averages) for a cluster."""
    try:
        svc = get_analytics_service()
        result = svc.calculate_cluster_analytics(cluster_id)
        if result is None:
            raise HTTPException(404, f"No analytics data for cluster '{cluster_id}'")
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_cluster_telemetry({cluster_id}) error: {exc}")
        raise HTTPException(500, f"Failed to retrieve cluster analytics: {exc}")


# ===========================================================================
# 10.3 — Sensor registry endpoints                      (FR8.3-FR8.6)
# ===========================================================================

@router.get("/sensors", summary="List sensors")
async def get_sensors(
    location_id: Optional[str] = Query(None),
    cluster_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """Return sensors with optional location, cluster, and status filters."""
    try:
        oracle = get_oracle_client()
        if cluster_id:
            rows = oracle.get_sensors_by_cluster(cluster_id, status=status)
        else:
            rows = oracle.get_sensors(location_id=location_id)
        sensors = [_row_to_sensor(r) for r in rows]
        if status and not cluster_id:
            sensors = [s for s in sensors if s.status == status]
        logger.info(f"get_sensors: {len(sensors)}")
        return [s.model_dump(by_alias=False) for s in sensors]
    except Exception as exc:
        logger.error(f"get_sensors error: {exc}")
        raise HTTPException(500, f"Failed to retrieve sensors: {exc}")


@router.get("/sensors/nearby", summary="Find nearby sensors")
async def get_nearby_sensors(
    lat: float = Query(..., description="Latitude of query point"),
    lng: float = Query(..., description="Longitude of query point"),
    radius_km: float = Query(1.0, ge=0.01, le=50.0, description="Search radius in km"),
    limit: int = Query(20, ge=1, le=100),
):
    """Return sensors within *radius_km* of the given GPS position, sorted by distance."""
    try:
        results = find_nearby_sensors(
            latitude=lat,
            longitude=lng,
            radius_km=radius_km,
            limit=limit,
        )
        return {"query": {"lat": lat, "lng": lng, "radius_km": radius_km}, "count": len(results), "sensors": results}
    except Exception as exc:
        logger.error(f"get_nearby_sensors error: {exc}")
        raise HTTPException(500, f"Failed to find nearby sensors: {exc}")


@router.get("/sensors/{sensor_id}", summary="Get sensor by ID")
async def get_sensor(sensor_id: str):
    """Return full registry record for a single sensor."""
    try:
        oracle = get_oracle_client()
        row = oracle.get_sensor(sensor_id)
        if not row:
            raise HTTPException(404, f"Sensor '{sensor_id}' not found")
        return _row_to_sensor(row).model_dump(by_alias=False)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_sensor({sensor_id}) error: {exc}")
        raise HTTPException(500, f"Failed to retrieve sensor: {exc}")


@router.get("/sensors/{sensor_id}/capabilities", summary="Get sensor capabilities")
async def get_sensor_capabilities(sensor_id: str):
    """Return the metrics a sensor can measure (e.g. CO2, PM2.5, Humidity)."""
    try:
        oracle = get_oracle_client()
        rows = oracle.get_sensor_capabilities(sensor_id)
        caps = [_row_to_capability(r).model_dump(by_alias=False) for r in rows]
        logger.info(f"get_sensor_capabilities({sensor_id}): {len(caps)}")
        return caps
    except Exception as exc:
        logger.error(f"get_sensor_capabilities error: {exc}")
        raise HTTPException(500, f"Failed to retrieve capabilities: {exc}")


@router.get("/sensors/{sensor_id}/health", summary="Get sensor health log")
async def get_sensor_health(
    sensor_id: str,
    limit: int = Query(10, ge=1, le=100),
):
    """Return the most recent health log entries for a sensor."""
    try:
        oracle = get_oracle_client()
        # Check sensor exists
        row = oracle.get_sensor(sensor_id)
        if not row:
            raise HTTPException(404, f"Sensor '{sensor_id}' not found")

        # get_sensor_health_logs may not exist on all deployments — fail gracefully
        if hasattr(oracle, "get_sensor_health_logs"):
            logs = oracle.get_sensor_health_logs(sensor_id, limit=limit)
        else:
            logs = []

        return {
            "sensorId": sensor_id,
            "status": row.get("status", "Unknown"),
            "lastMaintenance": str(row.get("lastmaintenance", "")),
            "nextMaintenance": str(row.get("nextmaintenance", "")),
            "healthLogs": logs,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_sensor_health({sensor_id}) error: {exc}")
        raise HTTPException(500, f"Failed to retrieve sensor health: {exc}")


@router.get("/sensors/{sensor_id}/analytics", response_model=Analytics,
            summary="Get sensor analytics")
async def get_sensor_analytics(sensor_id: str):
    """Return moving averages + AQI for the last 10 telemetry readings."""
    try:
        svc = get_analytics_service()
        analytics = svc.calculate_moving_average(sensor_id)
        if analytics is None:
            raise HTTPException(404, f"No telemetry data found for sensor {sensor_id}")
        return analytics
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_sensor_analytics({sensor_id}) error: {exc}")
        raise HTTPException(500, f"Failed to calculate analytics: {exc}")


# ===========================================================================
# 10.4 — Updated telemetry endpoints                      (FR3.1-FR3.4)
# ===========================================================================

def _doc_to_telemetry(doc: dict) -> dict:
    """
    Convert a MongoDB telemetry document to a flat response dict.

    Supports both nested ``data.*`` layout (v2) and flat layout (v1/backward-compat).
    Returns all available fields so new clients see PM2.5 / Humidity / AQI while
    old clients (checking only co2/noise/temperature) remain unaffected.
    """
    ts = doc.get("timestamp")
    if ts and hasattr(ts, "tzinfo") and ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    data = doc.get("data") or {}
    def _v(field):
        return data.get(field) if data.get(field) is not None else doc.get(field)

    result = {
        "sensorId":    doc.get("sensorId"),
        "locationId":  doc.get("locationId"),
        "clusterId":   doc.get("clusterId"),
        "timestamp":   ts.isoformat() if ts else None,
        # Core (v1)
        "co2":         _v("co2"),
        "noise":       _v("noise"),
        "temperature": _v("temperature"),
        # New (v2)
        "pm25":        _v("pm25"),
        "humidity":    _v("humidity"),
        # Mirror nested + quality so the frontend can read either shape
        "data": {
            "co2":         _v("co2"),
            "noise":       _v("noise"),
            "temperature": _v("temperature"),
            "pm25":        _v("pm25"),
            "humidity":    _v("humidity"),
        },
        "quality":  doc.get("quality"),
        "location": doc.get("location"),
    }
    # Include AQI if PM2.5 is present
    if result["pm25"] is not None:
        try:
            from app.utils.aqi import calculate_aqi
            aqi_result = calculate_aqi(result["pm25"])
            if aqi_result:
                result["aqi"] = aqi_result.aqi
                result["aqi_category"] = aqi_result.category
        except Exception:
            pass
    return result


@router.get("/telemetry/{sensor_id}", summary="Get telemetry for a sensor")
async def get_telemetry(
    sensor_id: str,
    start_time: Optional[datetime] = Query(None, description="ISO 8601 start"),
    end_time:   Optional[datetime] = Query(None, description="ISO 8601 end"),
    limit:      int = Query(100, ge=1, le=2000),
    bucket_minutes: Optional[int] = Query(
        None, ge=1, le=10080,
        description="Aggregation bucket size in minutes. Overrides the auto-bucketing heuristic.",
    ),
    cluster_id: Optional[str] = Query(None, description="Filter — only return if sensor is in this cluster"),
    near_lat:   Optional[float] = Query(None, description="Geospatial filter — latitude"),
    near_lng:   Optional[float] = Query(None, description="Geospatial filter — longitude"),
    near_km:    float = Query(1.0, description="Geospatial filter — radius in km"),
):
    """
    Return telemetry for a sensor with optional time, cluster, and geospatial filters.

    - 10.4 / FR3.1-FR3.4: returns PM2.5, Humidity, and derived AQI alongside legacy fields.
    - Cluster filter: returns 404 if the sensor doesn't belong to the given cluster.
    - Geospatial filter: returns 404 if the sensor falls outside the radius.
    - Time bucketing: >8 h → 5-min buckets; >2 h → 1-min buckets; else raw.
    """
    try:
        # --- Time range defaults -------------------------------------------------
        if start_time and end_time and start_time >= end_time:
            raise HTTPException(400, "start_time must be less than end_time")

        if not start_time and not end_time:
            end_time   = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)
        elif start_time and not end_time:
            end_time = datetime.now(timezone.utc)

        # --- Cluster filter -------------------------------------------------------
        if cluster_id:
            oracle = get_oracle_client()
            row = oracle.get_sensor(sensor_id)
            if not row or row.get("clusterid") != cluster_id:
                raise HTTPException(404, f"Sensor '{sensor_id}' not in cluster '{cluster_id}'")

        # --- Geospatial filter ----------------------------------------------------
        if near_lat is not None and near_lng is not None:
            oracle = get_oracle_client()
            row = oracle.get_sensor(sensor_id)
            if row:
                from app.utils.spatial import haversine_distance
                s_lat = row.get("latitude", 0.0)
                s_lng = row.get("longitude", 0.0)
                dist = haversine_distance(near_lat, near_lng, s_lat, s_lng)
                if dist > near_km:
                    raise HTTPException(
                        404,
                        f"Sensor '{sensor_id}' is {dist:.2f} km away — outside {near_km} km radius",
                    )

        # --- Query ---------------------------------------------------------------
        mongo = get_mongodb_client()
        time_delta = end_time - start_time if start_time and end_time else None

        # Explicit bucket override — used by long-range views (year, month).
        if bucket_minutes is not None:
            docs = mongo.query_telemetry_aggregated(
                sensor_id=sensor_id, start_time=start_time,
                end_time=end_time, bucket_minutes=bucket_minutes,
            )
        elif time_delta and time_delta.total_seconds() > 8 * 3600:
            docs = mongo.query_telemetry_aggregated(
                sensor_id=sensor_id, start_time=start_time,
                end_time=end_time, bucket_minutes=5,
            )
        elif time_delta and time_delta.total_seconds() > 2 * 3600:
            docs = mongo.query_telemetry_aggregated(
                sensor_id=sensor_id, start_time=start_time,
                end_time=end_time, bucket_minutes=1,
            )
        else:
            docs = mongo.query_telemetry(
                sensor_id=sensor_id, start_time=start_time,
                end_time=end_time, limit=limit,
            )

        result = [_doc_to_telemetry(d) for d in docs]
        logger.info(f"get_telemetry({sensor_id}): {len(result)} records")
        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_telemetry({sensor_id}) error: {exc}")
        raise HTTPException(500, f"Failed to retrieve telemetry: {exc}")


# ===========================================================================
# Pre-existing shared endpoints (backward-compat)
# ===========================================================================

@router.get("/alerts", summary="List alerts")
async def get_alerts(
    level:       Optional[str] = Query(None),
    alert_type:  Optional[str] = Query(None, description="THRESHOLD/PREDICTIVE/ANOMALY/CLUSTER"),
    location_id: Optional[str] = Query(None),
    status:      Optional[str] = Query(None, description="OPEN/ACKNOWLEDGED/RESOLVED"),
    limit:       int = Query(100, ge=1, le=1000),
):
    """Return recent alerts with optional level/type/location/status filters."""
    if level and level not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        raise HTTPException(400, f"Invalid alert level: {level}")
    if alert_type and alert_type not in ("THRESHOLD", "PREDICTIVE", "ANOMALY", "CLUSTER"):
        raise HTTPException(400, f"Invalid alert type: {alert_type}")
    if status and status not in ("OPEN", "ACKNOWLEDGED", "RESOLVED"):
        raise HTTPException(400, f"Invalid alert status: {status}")
    try:
        oracle = get_oracle_client()
        rows   = oracle.get_alerts(level=level, location_id=location_id, limit=limit)
        # Server-side filter for type/status (Oracle helper doesn't support these yet)
        if alert_type:
            rows = [r for r in rows if (r.get("alerttype") or "THRESHOLD") == alert_type]
        if status:
            rows = [r for r in rows if (r.get("status") or "OPEN") == status]
        alerts = []
        for r in rows:
            a = Alert(
                alertId=r["alertid"],
                sensorId=r.get("sensorid"),
                locationId=r.get("locationid", "unknown_location"),
                alertType=r.get("alerttype", "THRESHOLD"),
                metricType=r["metrictype"],
                value=r["value"],
                severity=r.get("alertlevel") or r.get("severity") or "LOW",
                status=r.get("status", "OPEN"),
                threshold=r.get("threshold"),
                predictedValue=r.get("predictedvalue"),
                confidenceScore=r.get("confidencescore"),
                createdAt=r["createdat"],
            )
            alerts.append(a.model_dump(by_alias=False))
        return alerts
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_alerts error: {exc}")
        raise HTTPException(500, f"Failed to retrieve alerts: {exc}")


@router.post("/alerts/{alert_id}/acknowledge", summary="Acknowledge an alert")
async def acknowledge_alert(alert_id: str):
    """Transition alert OPEN → ACKNOWLEDGED."""
    try:
        svc = get_alert_service()
        ok = svc.acknowledge_alert(alert_id)
        if not ok:
            raise HTTPException(404, f"Alert '{alert_id}' not found or update failed")
        oracle = get_oracle_client()
        rows = oracle.get_alerts(limit=1000)
        match = next((r for r in rows if r.get("alertid") == alert_id), None)
        if not match:
            return {"alertId": alert_id, "status": "ACKNOWLEDGED"}
        return {
            "alertId": match["alertid"],
            "sensorId": match.get("sensorid"),
            "locationId": match.get("locationid"),
            "alertType": match.get("alerttype", "THRESHOLD"),
            "metricType": match["metrictype"],
            "value": match["value"],
            "severity": match.get("severity") or match.get("alertlevel") or "LOW",
            "status": "ACKNOWLEDGED",
            "createdAt": match["createdat"],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"acknowledge_alert({alert_id}) error: {exc}")
        raise HTTPException(500, f"Failed to acknowledge alert: {exc}")


@router.post("/alerts/{alert_id}/resolve", summary="Resolve an alert")
async def resolve_alert(alert_id: str):
    """Transition alert → RESOLVED."""
    try:
        svc = get_alert_service()
        ok = svc.resolve_alert(alert_id)
        if not ok:
            raise HTTPException(404, f"Alert '{alert_id}' not found or update failed")
        oracle = get_oracle_client()
        rows = oracle.get_alerts(limit=1000)
        match = next((r for r in rows if r.get("alertid") == alert_id), None)
        if not match:
            return {"alertId": alert_id, "status": "RESOLVED"}
        return {
            "alertId": match["alertid"],
            "sensorId": match.get("sensorid"),
            "locationId": match.get("locationid"),
            "alertType": match.get("alerttype", "THRESHOLD"),
            "metricType": match["metrictype"],
            "value": match["value"],
            "severity": match.get("severity") or match.get("alertlevel") or "LOW",
            "status": "RESOLVED",
            "createdAt": match["createdat"],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"resolve_alert({alert_id}) error: {exc}")
        raise HTTPException(500, f"Failed to resolve alert: {exc}")


@router.get("/leaderboard", response_model=List[LeaderboardEntry], summary="Clean Score leaderboard")
async def get_leaderboard(limit: int = Query(100, ge=1, le=1000)):
    """Return locations ranked by environmental quality (Clean Score)."""
    try:
        oracle = get_oracle_client()
        rows   = oracle.get_leaderboard(limit=limit)
        result = []
        for r in rows:
            result.append(LeaderboardEntry(
                locationId=r["locationid"],
                locationName=r["locationname"],
                avgCO2=r["avgco2"],
                avgNoise=r["avgnoise"],
                avgTemperature=r["avgtemperature"],
                avgPM25=r.get("avgpm25"),
                avgHumidity=r.get("avghumidity"),
                aqi=r.get("aqi"),
                aqi_category=r.get("aqi_category"),
                cleanScore=r["cleanscore"],
                rank=r["rank"],
            ))
        return result
    except Exception as exc:
        logger.error(f"get_leaderboard error: {exc}")
        raise HTTPException(500, f"Failed to retrieve leaderboard: {exc}")


# ============================================================================
# Historical summary (Oracle TELEMETRY_SUMMARY)
# ============================================================================
@router.get("/locations/{location_id}/history", summary="Historical telemetry summary for a location")
async def get_location_history(
    location_id: str,
    granularity: str = Query("HOURLY", regex="^(HOURLY|DAILY|WEEKLY)$"),
    start_time: Optional[datetime] = Query(None),
    end_time:   Optional[datetime] = Query(None),
):
    """
    Return pre-aggregated telemetry summaries from Oracle TELEMETRY_SUMMARY
    for a location (city / district / ward) at the requested granularity.

    Granularity:
      - HOURLY: 1-hour buckets — best for "Hôm nay" and "Tuần"
      - DAILY:  1-day buckets — best for "Tháng" and "Năm"
      - WEEKLY: 1-week buckets — coarse year overview
    """
    try:
        if not end_time:
            end_time = datetime.now(timezone.utc)
        if not start_time:
            default_days = {"HOURLY": 7, "DAILY": 30, "WEEKLY": 365}.get(granularity, 7)
            start_time = end_time - timedelta(days=default_days)

        oracle = get_oracle_client()
        conn = oracle._pool.acquire()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT TimeBucket, AvgPM25, MaxPM25,
                       AvgCO2, MaxCO2, MinCO2,
                       AvgNoise, MaxNoise, MinNoise,
                       AvgTemperature, MaxTemperature, MinTemperature,
                       AvgHumidity, AQI, CleanScore, DataPoints
                  FROM TELEMETRY_SUMMARY
                 WHERE LocationID = :loc
                   AND Granularity = :gran
                   AND TimeBucket BETWEEN :s AND :e
                 ORDER BY TimeBucket
                """,
                {"loc": location_id, "gran": granularity, "s": start_time, "e": end_time},
            )
            rows = cur.fetchall()
            cur.close()
        finally:
            oracle._pool.release(conn)

        result = []
        for r in rows:
            (tb, avg_pm25, max_pm25, avg_co2, max_co2, min_co2,
             avg_noise, max_noise, min_noise, avg_temp, max_temp, min_temp,
             avg_hum, aqi, clean, n) = r
            result.append({
                "timeBucket": tb.isoformat() if tb else None,
                "avgPM25": float(avg_pm25) if avg_pm25 is not None else None,
                "maxPM25": float(max_pm25) if max_pm25 is not None else None,
                "avgCO2": float(avg_co2) if avg_co2 is not None else None,
                "maxCO2": float(max_co2) if max_co2 is not None else None,
                "minCO2": float(min_co2) if min_co2 is not None else None,
                "avgNoise": float(avg_noise) if avg_noise is not None else None,
                "maxNoise": float(max_noise) if max_noise is not None else None,
                "minNoise": float(min_noise) if min_noise is not None else None,
                "avgTemperature": float(avg_temp) if avg_temp is not None else None,
                "maxTemperature": float(max_temp) if max_temp is not None else None,
                "minTemperature": float(min_temp) if min_temp is not None else None,
                "avgHumidity": float(avg_hum) if avg_hum is not None else None,
                "aqi": int(aqi) if aqi is not None else None,
                "cleanScore": int(clean) if clean is not None else None,
                "dataPoints": int(n) if n is not None else 0,
            })
        return result
    except Exception as exc:
        logger.error(f"get_location_history({location_id}) error: {exc}")
        raise HTTPException(500, f"Failed to retrieve history: {exc}")
