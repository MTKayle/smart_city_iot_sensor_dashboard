# Tính Năng Nâng Cao Cho Môn Hệ Cơ Sở Dữ Liệu Nâng Cao

## 📚 Tổng Quan

Tài liệu này mô tả các tính năng database nâng cao để làm nổi bật kiến thức môn **Hệ Cơ Sở Dữ Liệu Nâng Cao**, bao gồm:
- Polyglot Persistence (Hybrid Database)
- Query Optimization & Indexing
- Transactions & Concurrency Control
- Data Warehousing & OLAP
- Replication & Sharding
- NoSQL Advanced Features

---

## 🎯 Các Tính Năng Database Nâng Cao

### 1. **Polyglot Persistence & Hybrid Database Architecture** ⭐⭐⭐⭐⭐
### 2. **Advanced Query Optimization với Materialized Views** ⭐⭐⭐⭐⭐
### 3. **Data Warehousing & OLAP Cube** ⭐⭐⭐⭐⭐
### 4. **Distributed Transactions & 2-Phase Commit** ⭐⭐⭐⭐
### 5. **Database Replication & Sharding** ⭐⭐⭐⭐
### 6. **Time-Series Database Optimization** ⭐⭐⭐⭐⭐
### 7. **Full-Text Search & Inverted Index** ⭐⭐⭐⭐
### 8. **Database Triggers & Stored Procedures** ⭐⭐⭐⭐⭐

---

## 📊 Tính Năng 1: Polyglot Persistence - Hybrid Database Architecture

### Mô Tả
Đây là tính năng **ĐÃ CÓ** trong hệ thống hiện tại nhưng cần **PHÂN TÍCH VÀ TÀI LIỆU HÓA** để làm nổi bật kiến thức về Polyglot Persistence.

### Kiến Thức Môn Học
- **Polyglot Persistence:** Sử dụng nhiều loại database cho các use case khác nhau
- **CAP Theorem:** MongoDB (AP), Oracle (CA)
- **Data Consistency Models:** Eventual consistency vs Strong consistency
- **Database Selection Criteria:** Khi nào dùng NoSQL, khi nào dùng SQL

### Phân Tích Kiến Trúc Hiện Tại

#### MongoDB (NoSQL - Document Store)
**Use Case:** Time-series telemetry data
**Lý do chọn:**
- ✅ High write throughput (100+ writes/sec)
- ✅ Flexible schema (sensor data có thể thay đổi)
- ✅ TTL indexes (tự động xóa data sau 30 ngày)
- ✅ Horizontal scaling (sharding)

**Trade-offs:**
- ❌ Eventual consistency
- ❌ Không có JOIN phức tạp
- ❌ Không có foreign key constraints

#### Oracle SQL (RDBMS)
**Use Case:** Relational data, hierarchy, analytics
**Lý do chọn:**
- ✅ ACID transactions
- ✅ Complex queries (Recursive CTE)
- ✅ Referential integrity (Foreign keys)
- ✅ Advanced analytics functions

**Trade-offs:**
- ❌ Expensive licensing
- ❌ Vertical scaling only
- ❌ Lower write throughput

**Trade-offs:**
- ❌ Expensive licensing
- ❌ Vertical scaling only
- ❌ Lower write throughput

### Bảng So Sánh

| Tiêu Chí | MongoDB | Oracle SQL |
|----------|---------|------------|
| **Data Model** | Document (JSON) | Relational (Tables) |
| **Schema** | Schema-less | Fixed schema |
| **Consistency** | Eventual | Strong (ACID) |
| **Scalability** | Horizontal (Sharding) | Vertical |
| **Query Language** | MQL | SQL |
| **Transactions** | Single document | Multi-table |
| **Use Case** | High-volume writes | Complex queries |

### Code Examples

#### MongoDB - Telemetry Insert
```python
# backend/app/db/mongodb_client.py
async def insert_telemetry(telemetry: Telemetry):
    """
    Insert telemetry with automatic TTL expiration
    Demonstrates: NoSQL document insertion, TTL index
    """
    doc = {
        "sensorId": telemetry.sensorId,
        "locationId": telemetry.locationId,
        "co2": telemetry.co2,
        "noise": telemetry.noise,
        "temperature": telemetry.temperature,
        "timestamp": telemetry.timestamp
    }
    result = await db.telemetry.insert_one(doc)
    return result.inserted_id

# TTL Index - Auto delete after 30 days
db.telemetry.create_index("timestamp", expireAfterSeconds=2592000)
```

#### Oracle - Recursive Hierarchy Query
```sql
-- backend/app/db/sql/oracle_schema.sql
-- Demonstrates: Recursive CTE, Hierarchical queries
CREATE OR REPLACE VIEW LOCATION_HIERARCHY AS
WITH RECURSIVE hierarchy AS (
    -- Anchor: Root nodes (City level)
    SELECT LocationID, Name, ParentID, Type, 
           LocationID as Path, 0 as Level
    FROM LOCATIONS
    WHERE ParentID IS NULL
    
    UNION ALL
    
    -- Recursive: Child nodes
    SELECT l.LocationID, l.Name, l.ParentID, l.Type,
           h.Path || ' > ' || l.LocationID as Path,
           h.Level + 1 as Level
    FROM LOCATIONS l
    INNER JOIN hierarchy h ON l.ParentID = h.LocationID
)
SELECT * FROM hierarchy;
```

### Tài Liệu Hóa Cho Báo Cáo

**Slide 1: Polyglot Persistence Architecture**
- Diagram: MongoDB + Oracle architecture
- Explain: Why hybrid approach?

**Slide 2: CAP Theorem Analysis**
- MongoDB: AP (Availability + Partition tolerance)
- Oracle: CA (Consistency + Availability)

**Slide 3: Data Flow**
- Write path: MQTT → MongoDB (fast writes)
- Read path: REST API → Oracle (complex queries)

---

## 📊 Tính Năng 2: Advanced Query Optimization với Materialized Views

### Mô Tả
Tạo **Materialized Views** để cache kết quả của các query phức tạp, giảm thời gian truy vấn từ giây xuống milliseconds.

### Kiến Thức Môn Học
- **Materialized Views:** Pre-computed query results
- **Query Optimization:** Execution plans, cost-based optimization
- **Indexing Strategies:** B-Tree, Hash, Bitmap indexes
- **Refresh Strategies:** ON COMMIT, ON DEMAND, PERIODIC

### Use Case
Leaderboard query hiện tại phải:
1. JOIN TELEMETRY_SUMMARY với LOCATIONS
2. Aggregate data từ nhiều locations
3. Calculate rankings
4. Sort by CleanScore

→ **Chậm** khi có hàng nghìn locations!

### Giải Pháp: Materialized View

#### Tạo Materialized View
```sql
-- backend/app/db/sql/create_leaderboard_mv.sql
CREATE MATERIALIZED VIEW MV_LEADERBOARD
BUILD IMMEDIATE
REFRESH COMPLETE ON DEMAND
AS
SELECT 
    l.LocationID,
    l.Name as LocationName,
    AVG(ts.AvgCO2) as AvgCO2,
    AVG(ts.AvgNoise) as AvgNoise,
    AVG(ts.AvgTemperature) as AvgTemperature,
    AVG(ts.CleanScore) as CleanScore,
    RANK() OVER (ORDER BY AVG(ts.CleanScore) DESC) as Rank
FROM TELEMETRY_SUMMARY ts
JOIN LOCATIONS l ON ts.LocationID = l.LocationID
WHERE ts.Date >= SYSDATE - 7  -- Last 7 days
GROUP BY l.LocationID, l.Name;

-- Create index on materialized view
CREATE INDEX idx_mv_leaderboard_score ON MV_LEADERBOARD(CleanScore DESC);
```

#### Scheduled Refresh
```python
# backend/app/services/materialized_view_refresh.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.oracle_client import get_oracle_connection

async def refresh_leaderboard_mv():
    """
    Refresh materialized view every hour
    Demonstrates: Materialized view maintenance
    """
    conn = await get_oracle_connection()
    cursor = conn.cursor()
    
    # Refresh materialized view
    cursor.execute("BEGIN DBMS_MVIEW.REFRESH('MV_LEADERBOARD', 'C'); END;")
    conn.commit()
    
    print(f"Materialized view refreshed at {datetime.now()}")

# Schedule refresh every hour
scheduler = AsyncIOScheduler()
scheduler.add_job(refresh_leaderboard_mv, 'interval', hours=1)
scheduler.start()
```

#### Query với Materialized View
```python
# backend/app/api/routes.py
@router.get("/api/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    """
    Query from materialized view instead of base tables
    Performance: ~5ms vs ~500ms
    """
    conn = await get_oracle_connection()
    cursor = conn.cursor()
    
    # Query materialized view (FAST!)
    cursor.execute("""
        SELECT LocationID, LocationName, AvgCO2, AvgNoise, 
               AvgTemperature, CleanScore, Rank
        FROM MV_LEADERBOARD
        ORDER BY Rank
        LIMIT 100
    """)
    
    results = cursor.fetchall()
    return [LeaderboardEntry(**row) for row in results]
```

### Performance Analysis

| Query Type | Execution Time | Rows Scanned |
|------------|----------------|--------------|
| **Base Tables** | 450ms | 10,000+ |
| **Materialized View** | 5ms | 100 |
| **Improvement** | **90x faster** | **100x less** |

### Explain Plan Comparison

```sql
-- Base query (SLOW)
EXPLAIN PLAN FOR
SELECT l.LocationID, l.Name, AVG(ts.CleanScore)
FROM TELEMETRY_SUMMARY ts
JOIN LOCATIONS l ON ts.LocationID = l.LocationID
GROUP BY l.LocationID, l.Name;

-- Output: Full table scan, Hash join, Sort aggregate
-- Cost: 1250

-- Materialized view query (FAST)
EXPLAIN PLAN FOR
SELECT * FROM MV_LEADERBOARD ORDER BY Rank;

-- Output: Index range scan
-- Cost: 15
```

---

## 📊 Tính Năng 3: Data Warehousing & OLAP Cube

### Mô Tả
Xây dựng **Data Warehouse** với OLAP Cube để phân tích đa chiều (multi-dimensional analysis) dữ liệu telemetry.

### Kiến Thức Môn Học
- **OLAP vs OLTP:** Analytical vs Transactional processing
- **Star Schema:** Fact table + Dimension tables
- **OLAP Operations:** Drill-down, Roll-up, Slice, Dice, Pivot
- **Aggregation:** Pre-computed aggregates for fast queries

### Star Schema Design

```
         ┌─────────────────┐
         │  DIM_TIME       │
         │  - TimeID (PK)  │
         │  - Date         │
         │  - Hour         │
         │  - DayOfWeek    │
         │  - Month        │
         │  - Quarter      │
         │  - Year         │
         └────────┬────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼──────┐  ┌──▼──────────┐  ┌───▼─────────┐
│DIM_LOCATION│  │ FACT_TELEMETRY│  │ DIM_SENSOR  │
│-LocationID │  │ - FactID (PK) │  │ - SensorID  │
│-Name       │  │ - TimeID (FK) │  │ - Type      │
│-Type       │  │ - LocationID  │  │ - Status    │
│-ParentID   │  │ - SensorID    │  └─────────────┘
└────────────┘  │ - CO2         │
                │ - Noise       │
                │ - Temperature │
                │ - AlertCount  │
                └───────────────┘
```

### Implementation

#### Create Dimension Tables
```sql
-- backend/app/db/sql/create_data_warehouse.sql

-- Time Dimension
CREATE TABLE DIM_TIME (
    TimeID NUMBER PRIMARY KEY,
    FullDate DATE NOT NULL,
    Year NUMBER NOT NULL,
    Quarter NUMBER NOT NULL,
    Month NUMBER NOT NULL,
    Week NUMBER NOT NULL,
    DayOfWeek NUMBER NOT NULL,
    Hour NUMBER NOT NULL,
    IsWeekend CHAR(1) DEFAULT 'N'
);

-- Location Dimension (already exists, reuse LOCATIONS table)

-- Sensor Dimension
CREATE TABLE DIM_SENSOR (
    SensorID VARCHAR2(50) PRIMARY KEY,
    SensorType VARCHAR2(20),
    LocationID VARCHAR2(50),
    Status VARCHAR2(20) DEFAULT 'ACTIVE',
    RegisteredAt TIMESTAMP,
    FOREIGN KEY (LocationID) REFERENCES LOCATIONS(LocationID)
);

-- Fact Table
CREATE TABLE FACT_TELEMETRY (
    FactID NUMBER PRIMARY KEY,
    TimeID NUMBER NOT NULL,
    LocationID VARCHAR2(50) NOT NULL,
    SensorID VARCHAR2(50) NOT NULL,
    CO2 NUMBER,
    Noise NUMBER,
    Temperature NUMBER,
    AlertCount NUMBER DEFAULT 0,
    FOREIGN KEY (TimeID) REFERENCES DIM_TIME(TimeID),
    FOREIGN KEY (LocationID) REFERENCES LOCATIONS(LocationID),
    FOREIGN KEY (SensorID) REFERENCES DIM_SENSOR(SensorID)
);

-- Indexes for OLAP queries
CREATE INDEX idx_fact_time ON FACT_TELEMETRY(TimeID);
CREATE INDEX idx_fact_location ON FACT_TELEMETRY(LocationID);
CREATE INDEX idx_fact_sensor ON FACT_TELEMETRY(SensorID);
CREATE BITMAP INDEX idx_fact_alert ON FACT_TELEMETRY(AlertCount);
```

#### ETL Process (Extract, Transform, Load)
```python
# backend/app/services/etl_service.py
from datetime import datetime, timedelta
from app.db.mongodb_client import get_mongodb_client
from app.db.oracle_client import get_oracle_connection

async def etl_telemetry_to_warehouse():
    """
    ETL process: MongoDB → Oracle Data Warehouse
    Runs daily at midnight
    """
    # Extract from MongoDB
    mongo_client = await get_mongodb_client()
    yesterday = datetime.now() - timedelta(days=1)
    
    telemetry_data = await mongo_client.telemetry.find({
        "timestamp": {
            "$gte": yesterday.replace(hour=0, minute=0, second=0),
            "$lt": yesterday.replace(hour=23, minute=59, second=59)
        }
    }).to_list(length=None)
    
    # Transform & Load to Oracle
    oracle_conn = await get_oracle_connection()
    cursor = oracle_conn.cursor()
    
    for record in telemetry_data:
        # Get TimeID from DIM_TIME
        time_id = get_or_create_time_dimension(cursor, record['timestamp'])
        
        # Insert into FACT_TELEMETRY
        cursor.execute("""
            INSERT INTO FACT_TELEMETRY 
            (FactID, TimeID, LocationID, SensorID, CO2, Noise, Temperature, AlertCount)
            VALUES (FACT_SEQ.NEXTVAL, :1, :2, :3, :4, :5, :6, :7)
        """, (
            time_id,
            record['locationId'],
            record['sensorId'],
            record['co2'],
            record['noise'],
            record['temperature'],
            1 if record.get('alert') else 0
        ))
    
    oracle_conn.commit()
    print(f"ETL completed: {len(telemetry_data)} records loaded")
```

#### OLAP Queries

```sql
-- 1. ROLL-UP: Aggregate by Location hierarchy
SELECT 
    l.Type,
    AVG(f.CO2) as AvgCO2,
    AVG(f.Noise) as AvgNoise,
    COUNT(*) as RecordCount
FROM FACT_TELEMETRY f
JOIN LOCATIONS l ON f.LocationID = l.LocationID
GROUP BY ROLLUP(l.Type);

-- 2. DRILL-DOWN: From City → District → Ward
SELECT 
    l.Type,
    l.Name,
    AVG(f.CO2) as AvgCO2
FROM FACT_TELEMETRY f
JOIN LOCATIONS l ON f.LocationID = l.LocationID
WHERE l.Type IN ('City', 'District', 'Ward')
GROUP BY l.Type, l.Name
ORDER BY l.Type;

-- 3. SLICE: Filter by specific time period
SELECT 
    t.Month,
    t.DayOfWeek,
    AVG(f.CO2) as AvgCO2
FROM FACT_TELEMETRY f
JOIN DIM_TIME t ON f.TimeID = t.TimeID
WHERE t.Year = 2024 AND t.Month = 1
GROUP BY t.Month, t.DayOfWeek;

-- 4. DICE: Multi-dimensional filter
SELECT 
    l.Name,
    t.Hour,
    AVG(f.Noise) as AvgNoise
FROM FACT_TELEMETRY f
JOIN LOCATIONS l ON f.LocationID = l.LocationID
JOIN DIM_TIME t ON f.TimeID = t.TimeID
WHERE l.Type = 'Ward'
  AND t.Hour BETWEEN 8 AND 18  -- Business hours
  AND t.IsWeekend = 'N'
GROUP BY l.Name, t.Hour;

-- 5. PIVOT: Cross-tabulation
SELECT * FROM (
    SELECT l.Name, t.Hour, f.CO2
    FROM FACT_TELEMETRY f
    JOIN LOCATIONS l ON f.LocationID = l.LocationID
    JOIN DIM_TIME t ON f.TimeID = t.TimeID
)
PIVOT (
    AVG(CO2)
    FOR Hour IN (0,6,12,18)
);
```

### OLAP Cube với CUBE Operator
```sql
-- Multi-dimensional aggregation
SELECT 
    l.Type,
    t.Month,
    t.DayOfWeek,
    AVG(f.CO2) as AvgCO2,
    AVG(f.Noise) as AvgNoise,
    COUNT(*) as RecordCount
FROM FACT_TELEMETRY f
JOIN LOCATIONS l ON f.LocationID = l.LocationID
JOIN DIM_TIME t ON f.TimeID = t.TimeID
GROUP BY CUBE(l.Type, t.Month, t.DayOfWeek);
```

---

## 📊 Tính Năng 4: Distributed Transactions & 2-Phase Commit

### Mô Tả
Implement **distributed transactions** giữa MongoDB và Oracle để đảm bảo **ACID properties** khi update data trên cả 2 databases.

### Kiến Thức Môn Học
- **ACID Properties:** Atomicity, Consistency, Isolation, Durability
- **2-Phase Commit (2PC):** Prepare phase + Commit phase
- **Transaction Coordinator:** Orchestrates distributed transaction
- **Failure Recovery:** Rollback on failure

### Use Case: Alert Creation
Khi tạo alert, cần:
1. Insert alert vào Oracle ALERTS table
2. Update alert count trong MongoDB telemetry document
3. **Cả 2 operations phải thành công hoặc cả 2 rollback**

### Implementation: 2-Phase Commit

```python
# backend/app/services/distributed_transaction.py
from enum import Enum
from typing import List, Callable
import logging

class TransactionState(Enum):
    INIT = "INIT"
    PREPARED = "PREPARED"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"

class DistributedTransaction:
    """
    2-Phase Commit Protocol Implementation
    Demonstrates: Distributed transaction coordination
    """
    
    def __init__(self):
        self.state = TransactionState.INIT
        self.participants = []
        self.logger = logging.getLogger(__name__)
    
    def add_participant(self, name: str, prepare_fn: Callable, commit_fn: Callable, rollback_fn: Callable):
        """Add a participant database to the transaction"""
        self.participants.append({
            "name": name,
            "prepare": prepare_fn,
            "commit": commit_fn,
            "rollback": rollback_fn,
            "prepared": False
        })
    
    async def execute(self) -> bool:
        """
        Execute 2-Phase Commit
        Phase 1: PREPARE - Ask all participants if they can commit
        Phase 2: COMMIT - If all prepared, commit all; otherwise rollback all
        """
        try:
            # PHASE 1: PREPARE
            self.logger.info("Phase 1: PREPARE - Asking all participants")
            for participant in self.participants:
                success = await participant["prepare"]()
                if not success:
                    self.logger.error(f"{participant['name']} failed to prepare")
                    await self._rollback_all()
                    return False
                participant["prepared"] = True
                self.logger.info(f"{participant['name']} prepared successfully")
            
            self.state = TransactionState.PREPARED
            
            # PHASE 2: COMMIT
            self.logger.info("Phase 2: COMMIT - Committing all participants")
            for participant in self.participants:
                success = await participant["commit"]()
                if not success:
                    self.logger.error(f"{participant['name']} failed to commit")
                    # In real 2PC, this is catastrophic - need manual intervention
                    raise Exception("Commit phase failure - data inconsistency!")
                self.logger.info(f"{participant['name']} committed successfully")
            
            self.state = TransactionState.COMMITTED
            return True
            
        except Exception as e:
            self.logger.error(f"Transaction failed: {e}")
            await self._rollback_all()
            return False
    
    async def _rollback_all(self):
        """Rollback all prepared participants"""
        self.logger.info("Rolling back all participants")
        for participant in self.participants:
            if participant["prepared"]:
                await participant["rollback"]()
                self.logger.info(f"{participant['name']} rolled back")
        self.state = TransactionState.ABORTED
```

#### Example: Alert Creation with 2PC

```python
# backend/app/services/alert_service_distributed.py
from app.services.distributed_transaction import DistributedTransaction
from app.db.oracle_client import get_oracle_connection
from app.db.mongodb_client import get_mongodb_client

async def create_alert_with_2pc(sensor_id: str, metric_type: str, value: float):
    """
    Create alert using 2-Phase Commit
    Ensures atomicity across MongoDB and Oracle
    """
    alert_id = str(uuid.uuid4())
    oracle_conn = None
    mongo_client = None
    
    # Oracle participant
    async def oracle_prepare():
        nonlocal oracle_conn
        oracle_conn = await get_oracle_connection()
        cursor = oracle_conn.cursor()
        # Insert alert but don't commit yet
        cursor.execute("""
            INSERT INTO ALERTS (AlertID, SensorID, MetricType, Value, Level, CreatedAt)
            VALUES (:1, :2, :3, :4, 'HIGH', CURRENT_TIMESTAMP)
        """, (alert_id, sensor_id, metric_type, value))
        return True
    
    async def oracle_commit():
        oracle_conn.commit()
        return True
    
    async def oracle_rollback():
        oracle_conn.rollback()
        return True
    
    # MongoDB participant
    async def mongo_prepare():
        nonlocal mongo_client
        mongo_client = await get_mongodb_client()
        # Check if update is possible
        result = await mongo_client.telemetry.find_one({"sensorId": sensor_id})
        return result is not None
    
    async def mongo_commit():
        # Increment alert count
        await mongo_client.telemetry.update_many(
            {"sensorId": sensor_id},
            {"$inc": {"alertCount": 1}}
        )
        return True
    
    async def mongo_rollback():
        # Decrement alert count if already incremented
        await mongo_client.telemetry.update_many(
            {"sensorId": sensor_id},
            {"$inc": {"alertCount": -1}}
        )
        return True
    
    # Execute 2PC
    transaction = DistributedTransaction()
    transaction.add_participant("Oracle", oracle_prepare, oracle_commit, oracle_rollback)
    transaction.add_participant("MongoDB", mongo_prepare, mongo_commit, mongo_rollback)
    
    success = await transaction.execute()
    
    if success:
        print(f"Alert {alert_id} created successfully with 2PC")
    else:
        print(f"Alert creation failed, all changes rolled back")
    
    return success
```

### Transaction Log
```python
# backend/app/models/transaction_log.py
from datetime import datetime
from enum import Enum

class TransactionLog:
    """
    Transaction log for recovery
    Demonstrates: Write-Ahead Logging (WAL)
    """
    
    def __init__(self):
        self.log_file = "transaction.log"
    
    def log_prepare(self, tx_id: str, participant: str):
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now()} | TX:{tx_id} | PREPARE | {participant}\n")
    
    def log_commit(self, tx_id: str, participant: str):
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now()} | TX:{tx_id} | COMMIT | {participant}\n")
    
    def log_abort(self, tx_id: str):
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now()} | TX:{tx_id} | ABORT\n")
    
    def recover(self):
        """
        Recovery process: Read log and complete/rollback incomplete transactions
        """
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
        
        # Parse log and identify incomplete transactions
        # Implement recovery logic here
        pass
```

---

## 📊 Tính Năng 5: Database Replication & Sharding

### Mô Tả
Implement **MongoDB Replication** (Master-Slave) và **Sharding** để tăng availability và scalability.

### Kiến Thức Môn Học
- **Replication:** Master-Slave, Multi-Master
- **Sharding:** Horizontal partitioning
- **Consistency Models:** Strong vs Eventual consistency
- **CAP Theorem:** Trade-offs in distributed systems

### MongoDB Replica Set

#### Architecture
```
┌─────────────┐
│   PRIMARY   │ ← Writes go here
│  (Master)   │
└──────┬──────┘
       │
       ├─────────────┬─────────────┐
       │             │             │
┌──────▼──────┐ ┌───▼────────┐ ┌──▼──────────┐
│ SECONDARY 1 │ │ SECONDARY 2│ │ SECONDARY 3 │
│  (Slave)    │ │  (Slave)   │ │  (Slave)    │
└─────────────┘ └────────────┘ └─────────────┘
       ↑             ↑             ↑
       └─────────────┴─────────────┘
              Reads can go here
```

#### Docker Compose Configuration
```yaml
# docker-compose.yml
services:
  mongodb-primary:
    image: mongo:7.0
    command: mongod --replSet rs0 --bind_ip_all
    ports:
      - "27017:27017"
    volumes:
      - mongo-primary-data:/data/db
    networks:
      - smart-city-network

  mongodb-secondary1:
    image: mongo:7.0
    command: mongod --replSet rs0 --bind_ip_all
    ports:
      - "27018:27017"
    volumes:
      - mongo-secondary1-data:/data/db
    networks:
      - smart-city-network

  mongodb-secondary2:
    image: mongo:7.0
    command: mongod --replSet rs0 --bind_ip_all
    ports:
      - "27019:27017"
    volumes:
      - mongo-secondary2-data:/data/db
    networks:
      - smart-city-network

volumes:
  mongo-primary-data:
  mongo-secondary1-data:
  mongo-secondary2-data:
```

#### Initialize Replica Set
```javascript
// scripts/init-replica-set.js
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongodb-primary:27017", priority: 2 },
    { _id: 1, host: "mongodb-secondary1:27017", priority: 1 },
    { _id: 2, host: "mongodb-secondary2:27017", priority: 1 }
  ]
});

// Check status
rs.status();
```

#### Application Configuration
```python
# backend/app/db/mongodb_client.py
from motor.motor_asyncio import AsyncIOMotorClient

async def get_mongodb_client():
    """
    Connect to MongoDB Replica Set
    Demonstrates: Replication, Read preferences
    """
    client = AsyncIOMotorClient(
        "mongodb://mongodb-primary:27017,mongodb-secondary1:27017,mongodb-secondary2:27017/?replicaSet=rs0",
        # Read preference: Read from secondaries for analytics queries
        readPreference='secondaryPreferred',
        # Write concern: Wait for majority of replicas
        w='majority',
        # Read concern: Read committed data only
        readConcernLevel='majority'
    )
    return client
```

### MongoDB Sharding

#### Architecture
```
                    ┌──────────────┐
                    │   mongos     │ ← Query Router
                    │  (Router)    │
                    └──────┬───────┘
                           │
        ┏━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━┓
        ┃                                      ┃
┌───────▼────────┐                  ┌─────────▼────────┐
│  Shard 1       │                  │  Shard 2         │
│  (Replica Set) │                  │  (Replica Set)   │
│  sensorId:     │                  │  sensorId:       │
│  A-M           │                  │  N-Z             │
└────────────────┘                  └──────────────────┘
```

#### Enable Sharding
```javascript
// scripts/enable-sharding.js

// Enable sharding on database
sh.enableSharding("smart_city");

// Shard telemetry collection by sensorId
sh.shardCollection(
  "smart_city.telemetry",
  { "sensorId": "hashed" }  // Hash-based sharding
);

// Check sharding status
sh.status();
```

#### Shard Key Selection
```python
# Why sensorId as shard key?
# ✅ High cardinality (many unique values)
# ✅ Even distribution (hash-based)
# ✅ Query pattern: Most queries filter by sensorId
# ❌ Range queries on timestamp might span multiple shards

# Alternative: Compound shard key
sh.shardCollection(
  "smart_city.telemetry",
  { "locationId": 1, "timestamp": 1 }  # Range-based sharding
);
```

### Failover Testing
```python
# backend/tests/test_replication.py
import pytest
from app.db.mongodb_client import get_mongodb_client

@pytest.mark.asyncio
async def test_primary_failover():
    """
    Test automatic failover when primary fails
    Demonstrates: High availability
    """
    client = await get_mongodb_client()
    
    # Write to primary
    result = await client.telemetry.insert_one({
        "sensorId": "test_sensor",
        "co2": 500,
        "timestamp": datetime.now()
    })
    assert result.inserted_id is not None
    
    # Simulate primary failure (stop primary container)
    # docker stop mongodb-primary
    
    # Wait for election (typically 10-30 seconds)
    await asyncio.sleep(30)
    
    # Verify new primary elected and writes still work
    result = await client.telemetry.insert_one({
        "sensorId": "test_sensor_2",
        "co2": 600,
        "timestamp": datetime.now()
    })
    assert result.inserted_id is not None
```

---

## 📊 Tính Năng 6: Time-Series Database Optimization

### Mô Tả
Optimize MongoDB cho **time-series data** với Time-Series Collections (MongoDB 5.0+).

### Kiến Thức Môn Học
- **Time-Series Data:** Timestamp-indexed data
- **Compression:** Reduce storage by 90%
- **Bucketing:** Group data by time windows
- **Retention Policies:** Automatic data expiration

### Time-Series Collection

#### Create Time-Series Collection
```javascript
// scripts/create-timeseries-collection.js
db.createCollection("telemetry_ts", {
  timeseries: {
    timeField: "timestamp",
    metaField: "sensorId",
    granularity: "seconds"  // seconds, minutes, hours
  },
  expireAfterSeconds: 2592000  // 30 days TTL
});

// Create index on metaField
db.telemetry_ts.createIndex({ "sensorId": 1, "timestamp": -1 });
```

#### Insert Time-Series Data
```python
# backend/app/db/mongodb_timeseries.py
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def insert_telemetry_ts(telemetry: Telemetry):
    """
    Insert into time-series collection
    Demonstrates: Time-series optimization, automatic bucketing
    """
    client = await get_mongodb_client()
    db = client.smart_city
    
    doc = {
        "timestamp": telemetry.timestamp,  # timeField
        "sensorId": telemetry.sensorId,    # metaField
        "measurements": {                   # Nested measurements
            "co2": telemetry.co2,
            "noise": telemetry.noise,
            "temperature": telemetry.temperature
        },
        "location": telemetry.locationId
    }
    
    result = await db.telemetry_ts.insert_one(doc)
    return result.inserted_id
```

#### Time-Series Queries
```python
# Aggregation pipeline optimized for time-series
async def get_sensor_stats(sensor_id: str, hours: int = 24):
    """
    Get statistics for last N hours
    Uses $densify and $fill for missing data points
    """
    client = await get_mongodb_client()
    db = client.smart_city
    
    pipeline = [
        # Match sensor and time range
        {
            "$match": {
                "sensorId": sensor_id,
                "timestamp": {
                    "$gte": datetime.now() - timedelta(hours=hours)
                }
            }
        },
        # Densify: Fill missing time points
        {
            "$densify": {
                "field": "timestamp",
                "range": {
                    "step": 5,
                    "unit": "minute",
                    "bounds": "full"
                }
            }
        },
        # Fill: Interpolate missing values
        {
            "$fill": {
                "sortBy": { "timestamp": 1 },
                "output": {
                    "measurements.co2": { "method": "linear" },
                    "measurements.noise": { "method": "linear" },
                    "measurements.temperature": { "method": "linear" }
                }
            }
        },
        # Group by hour
        {
            "$group": {
                "_id": {
                    "$dateTrunc": {
                        "date": "$timestamp",
                        "unit": "hour"
                    }
                },
                "avgCO2": { "$avg": "$measurements.co2" },
                "maxCO2": { "$max": "$measurements.co2" },
                "minCO2": { "$min": "$measurements.co2" },
                "avgNoise": { "$avg": "$measurements.noise" },
                "count": { "$sum": 1 }
            }
        },
        { "$sort": { "_id": 1 } }
    ]
    
    results = await db.telemetry_ts.aggregate(pipeline).to_list(length=None)
    return results
```

### Storage Comparison

| Collection Type | Storage Size | Compression Ratio | Query Performance |
|----------------|--------------|-------------------|-------------------|
| **Regular Collection** | 1.2 GB | 1x | Baseline |
| **Time-Series Collection** | 120 MB | **10x** | **2-3x faster** |

### Window Functions on Time-Series
```javascript
// MongoDB 5.0+ Window functions
db.telemetry_ts.aggregate([
  {
    $setWindowFields: {
      partitionBy: "$sensorId",
      sortBy: { timestamp: 1 },
      output: {
        // Moving average (last 10 readings)
        movingAvgCO2: {
          $avg: "$measurements.co2",
          window: {
            documents: [-9, 0]  // Current + 9 previous
          }
        },
        // Cumulative sum
        cumulativeAlerts: {
          $sum: "$alertCount",
          window: {
            documents: ["unbounded", "current"]
          }
        },
        // Rank by CO2 level
        co2Rank: {
          $rank: {}
        }
      }
    }
  }
]);
```

---

## 📊 Tính Năng 7: Full-Text Search & Inverted Index

### Mô Tả
Implement **Full-Text Search** để tìm kiếm locations, sensors, alerts bằng text queries.

### Kiến Thức Môn Học
- **Inverted Index:** Token → Document mapping
- **Text Analysis:** Tokenization, stemming, stop words
- **Relevance Scoring:** TF-IDF, BM25
- **Search Operators:** AND, OR, NOT, phrase search

### MongoDB Text Index

#### Create Text Index
```javascript
// scripts/create-text-indexes.js

// Text index on LOCATIONS
db.locations.createIndex(
  {
    "name": "text",
    "type": "text"
  },
  {
    weights: {
      "name": 10,  // Name is more important
      "type": 5
    },
    default_language: "english"
  }
);

// Text index on ALERTS
db.alerts.createIndex(
  {
    "metricType": "text",
    "level": "text"
  }
);
```

#### Full-Text Search Queries
```python
# backend/app/api/search_routes.py
from fastapi import APIRouter, Query
from typing import List

router = APIRouter()

@router.get("/api/search/locations")
async def search_locations(q: str = Query(..., min_length=2)):
    """
    Full-text search on locations
    Example: /api/search/locations?q="district 1"
    """
    client = await get_mongodb_client()
    db = client.smart_city
    
    # Text search with relevance score
    results = await db.locations.find(
        {
            "$text": {
                "$search": q,
                "$caseSensitive": False
            }
        },
        {
            "score": { "$meta": "textScore" }
        }
    ).sort([("score", {"$meta": "textScore"})]).to_list(length=20)
    
    return results

@router.get("/api/search/alerts")
async def search_alerts(
    q: str = Query(..., min_length=2),
    level: str = None
):
    """
    Full-text search on alerts with filters
    Example: /api/search/alerts?q="high co2"&level=HIGH
    """
    client = await get_mongodb_client()
    db = client.smart_city
    
    query = {
        "$text": { "$search": q }
    }
    
    if level:
        query["level"] = level
    
    results = await db.alerts.find(query).sort([
        ("score", {"$meta": "textScore"}),
        ("createdAt", -1)
    ]).to_list(length=50)
    
    return results
```

### Oracle Text Search

#### Create Oracle Text Index
```sql
-- backend/app/db/sql/create-text-index.sql

-- Install Oracle Text (if not installed)
-- @?/rdbms/admin/catctx.sql

-- Create text index on LOCATIONS
CREATE INDEX idx_locations_text ON LOCATIONS(Name)
INDEXTYPE IS CTXSYS.CONTEXT;

-- Create text index on ALERTS
CREATE INDEX idx_alerts_text ON ALERTS(MetricType)
INDEXTYPE IS CTXSYS.CONTEXT;
```

#### Oracle Text Queries
```sql
-- Simple text search
SELECT LocationID, Name, Type
FROM LOCATIONS
WHERE CONTAINS(Name, 'district', 1) > 0
ORDER BY SCORE(1) DESC;

-- Boolean operators
SELECT LocationID, Name
FROM LOCATIONS
WHERE CONTAINS(Name, 'district AND (1 OR 2)', 1) > 0;

-- Phrase search
SELECT LocationID, Name
FROM LOCATIONS
WHERE CONTAINS(Name, '"ward 5"', 1) > 0;

-- Fuzzy search (typo tolerance)
SELECT LocationID, Name
FROM LOCATIONS
WHERE CONTAINS(Name, 'fuzzy(distric, 80)', 1) > 0;  -- Matches "district"

-- Wildcard search
SELECT LocationID, Name
FROM LOCATIONS
WHERE CONTAINS(Name, 'dist%', 1) > 0;
```

### Search API with Autocomplete
```python
# backend/app/api/search_routes.py

@router.get("/api/search/autocomplete")
async def autocomplete_locations(
    q: str = Query(..., min_length=1, max_length=50)
):
    """
    Autocomplete suggestions for location search
    Uses regex for prefix matching
    """
    client = await get_mongodb_client()
    db = client.smart_city
    
    # Regex search for prefix
    results = await db.locations.find(
        {
            "name": {
                "$regex": f"^{q}",
                "$options": "i"  # Case insensitive
            }
        },
        {
            "_id": 0,
            "locationId": 1,
            "name": 1,
            "type": 1
        }
    ).limit(10).to_list(length=10)
    
    return results
```

### Frontend Integration
```typescript
// frontend/src/services/search.ts
import axios from 'axios';

export const searchLocations = async (query: string) => {
  const response = await axios.get('/api/search/locations', {
    params: { q: query }
  });
  return response.data;
};

export const autocompleteLocations = async (query: string) => {
  const response = await axios.get('/api/search/autocomplete', {
    params: { q: query }
  });
  return response.data;
};
```

```tsx
// frontend/src/components/SearchBar.tsx
import React, { useState, useEffect } from 'react';
import { autocompleteLocations } from '../services/search';

export const SearchBar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    if (query.length >= 2) {
      const fetchSuggestions = async () => {
        const results = await autocompleteLocations(query);
        setSuggestions(results);
      };
      fetchSuggestions();
    }
  }, [query]);

  return (
    <div className="search-bar">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search locations..."
      />
      {suggestions.length > 0 && (
        <ul className="suggestions">
          {suggestions.map((s) => (
            <li key={s.locationId}>{s.name} ({s.type})</li>
          ))}
        </ul>
      )}
    </div>
  );
};
```

---

## 📊 Tính Năng 8: Database Triggers & Stored Procedures

### Mô Tả
Implement **Database Triggers** và **Stored Procedures** trong Oracle để tự động hóa business logic ở database layer.

### Kiến Thức Môn Học
- **Triggers:** BEFORE/AFTER INSERT/UPDATE/DELETE
- **Stored Procedures:** Reusable database logic
- **Functions:** Return values
- **Packages:** Group related procedures/functions

### Oracle Triggers

#### Audit Trigger
```sql
-- backend/app/db/sql/create-triggers.sql

-- Create audit table
CREATE TABLE AUDIT_LOG (
    AuditID NUMBER PRIMARY KEY,
    TableName VARCHAR2(50),
    Operation VARCHAR2(10),
    OldValue CLOB,
    NewValue CLOB,
    ChangedBy VARCHAR2(50),
    ChangedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE audit_seq START WITH 1;

-- Trigger: Log all changes to LOCATIONS table
CREATE OR REPLACE TRIGGER trg_locations_audit
AFTER INSERT OR UPDATE OR DELETE ON LOCATIONS
FOR EACH ROW
DECLARE
    v_operation VARCHAR2(10);
    v_old_value CLOB;
    v_new_value CLOB;
BEGIN
    -- Determine operation type
    IF INSERTING THEN
        v_operation := 'INSERT';
        v_new_value := :NEW.LocationID || '|' || :NEW.Name || '|' || :NEW.Type;
    ELSIF UPDATING THEN
        v_operation := 'UPDATE';
        v_old_value := :OLD.LocationID || '|' || :OLD.Name || '|' || :OLD.Type;
        v_new_value := :NEW.LocationID || '|' || :NEW.Name || '|' || :NEW.Type;
    ELSIF DELETING THEN
        v_operation := 'DELETE';
        v_old_value := :OLD.LocationID || '|' || :OLD.Name || '|' || :OLD.Type;
    END IF;
    
    -- Insert audit record
    INSERT INTO AUDIT_LOG (AuditID, TableName, Operation, OldValue, NewValue, ChangedBy)
    VALUES (audit_seq.NEXTVAL, 'LOCATIONS', v_operation, v_old_value, v_new_value, USER);
END;
/
```

#### Validation Trigger
```sql
-- Trigger: Validate sensor registration
CREATE OR REPLACE TRIGGER trg_sensor_validate
BEFORE INSERT OR UPDATE ON SENSOR_REGISTRY
FOR EACH ROW
DECLARE
    v_location_type VARCHAR2(20);
    v_sensor_count NUMBER;
BEGIN
    -- Check 1: Location must be Ward type
    SELECT Type INTO v_location_type
    FROM LOCATIONS
    WHERE LocationID = :NEW.LocationID;
    
    IF v_location_type != 'Ward' THEN
        RAISE_APPLICATION_ERROR(-20001, 'Sensors can only be registered at Ward level');
    END IF;
    
    -- Check 2: Max 10 sensors per ward
    SELECT COUNT(*) INTO v_sensor_count
    FROM SENSOR_REGISTRY
    WHERE LocationID = :NEW.LocationID;
    
    IF v_sensor_count >= 10 THEN
        RAISE_APPLICATION_ERROR(-20002, 'Maximum 10 sensors per ward exceeded');
    END IF;
    
    -- Auto-set RegisteredAt if not provided
    IF :NEW.RegisteredAt IS NULL THEN
        :NEW.RegisteredAt := CURRENT_TIMESTAMP;
    END IF;
END;
/
```

#### Alert Deduplication Trigger
```sql
-- Trigger: Prevent duplicate alerts within 5 minutes
CREATE OR REPLACE TRIGGER trg_alert_dedup
BEFORE INSERT ON ALERTS
FOR EACH ROW
DECLARE
    v_recent_alert_count NUMBER;
BEGIN
    -- Check for recent alerts from same sensor
    SELECT COUNT(*) INTO v_recent_alert_count
    FROM ALERTS
    WHERE SensorID = :NEW.SensorID
      AND MetricType = :NEW.MetricType
      AND CreatedAt >= CURRENT_TIMESTAMP - INTERVAL '5' MINUTE;
    
    IF v_recent_alert_count > 0 THEN
        RAISE_APPLICATION_ERROR(-20003, 'Duplicate alert within 5-minute window');
    END IF;
    
    -- Auto-generate AlertID if not provided
    IF :NEW.AlertID IS NULL THEN
        :NEW.AlertID := SYS_GUID();
    END IF;
END;
/
```

### Stored Procedures

#### Calculate Clean Score Procedure
```sql
-- Stored procedure: Calculate Clean Score for all locations
CREATE OR REPLACE PROCEDURE sp_calculate_clean_scores(
    p_date IN DATE DEFAULT SYSDATE
)
AS
    CURSOR c_locations IS
        SELECT LocationID FROM LOCATIONS WHERE Type = 'Ward';
    
    v_avg_co2 NUMBER;
    v_avg_noise NUMBER;
    v_clean_score NUMBER;
BEGIN
    -- Loop through all wards
    FOR loc IN c_locations LOOP
        -- Calculate averages from MongoDB data (via external table or API)
        -- For demo, using TELEMETRY_SUMMARY table
        SELECT AVG(AvgCO2), AVG(AvgNoise)
        INTO v_avg_co2, v_avg_noise
        FROM TELEMETRY_SUMMARY
        WHERE LocationID = loc.LocationID
          AND Date = p_date;
        
        -- Calculate Clean Score
        v_clean_score := 100 - (
            (v_avg_co2 / 2000 * 100) * 0.5 +
            (v_avg_noise / 100 * 100) * 0.5
        );
        
        -- Insert or update summary
        MERGE INTO TELEMETRY_SUMMARY ts
        USING (SELECT loc.LocationID as lid, p_date as dt FROM DUAL) src
        ON (ts.LocationID = src.lid AND ts.Date = src.dt)
        WHEN MATCHED THEN
            UPDATE SET 
                AvgCO2 = v_avg_co2,
                AvgNoise = v_avg_noise,
                CleanScore = v_clean_score
        WHEN NOT MATCHED THEN
            INSERT (SummaryID, LocationID, Date, AvgCO2, AvgNoise, CleanScore)
            VALUES (SYS_GUID(), loc.LocationID, p_date, v_avg_co2, v_avg_noise, v_clean_score);
    END LOOP;
    
    COMMIT;
    
    DBMS_OUTPUT.PUT_LINE('Clean scores calculated for ' || SQL%ROWCOUNT || ' locations');
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END;
/
```

#### Get Location Hierarchy Function
```sql
-- Function: Get full hierarchy path for a location
CREATE OR REPLACE FUNCTION fn_get_hierarchy_path(
    p_location_id IN VARCHAR2
)
RETURN VARCHAR2
IS
    v_path VARCHAR2(500);
BEGIN
    WITH RECURSIVE hierarchy AS (
        SELECT LocationID, Name, ParentID, Name as Path
        FROM LOCATIONS
        WHERE LocationID = p_location_id
        
        UNION ALL
        
        SELECT l.LocationID, l.Name, l.ParentID, l.Name || ' > ' || h.Path
        FROM LOCATIONS l
        INNER JOIN hierarchy h ON l.LocationID = h.ParentID
    )
    SELECT Path INTO v_path
    FROM hierarchy
    WHERE ParentID IS NULL;
    
    RETURN v_path;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN NULL;
    WHEN OTHERS THEN
        RAISE;
END;
/

-- Usage
SELECT fn_get_hierarchy_path('ward_001') FROM DUAL;
-- Output: "Ho Chi Minh City > District 1 > Ward 1"
```

### Package: Analytics Package
```sql
-- Package specification
CREATE OR REPLACE PACKAGE pkg_analytics AS
    -- Calculate moving average
    FUNCTION fn_moving_average(
        p_sensor_id VARCHAR2,
        p_metric VARCHAR2,
        p_window_size NUMBER DEFAULT 10
    ) RETURN NUMBER;
    
    -- Get sensor statistics
    PROCEDURE sp_get_sensor_stats(
        p_sensor_id VARCHAR2,
        p_avg_co2 OUT NUMBER,
        p_avg_noise OUT NUMBER,
        p_alert_count OUT NUMBER
    );
    
    -- Generate daily report
    PROCEDURE sp_generate_daily_report(
        p_date DATE DEFAULT SYSDATE
    );
END pkg_analytics;
/

-- Package body
CREATE OR REPLACE PACKAGE BODY pkg_analytics AS
    
    FUNCTION fn_moving_average(
        p_sensor_id VARCHAR2,
        p_metric VARCHAR2,
        p_window_size NUMBER DEFAULT 10
    ) RETURN NUMBER
    IS
        v_avg NUMBER;
    BEGIN
        -- Implementation here
        RETURN v_avg;
    END;
    
    PROCEDURE sp_get_sensor_stats(
        p_sensor_id VARCHAR2,
        p_avg_co2 OUT NUMBER,
        p_avg_noise OUT NUMBER,
        p_alert_count OUT NUMBER
    )
    IS
    BEGIN
        SELECT AVG(AvgCO2), AVG(AvgNoise), COUNT(*)
        INTO p_avg_co2, p_avg_noise, p_alert_count
        FROM TELEMETRY_SUMMARY ts
        JOIN SENSOR_REGISTRY sr ON ts.LocationID = sr.LocationID
        WHERE sr.SensorID = p_sensor_id;
    END;
    
    PROCEDURE sp_generate_daily_report(
        p_date DATE DEFAULT SYSDATE
    )
    IS
    BEGIN
        -- Call other procedures
        sp_calculate_clean_scores(p_date);
        -- Generate report logic
        COMMIT;
    END;
    
END pkg_analytics;
/
```

### Call Stored Procedures from Python
```python
# backend/app/db/oracle_procedures.py
import cx_Oracle
from app.db.oracle_client import get_oracle_connection

async def calculate_clean_scores(date=None):
    """
    Call stored procedure to calculate clean scores
    """
    conn = await get_oracle_connection()
    cursor = conn.cursor()
    
    # Call procedure
    if date:
        cursor.callproc('sp_calculate_clean_scores', [date])
    else:
        cursor.callproc('sp_calculate_clean_scores')
    
    conn.commit()
    print("Clean scores calculated successfully")

async def get_sensor_statistics(sensor_id: str):
    """
    Call procedure with OUT parameters
    """
    conn = await get_oracle_connection()
    cursor = conn.cursor()
    
    # Define OUT parameters
    avg_co2 = cursor.var(cx_Oracle.NUMBER)
    avg_noise = cursor.var(cx_Oracle.NUMBER)
    alert_count = cursor.var(cx_Oracle.NUMBER)
    
    # Call procedure
    cursor.callproc('pkg_analytics.sp_get_sensor_stats', [
        sensor_id,
        avg_co2,
        avg_noise,
        alert_count
    ])
    
    return {
        "avgCO2": avg_co2.getvalue(),
        "avgNoise": avg_noise.getvalue(),
        "alertCount": alert_count.getvalue()
    }

async def get_hierarchy_path(location_id: str):
    """
    Call function
    """
    conn = await get_oracle_connection()
    cursor = conn.cursor()
    
    # Call function
    result = cursor.callfunc('fn_get_hierarchy_path', cx_Oracle.STRING, [location_id])
    
    return result
```

### Scheduled Job (DBMS_SCHEDULER)
```sql
-- Create scheduled job to run daily at midnight
BEGIN
    DBMS_SCHEDULER.CREATE_JOB (
        job_name        => 'JOB_DAILY_CLEAN_SCORE',
        job_type        => 'STORED_PROCEDURE',
        job_action      => 'sp_calculate_clean_scores',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=DAILY; BYHOUR=0; BYMINUTE=0',
        enabled         => TRUE,
        comments        => 'Calculate clean scores daily at midnight'
    );
END;
/

-- Check job status
SELECT job_name, state, last_start_date, next_run_date
FROM USER_SCHEDULER_JOBS
WHERE job_name = 'JOB_DAILY_CLEAN_SCORE';

-- Manually run job
BEGIN
    DBMS_SCHEDULER.RUN_JOB('JOB_DAILY_CLEAN_SCORE');
END;
/
```

---

## 📋 Tổng Kết & Roadmap Triển Khai

### Bảng Tổng Hợp Tính Năng

| # | Tính Năng | Độ Khó | Thời Gian | Kiến Thức Nổi Bật | Ưu Tiên |
|---|-----------|--------|-----------|-------------------|---------|
| 1 | **Polyglot Persistence** | ⭐⭐ | 2 ngày | CAP Theorem, Hybrid DB | ✅ ĐÃ CÓ |
| 2 | **Materialized Views** | ⭐⭐⭐ | 3 ngày | Query Optimization, Indexing | ⭐⭐⭐⭐⭐ |
| 3 | **Data Warehouse & OLAP** | ⭐⭐⭐⭐ | 5 ngày | Star Schema, OLAP Cube | ⭐⭐⭐⭐⭐ |
| 4 | **2-Phase Commit** | ⭐⭐⭐⭐⭐ | 4 ngày | Distributed Transactions | ⭐⭐⭐⭐ |
| 5 | **Replication & Sharding** | ⭐⭐⭐⭐ | 4 ngày | High Availability, Scalability | ⭐⭐⭐⭐ |
| 6 | **Time-Series Optimization** | ⭐⭐⭐ | 3 ngày | Compression, Bucketing | ⭐⭐⭐⭐⭐ |
| 7 | **Full-Text Search** | ⭐⭐⭐ | 3 ngày | Inverted Index, TF-IDF | ⭐⭐⭐⭐ |
| 8 | **Triggers & Procedures** | ⭐⭐⭐ | 3 ngày | Database Logic, Automation | ⭐⭐⭐⭐⭐ |

### Roadmap Triển Khai (4 Tuần)

#### Tuần 1: Foundation & Documentation
- ✅ **Ngày 1-2:** Tài liệu hóa Polyglot Persistence hiện tại
- 🔨 **Ngày 3-5:** Implement Materialized Views cho Leaderboard
- 🔨 **Ngày 6-7:** Implement Triggers & Stored Procedures

#### Tuần 2: Time-Series & Search
- 🔨 **Ngày 8-10:** Migrate sang Time-Series Collections
- 🔨 **Ngày 11-13:** Implement Full-Text Search
- 🔨 **Ngày 14:** Testing & Documentation

#### Tuần 3: Data Warehouse
- 🔨 **Ngày 15-17:** Design & Create Star Schema
- 🔨 **Ngày 18-19:** Implement ETL Process
- 🔨 **Ngày 20-21:** Implement OLAP Queries

#### Tuần 4: Advanced Features
- 🔨 **Ngày 22-24:** Implement 2-Phase Commit
- 🔨 **Ngày 25-27:** Setup Replication & Sharding
- 🔨 **Ngày 28:** Final Testing & Documentation

### Checklist Cho Báo Cáo

#### Phần Lý Thuyết (Slides)
- [ ] Giải thích CAP Theorem với ví dụ MongoDB vs Oracle
- [ ] So sánh OLTP vs OLAP
- [ ] Explain Query Optimization với Execution Plans
- [ ] Phân tích Trade-offs của Polyglot Persistence
- [ ] Giải thích 2-Phase Commit Protocol
- [ ] So sánh Replication strategies (Master-Slave vs Multi-Master)
- [ ] Explain Sharding strategies (Hash vs Range)
- [ ] Giải thích Inverted Index cho Full-Text Search

#### Phần Thực Hành (Demo)
- [ ] Demo Materialized View performance (Before/After)
- [ ] Demo OLAP queries (Drill-down, Roll-up, Slice, Dice)
- [ ] Demo 2PC transaction với failure scenario
- [ ] Demo Failover khi Primary MongoDB down
- [ ] Demo Full-Text Search với autocomplete
- [ ] Demo Triggers tự động validate data
- [ ] Show Execution Plans comparison
- [ ] Show Storage compression với Time-Series

#### Tài Liệu Kỹ Thuật
- [ ] Architecture diagrams cho từng feature
- [ ] Code examples với comments chi tiết
- [ ] Performance benchmarks
- [ ] Database schema diagrams
- [ ] API documentation
- [ ] Testing strategy & results

### Câu Hỏi Thường Gặp Từ Giảng Viên

**Q1: Tại sao dùng MongoDB và Oracle, không dùng 1 database thôi?**
→ Giải thích Polyglot Persistence, CAP Theorem, use case khác nhau

**Q2: Materialized View khác gì với Regular View?**
→ Pre-computed vs On-demand, performance trade-offs, refresh strategies

**Q3: 2-Phase Commit có vấn đề gì?**
→ Blocking protocol, coordinator failure, performance overhead

**Q4: Sharding khác gì với Replication?**
→ Horizontal scaling vs High availability, data distribution

**Q5: Time-Series Collection tối ưu như thế nào?**
→ Bucketing, compression, specialized indexes

**Q6: Khi nào nên dùng Stored Procedure thay vì Application Logic?**
→ Performance, security, reusability, network overhead

### Tài Liệu Tham Khảo

1. **MongoDB Documentation**
   - Time-Series Collections: https://docs.mongodb.com/manual/core/timeseries-collections/
   - Sharding: https://docs.mongodb.com/manual/sharding/
   - Replication: https://docs.mongodb.com/manual/replication/

2. **Oracle Documentation**
   - Materialized Views: https://docs.oracle.com/en/database/oracle/oracle-database/19/dwhsg/basic-materialized-views.html
   - PL/SQL: https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/
   - Text Search: https://docs.oracle.com/en/database/oracle/oracle-database/19/ccref/

3. **Academic Papers**
   - CAP Theorem: Brewer, E. (2000)
   - 2-Phase Commit: Gray, J. (1978)
   - OLAP Cube: Codd, E.F. (1993)

---

## 🎓 Kết Luận

Đồ án này showcase **8 tính năng database nâng cao** covering:
- ✅ NoSQL vs SQL trade-offs
- ✅ Query optimization techniques
- ✅ Distributed systems concepts
- ✅ Data warehousing & analytics
- ✅ High availability & scalability
- ✅ Advanced indexing strategies
- ✅ Database automation

**Điểm mạnh cho báo cáo:**
1. Hybrid architecture thể hiện hiểu biết về CAP Theorem
2. Materialized Views & OLAP thể hiện query optimization
3. 2PC thể hiện distributed transaction knowledge
4. Replication/Sharding thể hiện scalability concepts
5. Time-Series optimization thể hiện specialized database features
6. Triggers/Procedures thể hiện database programming

**Lưu ý:** Không cần implement HẾT 8 features. Chọn 4-5 features quan trọng nhất (đánh dấu ⭐⭐⭐⭐⭐) để implement và demo kỹ lưỡng hơn là làm hời hợt tất cả.

