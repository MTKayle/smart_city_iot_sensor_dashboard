# Smart City IoT Dashboard - Backend

Production-ready FastAPI backend for Smart City IoT sensor monitoring.

## Project Structure

```
backend/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   │
│   ├── core/                     # Core modules
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   └── websocket_manager.py  # WebSocket connection manager
│   │
│   ├── api/                      # API layer (routes & endpoints)
│   │   ├── __init__.py
│   │   ├── routes.py             # REST API routes
│   │   └── websocket.py          # WebSocket endpoint
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── telemetry_service.py  # Telemetry processing
│   │   ├── alert_service.py      # Alert generation & management
│   │   └── analytics_service.py  # Analytics calculations
│   │
│   ├── db/                       # Database clients
│   │   ├── __init__.py
│   │   ├── mongodb_client.py     # MongoDB operations
│   │   ├── oracle_client.py      # Oracle operations
│   │   └── sql/                  # SQL schema files
│   │       ├── oracle_schema.sql
│   │       └── oracle_seed.sql
│   │
│   ├── messaging/                # Message broker layer
│   │   ├── __init__.py
│   │   └── mqtt_consumer.py      # MQTT consumer
│   │
│   ├── models/                   # Pydantic data models
│   │   ├── __init__.py
│   │   ├── telemetry.py          # Telemetry model
│   │   ├── sensor.py             # Sensor & Location models
│   │   ├── alert.py              # Alert model
│   │   └── analytics.py          # Analytics models
│   │
│   └── utils/                    # Utility functions
│       └── __init__.py
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_mongodb.py
│   ├── test_oracle.py
│   ├── test_mqtt_consumer.py
│   └── test_mqtt_integration.py
│
├── examples/                     # Example usage scripts
│   ├── __init__.py
│   ├── example_mqtt.py
│   ├── example_oracle.py
│   └── example_telemetry.py
│
├── Dockerfile                    # Docker image definition
├── startup.sh                    # Container startup script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Architecture

### Layered Architecture

1. **API Layer** (`app/api/`)
   - REST endpoints for data retrieval
   - WebSocket endpoint for real-time updates
   - Request validation and response serialization

2. **Service Layer** (`app/services/`)
   - Business logic implementation
   - Telemetry processing
   - Alert generation with deduplication
   - Analytics calculations

3. **Data Access Layer** (`app/db/`)
   - MongoDB client for time-series telemetry
   - Oracle client for relational data
   - Connection pooling and retry logic

4. **Messaging Layer** (`app/messaging/`)
   - MQTT consumer for sensor data ingestion
   - Message validation and routing

5. **Core Layer** (`app/core/`)
   - Configuration management
   - WebSocket connection management
   - Shared utilities

### Data Flow

```
IoT Sensors → MQTT Broker → MQTT Consumer → Telemetry Service
                                                    ↓
                                            MongoDB (storage)
                                                    ↓
                                            Alert Service → Oracle (alerts)
                                                    ↓
                                            WebSocket Manager → Frontend
```

## Running the Backend

### Development Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MQTT_BROKER_HOST=localhost
export MONGODB_URI=mongodb://admin:password@localhost:27017
export ORACLE_DSN=localhost:1521/XEPDB1

# Run the application
python -m app.main
```

### Production Mode (Docker)

```bash
# Build and run with docker-compose
docker-compose up -d backend
```

## API Endpoints

### REST API

- `GET /` - Root endpoint with API information
- `GET /health` - Health check
- `GET /api/locations` - Get location hierarchy
- `GET /api/sensors` - Get registered sensors
- `GET /api/telemetry/{sensor_id}` - Get sensor telemetry
- `GET /api/alerts` - Get recent alerts
- `GET /api/leaderboard` - Get environmental quality rankings
- `GET /api/sensors/{sensor_id}/analytics` - Get sensor analytics

### WebSocket

- `WS /ws` - Real-time telemetry and alert updates

## Configuration

Configuration is managed via environment variables (see `.env.example`):

- `MQTT_BROKER_HOST` - MQTT broker hostname
- `MQTT_BROKER_PORT` - MQTT broker port
- `MONGODB_URI` - MongoDB connection string
- `ORACLE_USER` - Oracle username
- `ORACLE_PASSWORD` - Oracle password
- `ORACLE_DSN` - Oracle data source name

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=app tests/
```

## Development Guidelines

### Import Convention

Use absolute imports from the `app` package:

```python
from app.models import Telemetry
from app.services import get_telemetry_service
from app.db import get_mongodb_client
```

### Adding New Features

1. **Models**: Add to `app/models/` and export in `__init__.py`
2. **Services**: Add to `app/services/` for business logic
3. **API Routes**: Add to `app/api/routes.py`
4. **Tests**: Add to `tests/` with `test_` prefix

### Code Style

- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Add docstrings for all public functions and classes
- Keep functions focused and single-purpose

## Troubleshooting

### Import Errors

Ensure `PYTHONPATH` includes the backend directory:

```bash
export PYTHONPATH=/path/to/backend:$PYTHONPATH
```

### Database Connection Issues

Check that MongoDB and Oracle are running and accessible:

```bash
# Test MongoDB
mongosh $MONGODB_URI

# Test Oracle
sqlplus $ORACLE_USER/$ORACLE_PASSWORD@$ORACLE_DSN
```

### MQTT Connection Issues

Verify MQTT broker is running:

```bash
docker-compose logs mosquitto
```

## License

[Add your license here]
