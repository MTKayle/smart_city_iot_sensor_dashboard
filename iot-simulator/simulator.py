#!/usr/bin/env python3
"""
IoT Sensor Simulator for Smart City Dashboard

Generates and publishes simulated sensor telemetry data to MQTT broker.
Supports multiple sensors with configurable publishing intervals.
"""

import os
import sys
import json
import time
import random
import logging
from datetime import datetime, timezone
from typing import List, Dict
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SensorSimulator:
    """Simulates IoT sensors publishing telemetry data via MQTT."""
    
    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        sensor_ids: List[str],
        publish_interval: int = 5
    ):
        """
        Initialize the sensor simulator.
        
        Args:
            broker_host: MQTT broker hostname or IP address
            broker_port: MQTT broker port number
            sensor_ids: List of sensor IDs to simulate
            publish_interval: Interval in seconds between publications
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.sensor_ids = sensor_ids
        self.publish_interval = publish_interval
        self.client = mqtt.Client()
        self.connected = False
        self.retry_delay = 1  # Initial retry delay in seconds
        self.max_retry_delay = 60  # Maximum retry delay
        
        # Set up MQTT callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        
        # Sensor location mapping (for realistic data)
        self.sensor_locations = self._initialize_sensor_locations()
    
    def _initialize_sensor_locations(self) -> Dict[str, str]:
        """
        Initialize sensor-to-location mapping.
        
        Parses HCMC sensor ID convention: sen_{district}_{ward}_{type}
        to derive ward location ID: ward_{district}_{ward}
        
        Returns:
            Dictionary mapping sensor IDs to location IDs
        """
        location_map = {}
        for sensor_id in self.sensor_ids:
            # Parse: sen_q1_01_co2 → ward_q1_01
            parts = sensor_id.split('_')
            if len(parts) >= 4 and parts[0] == 'sen':
                ward_id = f"ward_{parts[1]}_{parts[2]}"
                location_map[sensor_id] = ward_id
            else:
                # Fallback for old-style sensor IDs
                ward_num = (self.sensor_ids.index(sensor_id) % 5) + 1
                location_map[sensor_id] = f"ward_{ward_num:03d}"
        return location_map
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connection to MQTT broker is established."""
        if rc == 0:
            self.connected = True
            self.retry_delay = 1  # Reset retry delay on successful connection
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        else:
            self.connected = False
            logger.error(f"Connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker (code: {rc})")
    
    def _on_publish(self, client, userdata, mid):
        """Callback when message is published."""
        logger.debug(f"Message {mid} published successfully")
    
    def connect(self):
        """
        Connect to MQTT broker with exponential backoff retry logic.
        
        Implements exponential backoff: 1s, 2s, 4s, 8s, ..., up to 60s max.
        Retries indefinitely until connection is established.
        """
        while not self.connected:
            try:
                logger.info(f"Attempting to connect to MQTT broker at {self.broker_host}:{self.broker_port}")
                self.client.connect(self.broker_host, self.broker_port, keepalive=60)
                self.client.loop_start()
                
                # Wait for connection callback
                timeout = 10
                elapsed = 0
                while not self.connected and elapsed < timeout:
                    time.sleep(0.5)
                    elapsed += 0.5
                
                if not self.connected:
                    raise ConnectionError("Connection timeout")
                    
            except Exception as e:
                logger.error(f"Connection failed: {e}. Retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)
                
                # Exponential backoff with maximum cap
                self.retry_delay = min(self.retry_delay * 2, self.max_retry_delay)
    
    def generate_telemetry(self, sensor_id: str) -> Dict:
        """
        Generate random sensor telemetry data.
        
        Args:
            sensor_id: Sensor identifier
            
        Returns:
            Dictionary containing telemetry data
        """
        return {
            "sensorId": sensor_id,
            "locationId": self.sensor_locations.get(sensor_id, "ward_001"),
            "co2": round(random.uniform(300, 2000), 2),
            "noise": round(random.uniform(30, 100), 2),
            "temperature": round(random.uniform(15, 35), 2),
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
    
    def publish_telemetry(self, sensor_id: str):
        """
        Generate and publish telemetry data for a sensor.
        
        Args:
            sensor_id: Sensor identifier
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker. Skipping publish.")
            return
        
        telemetry = self.generate_telemetry(sensor_id)
        topic = f"sensors/{sensor_id}/telemetry"
        payload = json.dumps(telemetry)
        
        try:
            result = self.client.publish(topic, payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published to {topic}: CO2={telemetry['co2']:.1f}ppm, "
                          f"Noise={telemetry['noise']:.1f}dB, Temp={telemetry['temperature']:.1f}°C")
            else:
                logger.error(f"Failed to publish to {topic}: {result.rc}")
        except Exception as e:
            logger.error(f"Error publishing telemetry: {e}")
    
    def run(self):
        """
        Main loop: continuously publish telemetry data for all sensors.
        
        Publishes data at the configured interval until interrupted.
        """
        logger.info(f"Starting simulator for {len(self.sensor_ids)} sensors")
        logger.info(f"Publishing interval: {self.publish_interval} seconds")
        logger.info(f"Sensors: {', '.join(self.sensor_ids)}")
        
        try:
            while True:
                for sensor_id in self.sensor_ids:
                    self.publish_telemetry(sensor_id)
                
                time.sleep(self.publish_interval)
                
        except KeyboardInterrupt:
            logger.info("Simulator stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.disconnect()
    
    def disconnect(self):
        """Disconnect from MQTT broker and clean up resources."""
        logger.info("Disconnecting from MQTT broker...")
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False


def main():
    """Main entry point for the IoT simulator."""
    # Read configuration from environment variables
    broker_host = os.getenv("MQTT_BROKER_HOST", "mosquitto")
    broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    sensor_list = os.getenv("SENSOR_LIST", "sensor_001,sensor_002,sensor_003,sensor_004,sensor_005")
    publish_interval = int(os.getenv("PUBLISH_INTERVAL", "5"))
    
    # Parse sensor list
    sensor_ids = [s.strip() for s in sensor_list.split(",") if s.strip()]
    
    if not sensor_ids:
        logger.error("No sensors configured. Set SENSOR_LIST environment variable.")
        sys.exit(1)
    
    # Create and run simulator
    simulator = SensorSimulator(
        broker_host=broker_host,
        broker_port=broker_port,
        sensor_ids=sensor_ids,
        publish_interval=publish_interval
    )
    
    # Connect with retry logic
    simulator.connect()
    
    # Run main loop
    simulator.run()


if __name__ == "__main__":
    main()
