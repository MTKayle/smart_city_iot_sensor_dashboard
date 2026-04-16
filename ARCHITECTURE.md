# System Architecture

## Overview

The Smart City IoT Sensor Dashboard uses a microservices architecture with the following components:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose Network                    │
│                                                                  │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │ IoT Simulator│────────>│ MQTT Broker  │                     │
│  │   (Python)   │         │ (Mosquitto)  │                     │
│  └──────────────┘         │  Port: 1883  │                     │
│                           └──────┬───────┘                      │
│                                  │                              │
│                                  v                              │
│                           ┌──────────────┐                      │
│                           │   Backend    │                      │
│                           │  (FastAPI)   │                      │
│                           │  Port: 8000  │                      │
│                           └──┬────────┬──┘                      │
│                              │        │                         │
│                    ┌─────────┘        └─────────┐              │
│                    v                            v               │
│            ┌──────────────┐            ┌──────────────┐        │
│            │   MongoDB    │            │  Oracle XE   │        │
│            │ (Telemetry)  │            │ (Relational) │        │
│            │ Port: 27017  │            │ Port: 1521   │        │
│            └──────────────┘            └──────────────┘        │
│                    ^                            ^               │
│                    │                            │               │
│                    └────────────┬───────────────┘              │
│                                 │                               │
│                                 │                               │
│                           ┌─────┴────────┐                     │
│                           │   Frontend   │                     │
│                           │   (React)    │                     │
│                           │  Port: 3000  │                     │
│                           └──────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Telemetry Collection Flow

1. **IoT Simulator** generates sensor readings every 5 seconds
2. Publishes JSON messages to **MQTT Broker** on topic `sensors/{sensorId}/telemetry`
3. **Backend Consumer** subscribes to MQTT and receives messages
4. Backend validates and processes telemetry data
5. Stores time-series data in **MongoDB** (with 30-day TTL)
6. Stores alerts and analytics in **Oracle**
7. Broadcasts real-time updates via **WebSocket** to connected clients
8. **Frontend** receives updates and refreshes visualizations

### API Request Flow

1. **Frontend** makes HTTP GET request to Backend REST API
2. **Backend** queries MongoDB (telemetry) or Oracle (hierarchy, alerts, analytics)
3. Backend serializes response as JSON
4. **Frontend** receives data and updates UI components

## Component Responsibilities

### IoT Simulator
- Generate random sensor data (CO2, Noise, Temperature)
- Publish to MQTT every 5 seconds
- Support multiple sensor instances

### MQTT Broker (Mosquitto)
- Message routing between publishers and subscribers
- Message persistence
- Support concurrent connections

### Backend (FastAPI)
- MQTT message consumption and processing
- Data validation using Pydantic models
- Database operations (MongoDB + Oracle)
- Alert threshold evaluation
- Analytics calculations (moving averages, Clean Score)
- REST API endpoints
- WebSocket server for real-time updates

### MongoDB
- High-frequency time-series telemetry storage
- Automatic data expiration (TTL index, 30 days)
- Optimized for write-heavy workloads

### Oracle XE
- Location hierarchy (City > District > Ward)
- Sensor registry
- Alert records
- Analytics summaries
- Complex relational queries

### Frontend (React)
- Interactive map with sensor markers (Leaflet)
- Time-series charts (Chart.js)
- Leaderboard display
- Alerts panel
- Real-time updates via WebSocket

## Network Configuration

All services run in a Docker bridge network (`smart-city-network`) with:
- Internal DNS resolution (services can reference each other by name)
- Port mapping to host for external access
- Isolated from other Docker networks

## Data Persistence

Docker volumes ensure data survives container restarts:
- `mosquitto-data`: MQTT message persistence
- `mosquitto-logs`: MQTT broker logs
- `mongodb-data`: Telemetry time-series data
- `oracle-data`: Relational database files

## Security Considerations

**Development Configuration:**
- Anonymous MQTT access enabled
- Default database credentials
- CORS enabled for all origins

**Production Recommendations:**
- Enable MQTT authentication
- Use strong database passwords
- Configure CORS for specific origins
- Enable HTTPS/TLS
- Implement API authentication
- Use secrets management (Docker secrets, Vault)
- Network segmentation
- Regular security updates

## Scalability Considerations

**Current Architecture:**
- Single instance of each service
- Suitable for development and small deployments

**Scaling Options:**
- Multiple IoT simulator instances (already supported)
- Backend horizontal scaling (requires load balancer)
- MongoDB replica set for high availability
- Oracle RAC for enterprise deployments
- MQTT broker clustering
- Frontend CDN distribution

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Python + FastAPI | 3.11 / 0.109 |
| Frontend | React + TypeScript | 18 |
| MQTT Broker | Eclipse Mosquitto | 2.0 |
| Time-series DB | MongoDB | 7.0 |
| Relational DB | Oracle XE | 21 |
| Container Runtime | Docker + Docker Compose | 20.10+ / 2.0+ |
| Map Library | Leaflet | Latest |
| Charts Library | Chart.js | Latest |

## Development Workflow

1. Make code changes in `backend/`, `frontend/`, or `iot-simulator/`
2. Rebuild affected service: `docker-compose build <service>`
3. Restart service: `docker-compose up -d <service>`
4. View logs: `docker-compose logs -f <service>`
5. Test changes via API or frontend

## Monitoring and Observability

**Current Implementation:**
- Docker logs for all services
- FastAPI automatic OpenAPI documentation
- Health check endpoints (to be implemented)

**Future Enhancements:**
- Prometheus metrics
- Grafana dashboards
- Distributed tracing (OpenTelemetry)
- Centralized logging (ELK stack)
- Alert notifications (email, Slack)
