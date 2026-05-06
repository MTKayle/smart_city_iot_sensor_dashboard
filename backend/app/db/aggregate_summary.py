"""
Aggregate raw MongoDB telemetry into Oracle TELEMETRY_SUMMARY.

Why both stores: MongoDB is the high-frequency hot tier (every 5 min × 33
sensors) but is unsuitable for long-range relational analytics. Oracle holds
pre-aggregated summaries at HOURLY / DAILY / WEEKLY granularity per location
(district / ward / cluster / sensor) so the analytics & comparison views
can query historical trends with a simple WHERE TIMEBUCKET BETWEEN ... clause.

Idempotent: re-running the aggregator updates existing rows via MERGE, never
creates duplicates.

Usage:
    python -m app.db.aggregate_summary --granularity HOURLY --days 30
    python -m app.db.aggregate_summary --granularity DAILY  --days 365
    python -m app.db.aggregate_summary --granularity WEEKLY --days 365
"""

import argparse
import logging
import os
import statistics
import time
from datetime import datetime, timedelta, timezone
from typing import Iterable

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("summary_aggregator")


GRANULARITY_BUCKETS = {
    "HOURLY": timedelta(hours=1),
    "DAILY":  timedelta(days=1),
    "WEEKLY": timedelta(days=7),
}


def floor_to_bucket(ts: datetime, gran: str) -> datetime:
    """Floor a timestamp to its bucket boundary."""
    if gran == "HOURLY":
        return ts.replace(minute=0, second=0, microsecond=0)
    if gran == "DAILY":
        return ts.replace(hour=0, minute=0, second=0, microsecond=0)
    if gran == "WEEKLY":
        # ISO week-start: Monday 00:00
        floored = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        return floored - timedelta(days=floored.weekday())
    raise ValueError(f"Unknown granularity {gran}")


def compute_aqi_from_pm25(pm25: float | None) -> int | None:
    """US EPA breakpoints (24-hour PM2.5)."""
    if pm25 is None:
        return None
    bps = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500),
    ]
    p = max(0.0, pm25)
    for lo, hi, ilo, ihi in bps:
        if lo <= p <= hi:
            return int(ilo + (ihi - ilo) * (p - lo) / (hi - lo))
    return 500


def compute_clean_score(pm25: float | None, co2: float | None, noise: float | None) -> int | None:
    """Match the leaderboard formula: 100 - weighted normalised pollutants."""
    if pm25 is None or co2 is None or noise is None:
        return None
    n_pm25  = min(1.0, pm25 / 250.0)
    n_co2   = min(1.0, max(0.0, (co2 - 400) / 1600))
    n_noise = min(1.0, max(0.0, (noise - 30) / 70))
    score = 100 - (n_pm25 * 40 + n_co2 * 30 + n_noise * 30)
    return max(0, min(100, int(round(score))))


# ---------------------------------------------------------------------------
def fetch_buckets(mongo_col, location_ids: list[str], start: datetime, end: datetime,
                  bucket_seconds: int) -> dict[tuple[str, datetime], dict]:
    """
    One Mongo aggregation pipeline groups telemetry by (locationId, bucket).
    Returns: {(locationId, bucket_start_dt): {avg_*, max_*, min_*, stddev_*, n}}
    """
    pipeline = [
        {"$match": {
            "locationId": {"$in": location_ids},
            "timestamp": {"$gte": start, "$lt": end},
        }},
        {"$project": {
            "locationId": 1,
            # Bucket the timestamp by floor((epoch_seconds) / bucket_seconds) * bucket_seconds.
            "bucket": {
                "$toDate": {
                    "$multiply": [
                        bucket_seconds * 1000,
                        {"$floor": {"$divide": [
                            {"$toLong": "$timestamp"},
                            bucket_seconds * 1000,
                        ]}},
                    ],
                },
            },
            "co2":   {"$ifNull": ["$data.co2", None]},
            "noise": {"$ifNull": ["$data.noise", None]},
            "temperature": {"$ifNull": ["$data.temperature", None]},
            "pm25": {"$ifNull": ["$data.pm25", None]},
            "humidity": {"$ifNull": ["$data.humidity", None]},
        }},
        {"$group": {
            "_id": {"locationId": "$locationId", "bucket": "$bucket"},
            "avgCO2": {"$avg": "$co2"},
            "maxCO2": {"$max": "$co2"},
            "minCO2": {"$min": "$co2"},
            "stddevCO2": {"$stdDevPop": "$co2"},
            "avgNoise": {"$avg": "$noise"},
            "maxNoise": {"$max": "$noise"},
            "minNoise": {"$min": "$noise"},
            "stddevNoise": {"$stdDevPop": "$noise"},
            "avgTemp": {"$avg": "$temperature"},
            "maxTemp": {"$max": "$temperature"},
            "minTemp": {"$min": "$temperature"},
            "stddevTemp": {"$stdDevPop": "$temperature"},
            "avgPM25": {"$avg": "$pm25"},
            "maxPM25": {"$max": "$pm25"},
            "avgHumidity": {"$avg": "$humidity"},
            "n": {"$sum": 1},
        }},
    ]

    out: dict[tuple[str, datetime], dict] = {}
    for row in mongo_col.aggregate(pipeline, allowDiskUse=True):
        key = (row["_id"]["locationId"], row["_id"]["bucket"])
        out[key] = row
    return out


def expand_district_to_wards(oracle_cur, district_ids: list[str]) -> dict[str, list[str]]:
    """For a list of district IDs, return {districtId: [wardId, ...]}."""
    if not district_ids:
        return {}
    placeholders = ",".join([f":d{i}" for i in range(len(district_ids))])
    binds = {f"d{i}": v for i, v in enumerate(district_ids)}
    oracle_cur.execute(
        f"SELECT LocationID, ParentID FROM LOCATIONS WHERE Type='Ward' AND ParentID IN ({placeholders})",
        binds,
    )
    out: dict[str, list[str]] = {d: [] for d in district_ids}
    for ward_id, parent_id in oracle_cur:
        if parent_id in out:
            out[parent_id].append(ward_id)
    return out


# ---------------------------------------------------------------------------
def upsert_summary(oracle_cur, *, summary_id: str, location_id: str,
                   timebucket: datetime, granularity: str, agg: dict) -> None:
    avg_pm25 = agg.get("avgPM25")
    avg_co2  = agg.get("avgCO2")
    avg_noise = agg.get("avgNoise")
    aqi = compute_aqi_from_pm25(avg_pm25)
    clean = compute_clean_score(avg_pm25, avg_co2, avg_noise)

    sql = """
    MERGE INTO TELEMETRY_SUMMARY t
    USING (SELECT :summary_id AS SummaryID FROM dual) s
    ON (t.SummaryID = s.SummaryID)
    WHEN MATCHED THEN UPDATE SET
        AvgCO2 = :avg_co2, MaxCO2 = :max_co2, MinCO2 = :min_co2, StddevCO2 = :std_co2,
        AvgNoise = :avg_noise, MaxNoise = :max_noise, MinNoise = :min_noise, StddevNoise = :std_noise,
        AvgTemperature = :avg_temp, MaxTemperature = :max_temp, MinTemperature = :min_temp, StddevTemperature = :std_temp,
        AvgPM25 = :avg_pm25, MaxPM25 = :max_pm25,
        AvgHumidity = :avg_humidity,
        AQI = :aqi, CleanScore = :clean,
        DataPoints = :data_points,
        DataCompleteness = :completeness
    WHEN NOT MATCHED THEN INSERT (
        SummaryID, LocationID, TimeBucket, Granularity,
        AvgCO2, MaxCO2, MinCO2, StddevCO2,
        AvgNoise, MaxNoise, MinNoise, StddevNoise,
        AvgTemperature, MaxTemperature, MinTemperature, StddevTemperature,
        AvgPM25, MaxPM25, AvgHumidity,
        AQI, CleanScore,
        DataPoints, DataCompleteness
    ) VALUES (
        :summary_id, :location_id, :timebucket, :granularity,
        :avg_co2, :max_co2, :min_co2, :std_co2,
        :avg_noise, :max_noise, :min_noise, :std_noise,
        :avg_temp, :max_temp, :min_temp, :std_temp,
        :avg_pm25, :max_pm25, :avg_humidity,
        :aqi, :clean,
        :data_points, :completeness
    )
    """
    oracle_cur.execute(sql, {
        "summary_id": summary_id,
        "location_id": location_id,
        "timebucket": timebucket,
        "granularity": granularity,
        "avg_co2":  agg.get("avgCO2"),
        "max_co2":  agg.get("maxCO2"),
        "min_co2":  agg.get("minCO2"),
        "std_co2":  agg.get("stddevCO2"),
        "avg_noise":  agg.get("avgNoise"),
        "max_noise":  agg.get("maxNoise"),
        "min_noise":  agg.get("minNoise"),
        "std_noise":  agg.get("stddevNoise"),
        "avg_temp":   agg.get("avgTemp"),
        "max_temp":   agg.get("maxTemp"),
        "min_temp":   agg.get("minTemp"),
        "std_temp":   agg.get("stddevTemp"),
        "avg_pm25":   agg.get("avgPM25"),
        "max_pm25":   agg.get("maxPM25"),
        "avg_humidity": agg.get("avgHumidity"),
        "aqi": aqi,
        "clean": clean,
        "data_points": agg.get("n"),
        "completeness": 1.0,
    })


def merge_aggs(buckets: list[dict]) -> dict | None:
    """Roll up multiple ward-bucket aggregates into one district-bucket aggregate."""
    items = [b for b in buckets if b]
    if not items:
        return None
    total_n = sum(b["n"] for b in items)

    def w_avg(field: str) -> float | None:
        vals = [(b[field], b["n"]) for b in items if b.get(field) is not None]
        if not vals: return None
        return sum(v * n for v, n in vals) / sum(n for _, n in vals)

    return {
        "n": total_n,
        "avgCO2":   w_avg("avgCO2"),
        "maxCO2":   max((b["maxCO2"] for b in items if b.get("maxCO2") is not None), default=None),
        "minCO2":   min((b["minCO2"] for b in items if b.get("minCO2") is not None), default=None),
        "stddevCO2": statistics.fmean(b["stddevCO2"] for b in items if b.get("stddevCO2") is not None) if any(b.get("stddevCO2") for b in items) else None,
        "avgNoise":   w_avg("avgNoise"),
        "maxNoise":   max((b["maxNoise"] for b in items if b.get("maxNoise") is not None), default=None),
        "minNoise":   min((b["minNoise"] for b in items if b.get("minNoise") is not None), default=None),
        "stddevNoise": statistics.fmean(b["stddevNoise"] for b in items if b.get("stddevNoise") is not None) if any(b.get("stddevNoise") for b in items) else None,
        "avgTemp":   w_avg("avgTemp"),
        "maxTemp":   max((b["maxTemp"] for b in items if b.get("maxTemp") is not None), default=None),
        "minTemp":   min((b["minTemp"] for b in items if b.get("minTemp") is not None), default=None),
        "stddevTemp": statistics.fmean(b["stddevTemp"] for b in items if b.get("stddevTemp") is not None) if any(b.get("stddevTemp") for b in items) else None,
        "avgPM25":   w_avg("avgPM25"),
        "maxPM25":   max((b["maxPM25"] for b in items if b.get("maxPM25") is not None), default=None),
        "avgHumidity": w_avg("avgHumidity"),
    }


# ---------------------------------------------------------------------------
def aggregate(granularity: str, days: int) -> None:
    from pymongo import MongoClient
    import oracledb

    bucket_delta = GRANULARITY_BUCKETS[granularity]
    bucket_seconds = int(bucket_delta.total_seconds())

    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = floor_to_bucket(end - timedelta(days=days), granularity)

    # Mongo
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://admin:admin123@mongodb:27017/smart_city?authSource=admin")
    db_name   = os.getenv("MONGO_DATABASE", "smart_city")
    mclient = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    mclient.admin.command("ping")
    mcol = mclient[db_name]["telemetry"]

    # Oracle
    dsn = os.getenv("ORACLE_DSN", "oracle-xe:1521/XEPDB1")
    user = os.getenv("ORACLE_USER", "system")
    pwd  = os.getenv("ORACLE_PASSWORD", "OraclePass123")
    oconn = oracledb.connect(user=user, password=pwd, dsn=dsn)
    ocur = oconn.cursor()

    # Districts and wards
    ocur.execute("SELECT LocationID FROM LOCATIONS WHERE Type='District'")
    districts = [r[0] for r in ocur]
    district_to_wards = expand_district_to_wards(ocur, districts)
    all_wards = [w for ws in district_to_wards.values() for w in ws]

    logger.info(
        f"Aggregating {granularity} from {start.isoformat()} → {end.isoformat()} "
        f"({len(districts)} districts, {len(all_wards)} wards)"
    )

    t0 = time.time()
    ward_bucket_aggs = fetch_buckets(mcol, all_wards, start, end, bucket_seconds)
    logger.info(f"  Mongo aggregation: {len(ward_bucket_aggs)} ward-bucket rows in {time.time()-t0:.1f}s")

    inserted = 0

    # 1. Ward-level summaries — store at LOCATIONID = wardId.
    for (ward_id, bucket), agg in ward_bucket_aggs.items():
        sid = f"loc_{ward_id}_{bucket.strftime('%Y%m%d%H%M')}_{granularity}"
        upsert_summary(
            ocur, summary_id=sid, location_id=ward_id,
            timebucket=bucket, granularity=granularity, agg=agg,
        )
        inserted += 1

    oconn.commit()

    # 2. District-level summaries — roll up wards in each bucket.
    # Bucketise: {(districtId, bucket): [ward_aggs...]}
    buckets_by_district: dict[tuple[str, datetime], list[dict]] = {}
    for (ward_id, bucket), agg in ward_bucket_aggs.items():
        # Find district from ward
        for d_id, ward_list in district_to_wards.items():
            if ward_id in ward_list:
                buckets_by_district.setdefault((d_id, bucket), []).append(agg)
                break

    for (d_id, bucket), wards_aggs in buckets_by_district.items():
        rolled = merge_aggs(wards_aggs)
        if rolled is None: continue
        sid = f"loc_{d_id}_{bucket.strftime('%Y%m%d%H%M')}_{granularity}"
        upsert_summary(
            ocur, summary_id=sid, location_id=d_id,
            timebucket=bucket, granularity=granularity, agg=rolled,
        )
        inserted += 1

    # 3. City-level summaries — roll up all districts per bucket.
    buckets_by_city: dict[datetime, list[dict]] = {}
    for (d_id, bucket), wards_aggs in buckets_by_district.items():
        rolled = merge_aggs(wards_aggs)
        if rolled: buckets_by_city.setdefault(bucket, []).append(rolled)

    for bucket, district_aggs in buckets_by_city.items():
        rolled = merge_aggs(district_aggs)
        if rolled is None: continue
        sid = f"loc_city_hcmc_{bucket.strftime('%Y%m%d%H%M')}_{granularity}"
        upsert_summary(
            ocur, summary_id=sid, location_id="city_hcmc",
            timebucket=bucket, granularity=granularity, agg=rolled,
        )
        inserted += 1

    oconn.commit()
    logger.info(f"Done — {inserted} summary rows in {time.time()-t0:.1f}s")

    ocur.close()
    oconn.close()
    mclient.close()


# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--granularity", choices=["HOURLY", "DAILY", "WEEKLY"], default="HOURLY")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--all", action="store_true",
                        help="Run all three granularities at sensible windows.")
    args = parser.parse_args()

    if args.all:
        # Hourly for last 30 days, daily for full year, weekly for full year.
        for g, d in [("HOURLY", 35), ("DAILY", 365), ("WEEKLY", 365)]:
            logger.info(f"=== {g} (last {d} days) ===")
            aggregate(g, d)
    else:
        aggregate(args.granularity, args.days)


if __name__ == "__main__":
    main()
