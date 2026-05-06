"""
Telemetry Data Seeder for Smart City IoT Dashboard.

Generates a full year of realistic telemetry across two resolutions so the
analytics views (Today / Week / Month / Year) all have proper data without
exploding MongoDB:

  • Last 30 days  → 5-min resolution (full detail for live & trend views)
  • Days 30 → 365 → 1-hour resolution (sufficient for monthly / yearly views)

Total: ~550 K documents for 33 sensors.

Usage:
    python -m app.db.seed_telemetry
"""

import math
import random
import time
import logging
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("telemetry_seeder")

# ============================================================================
# Sensor Configuration (matches oracle_seed_v2.sql exactly)
# ============================================================================
SENSORS = [
    # District 1 – Ben Nghe Ward (cluster_q1_north)
    {"sensorId": "sen_q1_ben_nghe_01", "locationId": "ward_q1_ben_nghe", "clusterId": "cluster_q1_north", "lat": 10.7756, "lng": 106.7019},
    {"sensorId": "sen_q1_ben_nghe_02", "locationId": "ward_q1_ben_nghe", "clusterId": "cluster_q1_north", "lat": 10.7765, "lng": 106.7028},
    {"sensorId": "sen_q1_ben_nghe_03", "locationId": "ward_q1_ben_nghe", "clusterId": "cluster_q1_north", "lat": 10.7748, "lng": 106.7011},
    {"sensorId": "sen_q1_ben_nghe_04", "locationId": "ward_q1_ben_nghe", "clusterId": "cluster_q1_north", "lat": 10.7770, "lng": 106.7035},
    {"sensorId": "sen_q1_ben_nghe_05", "locationId": "ward_q1_ben_nghe", "clusterId": "cluster_q1_north", "lat": 10.7742, "lng": 106.7005},
    # District 1 – Ben Thanh Ward (cluster_q1_south)
    {"sensorId": "sen_q1_ben_thanh_01", "locationId": "ward_q1_ben_thanh", "clusterId": "cluster_q1_south", "lat": 10.7721, "lng": 106.6983},
    {"sensorId": "sen_q1_ben_thanh_02", "locationId": "ward_q1_ben_thanh", "clusterId": "cluster_q1_south", "lat": 10.7728, "lng": 106.6991},
    {"sensorId": "sen_q1_ben_thanh_03", "locationId": "ward_q1_ben_thanh", "clusterId": "cluster_q1_south", "lat": 10.7715, "lng": 106.6975},
    {"sensorId": "sen_q1_ben_thanh_04", "locationId": "ward_q1_ben_thanh", "clusterId": "cluster_q1_south", "lat": 10.7733, "lng": 106.6998},
    {"sensorId": "sen_q1_ben_thanh_05", "locationId": "ward_q1_ben_thanh", "clusterId": "cluster_q1_south", "lat": 10.7710, "lng": 106.6968},
    # District 1 – Nguyen Thai Binh Ward (cluster_q1_south)
    {"sensorId": "sen_q1_ntb_01", "locationId": "ward_q1_nguyen_thai_binh", "clusterId": "cluster_q1_south", "lat": 10.7689, "lng": 106.6945},
    {"sensorId": "sen_q1_ntb_02", "locationId": "ward_q1_nguyen_thai_binh", "clusterId": "cluster_q1_south", "lat": 10.7695, "lng": 106.6952},
    {"sensorId": "sen_q1_ntb_03", "locationId": "ward_q1_nguyen_thai_binh", "clusterId": "cluster_q1_south", "lat": 10.7683, "lng": 106.6938},
    {"sensorId": "sen_q1_ntb_04", "locationId": "ward_q1_nguyen_thai_binh", "clusterId": "cluster_q1_south", "lat": 10.7700, "lng": 106.6959},
    {"sensorId": "sen_q1_ntb_05", "locationId": "ward_q1_nguyen_thai_binh", "clusterId": "cluster_q1_south", "lat": 10.7678, "lng": 106.6931},
    # District 3 – Ward 1 (cluster_q3_central)
    {"sensorId": "sen_q3_w1_01", "locationId": "ward_q3_01", "clusterId": "cluster_q3_central", "lat": 10.7866, "lng": 106.6828},
    {"sensorId": "sen_q3_w1_02", "locationId": "ward_q3_01", "clusterId": "cluster_q3_central", "lat": 10.7873, "lng": 106.6835},
    {"sensorId": "sen_q3_w1_03", "locationId": "ward_q3_01", "clusterId": "cluster_q3_central", "lat": 10.7859, "lng": 106.6821},
    # District 3 – Ward 2 (cluster_q3_central)
    {"sensorId": "sen_q3_w2_01", "locationId": "ward_q3_02", "clusterId": "cluster_q3_central", "lat": 10.7823, "lng": 106.6789},
    {"sensorId": "sen_q3_w2_02", "locationId": "ward_q3_02", "clusterId": "cluster_q3_central", "lat": 10.7830, "lng": 106.6796},
    {"sensorId": "sen_q3_w2_03", "locationId": "ward_q3_02", "clusterId": "cluster_q3_central", "lat": 10.7816, "lng": 106.6782},
    # District 3 – Ward 3 (cluster_q3_central)
    {"sensorId": "sen_q3_w3_01", "locationId": "ward_q3_03", "clusterId": "cluster_q3_central", "lat": 10.7901, "lng": 106.6856},
    {"sensorId": "sen_q3_w3_02", "locationId": "ward_q3_03", "clusterId": "cluster_q3_central", "lat": 10.7908, "lng": 106.6863},
    {"sensorId": "sen_q3_w3_03", "locationId": "ward_q3_03", "clusterId": "cluster_q3_central", "lat": 10.7894, "lng": 106.6849},
    # District 5 – Ward 1 (cluster_q5_west)
    {"sensorId": "sen_q5_w1_01", "locationId": "ward_q5_01", "clusterId": "cluster_q5_west", "lat": 10.7545, "lng": 106.6664},
    {"sensorId": "sen_q5_w1_02", "locationId": "ward_q5_01", "clusterId": "cluster_q5_west", "lat": 10.7552, "lng": 106.6671},
    {"sensorId": "sen_q5_w1_03", "locationId": "ward_q5_01", "clusterId": "cluster_q5_west", "lat": 10.7538, "lng": 106.6657},
    # District 5 – Ward 2 (cluster_q5_west)
    {"sensorId": "sen_q5_w2_01", "locationId": "ward_q5_02", "clusterId": "cluster_q5_west", "lat": 10.7512, "lng": 106.6623},
    {"sensorId": "sen_q5_w2_02", "locationId": "ward_q5_02", "clusterId": "cluster_q5_west", "lat": 10.7519, "lng": 106.6630},
    {"sensorId": "sen_q5_w2_03", "locationId": "ward_q5_02", "clusterId": "cluster_q5_west", "lat": 10.7505, "lng": 106.6616},
    # District 5 – Ward 3 (cluster_q5_west)
    {"sensorId": "sen_q5_w3_01", "locationId": "ward_q5_03", "clusterId": "cluster_q5_west", "lat": 10.7578, "lng": 106.6701},
    {"sensorId": "sen_q5_w3_02", "locationId": "ward_q5_03", "clusterId": "cluster_q5_west", "lat": 10.7585, "lng": 106.6708},
    {"sensorId": "sen_q5_w3_03", "locationId": "ward_q5_03", "clusterId": "cluster_q5_west", "lat": 10.7571, "lng": 106.6694},
]

# Per-district pollution profiles (District 1 is busier/more polluted)
DISTRICT_PROFILES = {
    "ward_q1_ben_nghe":          {"co2": 480, "noise": 62, "temp": 29, "pm25": 45, "hum": 72},
    "ward_q1_ben_thanh":         {"co2": 520, "noise": 68, "temp": 30, "pm25": 52, "hum": 70},
    "ward_q1_nguyen_thai_binh":  {"co2": 460, "noise": 58, "temp": 29, "pm25": 40, "hum": 73},
    "ward_q3_01":                {"co2": 420, "noise": 55, "temp": 28, "pm25": 35, "hum": 75},
    "ward_q3_02":                {"co2": 410, "noise": 52, "temp": 28, "pm25": 33, "hum": 76},
    "ward_q3_03":                {"co2": 430, "noise": 54, "temp": 28, "pm25": 36, "hum": 74},
    "ward_q5_01":                {"co2": 390, "noise": 48, "temp": 27, "pm25": 30, "hum": 78},
    "ward_q5_02":                {"co2": 380, "noise": 46, "temp": 27, "pm25": 28, "hum": 79},
    "ward_q5_03":                {"co2": 400, "noise": 50, "temp": 27, "pm25": 32, "hum": 77},
}

# ============================================================================
# Data Generation
# ============================================================================
INTERVAL_RECENT_MIN = 5     # 5-min resolution for the recent window
INTERVAL_LEGACY_MIN = 60    # 1-hour resolution for older data (months 1-12)
DAYS_RECENT = 30            # high-res window covering today / week / month views
DAYS_TOTAL = 365            # one full year for the year view
TTL_DAYS = 380              # TTL slightly longer than DAYS_TOTAL

def generate_metrics(ts: datetime, profile: dict) -> dict:
    """Generate realistic sensor metrics with diurnal patterns."""
    hour = ts.hour + ts.minute / 60.0
    day_of_week = ts.weekday()  # 0=Mon, 6=Sun
    is_weekend = day_of_week >= 5

    # Rush-hour factor (peaks at 8am and 6pm)
    rush = max(
        math.exp(-((hour - 8) ** 2) / 6),
        math.exp(-((hour - 18) ** 2) / 6),
    )
    # Night factor (quiet at 2-4am)
    night = math.exp(-((hour - 3) ** 2) / 12)

    # Weekend reduces traffic impact by 40%
    weekend_mult = 0.6 if is_weekend else 1.0

    # CO2 (ppm)
    co2 = profile["co2"] + rush * 350 * weekend_mult - night * 80 + random.gauss(0, 25)
    co2 = round(max(300, min(2000, co2)), 1)

    # Noise (dB)
    noise = profile["noise"] + rush * 22 * weekend_mult - night * 18 + random.gauss(0, 4)
    noise = round(max(30, min(95, noise)), 1)

    # Temperature (°C) — peaks at ~14:00
    temp = profile["temp"] + 4 * math.sin(math.pi * (hour - 6) / 12) + random.gauss(0, 0.8)
    temp = round(max(22, min(38, temp)), 1)

    # PM2.5 (μg/m³) — correlates with traffic
    pm25 = profile["pm25"] + rush * 45 * weekend_mult - night * 10 + random.gauss(0, 6)
    pm25 = round(max(5, min(200, pm25)), 1)

    # Humidity (%) — inversely correlated with temperature
    hum = profile["hum"] - 12 * math.sin(math.pi * (hour - 6) / 12) + random.gauss(0, 3)
    hum = round(max(40, min(98, hum)), 1)

    return {"co2": co2, "noise": noise, "temperature": temp, "pm25": pm25, "humidity": hum}


def build_document(sensor: dict, ts: datetime) -> dict:
    """Build a single MongoDB telemetry document."""
    profile = DISTRICT_PROFILES.get(sensor["locationId"], DISTRICT_PROFILES["ward_q5_01"])
    metrics = generate_metrics(ts, profile)
    received = ts + timedelta(seconds=random.uniform(0.1, 1.5))
    expire = ts + timedelta(days=TTL_DAYS)

    return {
        "sensorId":   sensor["sensorId"],
        "locationId": sensor["locationId"],
        "clusterId":  sensor["clusterId"],
        "data":       metrics,
        "location": {
            "type": "Point",
            "coordinates": [sensor["lng"], sensor["lat"]],
        },
        "quality": {
            "batteryLevel":  round(random.uniform(70, 100), 1),
            "signalStrength": round(random.uniform(-70, -30), 1),
        },
        "timestamp":  ts,
        "receivedAt": received,
        "expireAt":   expire,
    }


# ============================================================================
# Main seeder
# ============================================================================
def seed(mongodb_uri: str = None):
    """Seed MongoDB with 7 days of telemetry data for all 33 sensors."""
    import os
    from pymongo import MongoClient, ASCENDING, DESCENDING, GEOSPHERE
    from pymongo.errors import BulkWriteError

    uri = mongodb_uri or os.getenv(
        "MONGODB_URI",
        "mongodb://admin:admin123@mongodb:27017/smart_city?authSource=admin",
    )
    db_name = os.getenv("MONGO_DATABASE", "smart_city")

    logger.info(f"Connecting to MongoDB at {uri}...")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[db_name]
    col = db["telemetry"]

    # ------------------------------------------------------------------
    # 1. Ensure indexes
    # ------------------------------------------------------------------
    logger.info("Ensuring MongoDB indexes...")
    col.create_index([("expireAt", ASCENDING)], name="ttl_expire_at", expireAfterSeconds=0)
    col.create_index([("sensorId", ASCENDING), ("timestamp", DESCENDING)], name="sensor_timestamp_unique", unique=True)
    col.create_index([("locationId", ASCENDING), ("timestamp", DESCENDING)], name="location_timestamp_index")
    col.create_index([("clusterId", ASCENDING), ("timestamp", DESCENDING)], name="cluster_timestamp_index")
    col.create_index([("location", GEOSPHERE)], name="location_2dsphere")
    logger.info("Indexes ensured.")

    # ------------------------------------------------------------------
    # 2. Check if data already exists
    # ------------------------------------------------------------------
    existing = col.count_documents({})
    if existing > 1000:
        logger.info(f"Telemetry collection already has {existing} documents. Skipping seed.")
        client.close()
        return

    # ------------------------------------------------------------------
    # 3. Generate & insert data — two passes for tiered resolution
    # ------------------------------------------------------------------
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    legacy_start = now - timedelta(days=DAYS_TOTAL)
    legacy_end   = now - timedelta(days=DAYS_RECENT)
    recent_start = legacy_end

    legacy_readings = int((DAYS_TOTAL - DAYS_RECENT) * 24 * 60 / INTERVAL_LEGACY_MIN)
    recent_readings = int(DAYS_RECENT * 24 * 60 / INTERVAL_RECENT_MIN)
    total_docs = (legacy_readings + recent_readings) * len(SENSORS)
    logger.info(
        f"Generating {total_docs} telemetry documents — "
        f"{legacy_readings} hourly + {recent_readings} 5-minute readings × {len(SENSORS)} sensors"
    )

    BATCH_SIZE = 2000
    batch = []
    inserted_total = 0
    duplicates_total = 0
    t0 = time.time()

    def emit(ts: datetime):
        nonlocal batch, inserted_total, duplicates_total
        for sensor in SENSORS:
            batch.append(build_document(sensor, ts))
            if len(batch) >= BATCH_SIZE:
                ins, dup = _flush(col, batch)
                inserted_total += ins
                duplicates_total += dup
                batch = []
                if inserted_total % 50000 < BATCH_SIZE:
                    elapsed = time.time() - t0
                    pct = inserted_total / total_docs * 100
                    logger.info(f"  Progress: {inserted_total}/{total_docs} ({pct:.0f}%) – {elapsed:.1f}s")

    # Legacy / coarse pass first (older → recent so timestamps stay ordered)
    for i in range(legacy_readings):
        emit(legacy_start + timedelta(minutes=i * INTERVAL_LEGACY_MIN))

    # Recent / fine pass
    for i in range(recent_readings):
        emit(recent_start + timedelta(minutes=i * INTERVAL_RECENT_MIN))

    # Flush remaining
    if batch:
        ins, dup = _flush(col, batch)
        inserted_total += ins
        duplicates_total += dup

    elapsed = time.time() - t0
    logger.info(f"Seed complete: {inserted_total} inserted, {duplicates_total} duplicates in {elapsed:.1f}s")
    client.close()


def _flush(col, batch):
    """Bulk insert a batch, handling duplicate key errors."""
    from pymongo.errors import BulkWriteError
    try:
        result = col.insert_many(batch, ordered=False)
        return len(result.inserted_ids), 0
    except BulkWriteError as bwe:
        inserted = bwe.details.get("nInserted", 0)
        dups = sum(1 for e in bwe.details.get("writeErrors", []) if e.get("code") == 11000)
        return inserted, dups


if __name__ == "__main__":
    seed()
