"""
Spatial query utilities for Smart City IoT Dashboard.

Provides:
- haversine_distance()  — great-circle distance between two GPS coordinates
- find_nearby_sensors() — sensors within a radius, backed by MongoDB geospatial query
                          + Oracle sensor registry details
- identify_hotspots()   — grid-based clustering to surface high-pollution areas

Validates: FR7.1, FR7.2, FR7.3, FR7.4
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Earth's mean radius (km)
_EARTH_RADIUS_KM = 6371.0088


# =============================================================================
# 9.1 — Haversine distance
# =============================================================================

def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two points on Earth using
    the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of point A (decimal degrees).
        lat2, lon2: Latitude and longitude of point B (decimal degrees).

    Returns:
        Distance in **kilometres** (float, always ≥ 0).

    Raises:
        ValueError: if any coordinate is outside [-90,90] (lat) or
                    [-180,180] (lon).

    Examples:
        >>> haversine_distance(10.7769, 106.7009, 10.8231, 106.6297)
        8.18   # ~8 km between two Ho Chi Minh City locations

        >>> haversine_distance(0, 0, 0, 0)
        0.0

    Validates: FR7.1, FR7.4
    """
    # Validate inputs
    for lat, lon, label in [(lat1, lon1, "A"), (lat2, lon2, "B")]:
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude of point {label} out of range: {lat}")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude of point {label} out of range: {lon}")

    # Convert degrees → radians
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi        = math.radians(lat2 - lat1)
    dlambda     = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return _EARTH_RADIUS_KM * c


def haversine_distance_meters(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """Haversine distance in **metres** (convenience wrapper)."""
    return haversine_distance(lat1, lon1, lat2, lon2) * 1000.0


# =============================================================================
# 9.2 — Nearby sensor finder
# =============================================================================

def find_nearby_sensors(
    latitude: float,
    longitude: float,
    radius_km: float,
    mongodb_client=None,
    oracle_client=None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Find sensors within *radius_km* of a given GPS position.

    Steps:
    1. Query MongoDB geospatial index (``$near``) for recent telemetry docs
       within *radius_km* × 1000 metres.
    2. Deduplicate by ``sensorId`` (keep the most recent reading per sensor).
    3. Enrich each result with sensor registry data from Oracle.
    4. Add a computed ``distance_km`` field.

    Args:
        latitude:        Query point latitude (decimal degrees).
        longitude:       Query point longitude (decimal degrees).
        radius_km:       Search radius in kilometres.
        mongodb_client:  MongoDBClient instance (auto-resolved if None).
        oracle_client:   OracleClient instance (auto-resolved if None).
        limit:           Maximum number of sensors to return.

    Returns:
        List of dicts, each containing:
            sensorId, locationId, clusterId, latitude, longitude,
            distance_km, latest_telemetry (nested), and Oracle sensor fields.

    Validates: FR7.1, FR7.3
    """
    if mongodb_client is None:
        from app.db.mongodb_client import get_mongodb_client
        mongodb_client = get_mongodb_client()
    if oracle_client is None:
        from app.db.oracle_client import get_oracle_client
        oracle_client = get_oracle_client()

    radius_m = radius_km * 1000.0

    # ── 1. Geospatial query ───────────────────────────────────────────────
    try:
        raw_docs = mongodb_client.find_nearby_sensors(
            longitude=longitude,
            latitude=latitude,
            max_distance_meters=radius_m,
            limit=limit * 5,  # over-fetch; deduplicate below
        )
    except Exception as exc:
        logger.error(f"[spatial] MongoDB geospatial query failed: {exc}")
        return []

    # ── 2. Deduplicate by sensorId (keep first = closest) ────────────────
    seen_sensors: Dict[str, dict] = {}
    for doc in raw_docs:
        sid = doc.get("sensorId")
        if sid and sid not in seen_sensors:
            seen_sensors[sid] = doc

    results: List[Dict[str, Any]] = []

    # ── 3 & 4. Enrich with Oracle + compute distance ──────────────────────
    for sensor_id, doc in list(seen_sensors.items())[:limit]:
        # Extract sensor location from GeoJSON Point
        geo = doc.get("location", {})
        coords = geo.get("coordinates", [None, None])
        sensor_lng = coords[0] if len(coords) > 0 else None
        sensor_lat = coords[1] if len(coords) > 1 else None

        # Fall back to top-level lat/lng if missing
        if sensor_lat is None:
            sensor_lat = doc.get("latitude")
        if sensor_lng is None:
            sensor_lng = doc.get("longitude")

        distance_km: Optional[float] = None
        if sensor_lat is not None and sensor_lng is not None:
            try:
                distance_km = round(
                    haversine_distance(latitude, longitude, sensor_lat, sensor_lng),
                    4,
                )
            except ValueError:
                pass

        # Oracle sensor registry details
        oracle_info: Dict[str, Any] = {}
        try:
            sensor_rec = oracle_client.get_sensor(sensor_id)
            if sensor_rec:
                oracle_info = sensor_rec
        except Exception as exc:
            logger.debug(f"[spatial] Oracle lookup failed for {sensor_id}: {exc}")

        entry = {
            "sensorId":        sensor_id,
            "locationId":      doc.get("locationId") or oracle_info.get("locationid"),
            "clusterId":       doc.get("clusterId") or oracle_info.get("clusterid"),
            "latitude":        sensor_lat,
            "longitude":       sensor_lng,
            "distance_km":     distance_km,
            "status":          oracle_info.get("status"),
            "sensorModel":     oracle_info.get("sensormodel"),
            "locationName":    oracle_info.get("locationname"),
            "latest_telemetry": {
                "timestamp": doc.get("timestamp"),
                "data":      doc.get("data", {}),
            },
        }
        results.append(entry)

    # Sort by distance
    results.sort(key=lambda r: r["distance_km"] if r["distance_km"] is not None else float("inf"))

    logger.info(
        f"[spatial] find_nearby_sensors({latitude},{longitude}, r={radius_km}km) "
        f"→ {len(results)} sensors"
    )
    return results


# =============================================================================
# 9.3 — Hotspot detection
# =============================================================================

def identify_hotspots(
    metric_type: str,
    threshold: Optional[float] = None,
    grid_resolution_km: float = 1.0,
    mongodb_client=None,
    oracle_client=None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """
    Identify geographic hotspots of high pollution for a given metric.

    Algorithm
    ---------
    1. Fetch the *limit* most-recent telemetry readings for every sensor
       (via Oracle sensor list + MongoDB).
    2. Apply optional *threshold* filter (keep docs where metric > threshold).
    3. Group docs into a lat/lng grid of *grid_resolution_km* spacing using
       integer-divided coordinates.
    4. For each non-empty grid cell compute:
       - centroid (mean lat, mean lng)
       - average metric value
       - reading count
       - list of sensor IDs contributing
    5. Return cells sorted by average value descending.

    Args:
        metric_type:          Metric to analyse: "co2", "noise", "pm25",
                              "humidity", or "temperature" (case-insensitive).
        threshold:            If set, only grid cells whose average **exceeds**
                              this value are returned.
        grid_resolution_km:   Size (km) of each grid cell (default 1 km).
        mongodb_client:       MongoDBClient (auto-resolved if None).
        oracle_client:        OracleClient (auto-resolved if None).
        limit:                Max readings to fetch per sensor.

    Returns:
        List of hotspot dicts (sorted by avg_value desc), each with:
            cell_id, center_lat, center_lng, avg_value, reading_count,
            sensor_ids, metric_type.

    Validates: FR7.2
    """
    if mongodb_client is None:
        from app.db.mongodb_client import get_mongodb_client
        mongodb_client = get_mongodb_client()
    if oracle_client is None:
        from app.db.oracle_client import get_oracle_client
        oracle_client = get_oracle_client()

    field = metric_type.lower()  # normalise to lowercase for doc lookup

    # ── 1. Collect readings ───────────────────────────────────────────────
    try:
        sensors = oracle_client.get_sensors()
    except Exception as exc:
        logger.error(f"[spatial] identify_hotspots: Oracle get_sensors failed: {exc}")
        return []

    # grid: cell_key → {"lats": [], "lngs": [], "values": [], "sensor_ids": set()}
    grid: Dict[str, Dict[str, Any]] = {}

    for sensor in sensors:
        sensor_id = sensor.get("sensorid")
        if not sensor_id:
            continue

        try:
            docs = mongodb_client.query_telemetry(sensor_id=sensor_id, limit=limit)
        except Exception as exc:
            logger.debug(f"[spatial] MongoDB query failed for {sensor_id}: {exc}")
            continue

        for doc in docs:
            # Extract metric value
            val = doc.get("data", {}).get(field)
            if val is None:
                val = doc.get(field)
            if val is None:
                continue
            val = float(val)

            # Extract coordinates
            geo    = doc.get("location", {})
            coords = geo.get("coordinates", [])
            if len(coords) < 2:
                continue
            lng, lat = float(coords[0]), float(coords[1])

            # Determine grid cell (integer multiples of resolution)
            # 1 degree lat ≈ 111 km;  use degrees directly as proxy
            deg_per_cell = grid_resolution_km / 111.0
            cell_lat = int(lat  / deg_per_cell)
            cell_lng = int(lng / deg_per_cell)
            cell_key = f"{cell_lat}:{cell_lng}"

            if cell_key not in grid:
                grid[cell_key] = {
                    "lats": [], "lngs": [], "values": [],
                    "sensor_ids": set(),
                }
            grid[cell_key]["lats"].append(lat)
            grid[cell_key]["lngs"].append(lng)
            grid[cell_key]["values"].append(val)
            grid[cell_key]["sensor_ids"].add(sensor_id)

    # ── 3 & 4. Build hotspot list ─────────────────────────────────────────
    hotspots: List[Dict[str, Any]] = []

    for cell_key, cell in grid.items():
        if not cell["values"]:
            continue

        avg_value = sum(cell["values"]) / len(cell["values"])

        # Apply threshold filter
        if threshold is not None and avg_value <= threshold:
            continue

        center_lat = sum(cell["lats"]) / len(cell["lats"])
        center_lng = sum(cell["lngs"]) / len(cell["lngs"])

        hotspots.append({
            "cell_id":       cell_key,
            "center_lat":    round(center_lat, 6),
            "center_lng":    round(center_lng, 6),
            "avg_value":     round(avg_value, 2),
            "reading_count": len(cell["values"]),
            "sensor_ids":    sorted(cell["sensor_ids"]),
            "metric_type":   metric_type,
        })

    # ── 5. Sort by avg_value descending ──────────────────────────────────
    hotspots.sort(key=lambda h: h["avg_value"], reverse=True)

    logger.info(
        f"[spatial] identify_hotspots(metric={metric_type}, "
        f"threshold={threshold}) → {len(hotspots)} cells"
    )
    return hotspots
