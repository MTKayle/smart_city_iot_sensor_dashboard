# 📡 Smart City IoT Dashboard — System Architecture & Data Flows

## Tổng quan hệ thống

Hệ thống Smart City IoT Dashboard gồm **7 service** chạy trong Docker containers, xử lý dữ liệu từ 33 cảm biến IoT theo thời gian thực.

```mermaid
graph TB
    subgraph "IoT Layer"
        SIM["🏭 IoT Simulator<br/>33 sensors × 5 metrics<br/>every 5s"]
    end

    subgraph "Message Broker"
        MQTT["🔌 Mosquitto<br/>MQTT Broker<br/>QoS 1"]
    end

    subgraph "Queue Layer (DURABLE)"
        REDIS["🔴 Redis 7<br/>Stream: telemetry:stream<br/>AOF persistence<br/>MAXLEN ~10,000"]
    end

    subgraph "Application Layer"
        BE["⚙️ FastAPI Backend<br/>MQTT Consumer<br/>Worker Pool (3)<br/>REST API + WebSocket"]
    end

    subgraph "Storage Layer"
        MONGO["🍃 MongoDB 7<br/>Time-series telemetry<br/>30-day TTL<br/>GeoJSON indexes"]
        ORA["🔶 Oracle XE<br/>9 tables (v2 schema)<br/>Alerts, Sensors<br/>Locations, Analytics"]
    end

    subgraph "Presentation Layer"
        FE["🖥️ React Frontend<br/>Dashboard + Charts<br/>Map + Alerts"]
    end

    SIM -->|"MQTT publish<br/>sensors/+/telemetry"| MQTT
    MQTT -->|"subscribe"| BE
    BE -->|"XADD"| REDIS
    REDIS -->|"XREADGROUP"| BE
    BE -->|"batch insert"| MONGO
    BE -->|"INSERT/UPDATE"| ORA
    BE <-->|"WebSocket /ws"| FE
    FE -->|"REST /api/*"| BE
    BE -->|"query"| MONGO
    BE -->|"query"| ORA

    style REDIS fill:#dc382d,color:#fff,stroke:#a52a2a
    style MQTT fill:#3c1361,color:#fff
    style MONGO fill:#13aa52,color:#fff
    style ORA fill:#f80000,color:#fff
```

---

## 🏗️ Tại sao chuyển từ `asyncio.Queue` sang Redis Streams?

| Tiêu chí | `asyncio.Queue` (cũ) | Redis Streams (mới) |
|----------|----------------------|---------------------|
| **Durability** | ❌ Mất hết khi process crash | ✅ AOF + RDB persistence |
| **Crash recovery** | ❌ Không thể khôi phục | ✅ XREADGROUP + XACK → auto re-deliver |
| **Multi-process** | ❌ Single process only | ✅ Consumer groups, nhiều workers |
| **Observability** | ❌ Chỉ có `qsize()` | ✅ XINFO, XLEN, XPENDING |
| **Backpressure** | ❌ Drop khi full | ✅ MAXLEN trim oldest entries |
| **Message ordering** | ✅ FIFO | ✅ FIFO (stream ID ordering) |
| **Latency** | ~0ms (in-memory) | ~0.1ms (local Redis) |
| **Horizontal scale** | ❌ Không | ✅ Redis Cluster |

> [!IMPORTANT]
> Redis được cấu hình `appendonly yes` (AOF) nên mọi message đều được ghi xuống disk.
> Nếu backend crash, khi restart workers sẽ tự động re-process các message chưa XACK.

---

## 🔄 Luồng 1: Telemetry Ingestion (Luồng chính)

Đây là luồng cốt lõi — từ cảm biến đến dashboard.

```mermaid
sequenceDiagram
    participant S as 🏭 IoT Sensor
    participant M as 🔌 MQTT Broker
    participant C as 📥 MQTT Consumer<br/>(paho thread)
    participant R as 🔴 Redis Stream
    participant W as ⚙️ Worker Pool<br/>(3 async workers)
    participant MG as 🍃 MongoDB
    participant O as 🔶 Oracle
    participant WS as 🖥️ WebSocket<br/>Dashboard

    S->>M: PUBLISH sensors/{id}/telemetry (QoS 1)
    M->>C: DELIVER message
    
    Note over C: 1. Decode UTF-8<br/>2. JSON parse<br/>3. Pydantic validate

    C->>R: XADD telemetry:stream MAXLEN ~10000<br/>{payload: JSON}
    
    Note over R: ✅ Message persisted (AOF)<br/>Survives crash

    R->>W: XREADGROUP GROUP workers consumer-{i}<br/>COUNT 100 BLOCK 1000ms

    Note over W: Collect batch<br/>(up to 100 msgs OR 1s timeout)

    rect rgb(20, 20, 60)
        Note over W: 🔄 Enrich via Oracle (thread-pool)
        W->>O: SELECT lat, lng, clusterId, locationId<br/>FROM SENSOR_REGISTRY WHERE sensorId = ?
        O-->>W: geolocation data
        Note over W: Build GeoJSON Point<br/>Set expireAt = now + 30 days
    end

    rect rgb(10, 80, 40)
        Note over W,WS: ⚡ PARALLEL FAN-OUT (asyncio.gather)
        par Branch A: MongoDB
            W->>MG: batch_insert_telemetry(enriched_docs)
            MG-->>W: inserted=N, dupes=M
        and Branch B: Alert Engine
            W->>W: check_threshold_alerts()
            W->>W: check_predictive_alerts()
            W->>W: detect_anomalies()
            W->>O: INSERT INTO ALERTS (if triggered)
            W->>WS: broadcast({type: "alert", ...})
        and Branch C: WebSocket Broadcast
            W->>WS: broadcast({type: "telemetry", data: enriched})
            Note over WS: ⚡ Instant!<br/>No MongoDB round-trip
        end
    end

    W->>R: XACK telemetry:stream workers msg_id1 msg_id2 ...
    Note over R: ✅ Messages acknowledged<br/>Removed from pending list
```

### Chi tiết từng bước

| Bước | Component | Hành động | Durable? |
|------|-----------|-----------|----------|
| 1 | IoT Sensor | Publish MQTT (QoS 1) | ✅ MQTT retry |
| 2 | MQTT Consumer | Validate + JSON parse | — |
| 3 | MQTT Consumer → Redis | `XADD` to stream | ✅ Redis AOF |
| 4 | Worker | `XREADGROUP BLOCK` (batch 100/1s) | ✅ Consumer group |
| 5 | Worker | Enrich via Oracle | — |
| 6a | Worker → MongoDB | Batch insert (parallel) | ✅ MongoDB journal |
| 6b | Worker → Alert Engine | Threshold/Predictive/Anomaly (parallel) | ✅ Oracle commit |
| 6c | Worker → WebSocket | Broadcast enriched data (parallel) | — (real-time) |
| 7 | Worker → Redis | `XACK` message IDs | ✅ Remove from pending |

---

## 🚨 Luồng 2: Alert Engine (Chi tiết)

Mỗi telemetry message được kiểm tra qua **3 engine** cho **4 metrics** (CO2, Noise, PM2.5, Humidity).

```mermaid
flowchart TD
    T["Enriched Telemetry<br/>(from Worker)"]
    
    T --> L1{"CO2 value?"}
    T --> L2{"Noise value?"}
    T --> L3{"PM2.5 value?"}
    T --> L4{"Humidity value?"}

    L1 -->|"not null"| E1["Engine × 3"]
    L2 -->|"not null"| E2["Engine × 3"]
    L3 -->|"not null"| E3["Engine × 3"]
    L4 -->|"not null"| E4["Engine × 3"]

    subgraph "3 Alert Engines (per metric)"
        direction TB
        TH["6.1 Threshold<br/>value > threshold?<br/>severity = f(exceedance%)"]
        PR["6.3 Predictive<br/>Linear Regression (last 20)<br/>predict 1h ahead<br/>R² > 0.7?"]
        AN["6.4 Anomaly<br/>Z-score (last 100)<br/>|Z| > 3?"]
    end

    E1 --> TH
    E1 --> PR
    E1 --> AN

    TH --> DD{"6.2 Deduplicate<br/>5-min window?"}
    PR --> DD
    AN --> DD

    DD -->|"duplicate"| SKIP["⏭️ Skip"]
    DD -->|"new"| CREATE["Create Alert"]

    CREATE --> ORA["Oracle INSERT<br/>ALERTS table"]
    CREATE --> CACHE["Update dedup cache"]
    CREATE --> WSBC["WebSocket broadcast<br/>{type: 'alert'}"]

    style TH fill:#e74c3c,color:#fff
    style PR fill:#3498db,color:#fff
    style AN fill:#9b59b6,color:#fff
    style DD fill:#f39c12,color:#000
```

### 6.1 — Threshold Alert (Ngưỡng cố định)

```
if value > threshold:
    exceedance_pct = ((value - threshold) / threshold) × 100%
    severity = lookup(exceedance_pct, ranges)
    → CREATE ALERT
```

| Metric | Threshold | Unit | 0% | 25% | 50% | 100% |
|--------|-----------|------|----|-----|-----|------|
| CO2 | 1000 | ppm | LOW | MEDIUM | HIGH | CRITICAL |
| Noise | 85 | dB | LOW | MEDIUM | HIGH | CRITICAL |
| PM2.5 | 55 | µg/m³ | LOW | MEDIUM | HIGH | CRITICAL |
| Humidity | 90 | % | LOW | MEDIUM | HIGH | CRITICAL |

### 6.3 — Predictive Alert (Dự đoán)

```
readings = MongoDB.query(sensorId, limit=20)  ← last 20 readings
model = LinearRegression().fit(timestamps, values)
r2 = model.score()

if r2 > 0.7:
    predicted = model.predict(now + 1_hour)
    if predicted > threshold:
        → CREATE ALERT (type=PREDICTIVE, confidence=r2)
```

### 6.4 — Anomaly Detection (Bất thường)

```
readings = MongoDB.query(sensorId, limit=100)  ← ~24 hours
mean = avg(values)
std  = stdev(values)
z    = (current_value - mean) / std

if |z| > 3:
    confidence = 1 - 1/z²
    → CREATE ALERT (type=ANOMALY, confidence)
```

### 6.2 — Deduplication (Chống trùng lặp)

```
cache_key = "{sensorId}:{metricType}:{alertType}"

# Tier 1: In-memory cache (O(1))
if cache[key] exists AND (now - cache[key]) < 5 minutes:
    → SKIP (duplicate)

# Tier 2: Oracle fallback (after restart, cache empty)
SELECT * FROM ALERTS
WHERE SensorID=? AND MetricType=? AND AlertType=?
AND CreatedAt >= CURRENT_TIMESTAMP - 5 MINUTES
```

### 6.5 — Alert Lifecycle

```mermaid
stateDiagram-v2
    [*] --> OPEN: Alert Created<br/>(auto by engine)
    OPEN --> ACKNOWLEDGED: acknowledge_alert(id)<br/>SET AcknowledgedAt
    OPEN --> RESOLVED: resolve_alert(id)<br/>SET ResolvedAt
    ACKNOWLEDGED --> RESOLVED: resolve_alert(id)<br/>SET ResolvedAt
    RESOLVED --> [*]
```

---

## 📊 Luồng 3: Analytics Pipeline (Scheduled)

Chạy tự động bởi APScheduler, tổng hợp dữ liệu theo giờ.

```mermaid
sequenceDiagram
    participant SCH as ⏰ APScheduler<br/>(hourly cron)
    participant AS as 📊 Analytics Service
    participant MG as 🍃 MongoDB
    participant ORA as 🔶 Oracle

    Note over SCH: Every hour at :00

    SCH->>AS: trigger hourly_aggregation()
    
    AS->>MG: Aggregation Pipeline<br/>$match (last 1 hour)<br/>$group by sensorId<br/>$avg, $max, $min, $stdDev
    MG-->>AS: aggregated results per sensor

    AS->>AS: Calculate Clean Score<br/>= 100 - (CO2_norm × 0.4 + Noise_norm × 0.3 + Temp_dev × 0.3)

    AS->>AS: Calculate AQI<br/>= EPA breakpoints from PM2.5

    AS->>ORA: INSERT INTO TELEMETRY_SUMMARY<br/>(SensorID, TimeBucket, Granularity='1h',<br/>AvgCO2, MaxCO2, MinCO2, StdDevCO2,<br/>AvgNoise, AvgPM25, AvgHumidity,<br/>CleanScore, AQI, DataPoints)
    ORA-->>AS: committed

    Note over AS: Also aggregate per cluster and location
```

---

## 🌐 Luồng 4: REST API

```mermaid
flowchart LR
    subgraph "Frontend (React)"
        FE["Dashboard Client"]
    end

    subgraph "Backend (FastAPI)"
        R1["GET /api/locations"]
        R2["GET /api/sensors"]
        R3["GET /api/telemetry/{id}"]
        R4["GET /api/alerts"]
        R5["GET /api/leaderboard"]
        R6["GET /api/sensors/{id}/analytics"]
        R7["GET /api/health"]
        R8["GET /pipeline/metrics"]
    end

    subgraph "Data Sources"
        ORA["Oracle"]
        MG["MongoDB"]
        RED["Redis"]
    end

    FE --> R1 --> ORA
    FE --> R2 --> ORA
    FE --> R3 --> MG
    FE --> R4 --> ORA
    FE --> R5 --> ORA
    FE --> R6 --> MG
    FE --> R7
    FE --> R8 --> RED
```

| Endpoint | Method | Source | Mô tả |
|----------|--------|-------|-------|
| `/api/health` | GET | — | Health check |
| `/api/locations` | GET | Oracle | Danh sách locations (hierarchy) |
| `/api/sensors` | GET | Oracle | Danh sách sensors (+ filter by location) |
| `/api/telemetry/{sensor_id}` | GET | MongoDB | Telemetry data (time range, auto-aggregate) |
| `/api/alerts` | GET | Oracle | Alerts (filter: level, location) |
| `/api/leaderboard` | GET | Oracle | Xếp hạng theo Clean Score |
| `/api/sensors/{id}/analytics` | GET | MongoDB | Moving averages (last 10 readings) |
| `/pipeline/metrics` | GET | Redis | Worker pool metrics |

---

## 📡 Luồng 5: WebSocket Real-time

```mermaid
sequenceDiagram
    participant FE as 🖥️ Dashboard
    participant WS as WebSocket /ws
    participant MGR as WebSocketManager
    participant WP as Worker Pool

    FE->>WS: Connect ws://host:8000/ws
    WS->>MGR: manager.connect(ws)
    MGR-->>FE: {type: "connection_ack"}

    loop Every 30s
        MGR-->>FE: {type: "heartbeat"}
    end

    Note over WP: Telemetry processed...
    WP->>MGR: broadcast({type: "telemetry", data: {...}})
    MGR-->>FE: {type: "telemetry", data: {...}}

    Note over WP: Alert triggered...
    WP->>MGR: broadcast({type: "alert", data: {...}})
    MGR-->>FE: {type: "alert", data: {...}}

    Note over WP: Alert lifecycle...
    WP->>MGR: broadcast({type: "alert_update", data: {alertId, status}})
    MGR-->>FE: {type: "alert_update", data: {...}}
```

### WebSocket Message Types

| Type | Direction | Payload |
|------|-----------|---------|
| `connection_ack` | Server → Client | `{message: "Connected successfully"}` |
| `heartbeat` | Server → Client | `{message: "Connection alive"}` |
| `telemetry` | Server → Client | Full enriched telemetry object |
| `alert` | Server → Client | Full alert object |
| `alert_update` | Server → Client | `{alertId, status, updatedAt}` |
| `ping` | Client → Server | `{}` |
| `pong` | Server → Client | `{}` |

---

## 🗄️ Database Schema

### Oracle (Relational — 9 tables)

```mermaid
erDiagram
    LOCATIONS ||--o{ SENSOR_CLUSTERS : "has"
    LOCATIONS ||--o{ SENSOR_REGISTRY : "contains"
    SENSOR_CLUSTERS ||--o{ SENSOR_REGISTRY : "groups"
    SENSOR_REGISTRY ||--o{ SENSOR_CAPABILITIES : "has"
    SENSOR_REGISTRY ||--o{ ALERTS : "triggers"
    SENSOR_CLUSTERS ||--o{ ALERTS : "triggers"
    LOCATIONS ||--o{ ALERTS : "belongs to"
    INCIDENTS ||--o{ INCIDENT_ALERTS : "links"
    ALERTS ||--o{ INCIDENT_ALERTS : "linked by"
    SENSOR_REGISTRY ||--o{ SENSOR_HEALTH_LOGS : "logs"
    SENSOR_REGISTRY ||--o{ TELEMETRY_SUMMARY : "aggregates"

    LOCATIONS {
        VARCHAR2 LocationID PK
        VARCHAR2 Name
        VARCHAR2 ParentID FK
        VARCHAR2 Type "City|District|Ward"
        NUMBER CenterLat
        NUMBER CenterLng
    }

    SENSOR_REGISTRY {
        VARCHAR2 SensorID PK
        VARCHAR2 LocationID FK
        VARCHAR2 ClusterID FK
        NUMBER Latitude
        NUMBER Longitude
        VARCHAR2 Status "Active|Offline|..."
    }

    ALERTS {
        VARCHAR2 AlertID PK
        VARCHAR2 SensorID FK
        VARCHAR2 AlertType "THRESHOLD|PREDICTIVE|ANOMALY"
        VARCHAR2 MetricType "CO2|Noise|PM25|Humidity"
        NUMBER Value
        NUMBER Threshold
        NUMBER PredictedValue
        NUMBER ConfidenceScore
        VARCHAR2 Severity "LOW|MEDIUM|HIGH|CRITICAL"
        VARCHAR2 Status "OPEN|ACKNOWLEDGED|RESOLVED"
        TIMESTAMP AcknowledgedAt
        TIMESTAMP ResolvedAt
    }

    TELEMETRY_SUMMARY {
        VARCHAR2 SummaryID PK
        TIMESTAMP TimeBucket
        VARCHAR2 Granularity "1h|1d"
        NUMBER AvgCO2
        NUMBER AvgNoise
        NUMBER AvgPM25
        NUMBER CleanScore
        NUMBER AQI
    }
```

### MongoDB (Time-series)

```javascript
// Collection: telemetry
{
  sensorId:   "sen_q1_01_co2",        // indexed
  locationId: "ward_q1",              // indexed
  clusterId:  "cluster_q1",           // indexed
  data: {
    co2:         450.5,
    noise:       62.3,
    temperature: 28.1,
    pm25:        35.2,
    humidity:    72.0
  },
  location: {                          // 2dsphere index
    type: "Point",
    coordinates: [106.6297, 10.8231]
  },
  quality: {
    batteryLevel:   85.0,
    signalStrength: -45.2
  },
  timestamp:  ISODate("2026-05-03T14:00:00Z"),
  receivedAt: ISODate("2026-05-03T14:00:01Z"),
  expireAt:   ISODate("2026-06-02T14:00:01Z")  // TTL 30 days
}

// Indexes:
// - {expireAt: 1}            TTL index (auto-delete after 30 days)
// - {sensorId: 1, timestamp: -1}    compound
// - {locationId: 1, timestamp: -1}  compound
// - {clusterId: 1, timestamp: -1}   compound
// - {location: "2dsphere"}          geospatial
```

### Redis (Message Queue)

```
Stream: telemetry:stream
├── MAXLEN ~10,000 (auto-trim oldest)
├── Consumer Group: "workers"
│   ├── consumer-0
│   ├── consumer-1
│   └── consumer-2
├── AOF persistence: appendonly yes
└── Memory limit: 256MB (allkeys-lru eviction)
```

---

## 🐳 Service Dependencies

```mermaid
graph TD
    MQ["Mosquitto<br/>:1883"] 
    MDB["MongoDB<br/>:27017"]
    ORA["Oracle XE<br/>:1521"]
    RED["Redis<br/>:6379"]
    BE["Backend<br/>:8000"]
    FE["Frontend<br/>:3000"]
    SIM["IoT Simulator"]

    BE -->|depends_on healthy| MDB
    BE -->|depends_on healthy| ORA
    BE -->|depends_on healthy| RED
    BE -->|depends_on started| MQ
    FE -->|depends_on| BE
    SIM -->|depends_on| MQ

    style RED fill:#dc382d,color:#fff
    style MDB fill:#13aa52,color:#fff
    style ORA fill:#f80000,color:#fff
    style MQ fill:#3c1361,color:#fff
    style BE fill:#009688,color:#fff
    style FE fill:#61dafb,color:#000
```

---

## ⚙️ Environment Variables

| Variable | Default | Service | Mô tả |
|----------|---------|---------|-------|
| `MQTT_BROKER_HOST` | mosquitto | Backend, Simulator | MQTT broker hostname |
| `MQTT_BROKER_PORT` | 1883 | Backend, Simulator | MQTT broker port |
| `MONGODB_URI` | mongodb://admin:admin123@mongodb:27017/... | Backend | MongoDB connection string |
| `ORACLE_USER` | SMARTCITY | Backend | Oracle app schema user |
| `ORACLE_PASSWORD` | SmartCity2026! | Backend | Oracle app user password |
| `ORACLE_DSN` | oracle-xe:1521/XEPDB1 | Backend | Oracle TNS connect string |
| `REDIS_URL` | redis://redis:6379/0 | Backend | Redis Streams URL |
| `REACT_APP_API_URL` | http://localhost:8000 | Frontend | Backend API base URL |
| `REACT_APP_WS_URL` | ws://localhost:8000/ws | Frontend | WebSocket endpoint |

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI entry point + lifespan
│   ├── core/
│   │   ├── config.py              # Settings (env vars)
│   │   └── websocket_manager.py   # WebSocket broadcast manager
│   ├── messaging/
│   │   ├── mqtt_consumer.py       # MQTT subscriber → Redis XADD
│   │   └── worker_pool.py         # Redis Streams worker pool (3 workers)
│   ├── services/
│   │   ├── alert_service.py       # Threshold + Predictive + Anomaly + Lifecycle
│   │   ├── telemetry_service.py   # Enrichment + validation (legacy)
│   │   ├── analytics_service.py   # Moving averages + Clean Score
│   │   └── scheduler.py           # APScheduler hourly aggregation
│   ├── db/
│   │   ├── oracle_client.py       # Oracle connection pool + CRUD
│   │   ├── mongodb_client.py      # MongoDB client + batch insert
│   │   └── sql/                   # Schema v2 + seed data
│   ├── models/                    # Pydantic models
│   └── api/
│       ├── routes.py              # REST endpoints
│       └── websocket.py           # WebSocket /ws endpoint
├── tests/
│   └── test_alert_service_v2.py   # 25+ alert engine tests
├── requirements.txt               # Python deps (+ scikit-learn, numpy, redis)
└── Dockerfile
```
