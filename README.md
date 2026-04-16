# Smart City IoT Sensor Dashboard

A distributed real-time monitoring platform that collects, stores, analyzes, and visualizes environmental telemetry data from IoT sensors deployed across urban areas.

## System Architecture

The platform consists of five primary layers:

1. **Data Generation Layer**: IoT simulators publishing sensor readings via MQTT
2. **Message Transport Layer**: MQTT broker handling pub/sub messaging
3. **Processing Layer**: FastAPI backend consuming MQTT messages, processing data, and managing business logic
4. **Storage Layer**: Hybrid database (MongoDB for telemetry, Oracle for relational/analytics)
5. **Presentation Layer**: React frontend with real-time WebSocket updates and interactive visualizations

## Components

- **MQTT Broker** (Eclipse Mosquitto): Message routing on port 1883
- **MongoDB**: High-frequency time-series telemetry storage on port 27017
- **Oracle XE**: Relational data, hierarchy, alerts, and analytics on port 1521
- **Backend** (FastAPI): REST API and WebSocket server on port 8000
- **Frontend** (React): Interactive dashboard on port 3000
- **IoT Simulator**: Generates and publishes simulated sensor data

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available for Docker
- Ports 1883, 8000, 3000, 27017, 1521 available

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd smart_city_iot_sensor_dashboard
```

### 2. Configure Environment Variables

Copy the example environment file and customize as needed:

```bash
cp .env.example .env
```

Edit `.env` to configure:
- Database credentials
- MQTT broker settings
- API endpoints
- Sensor list for simulation

### 3. Start All Services

```bash
docker-compose up -d
```

This will:
- Pull required Docker images
- Build custom images for backend, frontend, and IoT simulator
- Create Docker volumes for data persistence
- Start all services with proper networking and dependencies

### 4. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

All services should show status "Up" or "Up (healthy)".

### 5. Access the Dashboard

Open your browser and navigate to:

```
http://localhost:3000
```

## Usage

### Accessing the API

The REST API is available at `http://localhost:8000`

API documentation (OpenAPI/Swagger):
```
http://localhost:8000/docs
```

### Key API Endpoints

- `GET /api/locations` - Retrieve location hierarchy
- `GET /api/sensors` - Retrieve all registered sensors
- `GET /api/telemetry/{sensorId}` - Get sensor telemetry data
- `GET /api/alerts` - Retrieve active alerts
- `GET /api/leaderboard` - Get locations ranked by environmental quality
- `GET /api/sensors/{sensorId}/analytics` - Get moving averages

### WebSocket Connection

Connect to real-time updates:
```
ws://localhost:8000/ws
```

### Monitoring Logs

View logs for specific services:

```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# IoT Simulator logs
docker-compose logs -f iot-simulator

# MQTT Broker logs
docker-compose logs -f mosquitto

# All logs
docker-compose logs -f
```

## Data Persistence

The following Docker volumes are created for data persistence:

- `mosquitto-data`: MQTT broker message persistence
- `mosquitto-logs`: MQTT broker logs
- `mongodb-data`: MongoDB telemetry data (auto-deleted after 30 days)
- `oracle-data`: Oracle database files (locations, sensors, alerts, analytics)

## Stopping the System

Stop all services:

```bash
docker-compose down
```

Stop and remove volumes (WARNING: deletes all data):

```bash
docker-compose down -v
```

## Troubleshooting

### Services Not Starting

1. Check if required ports are available:
```bash
netstat -tuln | grep -E '1883|8000|3000|27017|1521'
```

2. Check Docker logs for specific service:
```bash
docker-compose logs <service-name>
```

### Database Connection Issues

Wait for databases to be fully initialized (may take 1-2 minutes on first start):

```bash
# Check MongoDB health
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Check Oracle health
docker-compose exec oracle-xe healthcheck.sh
```

### MQTT Connection Issues

Verify MQTT broker is accepting connections:

```bash
docker-compose exec mosquitto mosquitto_sub -t 'sensors/#' -v
```

### Frontend Not Loading

1. Check backend is running: `curl http://localhost:8000/health`
2. Check browser console for errors
3. Verify environment variables in `.env` are correct

## Development

### Rebuilding Services

After code changes, rebuild specific service:

```bash
docker-compose build backend
docker-compose up -d backend
```

Rebuild all services:

```bash
docker-compose build
docker-compose up -d
```

### Running Tests

Tests will be added in subsequent implementation tasks.

## Project Structure

```
smart_city_iot_sensor_dashboard/
├── backend/              # FastAPI backend application
├── frontend/             # React TypeScript dashboard
├── iot-simulator/        # IoT data simulator
├── docker/               # Docker configuration files
│   └── mosquitto/        # MQTT broker configuration
├── docker-compose.yml    # Service orchestration
├── .env.example          # Environment variables template
└── README.md             # This file
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
