# 🚀 DATABASE REDESIGN - IMPLEMENTATION PLAN

**Project:** Smart City IoT Dashboard - Production Database Redesign  
**Start Date:** May 2, 2026  
**Target Completion:** May 16, 2026 (2 weeks)  
**Team Size:** 1 Developer

---

## 📅 SPRINT OVERVIEW

### Sprint 1: Core Infrastructure (Week 1)
- **Days 1-2:** Database Schema & Models
- **Days 3-4:** MongoDB Setup & Service Layer Foundation
- **Day 5:** Testing & Validation

### Sprint 2: Features & Integration (Week 2)
- **Days 6-7:** Alert System & Analytics
- **Days 8-9:** API & Frontend Updates
- **Day 10:** End-to-End Testing & Deployment

---

## 📋 DETAILED TASK BREAKDOWN

### 🔵 SPRINT 1 - WEEK 1

---

#### **DAY 1: Database Schema Setup**

##### Task 1.1: Deploy Oracle Schema v2 ⏱️ 2 hours
**Priority:** 🔴 Critical  
**Dependencies:** None

**Steps:**
1. Backup current Oracle database
   ```bash
   # Create backup
   docker exec oracle-db expdp system/password@XEPDB1 \
     schemas=SYSTEM directory=DATA_PUMP_DIR dumpfile=backup_$(date +%Y%m%d).dmp
   ```

2. Drop old tables (if exists)
   ```sql
   -- Run cleanup script
   @backend/app/db/sql/cleanup_old_schema.sql
   ```

3. Execute new schema
   ```bash
   sqlplus system/password@localhost:1521/XEPDB1 @backend/app/db/sql/oracle_schema_v2.sql
   ```

4. Verify tables created
   ```sql
   SELECT table_name FROM user_tables ORDER BY table_name;
   ```

**Acceptance Criteria:**
- ✅ All 9 tables created successfully
- ✅ All triggers working
- ✅ All indexes created
- ✅ No errors in SQL*Plus output

**Files Modified:**
- None (new schema file already created)

---

##### Task 1.2: Load Seed Data ⏱️ 1 hour
**Priority:** 🔴 Critical  
**Dependencies:** Task 1.1

**Steps:**
1. Execute seed data script
   ```bash
   sqlplus system/password@localhost:1521/XEPDB1 @backend/app/db/sql/oracle_seed_v2.sql
   ```

2. Verify data loaded
   ```sql
   SELECT 'Locations' as Entity, COUNT(*) as Count FROM LOCATIONS
   UNION ALL
   SELECT 'Sensors', COUNT(*) FROM SENSOR_REGISTRY
   UNION ALL
   SELECT 'Capabilities', COUNT(*) FROM SENSOR_CAPABILITIES;
   ```

3. Test triggers
   ```sql
   -- Test cluster count trigger
   SELECT ClusterID, SensorCount FROM SENSOR_CLUSTERS;
   ```

**Acceptance Criteria:**
- ✅ 13 locations inserted (1 city + 3 districts + 9 wards)
- ✅ 4 clusters created
- ✅ 33 sensors inserted
- ✅ 165 capabilities inserted (33 sensors × 5 metrics)
- ✅ Cluster sensor counts are correct

**Files Modified:**
- None

---

##### Task 1.3: Fix Telemetry Model ⏱️ 2 hours
**Priority:** 🔴 Critical  
**Dependencies:** None

**Steps:**
1. Backup current telemetry.py
   ```bash
   cp backend/app/models/telemetry.py backend/app/models/telemetry.py.backup
   ```

2. Rewrite telemetry.py with new structure
   - Add `TelemetryData` model
   - Add `GeoLocation` model
   - Add `DataQuality` model
   - Update `Telemetry` model
   - Add backward compatibility

3. Test model validation
   ```python
   # Create test script
   python -c "from backend.app.models.telemetry import Telemetry; print('OK')"
   ```

**Acceptance Criteria:**
- ✅ No syntax errors
- ✅ All validators working
- ✅ Pydantic models validate correctly
- ✅ Backward compatibility maintained

**Files Modified:**
- `backend/app/models/telemetry.py`

**Code Template:**
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

class TelemetryData(BaseModel):
    co2: Optional[float] = Field(None, ge=0, le=5000)
    noise: Optional[float] = Field(None, ge=0, le=120)
    temperature: Optional[float] = Field(None, ge=-50, le=60)
    pm25: Optional[float] = Field(None, ge=0, le=500)
    humidity: Optional[float] = Field(None, ge=0, le=100)

class GeoLocation(BaseModel):
    type: str = "Point"
    coordinates: list[float]  # [lng, lat]

class DataQuality(BaseModel):
    batteryLevel: Optional[float] = None
    signalStrength: Optional[float] = None

class Telemetry(BaseModel):
    sensorId: str
    locationId: str
    clusterId: Optional[str] = None
    data: TelemetryData
    location: GeoLocation
    quality: Optional[DataQuality] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    receivedAt: datetime = Field(default_factory=datetime.utcnow)
    expireAt: Optional[datetime] = None
```

---

##### Task 1.4: Update Alert Model ⏱️ 1 hour
**Priority:** 🟡 High  
**Dependencies:** Task 1.1

**Steps:**
1. Update `backend/app/models/alert.py`
2. Add new fields: `clusterId`, `predictedValue`, `confidenceScore`
3. Add new alert types: `PREDICTIVE`, `ANOMALY`, `CLUSTER`
4. Update validation rules

**Acceptance Criteria:**
- ✅ Model matches new ALERTS table schema
- ✅ All new fields included
- ✅ Validation rules updated

**Files Modified:**
- `backend/app/models/alert.py`

---

#### **DAY 2: MongoDB Setup**

##### Task 2.1: Create MongoDB Indexes Script ⏱️ 1 hour
**Priority:** 🔴 Critical  
**Dependencies:** None

**Steps:**
1. Create `backend/app/db/mongodb_indexes.js`
2. Add all required indexes
3. Test index creation

**Acceptance Criteria:**
- ✅ TTL index created
- ✅ All compound indexes created
- ✅ Geospatial index created
- ✅ Script runs without errors

**Files Created:**
- `backend/app/db/mongodb_indexes.js`

**Code Template:**
```javascript
// TTL Index
db.telemetry.createIndex(
  { expireAt: 1 },
  { expireAfterSeconds: 0 }
);

// Sensor + Time
db.telemetry.createIndex(
  { sensorId: 1, timestamp: -1 }
);

// Location + Time
db.telemetry.createIndex(
  { locationId: 1, timestamp: -1 }
);

// Cluster + Time
db.telemetry.createIndex(
  { clusterId: 1, timestamp: -1 }
);

// Geospatial
db.telemetry.createIndex(
  { location: "2dsphere" }
);
```

---

##### Task 2.2: Update MongoDB Client ⏱️ 2 hours
**Priority:** 🔴 Critical  
**Dependencies:** Task 2.1

**Steps:**
1. Update `backend/app/db/mongodb_client.py`
2. Add index creation on startup
3. Add geospatial query methods
4. Add cluster query methods
5. Test connection and indexes

**Acceptance Criteria:**
- ✅ Indexes created automatically on startup
- ✅ Geospatial queries working
- ✅ Cluster queries working
- ✅ All tests passing

**Files Modified:**
- `backend/app/db/mongodb_client.py`

**New Methods to Add:**
```python
async def create_indexes(self):
    """Create all required indexes"""
    
async def find_nearby_sensors(self, lat: float, lng: float, radius_meters: int):
    """Find sensors within radius using geospatial query"""
    
async def get_cluster_telemetry(self, cluster_id: str, start: datetime, end: datetime):
    """Get telemetry for all sensors in a cluster"""
```

---

##### Task 2.3: Update Telemetry Service ⏱️ 3 hours
**Priority:** 🔴 Critical  
**Dependencies:** Task 1.3, Task 2.2

**Steps:**
1. Update `backend/app/services/telemetry_service.py`
2. Add geolocation enrichment
3. Add cluster assignment
4. Add TTL calculation
5. Update MongoDB insert logic
6. Test with sample data

**Acceptance Criteria:**
- ✅ Geolocation added from sensor registry
- ✅ Cluster ID assigned correctly
- ✅ TTL set to 30 days
- ✅ All new fields populated
- ✅ Backward compatibility maintained

**Files Modified:**
- `backend/app/services/telemetry_service.py`

**Key Changes:**
```python
async def store_telemetry(self, telemetry_data: dict):
    # 1. Lookup sensor geolocation
    sensor = await oracle_client.get_sensor(telemetry_data['sensorId'])
    
    # 2. Create enhanced telemetry
    telemetry = Telemetry(
        sensorId=telemetry_data['sensorId'],
        locationId=sensor.locationId,
        clusterId=sensor.clusterId,
        data=TelemetryData(**telemetry_data['data']),
        location=GeoLocation(
            coordinates=[sensor.longitude, sensor.latitude]
        ),
        expireAt=datetime.utcnow() + timedelta(days=30)
    )
    
    # 3. Insert to MongoDB
    await mongodb_client.insert_telemetry(telemetry.dict())
```

---

#### **DAY 3: Oracle Client Updates**

##### Task 3.1: Add Sensor Registry Methods ⏱️ 2 hours
**Priority:** 🔴 Critical  
**Dependencies:** Task 1.1

**Steps:**
1. Update `backend/app/db/oracle_client.py`
2. Add methods for new tables
3. Test all CRUD operations

**Acceptance Criteria:**
- ✅ All sensor registry methods working
- ✅ Location hierarchy queries working
- ✅ Cluster queries working
- ✅ Capability queries working

**Files Modified:**
- `backend/app/db/oracle_client.py`

**New Methods:**
```python
async def get_sensor(self, sensor_id: str) -> SensorRegistry
async def get_sensors_by_location(self, location_id: str) -> List[SensorRegistry]
async def get_sensors_by_cluster(self, cluster_id: str) -> List[SensorRegistry]
async def get_sensor_capabilities(self, sensor_id: str) -> List[SensorCapability]
async def get_location_hierarchy(self, location_id: str) -> List[Location]
async def get_cluster(self, cluster_id: str) -> SensorCluster
```

---

##### Task 3.2: Update Alert Service - Part 1 (Threshold) ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Task 1.4

**Steps:**
1. Update `backend/app/services/alert_service.py`
2. Update threshold checking for new metrics (PM2.5, Humidity)
3. Add cluster-level alerts
4. Add alert deduplication
5. Test threshold alerts

**Acceptance Criteria:**
- ✅ PM2.5 thresholds working
- ✅ Humidity thresholds working
- ✅ Cluster alerts working
- ✅ Deduplication working

**Files Modified:**
- `backend/app/services/alert_service.py`

---

##### Task 3.3: Create Spatial Query Utilities ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Task 3.1

**Steps:**
1. Create `backend/app/utils/spatial.py`
2. Add Haversine distance calculation
3. Add nearby sensor finder
4. Add hotspot detection
5. Test spatial queries

**Acceptance Criteria:**
- ✅ Distance calculations accurate
- ✅ Nearby sensor queries working
- ✅ Hotspot detection working

**Files Created:**
- `backend/app/utils/spatial.py`

**Code Template:**
```python
import math
from typing import List, Tuple

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in meters between two points"""
    R = 6371000  # Earth radius in meters
    # ... implementation
    
async def find_nearby_sensors(
    target_lat: float, 
    target_lng: float, 
    radius_meters: int
) -> List[SensorRegistry]:
    """Find all sensors within radius"""
    # ... implementation
```

---

#### **DAY 4: Analytics & Aggregation**

##### Task 4.1: Add AQI Calculation ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** None

**Steps:**
1. Create `backend/app/utils/aqi.py`
2. Implement EPA AQI calculation
3. Add PM2.5 breakpoints
4. Test with sample data

**Acceptance Criteria:**
- ✅ AQI calculation accurate
- ✅ All breakpoints correct
- ✅ Edge cases handled

**Files Created:**
- `backend/app/utils/aqi.py`

**Code Template:**
```python
def calculate_aqi(pm25: float) -> int:
    """Calculate AQI from PM2.5 concentration"""
    breakpoints = [
        {'c_low': 0.0, 'c_high': 12.0, 'i_low': 0, 'i_high': 50},
        {'c_low': 12.1, 'c_high': 35.4, 'i_low': 51, 'i_high': 100},
        # ... more breakpoints
    ]
    # ... implementation
```

---

##### Task 4.2: Update Analytics Service ⏱️ 3 hours
**Priority:** 🟡 High  
**Dependencies:** Task 4.1

**Steps:**
1. Update `backend/app/services/analytics_service.py`
2. Add PM2.5 aggregation
3. Add humidity aggregation
4. Add AQI calculation
5. Add cluster-level aggregation
6. Test all analytics

**Acceptance Criteria:**
- ✅ PM2.5 analytics working
- ✅ Humidity analytics working
- ✅ AQI calculated correctly
- ✅ Cluster aggregation working

**Files Modified:**
- `backend/app/services/analytics_service.py`

---

##### Task 4.3: Update Scheduler Service ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Task 4.2

**Steps:**
1. Update `backend/app/services/scheduler.py`
2. Update hourly aggregation for new metrics
3. Add cluster aggregation job
4. Update TELEMETRY_SUMMARY inserts
5. Test scheduler

**Acceptance Criteria:**
- ✅ Hourly aggregation includes PM2.5, humidity
- ✅ Cluster aggregation working
- ✅ TELEMETRY_SUMMARY populated correctly

**Files Modified:**
- `backend/app/services/scheduler.py`

---

#### **DAY 5: Testing & Validation**

##### Task 5.1: Unit Tests for Models ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** All Day 1-4 tasks

**Steps:**
1. Update `backend/tests/test_models.py`
2. Add tests for new sensor models
3. Add tests for updated telemetry model
4. Add tests for updated alert model
5. Run all tests

**Acceptance Criteria:**
- ✅ All model tests passing
- ✅ Validation tests passing
- ✅ Edge cases covered

**Files Modified:**
- `backend/tests/test_models.py`

---

##### Task 5.2: Integration Tests ⏱️ 3 hours
**Priority:** 🟡 High  
**Dependencies:** Task 5.1

**Steps:**
1. Create `backend/tests/test_redesign_integration.py`
2. Test Oracle schema
3. Test MongoDB indexes
4. Test telemetry flow
5. Test analytics pipeline
6. Run all tests

**Acceptance Criteria:**
- ✅ Schema tests passing
- ✅ Index tests passing
- ✅ End-to-end flow working
- ✅ No data loss

**Files Created:**
- `backend/tests/test_redesign_integration.py`

---

##### Task 5.3: Manual Testing & Validation ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Task 5.2

**Steps:**
1. Start all services
2. Test sensor data ingestion
3. Verify MongoDB storage
4. Verify Oracle queries
5. Check aggregations
6. Document any issues

**Acceptance Criteria:**
- ✅ All services running
- ✅ Data flowing correctly
- ✅ No errors in logs
- ✅ Performance acceptable

---

### 🟢 SPRINT 2 - WEEK 2

---

#### **DAY 6: Advanced Alert System**

##### Task 6.1: Implement Predictive Alerts ⏱️ 3 hours
**Priority:** 🟡 High  
**Dependencies:** Sprint 1 complete

**Steps:**
1. Update `backend/app/services/alert_service.py`
2. Add linear regression logic
3. Add trend analysis
4. Add confidence scoring
5. Test predictive alerts

**Acceptance Criteria:**
- ✅ Linear regression working
- ✅ Predictions accurate
- ✅ Confidence scores calculated
- ✅ Alerts triggered correctly

**Files Modified:**
- `backend/app/services/alert_service.py`

**Dependencies to Add:**
```txt
scikit-learn==1.3.0
numpy==1.24.3
```

---

##### Task 6.2: Implement Anomaly Detection ⏱️ 3 hours
**Priority:** 🟡 High  
**Dependencies:** Task 6.1

**Steps:**
1. Add Z-score anomaly detection
2. Add statistical analysis
3. Add anomaly alerts
4. Test with sample data

**Acceptance Criteria:**
- ✅ Z-score calculation correct
- ✅ Anomalies detected
- ✅ False positives minimized
- ✅ Alerts triggered

**Files Modified:**
- `backend/app/services/alert_service.py`

---

##### Task 6.3: Alert Deduplication & Lifecycle ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Task 6.2

**Steps:**
1. Add alert deduplication logic
2. Add alert lifecycle management
3. Add alert acknowledgment
4. Add alert resolution
5. Test workflow

**Acceptance Criteria:**
- ✅ No duplicate alerts
- ✅ Lifecycle tracked
- ✅ Acknowledgment working
- ✅ Resolution working

**Files Modified:**
- `backend/app/services/alert_service.py`

---

#### **DAY 7: API Layer Updates**

##### Task 7.1: Add Location Endpoints ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Sprint 1 complete

**Steps:**
1. Update `backend/app/api/routes.py`
2. Add `/locations` endpoints
3. Add `/locations/{id}/hierarchy` endpoint
4. Add `/locations/{id}/sensors` endpoint
5. Test endpoints

**Acceptance Criteria:**
- ✅ All endpoints working
- ✅ Hierarchy queries correct
- ✅ Sensor listings correct

**Files Modified:**
- `backend/app/api/routes.py`

**New Endpoints:**
```python
@router.get("/locations")
async def get_locations()

@router.get("/locations/{location_id}")
async def get_location(location_id: str)

@router.get("/locations/{location_id}/hierarchy")
async def get_location_hierarchy(location_id: str)

@router.get("/locations/{location_id}/sensors")
async def get_location_sensors(location_id: str)
```

---

##### Task 7.2: Add Cluster Endpoints ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Task 7.1

**Steps:**
1. Add `/clusters` endpoints
2. Add `/clusters/{id}/sensors` endpoint
3. Add `/clusters/{id}/telemetry` endpoint
4. Add `/clusters/hotspots` endpoint
5. Test endpoints

**Acceptance Criteria:**
- ✅ All endpoints working
- ✅ Cluster data correct
- ✅ Hotspot detection working

**Files Modified:**
- `backend/app/api/routes.py`

---

##### Task 7.3: Add Sensor Registry Endpoints ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Task 7.2

**Steps:**
1. Add `/sensors` endpoints
2. Add `/sensors/{id}/capabilities` endpoint
3. Add `/sensors/{id}/health` endpoint
4. Add `/sensors/nearby` endpoint (spatial query)
5. Test endpoints

**Acceptance Criteria:**
- ✅ All endpoints working
- ✅ Capabilities listed correctly
- ✅ Health status correct
- ✅ Spatial queries working

**Files Modified:**
- `backend/app/api/routes.py`

---

##### Task 7.4: Update Telemetry Endpoints ⏱️ 1 hour
**Priority:** 🟡 High  
**Dependencies:** Task 7.3

**Steps:**
1. Update `/telemetry` endpoints for new model
2. Add cluster filtering
3. Add geospatial filtering
4. Test endpoints

**Acceptance Criteria:**
- ✅ New fields returned
- ✅ Filtering working
- ✅ Backward compatibility maintained

**Files Modified:**
- `backend/app/api/routes.py`

---

#### **DAY 8: IoT Simulator Updates**

##### Task 8.1: Update Simulator for New Schema ⏱️ 3 hours
**Priority:** 🔴 Critical  
**Dependencies:** Sprint 1 complete

**Steps:**
1. Update `iot-simulator/simulator.py`
2. Update sensor IDs to match seed data
3. Add PM2.5 generation
4. Add humidity generation
5. Add battery level simulation
6. Add signal strength simulation
7. Test simulator

**Acceptance Criteria:**
- ✅ All 33 sensors simulated
- ✅ PM2.5 data generated
- ✅ Humidity data generated
- ✅ Battery/signal simulated
- ✅ Data realistic

**Files Modified:**
- `iot-simulator/simulator.py`

**Key Changes:**
```python
SENSORS = [
    "sen_q1_ben_nghe_01",
    "sen_q1_ben_nghe_02",
    # ... all 33 sensors
]

def generate_telemetry(sensor_id):
    return {
        "sensorId": sensor_id,
        "data": {
            "co2": random.uniform(400, 600),
            "noise": random.uniform(50, 80),
            "temperature": random.uniform(24, 32),
            "pm25": random.uniform(20, 60),  # NEW
            "humidity": random.uniform(60, 85)  # NEW
        },
        "quality": {  # NEW
            "batteryLevel": random.uniform(70, 100),
            "signalStrength": random.uniform(-60, -30)
        },
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

##### Task 8.2: End-to-End Testing with Simulator ⏱️ 2 hours
**Priority:** 🔴 Critical  
**Dependencies:** Task 8.1

**Steps:**
1. Start all services
2. Start simulator
3. Monitor data flow
4. Verify MongoDB storage
5. Verify Oracle aggregation
6. Verify WebSocket broadcasts
7. Check for errors

**Acceptance Criteria:**
- ✅ Data flowing end-to-end
- ✅ No errors
- ✅ Performance acceptable
- ✅ All metrics captured

---

#### **DAY 9: Frontend Updates**

##### Task 9.1: Update TypeScript Types ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Day 7 complete

**Steps:**
1. Update `frontend/src/types/index.ts`
2. Add `Location` type
3. Add `SensorCluster` type
4. Add `SensorRegistry` type
5. Update `Telemetry` type
6. Add `SensorCapability` type

**Acceptance Criteria:**
- ✅ All types defined
- ✅ Types match backend models
- ✅ No TypeScript errors

**Files Modified:**
- `frontend/src/types/index.ts`

---

##### Task 9.2: Update API Service ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Task 9.1

**Steps:**
1. Update `frontend/src/services/api.ts`
2. Add location API calls
3. Add cluster API calls
4. Add sensor registry API calls
5. Update telemetry API calls

**Acceptance Criteria:**
- ✅ All API calls working
- ✅ Types correct
- ✅ Error handling working

**Files Modified:**
- `frontend/src/services/api.ts`

---

##### Task 9.3: Update Components ⏱️ 4 hours
**Priority:** 🟡 High  
**Dependencies:** Task 9.2

**Steps:**
1. Update `MapView.tsx` for clusters
2. Update `ChartView.tsx` for PM2.5 & humidity
3. Update `Leaderboard.tsx` for new metrics
4. Update `AlertsPanel.tsx` for new alert types
5. Test all components

**Acceptance Criteria:**
- ✅ Clusters displayed on map
- ✅ PM2.5 & humidity charts working
- ✅ New metrics in leaderboard
- ✅ New alert types displayed

**Files Modified:**
- `frontend/src/components/MapView.tsx`
- `frontend/src/components/ChartView.tsx`
- `frontend/src/components/Leaderboard.tsx`
- `frontend/src/components/AlertsPanel.tsx`

---

#### **DAY 10: Final Testing & Deployment**

##### Task 10.1: Comprehensive Testing ⏱️ 3 hours
**Priority:** 🔴 Critical  
**Dependencies:** All previous tasks

**Steps:**
1. Run all unit tests
2. Run all integration tests
3. Run end-to-end tests
4. Performance testing
5. Load testing
6. Fix any issues found

**Acceptance Criteria:**
- ✅ All tests passing
- ✅ No critical bugs
- ✅ Performance acceptable
- ✅ System stable

---

##### Task 10.2: Documentation Update ⏱️ 2 hours
**Priority:** 🟡 High  
**Dependencies:** Task 10.1

**Steps:**
1. Update README.md
2. Update API documentation
3. Update database schema docs
4. Create migration guide
5. Update deployment guide

**Acceptance Criteria:**
- ✅ All docs updated
- ✅ Migration guide complete
- ✅ API docs accurate

**Files Modified:**
- `README.md`
- `backend/API_DOCUMENTATION.md`
- `DATABASE_REDESIGN_PRODUCTION.md`

---

##### Task 10.3: Deployment ⏱️ 2 hours
**Priority:** 🔴 Critical  
**Dependencies:** Task 10.2

**Steps:**
1. Update docker-compose.yml
2. Update environment variables
3. Build Docker images
4. Deploy to staging
5. Smoke test
6. Deploy to production

**Acceptance Criteria:**
- ✅ Docker images built
- ✅ Staging deployment successful
- ✅ Production deployment successful
- ✅ System operational

**Files Modified:**
- `docker-compose.yml`
- `.env.example`

---

## 📊 PROGRESS TRACKING

### Daily Standup Template
```markdown
**Yesterday:**
- Completed: [tasks]
- Blockers: [issues]

**Today:**
- Plan: [tasks]
- Focus: [priority]

**Risks:**
- [any concerns]
```

### Task Status Legend
- 🔴 Critical (must complete)
- 🟡 High (should complete)
- 🟢 Medium (nice to have)
- ⚪ Low (optional)

### Completion Checklist
- [ ] All database tables created
- [ ] All seed data loaded
- [ ] All models updated
- [ ] All services updated
- [ ] All API endpoints working
- [ ] All tests passing
- [ ] Frontend updated
- [ ] Documentation complete
- [ ] Deployed successfully

---

## 🚨 RISK MITIGATION

### Risk 1: Schema Migration Issues
**Mitigation:**
- Backup database before migration
- Test on staging first
- Have rollback plan ready

### Risk 2: Data Loss During Migration
**Mitigation:**
- Export all existing data
- Verify data integrity after migration
- Keep old schema for 1 week

### Risk 3: Performance Degradation
**Mitigation:**
- Benchmark before and after
- Monitor query performance
- Optimize indexes if needed

### Risk 4: Breaking Changes
**Mitigation:**
- Maintain backward compatibility
- Version API endpoints
- Gradual rollout

---

## 📈 SUCCESS METRICS

### Technical Metrics
- ✅ All 9 tables created
- ✅ 33 sensors with geolocation
- ✅ 165 sensor capabilities
- ✅ MongoDB indexes created
- ✅ < 100ms query response time
- ✅ 500+ inserts/second throughput
- ✅ 0 data loss
- ✅ 99.9% uptime

### Feature Metrics
- ✅ Predictive alerts working
- ✅ Anomaly detection working
- ✅ Spatial clustering working
- ✅ AQI calculation accurate
- ✅ PM2.5 & humidity tracked
- ✅ Hotspot detection working

---

## 🎯 DEFINITION OF DONE

A task is considered "done" when:
1. ✅ Code written and tested
2. ✅ Unit tests passing
3. ✅ Integration tests passing
4. ✅ Code reviewed (self-review)
5. ✅ Documentation updated
6. ✅ No critical bugs
7. ✅ Deployed to staging
8. ✅ Acceptance criteria met

---

**Plan Created:** May 2, 2026  
**Last Updated:** May 2, 2026  
**Status:** Ready to Execute
