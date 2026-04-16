# IoT Sensor Simulator

Python-based IoT sensor simulator that generates and publishes simulated environmental telemetry data to an MQTT broker.

## Features

- Generates realistic sensor data for CO2, Noise, and Temperature
- Publishes to MQTT broker using paho-mqtt library
- Configurable via environment variables
- Exponential backoff retry logic for connection failures
- Supports multiple sensors simultaneously
- Comprehensive logging

## Requirements

- Python 3.8+
- paho-mqtt 1.6.1
- python-dotenv 1.0.0

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Configure the simulator using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_BROKER_HOST` | MQTT broker hostname or IP | `mosquitto` |
| `MQTT_BROKER_PORT` | MQTT broker port | `1883` |
| `SENSOR_LIST` | Comma-separated sensor IDs | `sensor_001,sensor_002,sensor_003,sensor_004,sensor_005` |
| `PUBLISH_INTERVAL` | Seconds between publications | `5` |

## Usage

### Standalone

```bash
# Set environment variables
export MQTT_BROKER_HOST=localhost
export MQTT_BROKER_PORT=1883
export SENSOR_LIST=sensor_001,sensor_002,sensor_003
export PUBLISH_INTERVAL=5

# Run simulator
python simulator.py
```

### Docker

```bash
# Build image
docker build -t iot-simulator .

# Run container
docker run -e MQTT_BROKER_HOST=mosquitto \
           -e SENSOR_LIST=sensor_001,sensor_002 \
           iot-simulator
```

### Docker Compose

The simulator is included in the main `docker-compose.yml`:

```bash
docker-compose up iot-simulator
```

## Data Format

The simulator publishes JSON messages to topic `sensors/{sensorId}/telemetry`:

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

### Value Ranges

- **CO2**: 300-2000 ppm (parts per million)
- **Noise**: 30-100 dB (decibels)
- **Temperature**: 15-35°C (degrees Celsius)

## Connection Retry Logic

The simulator implements exponential backoff for connection failures:

- Initial retry delay: 1 second
- Maximum retry delay: 60 seconds
- Retry sequence: 1s → 2s → 4s → 8s → 16s → 32s → 60s (max)
- Retries indefinitely until connection succeeds

## Testing

Run unit tests:

```bash
pytest test_simulator.py -v
```

## Logging

The simulator logs all activities to stdout:

- Connection attempts and status
- Published telemetry data
- Errors and warnings
- Disconnection events

Log level can be adjusted in the code (default: INFO).

## Architecture

```
┌─────────────────┐
│  IoT Simulator  │
│                 │
│  - Generate     │
│    telemetry    │
│  - Publish via  │
│    MQTT         │
└────────┬────────┘
         │
         │ MQTT Protocol
         │ Topic: sensors/{id}/telemetry
         │
         ▼
┌─────────────────┐
│  MQTT Broker    │
│  (Mosquitto)    │
└─────────────────┘
```

## License

Part of the Smart City IoT Sensor Dashboard project.
