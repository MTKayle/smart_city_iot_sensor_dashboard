# Requirements Document

## Introduction

Hệ thống Smart City IoT Sensor Dashboard là một nền tảng giám sát và phân tích dữ liệu môi trường thời gian thực từ mạng lưới cảm biến IoT phân tán trong thành phố thông minh. Hệ thống thu thập dữ liệu telemetry tần suất cao (mỗi 5 giây) về các chỉ số CO2, tiếng ồn và nhiệt độ, lưu trữ trong kiến trúc hybrid database (MongoDB cho time-series data, Oracle SQL cho relational data và analytics), và cung cấp dashboard trực quan với bản đồ, biểu đồ, bảng xếp hạng và cảnh báo tự động.

## Glossary

- **System**: Smart City IoT Sensor Dashboard platform
- **IoT_Simulator**: Python script that generates and publishes simulated sensor data
- **MQTT_Broker**: Message broker that receives sensor data from IoT devices
- **Backend_Consumer**: Python FastAPI service that consumes MQTT messages and processes data
- **MongoDB_Store**: MongoDB database storing telemetry time-series data
- **Oracle_Store**: Oracle SQL database storing relational data, hierarchy, alerts, and analytics
- **REST_API**: RESTful API endpoints for data retrieval and management
- **WebSocket_Server**: Real-time bidirectional communication channel for live updates
- **Frontend_Dashboard**: React-based web interface with map visualization and charts
- **Telemetry_Data**: Time-series sensor measurements (CO2, noise, temperature)
- **Location_Hierarchy**: Geographic administrative structure (City > District > Ward > Sensor)
- **Alert**: Notification generated when sensor values exceed defined thresholds
- **Clean_Score**: Calculated metric ranking location environmental quality
- **TTL_Index**: Time-To-Live index that automatically deletes data after 30 days

## Requirements

### Requirement 1: Geographic Hierarchy Management

**User Story:** As a system administrator, I want to manage the geographic hierarchy of locations, so that sensors can be organized by administrative boundaries (City > District > Ward).

#### Acceptance Criteria

1. THE Oracle_Store SHALL store location records with LocationID, Name, ParentID, and Type attributes
2. WHEN a location is created, THE System SHALL validate that ParentID references an existing location or is NULL for root locations
3. THE System SHALL support recursive queries to retrieve the complete hierarchy path from any location to the root
4. WHEN querying a location, THE System SHALL return all descendant locations in the hierarchy tree
5. THE System SHALL enforce hierarchy constraints where City contains Districts, Districts contain Wards, and Wards contain Sensors

### Requirement 2: Sensor Device Registration

**User Story:** As a system administrator, I want to register IoT sensor devices with their physical locations, so that telemetry data can be associated with geographic positions.

#### Acceptance Criteria

1. THE Oracle_Store SHALL store sensor registry records with SensorID, LocationID, and SensorType attributes
2. WHEN a sensor is registered, THE System SHALL validate that LocationID references an existing Ward-level location
3. THE System SHALL support sensor types: CO2, Noise, and Temperature
4. WHEN a sensor is registered, THE REST_API SHALL return the complete sensor record including location hierarchy information
5. THE System SHALL prevent duplicate SensorID registrations

### Requirement 3: High-Frequency Telemetry Data Collection

**User Story:** As an IoT device, I want to publish sensor measurements every 5 seconds, so that the system captures real-time environmental data.

#### Acceptance Criteria

1. THE IoT_Simulator SHALL generate random sensor data for CO2 (ppm), Noise (dB), and Temperature (°C) every 5 seconds
2. WHEN sensor data is generated, THE IoT_Simulator SHALL publish messages to the MQTT_Broker with topic pattern "sensors/{sensorId}/telemetry"
3. THE MQTT_Broker SHALL accept connections from multiple IoT_Simulator instances concurrently
4. WHEN a telemetry message is published, THE Backend_Consumer SHALL subscribe to the MQTT_Broker and receive the message within 1 second
5. THE Backend_Consumer SHALL parse telemetry messages containing sensorId, locationId, co2, noise, temperature, and timestamp fields

### Requirement 4: Telemetry Data Storage with Automatic Cleanup

**User Story:** As a system operator, I want telemetry data to be stored efficiently and automatically deleted after 30 days, so that storage costs remain manageable.

#### Acceptance Criteria

1. WHEN telemetry data is received, THE Backend_Consumer SHALL insert the document into MongoDB_Store collection "telemetry"
2. THE MongoDB_Store SHALL create a TTL_Index on the timestamp field with expiration time of 30 days
3. THE MongoDB_Store SHALL automatically delete telemetry documents older than 30 days without manual intervention
4. THE System SHALL handle insertion rates of at least 100 documents per second
5. WHEN storing telemetry data, THE MongoDB_Store SHALL index documents by sensorId and timestamp for efficient querying

### Requirement 5: Telemetry Data Parsing and Serialization

**User Story:** As a developer, I want to parse and serialize telemetry data consistently, so that data integrity is maintained across system components.

#### Acceptance Criteria

1. WHEN a telemetry message is received from MQTT_Broker, THE Backend_Consumer SHALL parse the JSON payload into a Telemetry object
2. WHEN an invalid telemetry message is received, THE Backend_Consumer SHALL log a descriptive error and skip processing
3. THE System SHALL serialize Telemetry objects to JSON format for REST_API responses
4. FOR ALL valid Telemetry objects, parsing the JSON representation then serializing then parsing SHALL produce an equivalent object (round-trip property)
5. THE System SHALL validate that co2 values are non-negative, noise values are between 0-120 dB, and temperature values are between -50°C and 60°C

### Requirement 6: Real-Time Alert Generation

**User Story:** As an environmental monitor, I want to receive automatic alerts when sensor values exceed safety thresholds, so that I can respond to environmental hazards quickly.

#### Acceptance Criteria

1. WHEN telemetry data shows CO2 > 1000 ppm, THE Backend_Consumer SHALL create an alert record in Oracle_Store with Level "HIGH"
2. WHEN telemetry data shows Noise > 85 dB, THE Backend_Consumer SHALL create an alert record in Oracle_Store with Level "HIGH"
3. THE Oracle_Store SHALL store alert records with AlertID, SensorID, Value, Level, and CreatedAt attributes
4. WHEN an alert is created, THE Backend_Consumer SHALL publish the alert to all connected WebSocket_Server clients within 2 seconds
5. THE System SHALL prevent duplicate alerts for the same sensor within a 5-minute window

### Requirement 7: Moving Average Analytics

**User Story:** As a data analyst, I want to calculate moving averages of sensor readings, so that I can identify trends and smooth out short-term fluctuations.

#### Acceptance Criteria

1. WHEN querying telemetry data for a sensor, THE System SHALL calculate the moving average of the last 10 readings for each metric (CO2, Noise, Temperature)
2. THE Oracle_Store SHALL use window functions (AVG OVER) to compute moving averages efficiently
3. WHEN fewer than 10 readings exist, THE System SHALL calculate the average of all available readings
4. THE REST_API SHALL provide an endpoint "/api/sensors/{sensorId}/analytics" that returns moving average data
5. THE System SHALL update moving averages within 10 seconds of new telemetry data arrival

### Requirement 8: Location Clean Score Ranking

**User Story:** As a city planner, I want to see locations ranked by environmental quality, so that I can identify areas needing improvement.

#### Acceptance Criteria

1. THE System SHALL calculate Clean_Score for each location based on the formula: 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)
2. WHEN calculating Clean_Score, THE System SHALL normalize CO2 values using range 0-2000 ppm and Noise values using range 0-100 dB
3. THE Oracle_Store SHALL store daily Clean_Score summaries in TELEMETRY_SUMMARY table with LocationID, AvgCO2, AvgNoise, CleanScore, and Date attributes
4. THE REST_API SHALL provide an endpoint "/api/leaderboard" that returns locations ordered by Clean_Score descending
5. THE System SHALL recalculate Clean_Score for all locations daily at midnight

### Requirement 9: RESTful API for Data Access

**User Story:** As a frontend developer, I want to access sensor data and analytics through REST APIs, so that I can build interactive dashboards.

#### Acceptance Criteria

1. THE REST_API SHALL provide endpoint GET "/api/locations" to retrieve the complete location hierarchy
2. THE REST_API SHALL provide endpoint GET "/api/sensors" to retrieve all registered sensors with location information
3. THE REST_API SHALL provide endpoint GET "/api/telemetry/{sensorId}" to retrieve recent telemetry data with optional time range filters
4. THE REST_API SHALL provide endpoint GET "/api/alerts" to retrieve active alerts with optional filtering by level and location
5. WHEN a REST_API request fails, THE System SHALL return appropriate HTTP status codes (400 for bad requests, 404 for not found, 500 for server errors) with descriptive error messages
6. THE REST_API SHALL support CORS headers to allow cross-origin requests from the Frontend_Dashboard

### Requirement 10: Real-Time WebSocket Updates

**User Story:** As a dashboard user, I want to see live sensor data updates without refreshing the page, so that I can monitor environmental conditions in real-time.

#### Acceptance Criteria

1. THE WebSocket_Server SHALL accept client connections on endpoint "/ws"
2. WHEN a client connects, THE WebSocket_Server SHALL send a connection confirmation message
3. WHEN new telemetry data is received, THE Backend_Consumer SHALL broadcast the data to all connected WebSocket clients within 1 second
4. WHEN an alert is generated, THE Backend_Consumer SHALL broadcast the alert to all connected WebSocket clients within 1 second
5. WHEN a client disconnects, THE WebSocket_Server SHALL clean up the connection resources without affecting other clients

### Requirement 11: Interactive Map Visualization

**User Story:** As a dashboard user, I want to see sensor locations on an interactive map, so that I can understand the geographic distribution of environmental data.

#### Acceptance Criteria

1. THE Frontend_Dashboard SHALL display a Leaflet map showing all sensor locations as markers
2. WHEN a sensor marker is clicked, THE Frontend_Dashboard SHALL display a popup with current sensor readings and location information
3. THE Frontend_Dashboard SHALL color-code markers based on current alert status (green for normal, yellow for warning, red for high alert)
4. THE Frontend_Dashboard SHALL update marker colors in real-time when alerts are received via WebSocket
5. THE Frontend_Dashboard SHALL center the map on the city location with appropriate zoom level to show all sensors

### Requirement 12: Time-Series Chart Visualization

**User Story:** As a dashboard user, I want to see historical sensor data in charts, so that I can analyze trends over time.

#### Acceptance Criteria

1. THE Frontend_Dashboard SHALL display line charts for CO2, Noise, and Temperature metrics using Chart.js
2. WHEN a sensor is selected, THE Frontend_Dashboard SHALL fetch and display the last 100 telemetry readings for that sensor
3. THE Frontend_Dashboard SHALL update charts in real-time when new telemetry data is received via WebSocket
4. THE Frontend_Dashboard SHALL display time on the X-axis and metric values on the Y-axis with appropriate units (ppm, dB, °C)
5. THE Frontend_Dashboard SHALL allow users to toggle between different time ranges (1 hour, 6 hours, 24 hours)

### Requirement 13: Leaderboard Display

**User Story:** As a dashboard user, I want to see a ranked list of locations by environmental quality, so that I can identify the cleanest and most polluted areas.

#### Acceptance Criteria

1. THE Frontend_Dashboard SHALL display a leaderboard table showing locations ranked by Clean_Score
2. THE Frontend_Dashboard SHALL show location name, average CO2, average Noise, and Clean_Score for each entry
3. THE Frontend_Dashboard SHALL highlight the top 3 cleanest locations with visual indicators
4. THE Frontend_Dashboard SHALL refresh leaderboard data every 60 seconds
5. WHEN a location in the leaderboard is clicked, THE Frontend_Dashboard SHALL zoom the map to that location

### Requirement 14: Alerts Panel

**User Story:** As a dashboard user, I want to see active alerts in a dedicated panel, so that I can quickly identify environmental issues requiring attention.

#### Acceptance Criteria

1. THE Frontend_Dashboard SHALL display an alerts panel showing the most recent 20 alerts
2. THE Frontend_Dashboard SHALL show alert timestamp, sensor location, metric type, value, and severity level for each alert
3. THE Frontend_Dashboard SHALL color-code alerts by severity (red for HIGH, orange for MEDIUM, yellow for LOW)
4. WHEN a new alert is received via WebSocket, THE Frontend_Dashboard SHALL add it to the top of the alerts panel with a visual notification
5. THE Frontend_Dashboard SHALL allow users to filter alerts by severity level and location

### Requirement 15: Docker Containerization

**User Story:** As a DevOps engineer, I want to deploy the entire system using Docker Compose, so that I can easily set up development and production environments.

#### Acceptance Criteria

1. THE System SHALL provide a docker-compose.yml file that defines services for MQTT_Broker, MongoDB_Store, Oracle_Store, Backend_Consumer, and Frontend_Dashboard
2. WHEN docker-compose up is executed, THE System SHALL start all services with proper networking and dependencies
3. THE System SHALL configure environment variables for database connections, MQTT broker address, and API endpoints
4. THE System SHALL persist MongoDB_Store and Oracle_Store data using Docker volumes
5. THE System SHALL expose Frontend_Dashboard on port 3000, REST_API on port 8000, and MQTT_Broker on port 1883

### Requirement 16: Database Schema Initialization

**User Story:** As a database administrator, I want to initialize Oracle database schema automatically, so that the system is ready to use after deployment.

#### Acceptance Criteria

1. THE System SHALL provide SQL scripts to create LOCATIONS, SENSOR_REGISTRY, ALERTS, and TELEMETRY_SUMMARY tables
2. THE System SHALL create indexes on LocationID, SensorID, and CreatedAt columns for query performance
3. THE System SHALL create a recursive CTE view for querying location hierarchy paths
4. WHEN the Backend_Consumer starts, THE System SHALL execute schema initialization scripts if tables do not exist
5. THE System SHALL seed initial location hierarchy data (City > Districts > Wards) for testing purposes
