# Implementation Plan: Smart City IoT Sensor Dashboard

## Overview

This implementation plan breaks down the Smart City IoT Sensor Dashboard into incremental coding tasks. The system uses Python FastAPI for the backend, React TypeScript for the frontend, MongoDB for time-series telemetry data, Oracle SQL for relational data, and MQTT for IoT messaging. Each task builds on previous work, with property-based tests integrated throughout to validate correctness properties from the design document.

## Tasks

- [x] 1. Set up project structure and Docker environment
  - Create root directory structure: `/backend`, `/frontend`, `/iot-simulator`, `/docker`
  - Create `docker-compose.yml` with services: mosquitto, mongodb, oracle-xe, backend, frontend, iot-simulator
  - Configure Docker networks and volumes for data persistence
  - Create `.env` file template with environment variables for database connections and MQTT broker
  - Write README.md with setup and run instructions
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_


- [ ] 2. Initialize Oracle database schema and seed data
  - [x] 2.1 Create SQL schema initialization script
    - Write `backend/db/oracle_schema.sql` with CREATE TABLE statements for LOCATIONS, SENSOR_REGISTRY, ALERTS, TELEMETRY_SUMMARY
    - Add indexes on LocationID, ParentID, SensorID, CreatedAt columns
    - Add foreign key constraints for referential integrity
    - Create recursive CTE view LOCATION_HIERARCHY for hierarchy queries
    - _Requirements: 16.1, 16.2, 16.3, 1.1, 2.1, 6.3, 8.3_

  - [x] 2.2 Create SQL seed data script
    - Write `backend/db/oracle_seed.sql` with INSERT statements for sample location hierarchy (1 City, 3 Districts, 9 Wards)
    - Insert sample sensor registrations (27 sensors across wards)
    - _Requirements: 16.5_

  - [ ]* 2.3 Write property test for Location ParentID referential integrity
    - **Property 1: Location ParentID Referential Integrity**
    - **Validates: Requirements 1.2**
    - Test that location creation with non-existent ParentID is rejected
    - Use Hypothesis to generate random location data with invalid ParentIDs

  - [ ]* 2.4 Write property test for Hierarchy Type Constraints
    - **Property 4: Hierarchy Type Constraints**
    - **Validates: Requirements 1.5**
    - Test that City can only have District children, District can only have Ward children, Ward has no location children
    - Use Hypothesis to generate random hierarchy violations


- [ ] 3. Implement backend core data models and database clients
  - [x] 3.1 Create Pydantic data models
    - Write `backend/models.py` with Telemetry, Location, Sensor, Alert, Analytics, LeaderboardEntry classes
    - Add field validation (co2 >= 0, noise 0-120, temperature -50-60)
    - Add JSON schema examples for API documentation
    - _Requirements: 5.1, 5.3, 5.5_

  - [x] 3.2 Implement MongoDB client module
    - Write `backend/db/mongodb_client.py` with connection pooling
    - Implement insert_telemetry() and query_telemetry() functions
    - Create TTL index on timestamp field (30 days expiration)
    - Create compound index on (sensorId, timestamp)
    - Add error handling with exponential backoff retry
    - _Requirements: 4.1, 4.2, 4.3, 4.5_

  - [x] 3.3 Implement Oracle client module
    - Write `backend/db/oracle_client.py` with connection pooling using cx_Oracle
    - Implement functions: insert_location(), get_location_hierarchy(), insert_sensor(), get_sensors(), insert_alert(), get_alerts()
    - Add schema initialization logic to run SQL scripts on startup
    - Add error handling with exponential backoff retry
    - _Requirements: 1.1, 2.1, 6.3, 16.4_

  - [ ]* 3.4 Write property test for Telemetry round-trip serialization
    - **Property 9: Telemetry Round-Trip Serialization**
    - **Validates: Requirements 5.4, 5.1, 5.3, 3.5**
    - Test that Telemetry object → JSON → Telemetry produces equivalent object
    - Use Hypothesis to generate random valid Telemetry objects

  - [ ]* 3.5 Write property test for Telemetry value range validation
    - **Property 11: Telemetry Value Range Validation**
    - **Validates: Requirements 5.5**
    - Test that invalid values (negative co2, noise > 120, temperature < -50 or > 60) are rejected
    - Use Hypothesis to generate out-of-range values

  - [ ]* 3.6 Write unit tests for MongoDB client
    - Test insert_telemetry() with valid data
    - Test query_telemetry() with time range filters
    - Test connection error handling
    - Mock MongoDB connection

  - [ ]* 3.7 Write unit tests for Oracle client
    - Test insert_location() with valid hierarchy
    - Test get_location_hierarchy() recursive query
    - Test insert_sensor() with location validation
    - Mock Oracle connection


- [ ] 4. Implement IoT simulator
  - [x] 4.1 Create IoT simulator script
    - Write `iot-simulator/simulator.py` using paho-mqtt library
    - Generate random sensor data: CO2 (300-2000 ppm), Noise (30-100 dB), Temperature (15-35°C)
    - Publish to MQTT topic `sensors/{sensorId}/telemetry` every 5 seconds
    - Read sensor list and MQTT broker address from environment variables
    - Add connection retry logic with exponential backoff
    - _Requirements: 3.1, 3.2, 3.5_

  - [x] 4.2 Create Dockerfile for IoT simulator
    - Write `iot-simulator/Dockerfile` with Python base image
    - Install paho-mqtt dependency
    - Set entrypoint to run simulator.py
    - _Requirements: 15.1, 15.2_

  - [ ]* 4.3 Write unit tests for IoT simulator
    - Test telemetry message format and JSON structure
    - Test value ranges for CO2, Noise, Temperature
    - Mock MQTT client to avoid external dependencies


- [ ] 5. Implement MQTT consumer and telemetry processing
  - [x] 5.1 Create MQTT consumer module
    - Write `backend/mqtt_consumer.py` using paho-mqtt library
    - Subscribe to `sensors/+/telemetry` topic pattern
    - Parse incoming JSON messages into Telemetry objects
    - Validate data using Pydantic models
    - Call telemetry processing handler on valid messages
    - Log validation errors for invalid messages without crashing
    - Add reconnection logic with exponential backoff
    - _Requirements: 3.4, 3.5, 5.1, 5.2_

  - [x] 5.2 Implement telemetry processing handler
    - Write `backend/telemetry_handler.py` with process_telemetry() function
    - Insert telemetry data into MongoDB
    - Check alert thresholds (CO2 > 1000, Noise > 85)
    - Call alert creation if thresholds exceeded
    - Broadcast telemetry to WebSocket clients
    - _Requirements: 4.1, 6.1, 6.2, 10.3_

  - [ ]* 5.3 Write property test for invalid telemetry rejection
    - **Property 10: Invalid Telemetry Rejection**
    - **Validates: Requirements 5.2**
    - Test that malformed JSON, missing fields, invalid types are rejected gracefully
    - Use Hypothesis to generate invalid telemetry messages

  - [ ]* 5.4 Write property test for telemetry storage and retrieval
    - **Property 12: Telemetry Storage and Retrieval**
    - **Validates: Requirements 4.1**
    - Test that inserted telemetry can be queried back with same values
    - Use Hypothesis to generate random valid telemetry data

  - [ ]* 5.5 Write unit tests for MQTT consumer
    - Test message parsing with valid payloads
    - Test handling of malformed JSON
    - Test subscription to correct topic pattern
    - Mock MQTT client

  - [ ]* 5.6 Write unit tests for telemetry handler
    - Test MongoDB insertion
    - Test threshold detection logic
    - Test WebSocket broadcast
    - Mock database and WebSocket clients


- [ ] 6. Implement alert engine with deduplication
  - [x] 6.1 Create alert engine module
    - Write `backend/alert_engine.py` with create_alert() function
    - Check if alert already exists for sensor within 5-minute window
    - If no duplicate, insert alert into Oracle ALERTS table
    - Determine alert level based on threshold (HIGH for CO2 > 1000, Noise > 85)
    - Generate unique AlertID using UUID
    - Broadcast alert to WebSocket clients
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 6.2 Write property test for threshold-based alert generation
    - **Property 13: Threshold-Based Alert Generation**
    - **Validates: Requirements 6.1, 6.2**
    - Test that telemetry with CO2 > 1000 or Noise > 85 creates HIGH alert
    - Use Hypothesis to generate threshold-exceeding values

  - [ ]* 6.3 Write property test for alert deduplication
    - **Property 14: Alert Deduplication**
    - **Validates: Requirements 6.5**
    - Test that multiple threshold violations within 5 minutes create only one alert
    - Use Hypothesis to generate multiple telemetry readings in time windows

  - [ ]* 6.4 Write unit tests for alert engine
    - Test alert creation with threshold-exceeding values
    - Test deduplication logic with timestamps
    - Test alert level assignment
    - Mock Oracle database


- [ ] 7. Implement analytics module with moving averages and Clean Score
  - [x] 7.1 Create analytics module
    - Write `backend/analytics.py` with calculate_moving_average() function
    - Query last 10 telemetry readings from MongoDB for given sensor
    - Calculate arithmetic mean for CO2, Noise, Temperature
    - Handle case where fewer than 10 readings exist
    - Return Analytics object with MovingAverage data
    - _Requirements: 7.1, 7.3_

  - [x] 7.2 Implement Clean Score calculation
    - Write calculate_clean_score() function in `backend/analytics.py`
    - Normalize CO2 using range 0-2000 ppm: normalized_CO2 = (avgCO2 / 2000) * 100
    - Normalize Noise using range 0-100 dB: normalized_Noise = (avgNoise / 100) * 100
    - Calculate Clean Score: 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)
    - Store daily summaries in Oracle TELEMETRY_SUMMARY table
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 7.3 Implement scheduled analytics task
    - Write background task to calculate Clean Score for all locations daily at midnight
    - Use APScheduler or similar library for scheduling
    - Aggregate telemetry data by location from MongoDB
    - Insert/update TELEMETRY_SUMMARY records in Oracle
    - _Requirements: 8.5_

  - [ ]* 7.4 Write property test for moving average calculation
    - **Property 15: Moving Average Calculation**
    - **Validates: Requirements 7.1, 7.3**
    - Test that moving average equals arithmetic mean of last N readings (N = min(10, total))
    - Use Hypothesis to generate random telemetry sequences

  - [ ]* 7.5 Write property test for Clean Score calculation
    - **Property 16: Clean Score Calculation**
    - **Validates: Requirements 8.1, 8.2**
    - Test Clean Score formula with known input values
    - Use Hypothesis to generate random CO2 and Noise averages

  - [ ]* 7.6 Write unit tests for analytics module
    - Test moving average with exactly 10 readings
    - Test moving average with fewer than 10 readings
    - Test Clean Score with edge cases (0 values, max values)
    - Mock MongoDB and Oracle clients


- [x] 8. Implement REST API endpoints
  - [x] 8.1 Create FastAPI application and router
    - Write `backend/main.py` with FastAPI app initialization
    - Configure CORS middleware for cross-origin requests
    - Create `backend/api/routes.py` with APIRouter
    - Add health check endpoint GET `/health`
    - _Requirements: 9.6_

  - [x] 8.2 Implement location endpoints
    - Add GET `/api/locations` endpoint to retrieve complete location hierarchy
    - Query Oracle LOCATION_HIERARCHY view
    - Return List[Location] with parent-child relationships
    - _Requirements: 9.1, 1.3_

  - [x] 8.3 Implement sensor endpoints
    - Add GET `/api/sensors` endpoint to retrieve all sensors with location info
    - Join SENSOR_REGISTRY with LOCATIONS table
    - Return List[Sensor] with location hierarchy
    - _Requirements: 9.2, 2.4_

  - [x] 8.4 Implement telemetry endpoints
    - Add GET `/api/telemetry/{sensorId}` endpoint with optional query params start_time, end_time
    - Query MongoDB telemetry collection with time range filter
    - Default to last 24 hours if no time range specified
    - Validate start_time < end_time, return 400 if invalid
    - Return List[Telemetry] ordered by timestamp descending
    - _Requirements: 9.3_

  - [x] 8.5 Implement analytics endpoints
    - Add GET `/api/sensors/{sensorId}/analytics` endpoint
    - Call calculate_moving_average() from analytics module
    - Return Analytics object with moving averages
    - _Requirements: 7.4_

  - [x] 8.6 Implement alert endpoints
    - Add GET `/api/alerts` endpoint with optional query params level, location_id
    - Query Oracle ALERTS table with filters
    - Return List[Alert] ordered by CreatedAt descending, limit 100
    - _Requirements: 9.4_

  - [x] 8.7 Implement leaderboard endpoint
    - Add GET `/api/leaderboard` endpoint
    - Query Oracle TELEMETRY_SUMMARY table
    - Order by CleanScore descending
    - Return List[LeaderboardEntry] with rank numbers
    - _Requirements: 8.4_

  - [ ]* 8.8 Write property test for REST API error response codes
    - **Property 18: REST API Error Response Codes**
    - **Validates: Requirements 9.5**
    - Test that invalid requests return 400, not found returns 404, server errors return 500
    - Use Hypothesis to generate invalid request parameters

  - [ ]* 8.9 Write property test for leaderboard ordering
    - **Property 17: Leaderboard Ordering**
    - **Validates: Requirements 8.4**
    - Test that leaderboard is ordered by Clean Score descending
    - Use Hypothesis to generate random Clean Score data

  - [ ]* 8.10 Write unit tests for all REST API endpoints
    - Test each endpoint with valid requests
    - Test 404 responses for non-existent resources
    - Test 400 responses for invalid parameters
    - Test CORS headers presence
    - Use FastAPI TestClient, mock database layer


- [ ] 9. Implement WebSocket server for real-time updates
  - [x] 9.1 Create WebSocket manager module
    - Write `backend/websocket_manager.py` with WebSocketManager class
    - Implement connection registry to track active clients
    - Add connect() method to register new WebSocket connections
    - Add disconnect() method to clean up closed connections
    - Add broadcast() method to send messages to all connected clients
    - Send connection acknowledgment message on connect
    - _Requirements: 10.1, 10.2, 10.5_

  - [x] 9.2 Add WebSocket endpoint to FastAPI
    - Add WebSocket endpoint `/ws` in `backend/main.py`
    - Accept WebSocket connections and register with WebSocketManager
    - Handle connection lifecycle (connect, disconnect)
    - Keep connection alive with periodic heartbeat
    - _Requirements: 10.1_

  - [x] 9.3 Integrate WebSocket broadcasts in telemetry and alert handlers
    - Modify telemetry_handler.py to broadcast telemetry data via WebSocket
    - Modify alert_engine.py to broadcast alerts via WebSocket
    - Format messages with type field: {"type": "telemetry", "data": {...}} and {"type": "alert", "data": {...}}
    - _Requirements: 10.3, 10.4_

  - [ ]* 9.4 Write property test for WebSocket connection acknowledgment
    - **Property 19: WebSocket Connection Acknowledgment**
    - **Validates: Requirements 10.2**
    - Test that every successful connection receives confirmation message
    - Use WebSocket test client

  - [ ]* 9.5 Write property test for WebSocket client isolation
    - **Property 20: WebSocket Client Isolation**
    - **Validates: Requirements 10.5**
    - Test that disconnecting one client doesn't affect other clients
    - Use multiple WebSocket test clients

  - [ ]* 9.6 Write unit tests for WebSocket manager
    - Test connection registration and deregistration
    - Test broadcast to multiple clients
    - Test handling of disconnected clients
    - Mock WebSocket connections


- [ ] 10. Create backend Dockerfile and requirements
  - [x] 10.1 Create Python requirements file
    - Write `backend/requirements.txt` with dependencies: fastapi, uvicorn, pydantic, pymongo, cx_Oracle, paho-mqtt, apscheduler, python-dotenv
    - Pin versions for reproducibility
    - _Requirements: 15.2_

  - [x] 10.2 Create backend Dockerfile
    - Write `backend/Dockerfile` with Python 3.11 base image
    - Install Oracle Instant Client for cx_Oracle
    - Copy requirements.txt and install dependencies
    - Copy application code
    - Set entrypoint to run uvicorn server on port 8000
    - _Requirements: 15.1, 15.2, 15.5_

  - [x] 10.3 Create backend startup script
    - Write `backend/startup.sh` to initialize databases and start services
    - Wait for MongoDB and Oracle to be ready using health checks
    - Run Oracle schema initialization scripts
    - Start MQTT consumer in background thread
    - Start FastAPI server with uvicorn
    - _Requirements: 16.4_


- [x] 11. Checkpoint - Backend integration test
  - Ensure all backend tests pass, verify MQTT consumer connects to broker, verify database connections work, ask the user if questions arise.


- [ ] 12. Initialize React frontend project
  - [x] 12.1 Create React TypeScript project
    - Run `npx create-react-app frontend --template typescript` or use Vite
    - Install dependencies: mapbox-gl, @types/mapbox-gl, chart.js, react-chartjs-2, axios
    - Configure TypeScript with strict mode
    - Create directory structure: `/src/components`, `/src/services`, `/src/types`, `/src/hooks`
    - _Requirements: 11.1, 12.1_

  - [x] 12.2 Create TypeScript type definitions
    - Write `frontend/src/types/index.ts` with interfaces: Telemetry, Location, Sensor, Alert, Analytics, LeaderboardEntry
    - Match Pydantic models from backend
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 12.3 Create API client service
    - Write `frontend/src/services/api.ts` using axios
    - Implement functions: fetchLocations(), fetchSensors(), fetchTelemetry(), fetchAnalytics(), fetchAlerts(), fetchLeaderboard()
    - Configure base URL from environment variable
    - Add error handling and response type validation
    - _Requirements: 9.1, 9.2, 9.3, 9.4_


- [ ] 13. Implement WebSocket client service
  - [x] 13.1 Create WebSocket manager hook
    - Write `frontend/src/hooks/useWebSocket.ts` custom React hook
    - Establish WebSocket connection to `ws://backend:8000/ws` on mount
    - Implement reconnection logic with exponential backoff
    - Parse incoming messages and dispatch to callbacks based on type
    - Provide connection status indicator
    - Clean up connection on unmount
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 13.2 Write unit tests for WebSocket hook
    - Test connection establishment
    - Test message parsing and dispatching
    - Test reconnection logic
    - Mock WebSocket API


- [ ] 14. Implement MapView component with Mapbox GL JS
  - [x] 14.1 Create MapView component
    - Write `frontend/src/components/MapView.tsx` using mapbox-gl library
    - Display Mapbox GL JS map centered on city location with zoom level 12
    - Render markers for all sensors using sensor locations
    - Color-code markers based on alert status: green (normal), yellow (warning), red (high alert)
    - Add popup on marker click showing sensor ID, location name, and current readings
    - Update marker colors in real-time when alerts received via WebSocket
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 14.2 Write unit tests for MapView component
    - Test marker rendering for sensor list
    - Test marker color coding by alert status
    - Test popup display on marker click
    - Mock sensor data and WebSocket updates
    - Use React Testing Library


- [ ] 15. Implement ChartView component with Chart.js
  - [x] 15.1 Create ChartView component
    - Write `frontend/src/components/ChartView.tsx` using react-chartjs-2
    - Display three line charts for CO2 (ppm), Noise (dB), Temperature (°C)
    - Fetch last 100 telemetry readings for selected sensor on mount
    - Display time on X-axis and metric values on Y-axis with appropriate units
    - Add time range selector buttons: 1h, 6h, 24h
    - Update charts in real-time when new telemetry received via WebSocket
    - Implement auto-scaling Y-axis based on data range
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ]* 15.2 Write unit tests for ChartView component
    - Test chart rendering with telemetry data
    - Test time range selector functionality
    - Test real-time data appending
    - Mock API calls and WebSocket updates
    - Use React Testing Library


- [ ] 16. Implement Leaderboard component
  - [x] 16.1 Create Leaderboard component
    - Write `frontend/src/components/Leaderboard.tsx`
    - Display table with columns: Rank, Location Name, Avg CO2, Avg Noise, Clean Score
    - Fetch leaderboard data from `/api/leaderboard` on mount
    - Highlight top 3 locations with visual indicators (gold, silver, bronze)
    - Add click handler to zoom map to selected location
    - Auto-refresh data every 60 seconds
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [ ]* 16.2 Write unit tests for Leaderboard component
    - Test table rendering with leaderboard data
    - Test top 3 highlighting
    - Test click handler for location selection
    - Mock API calls
    - Use React Testing Library


- [ ] 17. Implement AlertsPanel component
  - [x] 17.1 Create AlertsPanel component
    - Write `frontend/src/components/AlertsPanel.tsx`
    - Display list of most recent 20 alerts
    - Show alert timestamp, sensor location, metric type, value, severity level
    - Color-code alerts by severity: red (HIGH), orange (MEDIUM), yellow (LOW)
    - Add filter controls for severity level and location
    - Update list in real-time when new alerts received via WebSocket
    - Show visual notification (toast or badge) for new alerts
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [ ]* 17.2 Write unit tests for AlertsPanel component
    - Test alert list rendering
    - Test color coding by severity
    - Test filter controls
    - Test real-time alert updates
    - Mock API calls and WebSocket updates
    - Use React Testing Library


- [ ] 18. Implement main App component and state management
  - [x] 18.1 Create App component with layout
    - Write `frontend/src/App.tsx` with main application layout
    - Create grid layout: MapView (left), ChartView (center), Leaderboard + AlertsPanel (right)
    - Add header with application title and connection status indicator
    - Implement sensor selection state (shared between MapView and ChartView)
    - _Requirements: 11.1, 12.1, 13.1, 14.1_

  - [x] 18.2 Create global state context
    - Write `frontend/src/context/AppContext.tsx` using React Context API
    - Store global state: sensors, locations, alerts, selectedSensor, connectionStatus
    - Provide state update functions
    - Integrate WebSocket hook to update state on real-time messages
    - _Requirements: 10.3, 10.4_

  - [ ]* 18.3 Write integration tests for App component
    - Test component rendering and layout
    - Test sensor selection flow
    - Test WebSocket message handling and state updates
    - Use React Testing Library and MSW for API mocking


- [ ] 19. Create frontend Dockerfile and configuration
  - [x] 19.1 Create frontend Dockerfile
    - Write `frontend/Dockerfile` with Node.js base image
    - Copy package.json and install dependencies
    - Copy application code
    - Build production bundle with `npm run build`
    - Use nginx to serve static files on port 3000
    - _Requirements: 15.1, 15.2, 15.5_

  - [x] 19.2 Create nginx configuration
    - Write `frontend/nginx.conf` to serve React app
    - Configure proxy for API requests to backend
    - Enable gzip compression
    - Set cache headers for static assets

  - [x] 19.3 Create environment configuration
    - Write `frontend/.env.example` with REACT_APP_API_URL and REACT_APP_WS_URL
    - Document environment variables in README
    - _Requirements: 15.3_


- [x] 20. Checkpoint - Frontend integration test
  - Ensure all frontend tests pass, verify components render correctly, verify API integration works, ask the user if questions arise.


- [ ] 21. Complete Docker Compose orchestration
  - [ ] 21.1 Finalize docker-compose.yml
    - Configure mosquitto service with port 1883, persistence volume
    - Configure mongodb service with port 27017, data volume, health check
    - Configure oracle-xe service with port 1521, data volume, initialization scripts, health check
    - Configure backend service with port 8000, depends_on mongodb and oracle-xe, environment variables
    - Configure frontend service with port 3000, depends_on backend, environment variables
    - Configure iot-simulator service, depends_on mosquitto, environment variables with sensor list
    - Set up Docker network for inter-service communication
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [ ] 21.2 Create environment variables file
    - Write `.env.example` with all required environment variables
    - Document: MQTT_BROKER_HOST, MONGODB_URI, ORACLE_DSN, API_BASE_URL, WS_URL
    - Include sensor list configuration for IoT simulator
    - _Requirements: 15.3_

  - [ ] 21.3 Create startup and health check scripts
    - Write `docker/wait-for-it.sh` script to wait for service availability
    - Add health check endpoints to backend API
    - Configure Docker Compose health checks for all services
    - _Requirements: 15.2_


- [ ] 22. Write remaining property tests for hierarchy and sensor registration
  - [ ]* 22.1 Write property test for Hierarchy Path Completeness
    - **Property 2: Hierarchy Path Completeness**
    - **Validates: Requirements 1.3**
    - Test that querying hierarchy path returns complete chain from location to root
    - Use Hypothesis to generate random location hierarchies

  - [ ]* 22.2 Write property test for Descendant Query Completeness
    - **Property 3: Descendant Query Completeness**
    - **Validates: Requirements 1.4**
    - Test that querying descendants returns all transitive children
    - Use Hypothesis to generate random location trees

  - [ ]* 22.3 Write property test for Sensor Registration Location Validation
    - **Property 5: Sensor Registration Location Validation**
    - **Validates: Requirements 2.2**
    - Test that sensor registration only accepts Ward-level locations
    - Use Hypothesis to generate sensors with various location types

  - [ ]* 22.4 Write property test for Sensor Type Validation
    - **Property 6: Sensor Type Validation**
    - **Validates: Requirements 2.3**
    - Test that only CO2, Noise, Temperature sensor types are accepted
    - Use Hypothesis to generate invalid sensor types

  - [ ]* 22.5 Write property test for Sensor Registration Response Completeness
    - **Property 7: Sensor Registration Response Completeness**
    - **Validates: Requirements 2.4**
    - Test that registration response contains all required fields plus hierarchy
    - Use Hypothesis to generate random sensor registrations

  - [ ]* 22.6 Write property test for Sensor ID Uniqueness
    - **Property 8: Sensor ID Uniqueness**
    - **Validates: Requirements 2.5**
    - Test that duplicate SensorID registration is rejected
    - Use Hypothesis to generate duplicate sensor IDs


- [ ] 23. End-to-end integration testing
  - [ ]* 23.1 Write end-to-end test for telemetry flow
    - Test: Publish telemetry via MQTT → Verify storage in MongoDB → Verify WebSocket broadcast
    - Use Docker Compose test environment
    - Verify data integrity through entire pipeline

  - [ ]* 23.2 Write end-to-end test for alert flow
    - Test: Publish threshold-exceeding telemetry → Verify alert creation in Oracle → Verify WebSocket alert broadcast
    - Use Docker Compose test environment
    - Verify alert deduplication works

  - [ ]* 23.3 Write end-to-end test for sensor registration flow
    - Test: Register sensor via REST API → Query via REST API → Verify complete response with hierarchy
    - Use Docker Compose test environment
    - Verify referential integrity constraints

  - [ ]* 23.4 Write end-to-end test for hierarchy queries
    - Test: Create location hierarchy → Query descendants → Verify completeness
    - Use Docker Compose test environment
    - Verify recursive queries work correctly


- [ ] 24. Documentation and final polish
  - [ ] 24.1 Write comprehensive README.md
    - Document system architecture and components
    - Add setup instructions: prerequisites, environment variables, Docker Compose commands
    - Add usage instructions: accessing dashboard, API endpoints, monitoring logs
    - Add troubleshooting section for common issues
    - Include architecture diagrams
    - _Requirements: 15.1_

  - [ ] 24.2 Add API documentation
    - Configure FastAPI automatic OpenAPI documentation
    - Add detailed docstrings to all API endpoints
    - Include request/response examples
    - Document error codes and messages
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 24.3 Add inline code documentation
    - Add docstrings to all Python modules, classes, and functions
    - Add JSDoc comments to TypeScript functions and components
    - Document complex algorithms (Clean Score calculation, moving averages)
    - Add comments explaining business logic

  - [ ] 24.4 Create deployment guide
    - Document production deployment considerations
    - Add security best practices (authentication, HTTPS, database credentials)
    - Document scaling strategies for high-traffic scenarios
    - Add monitoring and logging recommendations


- [ ] 25. Final checkpoint - System verification
  - Ensure all tests pass (unit, property, integration, end-to-end), verify Docker Compose starts all services successfully, verify dashboard displays real-time data, verify all 20 correctness properties are validated, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples, edge cases, and integration points
- Checkpoints ensure incremental validation at key milestones
- All code should be production-ready with proper error handling and logging
- Follow Python PEP 8 style guide and TypeScript/React best practices
- Use type hints in Python and strict TypeScript mode for type safety
