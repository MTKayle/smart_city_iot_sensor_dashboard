# MQTT Consumer Module

## Overview

The MQTT Consumer module (`mqtt_consumer.py`) is responsible for subscribing to IoT sensor telemetry topics, parsing incoming messages, validating data, and processing valid telemetry readings.

## Features

- **Topic Subscription**: Subscribes to `sensors/+/telemetry` wildcard pattern to receive messages from all sensors
- **JSON Parsing**: Parses incoming JSON payloads into structured data
- **Pydantic Validation**: Validates telemetry data using Pydantic models with strict type checking and range validation
- **Error Handling**: Gracefully handles invalid messages without crashing, logging descriptive errors
- **Reconnection Logic**: Implements exponential backoff for automatic reconnection (1s → 2s → 4s → 8s → ... → 60s max)
- **Configurable Handler**: Allows custom telemetry processing logic via callback function
- **Environment Configuration**: Reads broker settings from environment variables

## Requirements

This module implements the following requirements:
- **Requirement 3.4**: Backend Consumer subscribes to MQTT broker and receives messages within 1 second
- **Requirement 3.5**: Backend Consumer parses telemetry messages with all required fields
- **Requirement 5.1**: Parse telemetry messages into Telemetry objects
- **Requirement 5.2**: Log validation errors for invalid messages without crashing

## Installation

The required dependencies are already in `backend/requirements.txt`:

```bash
paho-mqtt==1.6.1
pydantic==2.5.3
```

## Usage

### Basic Usage

```python
from mqtt_consumer import MQTTConsumer
from models import Telemetry

def handle_telemetry(telemetry: Telemetry):
    """Process received telemetry data."""
    print(f"Received: {telemetry.sensorId} - CO2: {telemetry.co2} ppm")
    # Store in database, check alerts, etc.

# Create consumer
consumer = MQTTConsumer(
    broker_host="localhost",
    broker_port=1883,
    telemetry_handler=handle_telemetry
)

# Connect and run (blocking)
consumer.connect()
```

### Non-Blocking Usage (with FastAPI)

```python
from mqtt_consumer import MQTTConsumer
from fastapi import FastAPI

app = FastAPI()
consumer = MQTTConsumer(telemetry_handler=process_telemetry)

@app.on_event("startup")
async def startup_event():
    """Start MQTT consumer when FastAPI starts."""
    consumer.connect_async()  # Non-blocking

@app.on_event("shutdown")
async def shutdown_event():
    """Stop MQTT consumer when FastAPI shuts down."""
    consumer.disconnect()
```

### Environment Variables

The module reads configuration from environment variables:

- `MQTT_BROKER_HOST`: MQTT broker hostname (default: `mosquitto`)
- `MQTT_BROKER_PORT`: MQTT broker port (default: `1883`)

Example `.env` file:

```bash
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
```

## API Reference

### MQTTConsumer Class

#### Constructor

```python
MQTTConsumer(
    broker_host: Optional[str] = None,
    broker_port: Optional[int] = None,
    telemetry_handler: Optional[Callable[[Telemetry], None]] = None
)
```

**Parameters:**
- `broker_host`: MQTT broker hostname (defaults to `MQTT_BROKER_HOST` env var)
- `broker_port`: MQTT broker port (defaults to `MQTT_BROKER_PORT` env var)
- `telemetry_handler`: Callback function to process valid telemetry data

#### Methods

##### `connect()`

Connect to MQTT broker and start blocking message loop.

```python
consumer.connect()  # Blocks until disconnected
```

##### `connect_async()`

Connect to MQTT broker and start non-blocking message loop in background thread.

```python
consumer.connect_async()  # Returns immediately
```

##### `disconnect()`

Disconnect from MQTT broker and stop message loop.

```python
consumer.disconnect()
```

##### `set_telemetry_handler(handler)`

Set or update the telemetry processing handler.

```python
def new_handler(telemetry: Telemetry):
    print(f"New handler: {telemetry.sensorId}")

consumer.set_telemetry_handler(new_handler)
```

## Message Format

The MQTT consumer expects messages on topic `sensors/{sensorId}/telemetry` with the following JSON format:

```json
{
    "sensorId": "sensor_001",
    "locationId": "ward_001",
    "co2": 450.5,
    "noise": 65.2,
    "temperature": 25.3,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Validation Rules

- `sensorId`: Non-empty string
- `locationId`: Non-empty string
- `co2`: Float, 0 ≤ value ≤ 5000 ppm
- `noise`: Float, 0 ≤ value ≤ 120 dB
- `temperature`: Float, -50 ≤ value ≤ 60 °C
- `timestamp`: ISO 8601 datetime string

## Error Handling

### Invalid JSON

```python
# Message: "{ invalid json }"
# Result: Logged error, message skipped, consumer continues
```

### Missing Required Field

```python
# Message: {"locationId": "ward_001", "co2": 450.5, ...}  # Missing sensorId
# Result: Validation error logged, message skipped, consumer continues
```

### Out-of-Range Values

```python
# Message: {"sensorId": "sensor_001", "co2": -100, ...}  # Negative CO2
# Result: Validation error logged, message skipped, consumer continues
```

### Connection Loss

```python
# Broker disconnects unexpectedly
# Result: Automatic reconnection with exponential backoff (1s, 2s, 4s, 8s, ..., 60s max)
```

## Reconnection Logic

The consumer implements exponential backoff for reconnection:

1. **Initial delay**: 1 second
2. **Exponential increase**: Delay doubles after each attempt (1s → 2s → 4s → 8s → 16s → 32s → 60s)
3. **Maximum delay**: 60 seconds
4. **Infinite retries**: Continues attempting reconnection indefinitely
5. **Reset on success**: Delay resets to 1 second on successful connection

## Testing

### Unit Tests

Run unit tests with pytest:

```bash
pytest backend/test_mqtt_consumer.py -v
```

**Test Coverage:**
- Message parsing with valid payloads ✓
- Rejection of malformed JSON ✓
- Handling of missing required fields ✓
- Validation of CO2, noise, temperature ranges ✓
- Telemetry handler invocation ✓
- Connection success/failure callbacks ✓
- Reconnection with exponential backoff ✓

### Integration Test

Run integration test (requires running MQTT broker):

```bash
# Start MQTT broker
docker-compose up mosquitto

# Run integration test
python backend/test_mqtt_integration.py
```

## Examples

### Example 1: Standalone Consumer

```bash
python backend/example_mqtt_usage.py
```

This example demonstrates:
- Connecting to MQTT broker
- Processing telemetry data
- Checking alert thresholds
- Graceful shutdown on Ctrl+C

### Example 2: Integration with Database

```python
from mqtt_consumer import MQTTConsumer
from db.mongodb_client import MongoDBClient
from db.oracle_client import OracleClient

# Initialize database clients
mongo_client = MongoDBClient()
oracle_client = OracleClient()

def process_telemetry(telemetry: Telemetry):
    # Store in MongoDB
    mongo_client.insert_telemetry(telemetry)
    
    # Check alert thresholds
    if telemetry.co2 > 1000:
        oracle_client.create_alert(
            sensor_id=telemetry.sensorId,
            metric_type="CO2",
            value=telemetry.co2,
            level="HIGH"
        )

consumer = MQTTConsumer(telemetry_handler=process_telemetry)
consumer.connect()
```

## Logging

The module uses Python's `logging` module with the following levels:

- **INFO**: Connection events, subscription confirmations
- **DEBUG**: Individual message processing (disabled by default)
- **WARNING**: Unexpected disconnections, missing handler
- **ERROR**: JSON parsing errors, validation errors, connection failures

Configure logging in your application:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Troubleshooting

### Consumer not receiving messages

1. Check MQTT broker is running:
   ```bash
   docker-compose ps mosquitto
   ```

2. Verify broker connectivity:
   ```bash
   docker-compose exec mosquitto mosquitto_sub -t 'sensors/#' -v
   ```

3. Check environment variables:
   ```bash
   echo $MQTT_BROKER_HOST
   echo $MQTT_BROKER_PORT
   ```

### Validation errors

Check message format matches expected schema:
```bash
# Publish test message
docker-compose exec mosquitto mosquitto_pub -t 'sensors/test/telemetry' -m '{
  "sensorId": "test",
  "locationId": "ward_001",
  "co2": 450.5,
  "noise": 65.2,
  "temperature": 25.3,
  "timestamp": "2024-01-15T10:30:00Z"
}'
```

### Connection refused

1. Ensure broker is running on correct host/port
2. Check Docker network connectivity
3. Verify firewall rules allow port 1883

## Architecture Integration

The MQTT Consumer is part of the Smart City IoT Dashboard architecture:

```
IoT Simulator → MQTT Broker → MQTT Consumer → [MongoDB, Oracle, WebSocket]
                                    ↓
                            Telemetry Handler
                                    ↓
                    [Store, Alert Check, Broadcast]
```

## Next Steps

After implementing the MQTT consumer (Task 5.1), the next tasks are:

- **Task 5.2**: Implement telemetry processing handler
  - Store telemetry in MongoDB
  - Check alert thresholds
  - Create alerts in Oracle
  - Broadcast via WebSocket

- **Task 5.3**: Integrate MQTT consumer with FastAPI application
  - Start consumer on application startup
  - Stop consumer on application shutdown
  - Share database clients between REST API and MQTT consumer

## License

Part of the Smart City IoT Sensor Dashboard project.
