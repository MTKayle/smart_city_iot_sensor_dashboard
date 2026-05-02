# 🏗️ DATABASE REDESIGN IMPLEMENTATION STATUS

**Date:** May 2, 2026  
**Project:** Smart City IoT Dashboard - Production Database Redesign

---

## ✅ COMPLETED

### Phase 1: Database Schema

#### 1.1 Oracle SQL Schema (v2.0)
**File:** `backend/app/db/sql/oracle_schema_v2.sql`

**Created Tables:**
- ✅ `LOCATIONS` - Hierarchical location structure (City > District > Ward)
- ✅ `SENSOR_CLUSTERS` - Spatial clustering for hotspot detection
- ✅ `SENSOR_REGISTRY` - Enhanced sensor registry with geolocation
- ✅ `SENSOR_CAPABILITIES` - Normalized sensor capabilities
- ✅ `ALERTS` - Enhanced alert system (threshold + predictive + anomaly)
- ✅ `INCIDENTS` - Incident management system
- ✅ `INCIDENT_ALERTS` - Many-to-many junction table
- ✅ `SENSOR_HEALTH_LOGS` - Sensor health monitoring
- ✅ `TELEMETRY_SUMMARY` - Pre-aggregated telemetry data

**Features:**
- ✅ Auto-update triggers for `UpdatedAt` fields
- ✅ Auto-sync `LocationID` in ALERTS from sensor/cluster
- ✅ Auto-update cluster sensor count
- ✅ Comprehensive indexes for performance
- ✅ Foreign key constraints for data integrity
- ✅ Check constraints for data validation

#### 1.2 Seed Data (v2.0)
**File:** `backend/app/db/sql/oracle_seed_v2.sql`

**Data Inserted:**
- ✅ 1 City (Ho Chi Minh City)
- ✅ 3 Districts (District 1, 3, 5)
- ✅ 9 Wards (3 per district)
- ✅ 4 Sensor Clusters (spatial grouping)
- ✅ 33 Sensors (5-3 sensors per ward with realistic geolocation)
- ✅ 165 Sensor Capabilities (5 metrics per sensor: CO2, Noise, Temp, PM2.5, Humidity)

**Geolocation Coverage:**
- District 1: 15 sensors across 3 wards
- District 3: 9 sensors across 3 wards
- District 5: 9 sensors across 3 wards
- All sensors have precise lat/lng coordinates

#### 1.3 Python Models
**File:** `backend/app/models/sensor.py`

**Created Models:**
- ✅ `Location` - Location hierarchy model
- ✅ `SensorCluster` - Cluster model
- ✅ `SensorRegistry` - Enhanced sensor model with geolocation
- ✅ `SensorCapability` - Capability model
- ✅ `SensorHealthLog` - Health monitoring model
- ✅ `SensorWithCapabilities` - Composite model
- ✅ `SensorWithLocation` - Composite model with location details

---

## 🚧 IN PROGRESS

### Phase 1: Database Schema (Continued)

#### 1.4 Telemetry Model Update
**File:** `backend/app/models/telemetry.py`

**Status:** ⚠️ Needs update (syntax error in current file)

**Required Changes:**
- Add `TelemetryData` nested model (CO2, Noise, Temp, PM2.5, Humidity)
- Add `GeoLocation` model (GeoJSON Point)
- Add `DataQuality` model (battery, signal strength)
- Update `Telemetry` model to use nested models
- Add `clusterId` field
- Add `location` field (GeoJSON)
- Add `quality` field
- Add `receivedAt` and `expireAt` fields
- Add backward compatibility layer

---

## 📋 TODO

### Phase 2: MongoDB Setup

#### 2.1 MongoDB Indexes
**File:** `backend/app/db/mongodb_indexes.js` (to create)

**Required Indexes:**
- [ ] TTL index on `expireAt` (30 days auto-delete)
- [ ] Compound index on `sensorId + timestamp`
- [ ] Compound index on `locationId + timestamp`
- [ ] Compound index on `clusterId + timestamp`
- [ ] Time-only index on `timestamp`
- [ ] Geospatial index on `location` (2dsphere)

#### 2.2 MongoDB Client Update
**File:** `backend/app/db/mongodb_client.py`

**Required Changes:**
- [ ] Add index creation on startup
- [ ] Add TTL configuration
- [ ] Add geospatial query methods
- [ ] Add cluster-based query methods

### Phase 3: Service Layer Updates

#### 3.1 Telemetry Service
**File:** `backend/app/services/telemetry_service.py`

**Required Changes:**
- [ ] Update to use new `Telemetry` model
- [ ] Add geolocation enrichment (lookup sensor lat/lng)
- [ ] Add cluster assignment
- [ ] Add TTL calculation (30 days)
- [ ] Update MongoDB insert to include all new fields

#### 3.2 Alert Service
**File:** `backend/app/services/alert_service.py`

**Required Changes:**
- [ ] Add predictive alert logic (linear regression)
- [ ] Add anomaly detection (Z-score)
- [ ] Add alert deduplication
- [ ] Update to use new ALERTS table schema
- [ ] Add cluster-level alerts

#### 3.3 Analytics Service
**File:** `backend/app/services/analytics_service.py`

**Required Changes:**
- [ ] Add AQI calculation
- [ ] Add PM2.5 support
- [ ] Add humidity support
- [ ] Update aggregation queries for new schema
- [ ] Add spatial aggregation (cluster-based)

#### 3.4 Scheduler Service
**File:** `backend/app/services/scheduler.py`

**Required Changes:**
- [ ] Update hourly aggregation for new metrics
- [ ] Add cluster-level aggregation
- [ ] Update TELEMETRY_SUMMARY inserts

### Phase 4: API Layer Updates

#### 4.1 Routes
**File:** `backend/app/api/routes.py`

**Required Changes:**
- [ ] Add `/locations` endpoints (hierarchy queries)
- [ ] Add `/clusters` endpoints
- [ ] Add `/sensors` endpoints (with capabilities)
- [ ] Update `/telemetry` to support new model
- [ ] Add `/spatial` endpoints (nearby sensors, hotspots)
- [ ] Update `/analytics` for new metrics

#### 4.2 WebSocket
**File:** `backend/app/api/websocket.py`

**Required Changes:**
- [ ] Update broadcast format for new telemetry model
- [ ] Add cluster-level broadcasts

### Phase 5: IoT Simulator Updates

#### 5.1 Simulator
**File:** `iot-simulator/simulator.py`

**Required Changes:**
- [ ] Update to generate PM2.5 data
- [ ] Update to generate humidity data
- [ ] Add geolocation to payloads
- [ ] Add cluster ID to payloads
- [ ] Add battery level simulation
- [ ] Add signal strength simulation
- [ ] Update sensor IDs to match new seed data

### Phase 6: Frontend Updates

#### 6.1 Types
**File:** `frontend/src/types/index.ts`

**Required Changes:**
- [ ] Add `Location` type
- [ ] Add `SensorCluster` type
- [ ] Add `SensorRegistry` type
- [ ] Update `Telemetry` type for new fields
- [ ] Add `SensorCapability` type

#### 6.2 API Service
**File:** `frontend/src/services/api.ts`

**Required Changes:**
- [ ] Add location API calls
- [ ] Add cluster API calls
- [ ] Add sensor registry API calls
- [ ] Update telemetry API calls

#### 6.3 Components
**Files:** Various component files

**Required Changes:**
- [ ] Update MapView for clusters
- [ ] Update ChartView for PM2.5 and humidity
- [ ] Update Leaderboard for new metrics
- [ ] Update AlertsPanel for new alert types

### Phase 7: Testing

#### 7.1 Database Tests
- [ ] Test Oracle schema creation
- [ ] Test seed data insertion
- [ ] Test triggers
- [ ] Test constraints
- [ ] Test indexes

#### 7.2 Model Tests
- [ ] Test new sensor models
- [ ] Test new telemetry model
- [ ] Test validation rules

#### 7.3 Service Tests
- [ ] Test telemetry service with new model
- [ ] Test alert service (predictive + anomaly)
- [ ] Test analytics service (AQI, new metrics)
- [ ] Test spatial queries

#### 7.4 Integration Tests
- [ ] Test end-to-end data flow
- [ ] Test MQTT → MongoDB → Oracle
- [ ] Test aggregation pipeline
- [ ] Test WebSocket broadcasts

### Phase 8: Migration

#### 8.1 Data Migration
- [ ] Create migration script for existing data
- [ ] Backup current database
- [ ] Run schema v2 creation
- [ ] Migrate telemetry data (add geolocation)
- [ ] Verify data integrity

#### 8.2 Deployment
- [ ] Update docker-compose.yml
- [ ] Update environment variables
- [ ] Update documentation
- [ ] Deploy to production

---

## 🎯 NEXT STEPS (Priority Order)

1. **Fix telemetry.py syntax error** and complete model update
2. **Create MongoDB indexes script** and update mongodb_client.py
3. **Update telemetry_service.py** to use new model
4. **Update IoT simulator** to generate new data format
5. **Test end-to-end** with new schema
6. **Update alert_service.py** with predictive/anomaly detection
7. **Update analytics_service.py** with AQI and new metrics
8. **Update API routes** for new endpoints
9. **Update frontend** types and components
10. **Write comprehensive tests**

---

## 📊 PROGRESS SUMMARY

| Phase | Status | Progress |
|-------|--------|----------|
| Database Schema | 🟢 Complete | 100% |
| Seed Data | 🟢 Complete | 100% |
| Python Models | 🟡 In Progress | 80% |
| MongoDB Setup | 🔴 Not Started | 0% |
| Service Layer | 🔴 Not Started | 0% |
| API Layer | 🔴 Not Started | 0% |
| IoT Simulator | 🔴 Not Started | 0% |
| Frontend | 🔴 Not Started | 0% |
| Testing | 🔴 Not Started | 0% |
| Migration | 🔴 Not Started | 0% |

**Overall Progress:** 28% Complete

---

## 🔧 IMMEDIATE ACTION REQUIRED

### Fix Telemetry Model
The current `backend/app/models/telemetry.py` has a syntax error that needs to be fixed before proceeding.

**Error:** Unmatched parenthesis on line 10

**Solution:** Rewrite the file with proper syntax, adding:
- Nested `TelemetryData` model
- `GeoLocation` model
- `DataQuality` model
- Enhanced `Telemetry` model
- Backward compatibility layer

---

## 📝 NOTES

- All new sensor IDs follow pattern: `sen_{district}_{ward}_{number}`
- All sensors are combo sensors (measure 5 metrics)
- Geolocation is realistic for Ho Chi Minh City
- Clusters use 300m radius for spatial grouping
- TTL is set to 30 days for MongoDB telemetry
- Schema supports both sensor-level and cluster-level alerts
- Design supports predictive and anomaly detection alerts

---

**Last Updated:** May 2, 2026  
**Next Review:** After telemetry model fix
