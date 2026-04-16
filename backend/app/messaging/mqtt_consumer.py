"""
MQTT Consumer Module for Smart City IoT Dashboard.

This module subscribes to MQTT telemetry topics, parses incoming sensor data,
validates it using Pydantic models, and processes valid messages.

Implements:
- Subscription to sensors/+/telemetry topic pattern
- JSON parsing and Pydantic validation
- Graceful error handling for invalid messages
- Reconnection logic with exponential backoff
- Configuration via environment variables

Requirements: 3.4, 3.5, 5.1, 5.2
"""

import json
import logging
import os
import time
from typing import Callable, Optional
from datetime import datetime

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from app.models import Telemetry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MQTTConsumer:
    """
    MQTT Consumer that subscribes to sensor telemetry topics and processes messages.
    
    Features:
    - Automatic reconnection with exponential backoff
    - Message validation using Pydantic models
    - Graceful error handling
    - Configurable telemetry processing handler
    """
    
    def __init__(
        self,
        broker_host: Optional[str] = None,
        broker_port: Optional[int] = None,
        telemetry_handler: Optional[Callable[[Telemetry], None]] = None
    ):
        """
        Initialize MQTT Consumer.
        
        Args:
            broker_host: MQTT broker hostname (defaults to MQTT_BROKER_HOST env var)
            broker_port: MQTT broker port (defaults to MQTT_BROKER_PORT env var)
            telemetry_handler: Callback function to process valid telemetry data
        """
        self.broker_host = broker_host or os.getenv('MQTT_BROKER_HOST', 'mosquitto')
        self.broker_port = broker_port or int(os.getenv('MQTT_BROKER_PORT', '1883'))
        self.telemetry_handler = telemetry_handler
        
        # Reconnection parameters
        self.reconnect_delay = 1  # Initial delay in seconds
        self.max_reconnect_delay = 60  # Maximum delay in seconds
        self.reconnect_attempts = 0
        
        # MQTT client setup
        self.client = mqtt.Client(client_id=f"backend_consumer_{int(time.time())}")
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Topic pattern for sensor telemetry
        self.topic_pattern = "sensors/+/telemetry"
        
        logger.info(
            f"MQTT Consumer initialized - Broker: {self.broker_host}:{self.broker_port}"
        )
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback when client connects to MQTT broker.
        
        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            rc: Connection result code
        """
        if rc == 0:
            logger.info("Successfully connected to MQTT broker")
            # Reset reconnection parameters on successful connection
            self.reconnect_delay = 1
            self.reconnect_attempts = 0
            
            # Subscribe to telemetry topic pattern
            client.subscribe(self.topic_pattern)
            logger.info(f"Subscribed to topic pattern: {self.topic_pattern}")
        else:
            logger.error(f"Failed to connect to MQTT broker - Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        Callback when client disconnects from MQTT broker.
        
        Args:
            client: MQTT client instance
            userdata: User data
            rc: Disconnection result code
        """
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker - Return code: {rc}")
            self._reconnect_with_backoff()
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _reconnect_with_backoff(self):
        """
        Attempt to reconnect to MQTT broker with exponential backoff.
        
        Implements exponential backoff strategy:
        - Initial delay: 1 second
        - Doubles after each failed attempt
        - Maximum delay: 60 seconds
        """
        self.reconnect_attempts += 1
        
        logger.info(
            f"Attempting reconnection #{self.reconnect_attempts} "
            f"in {self.reconnect_delay} seconds..."
        )
        
        time.sleep(self.reconnect_delay)
        
        try:
            self.client.reconnect()
            logger.info("Reconnection attempt initiated")
        except Exception as e:
            logger.error(f"Reconnection attempt failed: {e}")
        finally:
            # Exponential backoff: double the delay, up to max
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
    
    def _on_message(self, client, userdata, msg):
        """
        Callback when message is received from MQTT broker.
        
        Parses JSON payload, validates using Pydantic Telemetry model,
        and calls telemetry handler for valid messages.
        
        Args:
            client: MQTT client instance
            userdata: User data
            msg: MQTT message object
        """
        try:
            # Decode message payload
            payload_str = msg.payload.decode('utf-8')
            logger.debug(f"Received message on topic {msg.topic}: {payload_str[:100]}")
            
            # Parse JSON payload
            try:
                payload_dict = json.loads(payload_str)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Invalid JSON in message from topic {msg.topic}: {e}. "
                    f"Payload: {payload_str[:200]}"
                )
                return
            
            # Validate and parse into Telemetry object
            try:
                telemetry = Telemetry(**payload_dict)
                logger.debug(
                    f"Valid telemetry received - Sensor: {telemetry.sensorId}, "
                    f"CO2: {telemetry.co2}, Noise: {telemetry.noise}, "
                    f"Temp: {telemetry.temperature}"
                )
                
                # Call telemetry handler if configured
                if self.telemetry_handler:
                    self.telemetry_handler(telemetry)
                else:
                    logger.warning("No telemetry handler configured - message not processed")
                    
            except ValidationError as e:
                logger.error(
                    f"Validation error for message from topic {msg.topic}: {e}. "
                    f"Payload: {payload_str[:200]}"
                )
                return
                
        except Exception as e:
            logger.error(
                f"Unexpected error processing message from topic {msg.topic}: {e}",
                exc_info=True
            )
    
    def set_telemetry_handler(self, handler: Callable[[Telemetry], None]):
        """
        Set or update the telemetry processing handler.
        
        Args:
            handler: Callback function that receives validated Telemetry objects
        """
        self.telemetry_handler = handler
        logger.info("Telemetry handler updated")
    
    def connect(self):
        """
        Connect to MQTT broker and start message loop.
        
        This method blocks and runs the MQTT client loop indefinitely.
        Use connect_async() for non-blocking operation.
        """
        try:
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            
            # Start blocking loop
            logger.info("Starting MQTT client loop...")
            self.client.loop_forever()
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def connect_async(self):
        """
        Connect to MQTT broker and start non-blocking message loop.
        
        Use this method when running MQTT consumer alongside other services
        (e.g., FastAPI application).
        """
        try:
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            
            # Start non-blocking loop
            self.client.loop_start()
            logger.info("MQTT client loop started in background thread")
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def disconnect(self):
        """
        Disconnect from MQTT broker and stop message loop.
        """
        logger.info("Disconnecting from MQTT broker...")
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")


# Example usage and testing
if __name__ == "__main__":
    """
    Standalone execution for testing MQTT consumer.
    
    This will connect to the broker and print received telemetry data.
    """
    def example_handler(telemetry: Telemetry):
        """Example handler that prints telemetry data."""
        print(f"\n{'='*60}")
        print(f"Telemetry Received:")
        print(f"  Sensor ID: {telemetry.sensorId}")
        print(f"  Location ID: {telemetry.locationId}")
        print(f"  CO2: {telemetry.co2} ppm")
        print(f"  Noise: {telemetry.noise} dB")
        print(f"  Temperature: {telemetry.temperature} °C")
        print(f"  Timestamp: {telemetry.timestamp}")
        print(f"{'='*60}\n")
    
    # Create consumer with example handler
    consumer = MQTTConsumer(telemetry_handler=example_handler)
    
    try:
        # Connect and run (blocking)
        consumer.connect()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        consumer.disconnect()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        consumer.disconnect()
