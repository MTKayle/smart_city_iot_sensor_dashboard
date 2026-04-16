# Smart City IoT Dashboard - REST API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication
Currently, no authentication is required (development mode).

## CORS
CORS is enabled for all origins. Configure via `CORS_ORIGINS` environment variable.

---

## Endpoints

### 1. Health Check

Check if the API server is running and healthy.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "smart-city-iot-backend"
}
```

**Status Codes:**
- `200 OK`: Service is healthy

---

### 2. Get Locations

Retrieve the complete location hierarchy (City > District > Ward).

**Endpoint:** `GET /api/locations`

**Response:**
```json
[
  {
    "locationId": "city_hcm",
    "name": "Ho Chi Minh City",
    "parentId": null,
    "type": "City"
  },
  {
    "locationId": "district_001",
    "name": "District 1",
    "parentId": "city_hcm",
    "type": "District"
  },
  {
    "locationId": "ward_001",
    "name": "Ward 1",
    "parentId": "district_001",
    "type": "Ward"
  }
]
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Database query failed

**Validates:** Requirements 9.1, 1.3

---

### 3. Get Sensors

Retrieve all registered sensors with their location information.

**Endpoint:** `GET /api/sensors`

**Query Parameters:**
- `location_id` (optional): Filter sensors by location ID

**Example Request:**
```
GET /api/sensors?location_id=ward_001
```

**Response:**
```json
[
  {
    "sensorId": "sensor_001",
    "locationId": "ward_001",
    "sensorType": "CO2",
    "registeredAt": "2024-01-01T00:00:00Z"
  },
  {
    "sensorId": "sensor_002",
    "locationId": "ward_001",
    "sensorType": "Noise",
    "registeredAt": "2024-01-01T00:00:00Z"
  }
]
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Database query failed

**Validates:** Requirements 9.2, 2.4

---

### 4. Get Telemetry Data

Retrieve telemetry data for a specific sensor with optional time range filtering.

**Endpoint:** `GET /api/telemetry/{sensorId}`

**Path Parameters:**
- `sensorId` (required): Sensor identifier

**Query Parameters:**
- `start_time` (optional): Start of time range (ISO 8601 format)
- `end_time` (optional): End of time range (ISO 8601 format)
- `limit` (optional): Maximum number of records (default: 100, max: 1000)

**Default Behavior:**
If no time range is specified, returns data from the last 24 hours.

**Example Request:**
```
GET /api/telemetry/sensor_001?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z&limit=50
```

**Response:**
```json
[
  {
    "sensorId": "sensor_001",
    "locationId": "ward_001",
    "co2": 450.5,
    "noise": 65.2,
    "temperature": 25.3,
    "timestamp": "2024-01-15T10:30:00Z"
  },
  {
    "sensorId": "sensor_001",
    "locationId": "ward_001",
    "co2": 455.8,
    "noise": 66.1,
    "temperature": 25.5,
    "timestamp": "2024-01-15T10:30:05Z"
  }
]
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid time range (start_time >= end_time)
- `500 Internal Server Error`: Database query failed

**Validates:** Requirement 9.3

---

### 5. Get Sensor Analytics

Get moving averages for a sensor's telemetry data.

**Endpoint:** `GET /api/sensors/{sensorId}/analytics`

**Path Parameters:**
- `sensorId` (required): Sensor identifier

**Example Request:**
```
GET /api/sensors/sensor_001/analytics
```

**Response:**
```json
{
  "sensorId": "sensor_001",
  "co2_moving_avg": {
    "metric": "CO2",
    "values": [450.5, 460.2, 455.8, 470.1, 465.3, 458.9, 462.4, 467.2, 461.5, 459.7],
    "average": 461.16,
    "window_size": 10
  },
  "noise_moving_avg": {
    "metric": "Noise",
    "values": [65.2, 67.1, 66.5, 68.3, 67.8, 66.9, 67.5, 68.1, 67.3, 66.8],
    "average": 67.15,
    "window_size": 10
  },
  "temperature_moving_avg": {
    "metric": "Temperature",
    "values": [25.3, 25.8, 25.5, 26.1, 25.9, 25.6, 25.8, 26.0, 25.7, 25.5],
    "average": 25.72,
    "window_size": 10
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: No telemetry data found for sensor
- `500 Internal Server Error`: Calculation failed

**Validates:** Requirement 7.4

---

### 6. Get Alerts

Retrieve alerts with optional filtering by level and location.

**Endpoint:** `GET /api/alerts`

**Query Parameters:**
- `level` (optional): Filter by alert level (LOW, MEDIUM, HIGH)
- `location_id` (optional): Filter by location ID
- `limit` (optional): Maximum number of alerts (default: 100, max: 1000)

**Example Request:**
```
GET /api/alerts?level=HIGH&limit=20
```

**Response:**
```json
[
  {
    "alertId": "alert_001",
    "sensorId": "sensor_001",
    "metricType": "CO2",
    "value": 1250.0,
    "level": "HIGH",
    "createdAt": "2024-01-15T10:30:05Z"
  },
  {
    "alertId": "alert_002",
    "sensorId": "sensor_003",
    "metricType": "Noise",
    "value": 92.5,
    "level": "HIGH",
    "createdAt": "2024-01-15T10:25:12Z"
  }
]
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid alert level
- `500 Internal Server Error`: Database query failed

**Validates:** Requirement 9.4

---

### 7. Get Leaderboard

Get locations ranked by environmental quality (Clean Score).

**Endpoint:** `GET /api/leaderboard`

**Query Parameters:**
- `limit` (optional): Maximum number of entries (default: 100, max: 1000)

**Example Request:**
```
GET /api/leaderboard?limit=10
```

**Response:**
```json
[
  {
    "locationId": "ward_001",
    "locationName": "Ward 1",
    "avgCO2": 420.5,
    "avgNoise": 55.2,
    "avgTemperature": 26.3,
    "cleanScore": 85.5,
    "rank": 1
  },
  {
    "locationId": "ward_005",
    "locationName": "Ward 5",
    "avgCO2": 450.8,
    "avgNoise": 58.7,
    "avgTemperature": 26.8,
    "cleanScore": 82.3,
    "rank": 2
  }
]
```

**Clean Score Calculation:**
```
normalized_CO2 = (avgCO2 / 2000) * 100
normalized_Noise = (avgNoise / 100) * 100
cleanScore = 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)
```

Higher Clean Score = Better environmental quality

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Database query failed

**Validates:** Requirement 8.4

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
  - Invalid time range (start_time >= end_time)
  - Invalid alert level (not LOW, MEDIUM, or HIGH)
  
- `404 Not Found`: Resource not found
  - Sensor has no telemetry data
  
- `500 Internal Server Error`: Server-side error
  - Database connection failure
  - Query execution failure
  - Unexpected errors

---

## Data Models

### Location
```typescript
{
  locationId: string;
  name: string;
  parentId: string | null;
  type: "City" | "District" | "Ward";
}
```

### Sensor
```typescript
{
  sensorId: string;
  locationId: string;
  sensorType: "CO2" | "Noise" | "Temperature";
  registeredAt: string; // ISO 8601 datetime
}
```

### Telemetry
```typescript
{
  sensorId: string;
  locationId: string;
  co2: number;        // ppm (0-5000)
  noise: number;      // dB (0-120)
  temperature: number; // °C (-50 to 60)
  timestamp: string;  // ISO 8601 datetime
}
```

### Alert
```typescript
{
  alertId: string;
  sensorId: string;
  metricType: "CO2" | "Noise" | "Temperature";
  value: number;
  level: "LOW" | "MEDIUM" | "HIGH";
  createdAt: string; // ISO 8601 datetime
}
```

### Analytics
```typescript
{
  sensorId: string;
  co2_moving_avg: MovingAverage;
  noise_moving_avg: MovingAverage;
  temperature_moving_avg: MovingAverage;
}
```

### MovingAverage
```typescript
{
  metric: string;
  values: number[];
  average: number;
  window_size: number; // max 10
}
```

### LeaderboardEntry
```typescript
{
  locationId: string;
  locationName: string;
  avgCO2: number;
  avgNoise: number;
  avgTemperature: number;
  cleanScore: number; // 0-100
  rank: number;       // 1 = best
}
```

---

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- View all endpoints and their parameters
- Test endpoints directly from the browser
- See request/response schemas
- Download OpenAPI specification

---

## Example Usage

See `backend/examples/example_api_usage.py` for a complete Python example demonstrating all endpoints.

### Quick Start with curl

```bash
# Health check
curl http://localhost:8000/api/health

# Get all locations
curl http://localhost:8000/api/locations

# Get all sensors
curl http://localhost:8000/api/sensors

# Get telemetry for a sensor
curl "http://localhost:8000/api/telemetry/sensor_001?limit=10"

# Get analytics for a sensor
curl http://localhost:8000/api/sensors/sensor_001/analytics

# Get HIGH level alerts
curl "http://localhost:8000/api/alerts?level=HIGH&limit=20"

# Get leaderboard
curl "http://localhost:8000/api/leaderboard?limit=10"
```

---

## Rate Limiting

Currently, no rate limiting is implemented. This should be added for production deployment.

## Caching

Currently, no caching is implemented. Consider adding Redis caching for frequently accessed data like locations and sensors.

## Pagination

Currently, pagination is implemented via the `limit` parameter. Consider adding offset-based or cursor-based pagination for large datasets.

---

## Support

For issues or questions, refer to:
- Main README: `README.md`
- Task Implementation Summary: `backend/TASK_8_IMPLEMENTATION_SUMMARY.md`
- Example Scripts: `backend/examples/`
