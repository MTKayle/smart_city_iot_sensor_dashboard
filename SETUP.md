# Quick Setup Guide

## Initial Setup

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Review and customize `.env` file** (optional):
   - Database credentials
   - MQTT broker settings
   - Sensor list for simulation

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to initialize** (first start may take 2-3 minutes):
   ```bash
   docker-compose ps
   ```

5. **Access the dashboard:**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - WebSocket: ws://localhost:8000/ws

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | React dashboard |
| Backend API | 8000 | REST API and WebSocket |
| MQTT Broker | 1883 | MQTT message broker |
| MongoDB | 27017 | Time-series database |
| Oracle XE | 1521 | Relational database |

## Useful Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Restart a service
```bash
docker-compose restart backend
```

### Stop all services
```bash
docker-compose down
```

### Stop and remove all data
```bash
docker-compose down -v
```

### Rebuild after code changes
```bash
docker-compose build backend
docker-compose up -d backend
```

## Troubleshooting

### Port conflicts
If ports are already in use, modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Change host port (left side)
```

### Database not ready
Wait longer for databases to initialize, or check logs:
```bash
docker-compose logs mongodb
docker-compose logs oracle-xe
```

### MQTT connection issues
Verify broker is running:
```bash
docker-compose logs mosquitto
```

## Next Steps

After setup is complete, the following tasks will implement:
- Task 2: Database schema and seed data
- Task 3: Backend data models and database clients
- Task 4: IoT simulator implementation
- And more...

Refer to `.kiro/specs/smart-city-iot-dashboard/tasks.md` for the complete implementation plan.
