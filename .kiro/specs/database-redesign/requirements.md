# Requirements Document: Database Redesign

## Functional Requirements

### FR1: Oracle Schema v2 Deployment
- **FR1.1**: System shall support hierarchical location structure (City → District → Ward)
- **FR1.2**: System shall store 33 sensors with geolocation coordinates
- **FR1.3**: System shall track 5 sensor capabilities per sensor (CO2, Noise, Temperature, PM2.5, Humidity)
- **FR1.4**: System shall organize sensors into 4 spatial clusters
- **FR1.5**: System shall support enhanced alert types (THRESHOLD, PREDICTIVE, ANOMALY, CLUSTER)

### FR2: MongoDB Enhancements
- **FR2.1**: System shall automatically delete telemetry data after 30 days using TTL index
- **FR2.2**: System shall support geospatial queries using 2dsphere index
- **FR2.3**: System shall support efficient sensor-based queries with compound indexes
- **FR2.4**: System shall support efficient location-based queries with compound indexes
- **FR2.5**: System shall support efficient cluster-based queries with compound indexes

### FR3: Data Models
- **FR3.1**: Telemetry model shall include geolocation (GeoJSON Point format)
- **FR3.2**: Telemetry model shall include data quality metrics (battery level, signal strength)
- **FR3.3**: Telemetry model shall include cluster assignment
- **FR3.4**: Telemetry model shall include TTL expiration timestamp
- **FR3.5**: Alert model shall support predictive value and confidence score fields
- **FR3.6**: Alert model shall support multiple alert types and severities

### FR4: Telemetry Processing
- **FR4.1**: System shall enrich telemetry with geolocation from sensor registry
- **FR4.2**: System shall assign cluster ID to telemetry based on sensor location
- **FR4.3**: System shall calculate TTL expiration (30 days from timestamp)
- **FR4.4**: System shall validate telemetry data ranges before storage
- **FR4.5**: System shall broadcast telemetry updates via WebSocket

### FR5: Alert System
- **FR5.1**: System shall generate threshold alerts when metrics exceed configured limits
- **FR5.2**: System shall generate predictive alerts using linear regression
- **FR5.3**: System shall generate anomaly alerts using Z-score analysis
- **FR5.4**: System shall deduplicate alerts within 5-minute windows
- **FR5.5**: System shall support alert acknowledgment and resolution

### FR6: Analytics & AQI
- **FR6.1**: System shall calculate Air Quality Index (AQI) from PM2.5 using EPA formula
- **FR6.2**: System shall aggregate telemetry data hourly
- **FR6.3**: System shall calculate Clean Score from multiple metrics
- **FR6.4**: System shall store aggregated data in TELEMETRY_SUMMARY table
- **FR6.5**: System shall support cluster-level analytics

### FR7: Spatial Queries
- **FR7.1**: System shall find sensors within specified radius using Haversine distance
- **FR7.2**: System shall identify pollution hotspots by metric type
- **FR7.3**: System shall support geospatial queries on telemetry data
- **FR7.4**: System shall calculate distances between sensors and points of interest

### FR8: API Endpoints
- **FR8.1**: System shall provide location hierarchy endpoints
- **FR8.2**: System shall provide cluster management endpoints
- **FR8.3**: System shall provide sensor registry endpoints
- **FR8.4**: System shall provide sensor capability endpoints
- **FR8.5**: System shall provide sensor health status endpoints
- **FR8.6**: System shall provide nearby sensor search endpoint

### FR9: Frontend Updates
- **FR9.1**: MapView shall display sensor clusters
- **FR9.2**: ChartView shall display PM2.5 and humidity charts
- **FR9.3**: Leaderboard shall display new metrics (PM2.5, humidity, AQI)
- **FR9.4**: AlertsPanel shall display new alert types (predictive, anomaly, cluster)

### FR10: IoT Simulator
- **FR10.1**: Simulator shall generate PM2.5 data (20-60 µg/m³)
- **FR10.2**: Simulator shall generate humidity data (60-85%)
- **FR10.3**: Simulator shall generate battery level data (70-100%)
- **FR10.4**: Simulator shall generate signal strength data (-60 to -30 dBm)
- **FR10.5**: Simulator shall support all 33 sensor IDs from seed data

## Non-Functional Requirements

### NFR1: Performance
- **NFR1.1**: Query response time shall be < 100ms (95th percentile)
- **NFR1.2**: Telemetry ingestion rate shall support 500+ inserts/second
- **NFR1.3**: WebSocket broadcast latency shall be < 50ms
- **NFR1.4**: Hourly aggregation shall complete within 5 minutes
- **NFR1.5**: Batch processing shall handle 100 messages per batch

### NFR2: Scalability
- **NFR2.1**: System shall support 33 sensors initially
- **NFR2.2**: System shall support expansion to 100+ sensors
- **NFR2.3**: MongoDB shall handle 30 days of telemetry data
- **NFR2.4**: System shall support 4 clusters initially with expansion capability

### NFR3: Reliability
- **NFR3.1**: System shall achieve 99.9% uptime
- **NFR3.2**: System shall have zero data loss during migration
- **NFR3.3**: System shall retry failed operations with exponential backoff
- **NFR3.4**: System shall use dead letter queue for permanent failures
- **NFR3.5**: System shall maintain data integrity across databases

### NFR4: Data Retention
- **NFR4.1**: MongoDB shall retain telemetry data for 30 days
- **NFR4.2**: Oracle shall retain aggregated data indefinitely
- **NFR4.3**: Oracle shall retain alert history indefinitely
- **NFR4.4**: System shall automatically purge expired telemetry data

### NFR5: Security
- **NFR5.1**: System shall validate all input data
- **NFR5.2**: System shall use parameterized queries to prevent SQL injection
- **NFR5.3**: System shall validate MongoDB queries to prevent injection
- **NFR5.4**: System shall manage secrets via environment variables
- **NFR5.5**: System shall implement rate limiting on API endpoints

### NFR6: Maintainability
- **NFR6.1**: Code shall follow PEP 8 style guidelines
- **NFR6.2**: All functions shall have docstrings
- **NFR6.3**: Database schema shall be version controlled
- **NFR6.4**: System shall have comprehensive logging
- **NFR6.5**: System shall have monitoring and alerting

### NFR7: Testing
- **NFR7.1**: Unit test coverage shall be > 80%
- **NFR7.2**: Integration tests shall cover all critical paths
- **NFR7.3**: System shall have end-to-end tests
- **NFR7.4**: System shall have performance benchmarks
- **NFR7.5**: System shall have load testing scenarios

### NFR8: Deployment
- **NFR8.1**: System shall use Docker containers
- **NFR8.2**: System shall use Docker Compose for orchestration
- **NFR8.3**: System shall have automated database migration scripts
- **NFR8.4**: System shall have rollback procedures
- **NFR8.5**: System shall have health check endpoints

## Data Requirements

### DR1: Oracle Tables
- **DR1.1**: LOCATIONS table shall store 13 locations (1 city + 3 districts + 9 wards)
- **DR1.2**: SENSOR_CLUSTERS table shall store 4 clusters
- **DR1.3**: SENSOR_REGISTRY table shall store 33 sensors
- **DR1.4**: SENSOR_CAPABILITIES table shall store 165 capabilities (33 × 5)
- **DR1.5**: ALERTS table shall support unlimited alert records
- **DR1.6**: TELEMETRY_SUMMARY table shall store hourly aggregations

### DR2: MongoDB Collections
- **DR2.1**: telemetry collection shall store raw sensor data
- **DR2.2**: telemetry collection shall have TTL index on expireAt field
- **DR2.3**: telemetry collection shall have geospatial index on location field
- **DR2.4**: telemetry collection shall have compound indexes for queries

### DR3: Data Validation
- **DR3.1**: CO2 values shall be between 0-5000 ppm
- **DR3.2**: Noise values shall be between 0-120 dB
- **DR3.3**: Temperature values shall be between -50 to 60°C
- **DR3.4**: PM2.5 values shall be between 0-500 µg/m³
- **DR3.5**: Humidity values shall be between 0-100%
- **DR3.6**: Battery level shall be between 0-100%
- **DR3.7**: Signal strength shall be between -120 to 0 dBm

## Integration Requirements

### IR1: MQTT Integration
- **IR1.1**: System shall consume messages from MQTT broker
- **IR1.2**: System shall use QoS level 1 for message delivery
- **IR1.3**: System shall handle MQTT reconnection automatically
- **IR1.4**: System shall validate MQTT message format

### IR2: WebSocket Integration
- **IR2.1**: System shall broadcast telemetry updates in real-time
- **IR2.2**: System shall broadcast alert notifications in real-time
- **IR2.3**: System shall manage WebSocket connections
- **IR2.4**: System shall handle WebSocket disconnections gracefully

### IR3: Database Integration
- **IR3.1**: System shall maintain connections to both Oracle and MongoDB
- **IR3.2**: System shall handle database connection failures
- **IR3.3**: System shall use connection pooling
- **IR3.4**: System shall implement retry logic for database operations

## Migration Requirements

### MR1: Schema Migration
- **MR1.1**: System shall backup existing Oracle database before migration
- **MR1.2**: System shall execute new schema creation scripts
- **MR1.3**: System shall verify all tables and indexes are created
- **MR1.4**: System shall load seed data for 33 sensors

### MR2: Data Migration
- **MR2.1**: System shall migrate existing telemetry data if applicable
- **MR2.2**: System shall verify data integrity after migration
- **MR2.3**: System shall maintain backward compatibility during migration
- **MR2.4**: System shall have rollback plan for failed migrations

### MR3: Service Updates
- **MR3.1**: System shall update all service layer code
- **MR3.2**: System shall update all API endpoints
- **MR3.3**: System shall update frontend components
- **MR3.4**: System shall update IoT simulator

---

**Requirements Version:** 1.0  
**Derived From:** Design Document v1.0  
**Last Updated:** May 2, 2026  
**Status:** Ready for Implementation
