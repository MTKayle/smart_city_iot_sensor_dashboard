# Implementation Tasks: Database Redesign

## Overview

This task list implements the production database redesign for the Smart City IoT Dashboard. The implementation follows a 2-week sprint structure with 10 days of focused development covering database schema migration, service layer updates, API enhancements, and frontend integration.

## Tasks

- [ ] 1. Deploy Oracle Schema v2 and Load Seed Data
  - [ ] 1.1 Backup current Oracle database
    - Create backup using Oracle Data Pump
    - Verify backup file created successfully
    - Store backup with timestamp
    - _Requirements: MR1.1_
  
  - [ ] 1.2 Execute Oracle schema v2 creation script
    - Run `backend/app/db/sql/oracle_schema_v2.sql`
    - Verify all 9 tables created (LOCATIONS, SENSOR_CLUSTERS, SENSOR_REGISTRY, SENSOR_CAPABILITIES, ALERTS, TELEMETRY_SUMMARY, and 3 supporting tables)
    - Verify all triggers created and functional
    - Verify all indexes created
    - Verify all foreign key constraints active
    - _Requirements: FR1.1, FR1.2, FR1.3, FR1.4, FR1.5, DR1.1, DR1.2, DR1.3, DR1.4, DR1.5, DR1.6_
  
  - [ ] 1.3 Load seed data for 33 sensors
    - Run `backend/app/db/sql/oracle_seed_v2.sql`
    - Verify 13 locations inserted (1 city + 3 districts + 9 wards)
    - Verify 4 sensor clusters created
    - Verify 33 sensors inserted with geolocation
    - Verify 165 sensor capabilities inserted (33 sensors × 5 metrics)
    - Verify cluster sensor counts are correct
    - Test triggers by inserting/deleting test sensor
    - _Requirements: DR1.1, DR1.2, DR1.3, DR1.4_
  
  - [ ] 1.4 Verify schema integrity
    - Query all tables to confirm data loaded
    - Test foreign key constraints
    - Test check constraints
    - Verify indexes are being used in query plans
    - _Requirements: NFR3.5_


- [x] 2. Update Data Models (Pydantic)
  - [x] 2.1 Create enhanced Telemetry model
    - Create `TelemetryData` class with 5 metrics (CO2, Noise, Temperature, PM2.5, Humidity)
    - Create `GeoLocation` class for GeoJSON Point format
    - Create `DataQuality` class for battery and signal strength
    - Update `Telemetry` class with new fields: locationId, clusterId, location, quality, expireAt
    - Add field validators for all metrics
    - Add backward compatibility for existing code
    - Test model validation with valid and invalid data
    - _Requirements: FR3.1, FR3.2, FR3.3, FR3.4, DR3.1, DR3.2, DR3.3, DR3.4, DR3.5, DR3.6, DR3.7_
  
  - [x] 2.2 Create enhanced Alert model
    - Add new fields: clusterId, predictedValue, confidenceScore
    - Add new AlertType enum: THRESHOLD, PREDICTIVE, ANOMALY, CLUSTER
    - Add new AlertSeverity enum: LOW, MEDIUM, HIGH, CRITICAL
    - Update validation rules
    - Test model with all alert types
    - _Requirements: FR1.5, FR3.5, FR3.6, FR5.1, FR5.2, FR5.3_
  
  - [x] 2.3 Create Sensor models
    - Create `SensorRegistry` model matching SENSOR_REGISTRY table
    - Create `SensorCapability` model matching SENSOR_CAPABILITIES table
    - Create `SensorCluster` model matching SENSOR_CLUSTERS table
    - Create `Location` model matching LOCATIONS table
    - Add validators for latitude/longitude ranges
    - Test all models with sample data
    - _Requirements: FR1.1, FR1.2, FR1.3, FR1.4_


- [x] 3. Update MongoDB Client and Create Indexes
  - [x] 3.1 Create MongoDB indexes script
    - Create `backend/app/db/mongodb_indexes.js`
    - Add TTL index on expireAt field (30 days)
    - Add compound index on (sensorId, timestamp)
    - Add compound index on (locationId, timestamp)
    - Add compound index on (clusterId, timestamp)
    - Add geospatial index on location field (2dsphere)
    - Test index creation script
    - _Requirements: FR2.1, FR2.2, FR2.3, FR2.4, FR2.5, DR2.2, DR2.3, DR2.4_
  
  - [x] 3.2 Update MongoDB client with index creation
    - Add `create_indexes()` method to run on startup
    - Add `find_nearby_sensors()` method for geospatial queries
    - Add `get_cluster_telemetry()` method for cluster queries
    - Update connection handling with retry logic
    - Test index creation on startup
    - Test geospatial queries
    - Test cluster queries
    - _Requirements: FR2.2, FR2.3, FR2.4, FR2.5, FR7.1, FR7.3, IR3.1, IR3.2, IR3.3, IR3.4_
  
  - [x] 3.3 Add batch insert method
    - Implement `batch_insert_telemetry()` with configurable batch size
    - Add duplicate handling (skip duplicates based on sensorId + timestamp)
    - Add error handling and retry logic
    - Return BatchInsertResult with counts
    - Test with batches of 100 documents
    - Test duplicate detection
    - _Requirements: NFR1.2, NFR1.5, NFR3.3_


- [x] 4. Update Telemetry Service
  - [x] 4.1 Implement telemetry enrichment
    - Create `enrich_telemetry_with_geolocation()` function
    - Query sensor registry from Oracle for geolocation
    - Add cluster ID assignment
    - Add GeoLocation object with coordinates
    - Calculate expireAt timestamp (current time + 30 days)
    - Add DataQuality fields if present
    - Test enrichment with sample telemetry
    - _Requirements: FR4.1, FR4.2, FR4.3, FR4.4_
  
  - [x] 4.2 Update telemetry storage logic
    - Update `store_telemetry()` to use enriched model
    - Use batch insert for better performance
    - Add validation before storage
    - Add error handling and logging
    - Test with valid and invalid telemetry
    - _Requirements: FR4.4, NFR1.2, NFR3.3_
  
  - [x] 4.3 Add WebSocket broadcast
    - Broadcast enriched telemetry via WebSocket
    - Format message with type field
    - Handle broadcast failures gracefully
    - Test WebSocket delivery
    - _Requirements: FR4.5, IR2.1, NFR1.3_


- [x] 5. Update Oracle Client
  - [x] 5.1 Add sensor registry methods
    - Implement `get_sensor(sensor_id)` method
    - Implement `get_sensors_by_location(location_id)` method
    - Implement `get_sensors_by_cluster(cluster_id)` method
    - Implement `get_sensor_capabilities(sensor_id)` method
    - Add connection pooling
    - Add error handling and retry logic
    - Test all CRUD operations
    - _Requirements: FR1.2, FR1.3, IR3.1, IR3.2, IR3.3, IR3.4_
  
  - [x] 5.2 Add location hierarchy methods
    - Implement `get_location_hierarchy(location_id)` method
    - Implement `get_location(location_id)` method
    - Implement `get_all_locations()` method
    - Test recursive hierarchy queries
    - _Requirements: FR1.1, FR8.1_
  
  - [x] 5.3 Add cluster methods
    - Implement `get_cluster(cluster_id)` method
    - Implement `get_all_clusters()` method
    - Implement `update_cluster_sensor_count()` method
    - Test cluster queries
    - _Requirements: FR1.4, FR8.2_


- [ ] 6. Implement Alert Service Enhancements
  - [ ] 6.1 Update threshold alert checking
    - Update `check_threshold_alerts()` for PM2.5 and humidity
    - Add configurable thresholds
    - Add severity calculation based on exceedance percentage
    - Test with threshold-exceeding values
    - _Requirements: FR5.1, FR10.1, FR10.2_
  
  - [ ] 6.2 Implement alert deduplication
    - Add deduplication logic (5-minute window)
    - Query recent alerts before creating new one
    - Skip duplicate alerts
    - Test deduplication with multiple violations
    - _Requirements: FR5.4_
  
  - [ ] 6.3 Implement predictive alerts
    - Create `check_predictive_alerts()` function
    - Query last 20 telemetry readings
    - Implement linear regression using scikit-learn
    - Predict value 1 hour ahead
    - Calculate confidence score (R²)
    - Generate alert if predicted value exceeds threshold and confidence > 0.7
    - Add scikit-learn and numpy to requirements.txt
    - Test with trending data
    - _Requirements: FR5.2, FR3.5_
  
  - [ ] 6.4 Implement anomaly detection
    - Create `detect_anomalies()` function
    - Query last 100 telemetry readings (24 hours)
    - Calculate mean and standard deviation
    - Calculate Z-score for current value
    - Generate alert if |Z-score| > 3
    - Calculate confidence score from Z-score
    - Test with anomalous values
    - _Requirements: FR5.3, FR3.5_
  
  - [ ] 6.5 Add alert lifecycle management
    - Implement alert acknowledgment
    - Implement alert resolution
    - Update alert status in Oracle
    - Test lifecycle transitions
    - _Requirements: FR5.5_


- [ ] 7. Implement Analytics Service
  - [ ] 7.1 Create AQI calculation utility
    - Create `backend/app/utils/aqi.py`
    - Implement `calculate_aqi(pm25)` using EPA breakpoints
    - Add all 6 AQI ranges (Good to Hazardous)
    - Test with known PM2.5 values
    - Verify AQI calculations match EPA standards
    - _Requirements: FR6.1_
  
  - [ ] 7.2 Update analytics service for new metrics
    - Add PM2.5 aggregation to `calculate_moving_average()`
    - Add humidity aggregation
    - Update Clean Score calculation to include PM2.5
    - Add AQI calculation to analytics
    - Test with sample telemetry data
    - _Requirements: FR6.3, FR6.1_
  
  - [ ] 7.3 Add cluster-level analytics
    - Implement `calculate_cluster_analytics()` function
    - Aggregate telemetry for all sensors in cluster
    - Calculate cluster-wide averages
    - Calculate cluster AQI
    - Test with cluster data
    - _Requirements: FR6.5_


- [ ] 8. Update Scheduler Service
  - [ ] 8.1 Update hourly aggregation
    - Update aggregation pipeline to include PM2.5 and humidity
    - Add AQI calculation to aggregation
    - Update TELEMETRY_SUMMARY inserts with new fields
    - Test aggregation with sample data
    - _Requirements: FR6.2, FR6.4_
  
  - [ ] 8.2 Add cluster aggregation job
    - Create cluster-level aggregation task
    - Schedule to run hourly
    - Insert cluster summaries to TELEMETRY_SUMMARY
    - Test cluster aggregation
    - _Requirements: FR6.5_
  
  - [ ] 8.3 Verify aggregation performance
    - Ensure aggregation completes within 5 minutes
    - Add logging for aggregation duration
    - Optimize queries if needed
    - _Requirements: NFR1.4_


- [ ] 9. Create Spatial Query Utilities
  - [ ] 9.1 Implement Haversine distance calculation
    - Create `backend/app/utils/spatial.py`
    - Implement `haversine_distance()` function
    - Test with known coordinates
    - Verify distance calculations are accurate
    - _Requirements: FR7.1, FR7.4_
  
  - [ ] 9.2 Implement nearby sensor finder
    - Implement `find_nearby_sensors()` function
    - Use MongoDB geospatial query
    - Fetch sensor details from Oracle
    - Test with various radius values
    - _Requirements: FR7.1, FR7.3_
  
  - [ ] 9.3 Implement hotspot detection
    - Implement `identify_hotspots()` function
    - Find areas with high pollution levels
    - Support filtering by metric type
    - Test hotspot detection
    - _Requirements: FR7.2_


- [ ] 10. Add New API Endpoints
  - [ ] 10.1 Add location endpoints
    - Add GET `/locations` endpoint
    - Add GET `/locations/{location_id}` endpoint
    - Add GET `/locations/{location_id}/hierarchy` endpoint
    - Add GET `/locations/{location_id}/sensors` endpoint
    - Test all endpoints with sample data
    - _Requirements: FR8.1_
  
  - [ ] 10.2 Add cluster endpoints
    - Add GET `/clusters` endpoint
    - Add GET `/clusters/{cluster_id}` endpoint
    - Add GET `/clusters/{cluster_id}/sensors` endpoint
    - Add GET `/clusters/{cluster_id}/telemetry` endpoint
    - Add GET `/clusters/hotspots` endpoint
    - Test all endpoints
    - _Requirements: FR8.2_
  
  - [ ] 10.3 Add sensor registry endpoints
    - Add GET `/sensors` endpoint
    - Add GET `/sensors/{sensor_id}` endpoint
    - Add GET `/sensors/{sensor_id}/capabilities` endpoint
    - Add GET `/sensors/{sensor_id}/health` endpoint
    - Add GET `/sensors/nearby` endpoint with lat, lng, radius params
    - Test all endpoints
    - _Requirements: FR8.3, FR8.4, FR8.5, FR8.6_
  
  - [ ] 10.4 Update telemetry endpoints
    - Update GET `/telemetry/{sensor_id}` to return new fields
    - Add cluster filtering support
    - Add geospatial filtering support
    - Maintain backward compatibility
    - Test updated endpoints
    - _Requirements: FR3.1, FR3.2, FR3.3, FR3.4_


- [ ] 11. Update IoT Simulator
  - [ ] 11.1 Update simulator for new schema
    - Update sensor IDs to match seed data (all 33 sensors)
    - Add PM2.5 generation (20-60 µg/m³)
    - Add humidity generation (60-85%)
    - Add battery level simulation (70-100%)
    - Add signal strength simulation (-60 to -30 dBm)
    - Update telemetry message format
    - Test simulator with all sensors
    - _Requirements: FR10.1, FR10.2, FR10.3, FR10.4, FR10.5_
  
  - [ ] 11.2 Test end-to-end data flow
    - Start all services (MQTT, MongoDB, Oracle, Backend)
    - Start simulator
    - Verify telemetry reaches MongoDB with enrichment
    - Verify alerts are generated
    - Verify WebSocket broadcasts work
    - Check for errors in logs
    - _Requirements: NFR1.1, NFR1.2, NFR1.3, NFR3.1_


- [ ] 12. Update Frontend Components
  - [ ] 12.1 Update TypeScript types
    - Update `frontend/src/types/index.ts`
    - Add `Location` type
    - Add `SensorCluster` type
    - Add `SensorRegistry` type
    - Add `SensorCapability` type
    - Update `Telemetry` type with new fields
    - Update `Alert` type with new fields
    - Verify no TypeScript errors
    - _Requirements: FR3.1, FR3.2, FR3.3, FR3.4, FR3.5, FR3.6_
  
  - [ ] 12.2 Update API service
    - Update `frontend/src/services/api.ts`
    - Add location API calls
    - Add cluster API calls
    - Add sensor registry API calls
    - Update telemetry API calls
    - Test all API calls
    - _Requirements: FR8.1, FR8.2, FR8.3, FR8.4, FR8.5, FR8.6_
  
  - [ ] 12.3 Update MapView component
    - Add cluster visualization
    - Update marker rendering for clusters
    - Add cluster popup information
    - Test cluster display on map
    - _Requirements: FR9.1_
  
  - [ ] 12.4 Update ChartView component
    - Add PM2.5 chart
    - Add humidity chart
    - Update chart configuration for 5 metrics
    - Test chart rendering with new data
    - _Requirements: FR9.2_
  
  - [ ] 12.5 Update Leaderboard component
    - Add PM2.5 column
    - Add humidity column
    - Add AQI column
    - Update sorting logic
    - Test leaderboard with new metrics
    - _Requirements: FR9.3_
  
  - [ ] 12.6 Update AlertsPanel component
    - Add support for PREDICTIVE alert type
    - Add support for ANOMALY alert type
    - Add support for CLUSTER alert type
    - Display confidence score for predictive/anomaly alerts
    - Update alert styling for new types
    - Test alert display
    - _Requirements: FR9.4_


- [ ] 13. Write Unit Tests
  - [ ] 13.1 Test data models
    - Test TelemetryData validation
    - Test GeoLocation validation
    - Test DataQuality validation
    - Test Telemetry model with all fields
    - Test Alert model with all types
    - Test Sensor models
    - Achieve > 80% coverage for models
    - _Requirements: NFR7.1_
  
  - [ ] 13.2 Test MongoDB client
    - Test index creation
    - Test batch insert
    - Test geospatial queries
    - Test cluster queries
    - Mock MongoDB connection
    - _Requirements: NFR7.1_
  
  - [ ] 13.3 Test Oracle client
    - Test sensor registry methods
    - Test location hierarchy methods
    - Test cluster methods
    - Mock Oracle connection
    - _Requirements: NFR7.1_
  
  - [ ] 13.4 Test telemetry service
    - Test enrichment logic
    - Test storage logic
    - Test WebSocket broadcast
    - Mock dependencies
    - _Requirements: NFR7.1_
  
  - [ ] 13.5 Test alert service
    - Test threshold checking
    - Test deduplication
    - Test predictive alerts
    - Test anomaly detection
    - Mock dependencies
    - _Requirements: NFR7.1_
  
  - [ ] 13.6 Test analytics service
    - Test AQI calculation
    - Test moving averages
    - Test Clean Score calculation
    - Test cluster analytics
    - _Requirements: NFR7.1_
  
  - [ ] 13.7 Test spatial utilities
    - Test Haversine distance
    - Test nearby sensor finder
    - Test hotspot detection
    - _Requirements: NFR7.1_


- [ ] 14. Write Integration Tests
  - [ ] 14.1 Test Oracle schema
    - Test table creation
    - Test foreign key constraints
    - Test triggers
    - Test indexes
    - _Requirements: NFR7.2_
  
  - [ ] 14.2 Test MongoDB indexes
    - Test TTL index functionality
    - Test geospatial index queries
    - Test compound index performance
    - _Requirements: NFR7.2_
  
  - [ ] 14.3 Test telemetry flow
    - Test MQTT → Consumer → Enrichment → MongoDB
    - Test WebSocket broadcast
    - Test alert generation
    - Verify data integrity
    - _Requirements: NFR7.2, NFR7.3_
  
  - [ ] 14.4 Test analytics pipeline
    - Test hourly aggregation
    - Test cluster aggregation
    - Test TELEMETRY_SUMMARY inserts
    - Verify calculations
    - _Requirements: NFR7.2_
  
  - [ ] 14.5 Test API endpoints
    - Test all location endpoints
    - Test all cluster endpoints
    - Test all sensor endpoints
    - Test error handling
    - Test response formats
    - _Requirements: NFR7.2_


- [ ] 15. Performance Testing and Optimization
  - [ ] 15.1 Benchmark query performance
    - Test query response times
    - Ensure < 100ms for 95th percentile
    - Identify slow queries
    - Optimize indexes if needed
    - _Requirements: NFR1.1_
  
  - [ ] 15.2 Load test telemetry ingestion
    - Test with 500+ inserts/second
    - Monitor MongoDB performance
    - Monitor CPU and memory usage
    - Verify no data loss
    - _Requirements: NFR1.2, NFR3.2_
  
  - [ ] 15.3 Test WebSocket performance
    - Measure broadcast latency
    - Ensure < 50ms latency
    - Test with multiple clients
    - _Requirements: NFR1.3_
  
  - [ ] 15.4 Test aggregation performance
    - Measure hourly aggregation duration
    - Ensure completes within 5 minutes
    - Optimize if needed
    - _Requirements: NFR1.4_


- [ ] 16. Documentation and Deployment
  - [ ] 16.1 Update API documentation
    - Document all new endpoints
    - Add request/response examples
    - Update OpenAPI spec
    - _Requirements: NFR6.2_
  
  - [ ] 16.2 Update README
    - Document new features
    - Update setup instructions
    - Add migration guide
    - Document new environment variables
    - _Requirements: NFR6.3_
  
  - [ ] 16.3 Create deployment scripts
    - Update docker-compose.yml
    - Create database migration script
    - Create rollback script
    - Test deployment on staging
    - _Requirements: NFR8.1, NFR8.2, NFR8.3, NFR8.4_
  
  - [ ] 16.4 Add health check endpoints
    - Add `/health` endpoint
    - Add `/health/mongodb` endpoint
    - Add `/health/oracle` endpoint
    - Test health checks
    - _Requirements: NFR8.5_
  
  - [ ] 16.5 Deploy to production
    - Backup production database
    - Run migration scripts
    - Deploy new code
    - Verify all services running
    - Monitor for errors
    - _Requirements: NFR3.1, NFR3.2, MR1.1, MR1.2, MR1.3, MR1.4_


- [x] 17. Worker Pool Data Flow Redesign
  - [x] 17.1 Create TelemetryPipeline (worker pool)
    - Create `backend/app/messaging/worker_pool.py`
    - Implement AsyncQueue (maxsize 10000, backpressure)
    - Implement configurable worker pool (default 3 workers)
    - Implement batch collection (100 messages OR 1 second timeout)
    - Add telemetry enrichment via Oracle in thread-pool executor
    - Add message-level deduplication (sensorId + timestamp)
    - _Requirements: NFR1.2, NFR3.3_
  
  - [x] 17.2 Implement parallel processing fan-out
    - Branch A: MongoDB batch insert (in executor)
    - Branch B: Alert engine — threshold, predictive, anomaly (in executor)
    - Branch C: WebSocket broadcast (direct from enriched data, no MongoDB round-trip)
    - All 3 branches run via `asyncio.gather()` in parallel
    - _Requirements: FR4.4, FR4.5, FR5.1–FR5.3, NFR1.3_
  
  - [x] 17.3 Update MQTT consumer for pipeline mode
    - Add `telemetry_pipeline` parameter to MQTTConsumer
    - Route messages to pipeline.enqueue() instead of direct handler
    - Keep backward-compatible legacy handler mode
    - Subscribe with QoS 1
    - Add message metrics (count, errors)
    - _Requirements: NFR1.2_
  
  - [x] 17.4 Update application entry point
    - Wire TelemetryPipeline in FastAPI lifespan
    - Start worker pool on startup, stop on shutdown
    - Connect MQTT consumer to pipeline
    - Add `/pipeline/metrics` observability endpoint
    - _Requirements: NFR1.1, NFR1.2, NFR1.3_

---

**Task List Version:** 1.1  
**Total Tasks:** 17 main tasks, 85+ sub-tasks  
**Estimated Duration:** 10 working days (2 weeks)  
**Last Updated:** May 3, 2026
