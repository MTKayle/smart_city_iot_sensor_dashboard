# Auto-Init Setup — One Command Deployment

## Usage

```bash
# Fresh start (first time or after code changes)
docker compose down -v
docker compose up --build -d

# Subsequent starts (data persists)
docker compose up -d
```

> [!NOTE]
> Oracle XE cold-start (fresh volume) takes ~3-5 minutes on Windows Docker Desktop. 
> If backend fails to start on first run, just wait and run `docker compose up -d backend` once Oracle is healthy.

## What Happens Automatically

### 1. Oracle Schema v2 (`startup.sh` → PL/SQL-aware parser)
| Object | Count |
|---|---|
| Tables | 9 (LOCATIONS, SENSOR_CLUSTERS, SENSOR_REGISTRY, SENSOR_CAPABILITIES, ALERTS, INCIDENTS, INCIDENT_ALERTS, SENSOR_HEALTH_LOGS, TELEMETRY_SUMMARY) |
| Views | 1 (LOCATION_HIERARCHY) |
| Triggers | 5 |
| Indexes | 23 |
| Seed Data | 13 locations, 4 clusters, 33 sensors, 165 capabilities |

### 2. MongoDB Indexes + Telemetry Seed (`seed_telemetry.py`)
| Index | Type | Purpose |
|---|---|---|
| `ttl_expire_at` | TTL | Auto-expire docs when `expireAt` passes |
| `sensor_timestamp_unique` | Compound + Unique | Efficient per-sensor queries, duplicate prevention |
| `location_timestamp_index` | Compound | Location-based time queries |
| `cluster_timestamp_index` | Compound | Cluster aggregation queries |
| `location_2dsphere` | Geospatial | Nearby sensor queries (`$near`) |

**Telemetry seed:** 66,528 documents (33 sensors × 2,016 readings × 7 days @ 5-min intervals)

Data features realistic patterns:
- **Rush-hour peaks** (8am, 6pm) for CO2, noise, PM2.5
- **Diurnal temperature cycle** (peaks ~2pm, HCM tropical range)
- **Weekend dampening** (40% less traffic impact)
- **Per-district profiles** (District 1 more polluted than District 5)

### 3. Idempotency
- Oracle: Checks if 33 sensors exist → skips if already initialized
- MongoDB: Checks if >1000 docs exist → skips if already seeded
- Indexes: `createIndex` is idempotent (safe to re-run)

## Files Changed

| File | Change |
|---|---|
| [startup.sh](file:///d:/DB%20Advance/smart-city/smart_city_iot_sensor_dashboard/backend/startup.sh) | Rewritten: v2 schema, PL/SQL parser, MongoDB seed |
| [seed_telemetry.py](file:///d:/DB%20Advance/smart-city/smart_city_iot_sensor_dashboard/backend/app/db/seed_telemetry.py) | **New**: 7-day realistic telemetry data generator |
| [mongodb_client.py](file:///d:/DB%20Advance/smart-city/smart_city_iot_sensor_dashboard/backend/app/db/mongodb_client.py) | Added: batch_insert, geospatial, cluster queries, aggregated queries |
| [oracle_schema_v2.sql](file:///d:/DB%20Advance/smart-city/smart_city_iot_sensor_dashboard/backend/app/db/sql/oracle_schema_v2.sql) | Added LOCATION_HIERARCHY view |
| [oracle_client.py](file:///d:/DB%20Advance/smart-city/smart_city_iot_sensor_dashboard/backend/app/db/oracle_client.py) | Disabled old _initialize_schema (handled by startup.sh) |
| [docker-compose.yml](file:///d:/DB%20Advance/smart-city/smart_city_iot_sensor_dashboard/docker-compose.yml) | Removed old v1 init mounts, increased Oracle health timeouts |
| [__init__.py](file:///d:/DB%20Advance/smart-city/smart_city_iot_sensor_dashboard/backend/app/models/__init__.py) | Added `Sensor = SensorRegistry` backward-compat alias |
