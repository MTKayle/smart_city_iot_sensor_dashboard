"""
Example usage of MQTT Consumer module.

This script demonstrates how to use the MQTTConsumer class to:
1. Connect to the MQTT broker
2. Subscribe to sensor telemetry topics
3. Process incoming telemetry data
4. Handle the data (e.g., store in database, trigger alerts)

Usage:
    python backend/example_mqtt_usage.py

Prerequisites:
    - MQTT broker running (docker-compose up mosquitto)
    - IoT simulator running (docker-compose up iot-simulator) [optional]
"""

import os
from datetime import datetime
from app.messaging.mqtt_consumer import MQTTConsumer
from app.models import Telemetry


def process_telemetry(telemetry: Telemetry):
    """
    Process received telemetry data.
    
    In a real application, this function would:
    - Store telemetry in MongoDB
    - Check alert thresholds
    - Create alerts in Oracle if thresholds exceeded
    - Broadcast updates via WebSocket
    
    Args:
        telemetry: Validated Telemetry object
    """
    print(f"\n{'='*70}")
    print(f"Processing Telemetry Data")
    print(f"{'='*70}")
    print(f"Sensor ID:    {telemetry.sensorId}")
    print(f"Location ID:  {telemetry.locationId}")
    print(f"CO2:          {telemetry.co2:.2f} ppm")
    print(f"Noise:        {telemetry.noise:.2f} dB")
    print(f"Temperature:  {telemetry.temperature:.2f} °C")
    print(f"Timestamp:    {telemetry.timestamp}")
    
    # Check alert thresholds
    alerts = []
    if telemetry.co2 > 1000:
        alerts.append(f"⚠ HIGH CO2 ALERT: {telemetry.co2} ppm (threshold: 1000 ppm)")
    if telemetry.noise > 85:
        alerts.append(f"⚠ HIGH NOISE ALERT: {telemetry.noise} dB (threshold: 85 dB)")
    
    if alerts:
        print(f"\n{'*'*70}")
        for alert in alerts:
            print(alert)
        print(f"{'*'*70}")
    
    # In real implementation, you would:
    # 1. Insert into MongoDB: mongodb_client.insert_telemetry(telemetry)
    # 2. Create alerts: oracle_client.create_alert(alert_data)
    # 3. Broadcast via WebSocket: websocket_manager.broadcast(telemetry)


def main():
    """
    Main function to run MQTT consumer.
    """
    print("\n" + "="*70)
    print("Smart City IoT Dashboard - MQTT Consumer Example")
    print("="*70)
    
    # Get configuration from environment variables
    broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
    broker_port = int(os.getenv('MQTT_BROKER_PORT', '1883'))
    
    print(f"\nConfiguration:")
    print(f"  MQTT Broker: {broker_host}:{broker_port}")
    print(f"  Topic Pattern: sensors/+/telemetry")
    
    # Create MQTT consumer with telemetry handler
    consumer = MQTTConsumer(
        broker_host=broker_host,
        broker_port=broker_port,
        telemetry_handler=process_telemetry
    )
    
    print(f"\nStarting MQTT consumer...")
    print(f"Press Ctrl+C to stop\n")
    
    try:
        # Connect and run (blocking)
        consumer.connect()
    except KeyboardInterrupt:
        print("\n\nReceived keyboard interrupt, shutting down...")
        consumer.disconnect()
        print("✓ MQTT consumer stopped successfully")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        consumer.disconnect()
        exit(1)


if __name__ == "__main__":
    main()
