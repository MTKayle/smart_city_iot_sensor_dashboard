# Smart City IoT Sensor Dashboard - System Architecture

## 📋 Project Overview

**Smart City IoT Sensor Dashboard** là hệ thống giám sát môi trường thời gian thực cho thành phố thông minh, thu thập và phân tích dữ liệu từ mạng lưới cảm biến IoT phân tán.

### Key Metrics
- **Data Collection**: 5-second intervals per sensor
- **Metrics Monitored**: CO2 (ppm), Noise (dB), Temperature (°C)
- **Data Retention**: 30 days auto-cleanup
- **Real-time Updates**: WebSocket push notifications
- **Alert Thresholds**: CO2 > 1000 ppm, Noise > 85 dB

---

## 🏗️ System Architecture

### Architecture Pattern
**Microservices + Event-Driven Architecture + Hybrid Database**

```
┌─────────────────────────────────────────────────────────────────┐
│                    IoT Sensors (Simulators)                     │
│              Generate telemetry every 5 seconds                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ MQTT Publish
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MQTT Broker (Mosquitto)                       │
│                  Pub/Sub Message Transport                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ Subscribe
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Services (FastAPI)                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MQTT Consumer → Telemetry Handler → Alert Engine       │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  REST API Endpoints (CRUD Operations)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  WebSocket Server (Real-time Push)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Analytics Module (Moving Average, Clean Score)         │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────┬─────────────────────────────┬────────────────────┘
               │                             │
               ▼                             ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│   MongoDB (NoSQL)        │    │   Oracle SQL (RDBMS)     │
│ ─────────────────────    │    │ ─────────────────────    │
│ • Telemetry time-series  │    │ • Location hierarchy     │
│ • TTL: 30 days           │    │ • Sensor registry        │
│ • High-frequency writes  │    │ • Alerts                 │
│ • Compound indexes       │    │ • Analytics summaries    │
└──────────────────────────┘    └──────────────────────────┘
               │                             │
               └──────────────┬──────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Frontend Dashboard (React)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Map View    │  │  Chart View  │  │  Leaderboard │          │
│  │  (Leaflet)   │  │  (Chart.js)  │  │  (Rankings)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────────────────────────────────────────┐           │
│  │  Alerts Panel (Real-time Notifications)         │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technology Stack

### Backend

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Python 3.11** | Backend language | • Excellent IoT/data processing libraries<br>• Fast development<br>• Strong typing with Pydantic |
| **FastAPI** | REST API framework | • High performance (async support)<br>• Auto OpenAPI docs<br>• Built-in validation with Pydantic<br>• WebSocket support |
| **Pydantic** | Data validation | • Automatic validation<br>• Type safety<br>• JSON serialization<br>• OpenAPI schema generation |
| **cx_Oracle** | Oracle database driver | • Official Oracle driver<br>• Connection pooling<br>• High performance |
| **PyMongo** | MongoDB driver | • Official MongoDB driver<br>• Simple API<br>• Connection pooling |
| **paho-mqtt** | MQTT client | • Lightweight<br>• Reliable pub/sub<br>• IoT standard protocol |

### Frontend
| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **React 18** | UI framework | • Component-based<br>• Large ecosystem<br>• Real-time updates support |
| **TypeScript** | Type safety | • Catch errors at compile time<br>• Better IDE support<br>• Maintainable code |
| **Leaflet** | Map visualization | • Open source<br>• Lightweight<br>• Rich plugin ecosystem |
| **Chart.js** | Time-series charts | • Simple API<br>• Responsive<br>• Real-time data support |
| **Axios** | HTTP client | • Promise-based<br>• Interceptors<br>• Error handling |

### Infrastructure
| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Docker** | Containerization | • Consistent environments<br>• Easy deployment<br>• Isolation |
| **Docker Compose** | Orchestration | • Multi-container management<br>• Service dependencies<br>• Network configuration |
| **Mosquitto** | MQTT broker | • Lightweight<br>• Open source<br>• Production-ready |
| **MongoDB** | Time-series DB | • High write throughput<br>• TTL indexes (auto-cleanup)<br>• Flexible schema |
| **Oracle SQL** | Relational DB | • ACID transactions<br>• Complex queries (recursive CTE)<br>• Data integrity |

---

## 🔄 Data Flow Architecture

### Flow 1: Telemetry Collection (Real-time)
```
IoT Sensor (every 5s)
    │ Generate: CO2, Noise, Temperature
    ▼
MQTT Publish
    │ Topic: sensors/{sensorId}/telemetry
    ▼
MQTT Broker (Mosquitto)
    │ Message Queue
    ▼
Backend MQTT Consumer
    │ Parse & Validate (Pydantic)
    ▼
┌───────────────────────────────────┐
│  Telemetry Handler (Service)     │
│  ├─ Insert → MongoDB              │
│  ├─ Check Thresholds              │
│  └─ Trigger Alert Engine          │
└───────────────┬───────────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
   MongoDB Store    Alert Engine
   (Time-series)         │
                         ▼
                   Oracle Store
                   (Alerts)
                         │
                         ▼
                 WebSocket Broadcast
                         │
                         ▼
                   Frontend Update
                   (Real-time)
```

### Flow 2: Dashboard Query (Request-Response)
```
User Action (Click sensor on map)
    │
    ▼
Frontend Request
    │ GET /api/telemetry/{sensorId}
    ▼
Backend REST API
    │ routes.py (Controller)
    ▼
Analytics Module (Service)
    │ calculate_moving_average()
    ▼
MongoDB Client (Repository)
    │ query_telemetry(limit=10)
    ▼
MongoDB Query
    │ Use compound index (sensorId, timestamp)
    ▼
Return Data
    │ JSON response
    ▼
Frontend Chart Update
    │ Chart.js renders
    ▼
User Sees Visualization
```

### Flow 3: Alert Generation (Event-Driven)
```
Telemetry: CO2 = 1250 ppm (> 1000 threshold)
    │
    ▼
Alert Engine (Service)
    │ Business Logic:
    │ ├─ Check deduplication (5-min window)
    │ ├─ Determine level (HIGH)
    │ └─ Generate AlertID (UUID)
    ▼
Oracle Client (Repository)
    │ INSERT INTO ALERTS
    ▼
Oracle Store
    │ Persist alert
    ▼
WebSocket Manager
    │ Broadcast to all clients
    ▼
Frontend Alerts Panel
    │ Show notification (red badge)
    ▼
User Notified
```

---

## 🎨 System Components

### 1. IoT Simulator
**Purpose**: Mô phỏng cảm biến IoT thực tế

**Functionality**:
- Generate random sensor data (CO2: 300-2000 ppm, Noise: 30-100 dB, Temp: 15-35°C)
- Publish to MQTT every 5 seconds
- Support multiple sensors concurrently
- Auto-reconnect on connection loss

**Technology**: Python + paho-mqtt

---

### 2. MQTT Broker (Mosquitto)
**Purpose**: Message transport layer cho IoT devices

**Functionality**:
- Receive telemetry from sensors
- Route messages to subscribers
- Handle connection management
- Persist messages (optional)

**Why MQTT?**
- Lightweight protocol (ideal for IoT)
- Pub/Sub pattern (decoupling)
- QoS levels (reliability)
- Low bandwidth usage

---

### 3. Backend Services (FastAPI)
**Purpose**: Core business logic và data processing


**Modules**:

#### a) MQTT Consumer
- Subscribe to `sensors/+/telemetry` topic
- Parse JSON messages
- Validate with Pydantic models
- Trigger telemetry handler

#### b) Telemetry Handler (Service Layer)
- Insert telemetry → MongoDB
- Check alert thresholds
- Trigger alert engine
- Broadcast to WebSocket clients

#### c) Alert Engine (Service Layer)
- Evaluate thresholds (CO2 > 1000, Noise > 85)
- Deduplication logic (5-minute window)
- Generate AlertID (UUID)
- Store alerts → Oracle
- Broadcast to WebSocket clients

#### d) Analytics Module (Service Layer)
- Calculate moving averages (last 10 readings)
- Compute Clean Score: `100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)`
- Daily aggregation (scheduled task)
- Store summaries → Oracle

#### e) REST API (Controller Layer)
- GET `/api/locations` - Location hierarchy
- GET `/api/sensors` - Sensor list
- GET `/api/telemetry/{sensorId}` - Historical data
- GET `/api/sensors/{sensorId}/analytics` - Moving averages
- GET `/api/alerts` - Alert list with filters
- GET `/api/leaderboard` - Clean Score rankings

#### f) WebSocket Server
- Endpoint: `/ws`
- Connection management
- Broadcast telemetry updates
- Broadcast alerts
- Client isolation

**Technology**: Python FastAPI + Uvicorn (ASGI server)

---

### 4. MongoDB (Time-Series Database)
**Purpose**: High-frequency telemetry storage

**Schema**:
```javascript
{
  sensorId: String,
  locationId: String,
  co2: Number,
  noise: Number,
  temperature: Number,
  timestamp: ISODate
}
```

**Indexes**:
- TTL Index: `{timestamp: 1}` with `expireAfterSeconds: 2592000` (30 days)
- Compound Index: `{sensorId: 1, timestamp: -1}`

**Why MongoDB?**
- Optimized for time-series data
- High write throughput (100+ docs/sec)
- Automatic TTL-based cleanup
- Flexible schema for sensor data
- Horizontal scaling capability

---

### 5. Oracle SQL (Relational Database)
**Purpose**: Structured data với complex relationships

**Tables**:
- `LOCATIONS` - Geographic hierarchy (City > District > Ward)
- `SENSOR_REGISTRY` - Sensor registration
- `ALERTS` - Threshold violations
- `TELEMETRY_SUMMARY` - Daily aggregated analytics

**Key Features**:
- Recursive CTE for hierarchy queries
- Foreign key constraints (referential integrity)
- Indexes for performance
- ACID transactions

**Why Oracle?**
- Strong ACID guarantees
- Complex queries (recursive CTE)
- Referential integrity enforcement
- Enterprise-grade reliability
- Advanced analytics functions

---

### 6. Frontend Dashboard (React)
**Purpose**: Interactive visualization interface

**Components**:

#### a) MapView (Leaflet)
- Display sensor locations on map
- Color-coded markers (green/yellow/red by alert status)
- Popup with sensor details
- Real-time marker updates

#### b) ChartView (Chart.js)
- Line charts for CO2, Noise, Temperature
- Time range selector (1h, 6h, 24h)
- Real-time data appending
- Auto-scaling Y-axis

#### c) Leaderboard
- Locations ranked by Clean Score
- Top 3 highlighting (gold/silver/bronze)
- Click to zoom map
- Auto-refresh every 60 seconds

#### d) Alerts Panel
- Recent 20 alerts
- Color-coded by severity
- Filter by level/location
- Real-time notifications

**Technology**: React + TypeScript + Leaflet + Chart.js

---

## 🔑 Key Design Decisions

### 1. Hybrid Database Strategy
**Decision**: MongoDB for telemetry + Oracle for relational data

**Rationale**:
- **MongoDB**: Handles high-frequency writes (every 5 seconds × N sensors)
- **Oracle**: Manages complex relationships (hierarchy, referential integrity)
- **Polyglot Persistence**: Right tool for right job

**Alternative Considered**: Single database (PostgreSQL)
- ❌ Time-series performance not optimal
- ❌ No built-in TTL indexes
- ❌ Harder to scale writes

---

### 2. MQTT for IoT Communication
**Decision**: MQTT pub/sub instead of HTTP polling

**Rationale**:
- **Lightweight**: Minimal bandwidth (critical for IoT)
- **Decoupling**: Sensors don't need to know backend
- **Reliability**: QoS levels, persistent sessions
- **Scalability**: Broker handles millions of messages

**Alternative Considered**: HTTP POST every 5 seconds
- ❌ Higher bandwidth usage
- ❌ Tight coupling (sensors need backend URL)
- ❌ No message queuing
- ❌ Connection overhead

---

### 3. WebSocket for Real-Time Updates
**Decision**: WebSocket push instead of HTTP polling

**Rationale**:
- **Low Latency**: < 1 second update time
- **Efficient**: Single persistent connection
- **Bidirectional**: Server can push updates
- **No Polling Overhead**: Reduces server load

**Alternative Considered**: HTTP polling every 5 seconds
- ❌ High latency (5-second delay)
- ❌ Wasted requests (polling empty data)
- ❌ Server load (constant requests)

---

### 4. Microservices Architecture
**Decision**: Separate services instead of monolith

**Rationale**:
- **Independent Scaling**: Scale IoT simulator separately from backend
- **Technology Flexibility**: Python backend, React frontend
- **Fault Isolation**: MQTT failure doesn't crash REST API
- **Development Velocity**: Teams work independently

**Services**:
1. IoT Simulator (data generation)
2. MQTT Broker (message transport)
3. Backend API (processing + storage)
4. Frontend (visualization)

---

### 5. Docker Containerization
**Decision**: Docker Compose for deployment

**Rationale**:
- **Consistency**: Same environment dev/prod
- **Easy Setup**: `docker-compose up` starts everything
- **Dependency Management**: Services start in correct order
- **Portability**: Run anywhere Docker runs

---

## 📊 Database Schema Design

### MongoDB: Telemetry Collection
```javascript
// Document structure
{
  "_id": ObjectId("..."),
  "sensorId": "sensor_001",
  "locationId": "ward_001",
  "co2": 450.5,
  "noise": 65.2,
  "temperature": 25.3,
  "timestamp": ISODate("2024-01-15T10:30:00Z")
}

// Indexes
db.telemetry.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 2592000 })
db.telemetry.createIndex({ "sensorId": 1, "timestamp": -1 })
```

**Design Rationale**:
- Flat structure for fast writes
- TTL index for automatic cleanup
- Compound index for efficient time-range queries

---

### Oracle: Relational Schema
```sql
-- Location Hierarchy (Recursive)
LOCATIONS
├─ LocationID (PK)
├─ Name
├─ ParentID (FK → LOCATIONS.LocationID)
└─ Type (City/District/Ward)

-- Sensor Registry
SENSOR_REGISTRY
├─ SensorID (PK)
├─ LocationID (FK → LOCATIONS.LocationID)
├─ SensorType (CO2/Noise/Temperature)
└─ RegisteredAt

-- Alerts
ALERTS
├─ AlertID (PK)
├─ SensorID (FK → SENSOR_REGISTRY.SensorID)
├─ MetricType
├─ Value
├─ Level (LOW/MEDIUM/HIGH)
└─ CreatedAt

-- Analytics Summary
TELEMETRY_SUMMARY
├─ SummaryID (PK)
├─ LocationID (FK → LOCATIONS.LocationID)
├─ Date
├─ AvgCO2, AvgNoise, AvgTemperature
└─ CleanScore
```

**Design Rationale**:
- Foreign keys enforce referential integrity
- Recursive CTE view for hierarchy queries
- Indexes on frequently queried columns
- Unique constraint on (LocationID, Date) for summaries

---

## 🚀 System Features

### 1. Real-Time Monitoring
- **Live telemetry updates** via WebSocket (< 1 second latency)
- **Interactive map** with color-coded sensor markers
- **Time-series charts** with auto-refresh
- **Alert notifications** with visual indicators

### 2. Geographic Hierarchy
- **3-level hierarchy**: City > District > Ward
- **Recursive queries** for complete paths
- **Descendant queries** for subtrees
- **Sensor-location association**

### 3. Alert System
- **Automatic threshold detection** (CO2 > 1000, Noise > 85)
- **Deduplication** (5-minute window)
- **Severity levels** (LOW/MEDIUM/HIGH)
- **Real-time notifications**

### 4. Analytics & Rankings
- **Moving averages** (last 10 readings)
- **Clean Score calculation** (environmental quality metric)
- **Leaderboard** (locations ranked by Clean Score)
- **Daily aggregation** (scheduled task at midnight)

### 5. Data Lifecycle Management
- **Automatic cleanup** (TTL: 30 days)
- **High-frequency ingestion** (100+ docs/sec)
- **Efficient storage** (time-series optimization)
- **Query performance** (compound indexes)

---

## 🔐 Error Handling & Resilience

### Connection Failures
- **Exponential backoff retry** (1s → 2s → 4s → 8s → max 60s)
- **Auto-reconnection** for MQTT and databases
- **Connection pooling** (reuse connections)
- **Health checks** (monitor service status)

### Data Validation
- **Pydantic validation** (reject invalid data)
- **Range checks** (co2 ≥ 0, noise 0-120, temp -50-60)
- **Type validation** (sensor types, location types)
- **Referential integrity** (foreign key constraints)

### Graceful Degradation
- **Service isolation** (MQTT failure doesn't affect REST API)
- **Partial functionality** (continue if one database down)
- **Error logging** (track failures for debugging)
- **User feedback** (appropriate HTTP status codes)

---

## 📈 Performance Considerations

### Write Performance
- **MongoDB**: Optimized for high-frequency writes (time-series)
- **Connection pooling**: Reuse connections (MongoDB: 10-50, Oracle: 2-10)
- **Async operations**: Non-blocking I/O with FastAPI
- **Batch processing**: Group operations when possible

### Read Performance
- **Indexes**: Compound indexes for common queries
- **Caching**: Connection pools reduce overhead
- **Query optimization**: Use views for complex queries (LOCATION_HIERARCHY)
- **Limit results**: Default limits (100 telemetry, 20 alerts)

### Network Performance
- **WebSocket**: Single persistent connection (vs polling)
- **MQTT**: Lightweight protocol (minimal overhead)
- **CORS**: Configured for cross-origin requests
- **Compression**: Gzip for HTTP responses

---

## 🧪 Testing Strategy

### Property-Based Testing (Hypothesis)
- **20 correctness properties** defined
- **100+ iterations** per property test
- **Random data generation** (catch edge cases)
- **Formal verification** of requirements

### Unit Testing (pytest)
- **Component isolation** (mock dependencies)
- **Edge case coverage** (empty data, max values)
- **Error handling** (connection failures, invalid data)
- **Integration points** (API endpoints, database operations)

### End-to-End Testing
- **Full pipeline tests** (MQTT → Storage → WebSocket)
- **Docker Compose environment** (realistic setup)
- **Data integrity validation** (round-trip tests)

---

## 📦 Deployment Architecture

### Docker Compose Services
```yaml
services:
  mosquitto:      # MQTT Broker
    ports: 1883
    
  mongodb:        # Time-series DB
    ports: 27017
    volumes: mongo-data
    
  oracle-xe:      # Relational DB
    ports: 1521
    volumes: oracle-data
    
  backend:        # FastAPI
    ports: 8000
    depends_on: [mongodb, oracle-xe, mosquitto]
    
  frontend:       # React + Nginx
    ports: 3000
    depends_on: [backend]
    
  iot-simulator:  # Data generator
    depends_on: [mosquitto]
```

### Network Configuration
- **Internal network**: Services communicate via service names
- **External ports**: Only frontend (3000) exposed to host
- **Service discovery**: Docker DNS resolution

### Data Persistence
- **MongoDB volume**: `/data/db`
- **Oracle volume**: `/opt/oracle/oradata`
- **Mosquitto volume**: `/mosquitto/data`

---

## 🎓 Architecture Patterns Used

### 1. Microservices Architecture
- **Service decomposition** by business capability
- **Independent deployment** and scaling
- **Technology diversity** (Python, React, MQTT)

### 2. Event-Driven Architecture (EDA)
- **Asynchronous messaging** via MQTT
- **Event sourcing** (telemetry events)
- **Reactive updates** via WebSocket

### 3. Layered Architecture (Backend)
```
API Layer (routes.py)
    ↓
Service Layer (telemetry_handler, alert_engine, analytics)
    ↓
Repository Layer (mongodb_client, oracle_client)
    ↓
Database Layer (MongoDB, Oracle)
```

### 4. Repository Pattern
- **Data access abstraction** (mongodb_client, oracle_client)
- **Connection pooling** (resource efficiency)
- **Retry logic** (resilience)

### 5. Singleton Pattern
- **Shared instances** (database clients)
- **Resource efficiency** (single connection pool)
- **Thread-safe** (connection pool management)

---

## 🎯 Business Logic: Clean Score Algorithm

### Formula
```
normalized_CO2 = (avgCO2 / 2000) × 100
normalized_Noise = (avgNoise / 100) × 100
cleanScore = 100 - (normalized_CO2 × 0.5 + normalized_Noise × 0.5)
```

### Example Calculation
```
Location: Ward 1
├─ Avg CO2: 400 ppm
├─ Avg Noise: 60 dB
│
Calculation:
├─ normalized_CO2 = (400 / 2000) × 100 = 20
├─ normalized_Noise = (60 / 100) × 100 = 60
└─ cleanScore = 100 - (20 × 0.5 + 60 × 0.5) = 100 - 40 = 60

Result: Clean Score = 60/100
```

### Interpretation
- **80-100**: Excellent air quality
- **60-79**: Good air quality
- **40-59**: Moderate air quality
- **0-39**: Poor air quality

---

## 🔄 Complete System Flow (End-to-End)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Data Generation                                        │
└─────────────────────────────────────────────────────────────────┘
IoT Simulator generates:
  CO2: 1250 ppm, Noise: 90 dB, Temperature: 28°C
  Timestamp: 2024-01-15T10:30:00Z
  SensorID: sensor_001

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Message Publishing                                     │
└─────────────────────────────────────────────────────────────────┘
MQTT Publish:
  Topic: sensors/sensor_001/telemetry
  Payload: {"sensorId": "sensor_001", "co2": 1250, ...}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Message Routing                                        │
└─────────────────────────────────────────────────────────────────┘
MQTT Broker routes message to subscribers

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Backend Processing                                     │
└─────────────────────────────────────────────────────────────────┘
MQTT Consumer receives message
  ↓
Parse JSON → Telemetry object (Pydantic validation)
  ↓
Telemetry Handler:
  ├─ Insert to MongoDB (time-series storage)
  ├─ Check thresholds (CO2: 1250 > 1000 ✓, Noise: 90 > 85 ✓)
  └─ Trigger Alert Engine

Alert Engine:
  ├─ Check deduplication (no alert in last 5 minutes)
  ├─ Create Alert object (AlertID: uuid, Level: HIGH)
  ├─ Insert to Oracle (ALERTS table)
  └─ Broadcast via WebSocket

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Real-Time Updates                                      │
└─────────────────────────────────────────────────────────────────┘
WebSocket broadcasts:
  Message 1: {"type": "telemetry", "data": {...}}
  Message 2: {"type": "alert", "data": {...}}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Frontend Updates                                       │
└─────────────────────────────────────────────────────────────────┘
Frontend receives WebSocket messages:
  ├─ MapView: Update marker color (green → red)
  ├─ ChartView: Append new data point
  ├─ AlertsPanel: Show notification (red badge)
  └─ User sees updates in < 1 second
```

---

## 📐 Scalability Considerations

### Horizontal Scaling
- **IoT Simulators**: Add more containers (simulate more sensors)
- **Backend**: Multiple FastAPI instances behind load balancer
- **MongoDB**: Replica sets + sharding
- **MQTT Broker**: Clustered Mosquitto

### Vertical Scaling
- **Connection pools**: Increase pool size
- **Database resources**: More CPU/RAM for databases
- **Worker threads**: Increase FastAPI workers

### Performance Targets
- **Telemetry ingestion**: 100+ messages/second
- **API response time**: < 200ms (p95)
- **WebSocket latency**: < 1 second
- **Database queries**: < 100ms (with indexes)

---

## 🛡️ Security Considerations (Future Enhancements)

### Authentication & Authorization
- JWT tokens for API access
- Role-based access control (RBAC)
- API key authentication for IoT devices

### Data Security
- TLS/SSL for MQTT (port 8883)
- HTTPS for REST API
- Database encryption at rest
- Secure credential management (secrets)

### Network Security
- Firewall rules (only expose necessary ports)
- VPC/private networks for internal communication
- Rate limiting for API endpoints
- DDoS protection

---

## 🎨 SLIDE DESIGN GUIDE - Single Comprehensive Slide

### 📐 Slide Layout (16:9 Landscape)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  SMART CITY IOT SENSOR DASHBOARD                                           │
│  Real-Time Environmental Monitoring Platform                               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    SYSTEM ARCHITECTURE                               │  │
│  │                                                                      │  │
│  │  IoT Sensors → MQTT Broker → Backend (FastAPI) → Databases         │  │
│  │     (5s)         (Pub/Sub)      ├─ MQTT Consumer                    │  │
│  │                                 ├─ REST API                          │  │
│  │                                 ├─ WebSocket                         │  │
│  │                                 └─ Analytics                         │  │
│  │                                      ↓           ↓                   │  │
│  │                                  MongoDB      Oracle                 │  │
│  │                                (Time-series) (Relational)            │  │
│  │                                      ↓                               │  │
│  │                              Frontend Dashboard (React)              │  │
│  │                              Map | Charts | Leaderboard | Alerts    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TECH STACK                    │  KEY FEATURES                             │
│  ────────────────────────────  │  ──────────────────────────────────────   │
│  Backend:  Python FastAPI      │  ✓ Real-time monitoring (< 1s latency)   │
│  Frontend: React + TypeScript  │  ✓ Auto alerts (CO2>1000, Noise>85)      │
│  Message:  MQTT (Mosquitto)    │  ✓ Interactive map (Leaflet)             │
│  DB:       MongoDB + Oracle    │  ✓ Time-series charts (Chart.js)         │
│  Deploy:   Docker Compose      │  ✓ Clean Score rankings                  │
│                                │  ✓ Auto data cleanup (30 days TTL)       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHY THIS ARCHITECTURE?                                                    │
│  ─────────────────────────────────────────────────────────────────────     │
│  • Hybrid DB: MongoDB (high-freq writes) + Oracle (complex queries)       │
│  • MQTT: Lightweight, decoupled, IoT-optimized                            │
│  • WebSocket: Server push (no polling overhead)                           │
│  • Microservices: Independent scaling & fault isolation                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Detailed Slide Design Instructions

### **Section 1: Header (Top 15%)**
**Content**:
- Title: "SMART CITY IOT SENSOR DASHBOARD"
- Subtitle: "Real-Time Environmental Monitoring Platform"

**Design**:
- Font: Bold, 36pt for title, 20pt for subtitle
- Color: Dark blue (#1a365d) on white background
- Alignment: Center

---

### **Section 2: Architecture Diagram (Middle 50%)**
**Content**: Visual flow diagram

**Design Elements**:

#### Left Side: Data Generation
```
┌─────────────┐
│ IoT Sensors │  ← Icon: 📡
│   (5s/msg)  │
└──────┬──────┘
       │ MQTT
       ▼
```
- Color: Green (#48bb78)
- Label: "Data Source"

#### Center: Processing
```
┌──────────────────┐
│  MQTT Broker     │  ← Icon: 📨
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Backend API     │  ← Icon: ⚙️
│  • MQTT Consumer │
│  • REST API      │
│  • WebSocket     │
│  • Analytics     │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│MongoDB │ │ Oracle │  ← Icons: 🗄️
└────────┘ └────────┘
```
- Color: Blue (#3182ce)
- Label: "Processing & Storage"

#### Right Side: Visualization
```
┌──────────────────┐
│   Frontend       │  ← Icon: 🖥️
│  • Map View      │
│  • Charts        │
│  • Leaderboard   │
│  • Alerts        │
└──────────────────┘
```
- Color: Purple (#805ad5)
- Label: "Visualization"

#### Arrows
- Solid arrows: Synchronous (REST API)
- Dashed arrows: Asynchronous (MQTT, WebSocket)
- Color: Gray (#718096)

---

### **Section 3: Tech Stack & Features (Bottom Left 20%)**
**Content**: Two columns

**Column 1: Tech Stack**
```
Backend:  Python FastAPI
Frontend: React + TypeScript
Message:  MQTT (Mosquitto)
DB:       MongoDB + Oracle
Deploy:   Docker Compose
```
- Font: 14pt, monospace for tech names
- Icon: 🔧 before "TECH STACK"

**Column 2: Key Features**
```
✓ Real-time monitoring (< 1s)
✓ Auto alerts (thresholds)
✓ Interactive map
✓ Time-series charts
✓ Clean Score rankings
✓ Auto cleanup (30d TTL)
```
- Font: 14pt
- Checkmarks: Green (#48bb78)
- Icon: ⭐ before "KEY FEATURES"

---

### **Section 4: Architecture Rationale (Bottom Right 15%)**
**Content**: Why this architecture?

```
WHY THIS ARCHITECTURE?
• Hybrid DB: Right tool for right job
• MQTT: IoT-optimized, lightweight
• WebSocket: Real-time push
• Microservices: Scalable & isolated
```
- Font: 14pt
- Bullet points: Orange (#dd6b20)
- Icon: 💡 before "WHY THIS ARCHITECTURE?"
- Background: Light gray (#f7fafc)

---

## 🎨 Color Palette

### Primary Colors
- **Blue**: #3182ce (Backend, Processing)
- **Green**: #48bb78 (IoT, Success)
- **Purple**: #805ad5 (Frontend)
- **Orange**: #dd6b20 (Highlights, Rationale)
- **Red**: #e53e3e (Alerts)

### Neutral Colors
- **Dark Gray**: #2d3748 (Text)
- **Light Gray**: #f7fafc (Backgrounds)
- **White**: #ffffff (Main background)

### Usage Guidelines
- **Backgrounds**: White or light gray
- **Text**: Dark gray (high contrast)
- **Accents**: Use primary colors for components
- **Arrows**: Gray with colored highlights

---

## 📝 Typography Guidelines

### Fonts
- **Title**: Sans-serif, Bold, 36pt
- **Subtitle**: Sans-serif, Regular, 20pt
- **Section Headers**: Sans-serif, Bold, 18pt
- **Body Text**: Sans-serif, Regular, 14pt
- **Code/Tech**: Monospace, 14pt

### Hierarchy
1. Title (largest, bold)
2. Section headers (medium, bold)
3. Body text (regular)
4. Annotations (smallest, italic)

---

## 🎯 Visual Elements

### Icons to Use
- 📡 IoT Sensors
- 📨 MQTT Broker
- ⚙️ Backend Processing
- 🗄️ Databases
- 🖥️ Frontend
- 🔧 Tech Stack
- ⭐ Features
- 💡 Rationale
- ⚠️ Alerts
- 📊 Analytics

### Shapes
- **Rectangles**: Components (rounded corners)
- **Cylinders**: Databases
- **Arrows**: Data flow
- **Boxes**: Grouping related items

---

## 📊 Slide Creation Tools

### Recommended Tools
1. **PowerPoint**: Easy, familiar
2. **Google Slides**: Collaborative
3. **Figma**: Professional design
4. **Canva**: Templates available
5. **Draw.io**: Diagram-focused

### Export Format
- **PDF**: For printing/sharing
- **PNG**: High resolution (300 DPI)
- **PPTX**: Editable format

---

## ✅ Slide Content Checklist

### Must Include
- [ ] Project title and subtitle
- [ ] Complete architecture diagram with flow
- [ ] All 6 main components (IoT, MQTT, Backend, MongoDB, Oracle, Frontend)
- [ ] Technology stack list
- [ ] Key features (6 items)
- [ ] Architecture rationale (4 reasons)
- [ ] Visual hierarchy (colors, sizes)
- [ ] Icons for visual interest
- [ ] Data flow arrows
- [ ] Clear labels

### Optional (If Space Allows)
- [ ] Performance metrics (5s intervals, 30d retention)
- [ ] Alert thresholds (CO2 > 1000, Noise > 85)
- [ ] Database types (Time-series vs Relational)

---

## 🎯 Presentation Tips

### When Presenting This Slide

**1. Start with Problem (15 seconds)**
"Thành phố thông minh cần giám sát môi trường real-time từ hàng trăm cảm biến IoT"

**2. Show Architecture Flow (30 seconds)**
"Hệ thống hoạt động như sau:
- Cảm biến gửi dữ liệu mỗi 5 giây qua MQTT
- Backend xử lý, lưu vào 2 databases
- Frontend hiển thị real-time qua WebSocket"

**3. Highlight Tech Choices (20 seconds)**
"Chúng tôi chọn:
- MongoDB cho time-series (write-heavy)
- Oracle cho relational data (complex queries)
- MQTT vì lightweight và IoT-optimized
- WebSocket cho real-time updates"

**4. Show Key Features (15 seconds)**
"Hệ thống cung cấp:
- Bản đồ real-time
- Cảnh báo tự động
- Phân tích xu hướng
- Xếp hạng chất lượng môi trường"

**Total: 80 seconds** (perfect for quick overview)

---

## 🎨 Alternative: Simplified Slide (If Too Crowded)

### Minimalist Version

```
┌─────────────────────────────────────────────────────────┐
│  SMART CITY IOT DASHBOARD                              │
│  Environmental Monitoring Platform                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  IoT → MQTT → Backend → Databases → Frontend           │
│  (5s)  (Pub/Sub) (FastAPI) (Mongo+Oracle) (React)     │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ Real-time    │  │ Hybrid DB    │  │ Microservices│ │
│  │ Updates      │  │ Strategy     │  │ Architecture │ │
│  │ (WebSocket)  │  │ (Polyglot)   │  │ (Docker)     │ │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
│                                                         │
│  Features: Map • Charts • Alerts • Rankings            │
│  Tech: Python • React • MQTT • MongoDB • Oracle        │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Quick Reference: Slide Content

### Copy-Paste Text for Slide

**Title**:
```
SMART CITY IOT SENSOR DASHBOARD
Real-Time Environmental Monitoring Platform
```

**Architecture Flow**:
```
IoT Sensors (27 sensors, 5s intervals)
    ↓ MQTT Publish
MQTT Broker (Mosquitto)
    ↓ Subscribe
Backend Services (FastAPI)
├─ MQTT Consumer
├─ REST API (6 endpoints)
├─ WebSocket Server
└─ Analytics Engine
    ↓ Store
Databases
├─ MongoDB (Time-series, TTL: 30d)
└─ Oracle (Hierarchy, Alerts)
    ↓ Query
Frontend Dashboard (React)
├─ Map View (Leaflet)
├─ Chart View (Chart.js)
├─ Leaderboard
└─ Alerts Panel
```

**Tech Stack**:
```
Backend:  Python FastAPI + Pydantic
Frontend: React + TypeScript
Message:  MQTT (Mosquitto)
Database: MongoDB + Oracle SQL
Deploy:   Docker Compose (6 services)
```

**Key Features**:
```
✓ Real-time monitoring (< 1s latency)
✓ Auto alerts (CO2 > 1000, Noise > 85)
✓ Interactive map with sensor markers
✓ Time-series charts (1h/6h/24h)
✓ Clean Score rankings
✓ Auto data cleanup (30 days TTL)
```

**Architecture Rationale**:
```
• Hybrid DB: MongoDB (writes) + Oracle (queries)
• MQTT: Lightweight, decoupled, IoT-standard
• WebSocket: Server push, no polling
• Microservices: Scalable, fault-isolated
```

---

## 🎯 Final Recommendations

### For Maximum Impact

**DO**:
- ✅ Use visual hierarchy (size, color, position)
- ✅ Keep text minimal (bullet points, not paragraphs)
- ✅ Use icons for visual interest
- ✅ Show data flow with arrows
- ✅ Highlight key technologies (bold, color)
- ✅ Use consistent color scheme

**DON'T**:
- ❌ Overcrowd with too much text
- ❌ Use more than 4-5 colors
- ❌ Make fonts too small (< 14pt)
- ❌ Use complex diagrams (keep it simple)
- ❌ Include code snippets (save for technical slides)

### Slide Dimensions
- **Standard**: 16:9 (1920×1080 px)
- **Margins**: 50px all sides
- **Safe zone**: Keep important content within 80% center

### File Naming
- `smart-city-iot-architecture.pptx`
- `smart-city-iot-architecture.pdf`
- `smart-city-iot-architecture.png`

---

## 🚀 Next Steps

1. **Create slide** using layout guide above
2. **Export as PDF** for sharing
3. **Practice presentation** (80-second overview)
4. **Prepare backup slides** (technical details if asked)

---

## 📎 Additional Resources

### For Deeper Dives (Backup Slides)
- Slide 2: Database schema details
- Slide 3: API endpoints documentation
- Slide 4: Performance metrics
- Slide 5: Security considerations
- Slide 6: Deployment guide

### Demo Flow
1. Show architecture slide (overview)
2. Live demo: IoT simulator → Dashboard updates
3. Show map with real-time markers
4. Trigger alert (CO2 > 1000)
5. Show leaderboard rankings

---

**Document Created**: 2024-01-15  
**Version**: 1.0  
**Author**: Smart City IoT Team
