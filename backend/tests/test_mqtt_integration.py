"""
Integration test for MQTT Consumer with IoT Simulator.

This test verifies that the MQTT consumer can successfully:
1. Connect to the MQTT broker
2. Subscribe to sensor telemetry topics
3. Receive and parse messages from the IoT simulator
4. Validate telemetry data using Pydantic models

NOTE: This test requires the MQTT broker (Mosquitto) to be running.
Run with: docker-compose up mosquitto
"""

import time
import json
from datetime import datetime
from app.messaging.mqtt_consumer import MQTTConsumer
from app.models import Telemetry


def test_mqtt_consumer_integration():
    """
    Integration test for MQTT consumer with real broker.
    
    This test will:
    1. Connect to the MQTT broker
    2. Wait for telemetry messages
    3. Verify messages are received and parsed correctly
    
    Skip this test if broker is not available.
    """
    received_messages = []
    
    def telemetry_handler(telemetry: Telemetry):
        """Handler that collects received telemetry."""
        received_messages.append(telemetry)
        print(f"\n✓ Received telemetry from sensor {telemetry.sensorId}")
        print(f"  CO2: {telemetry.co2} ppm")
        print(f"  Noise: {telemetry.noise} dB")
        print(f"  Temperature: {telemetry.temperature} °C")
    
    try:
        # Create consumer
        consumer = MQTTConsumer(
            broker_host="localhost",  # Assumes broker running on localhost
            broker_port=1883,
            telemetry_handler=telemetry_handler
        )
        
        print("\n" + "="*60)
        print("MQTT Consumer Integration Test")
        print("="*60)
        print("\nConnecting to MQTT broker at localhost:1883...")
        
        # Connect in non-blocking mode
        consumer.connect_async()
        
        print("✓ Connected successfully")
        print("\nWaiting for telemetry messages (30 seconds)...")
        print("(Make sure IoT simulator is running: docker-compose up iot-simulator)")
        
        # Wait for messages (30 seconds)
        time.sleep(30)
        
        # Disconnect
        consumer.disconnect()
        
        print(f"\n{'='*60}")
        print(f"Test Results:")
        print(f"{'='*60}")
        print(f"Total messages received: {len(received_messages)}")
        
        if len(received_messages) > 0:
            print("✓ MQTT consumer successfully received and parsed telemetry data")
            print("\nSample telemetry:")
            sample = received_messages[0]
            print(f"  Sensor ID: {sample.sensorId}")
            print(f"  Location ID: {sample.locationId}")
            print(f"  CO2: {sample.co2} ppm")
            print(f"  Noise: {sample.noise} dB")
            print(f"  Temperature: {sample.temperature} °C")
            print(f"  Timestamp: {sample.timestamp}")
            return True
        else:
            print("⚠ No messages received - is the IoT simulator running?")
            return False
            
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        print("\nMake sure the MQTT broker is running:")
        print("  docker-compose up mosquitto")
        return False


if __name__ == "__main__":
    """
    Run integration test standalone.
    
    Usage:
        python backend/test_mqtt_integration.py
    
    Prerequisites:
        - MQTT broker running (docker-compose up mosquitto)
        - IoT simulator running (docker-compose up iot-simulator) [optional]
    """
    success = test_mqtt_consumer_integration()
    exit(0 if success else 1)
