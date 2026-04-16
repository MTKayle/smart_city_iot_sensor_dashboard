"""
Example usage of Telemetry Handler with MQTT Consumer.

This script demonstrates how to integrate the telemetry handler with the MQTT consumer
to process incoming sensor data, store it in databases, and generate alerts.

Usage:
    python example_telemetry_handler_usage.py
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.messaging.mqtt_consumer import MQTTConsumer
from app.services import get_telemetry_service
from app.models import Telemetry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main function to run MQTT consumer with telemetry handler.
    
    This demonstrates the complete telemetry processing pipeline:
    1. MQTT consumer receives messages
    2. Validates telemetry data
    3. Telemetry handler processes data:
       - Stores in MongoDB
       - Checks alert thresholds
       - Creates alerts in Oracle
       - Broadcasts to WebSocket clients (if configured)
    """
    logger.info("Starting MQTT Consumer with Telemetry Handler...")
    
    # Get telemetry handler instance (without WebSocket for this example)
    telemetry_handler = get_telemetry_handler(websocket_manager=None)
    
    # Create MQTT consumer with telemetry handler
    consumer = MQTTConsumer(
        telemetry_handler=telemetry_service.process_telemetry
    )
    
    logger.info("=" * 70)
    logger.info("MQTT Consumer is running and processing telemetry data")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Telemetry Processing Pipeline:")
    logger.info("  1. Receive MQTT message on sensors/+/telemetry")
    logger.info("  2. Parse and validate JSON payload")
    logger.info("  3. Insert telemetry into MongoDB")
    logger.info("  4. Check alert thresholds:")
    logger.info("     - CO2 > 1000 ppm → HIGH alert")
    logger.info("     - Noise > 85 dB → HIGH alert")
    logger.info("  5. Create alerts in Oracle (with 5-minute deduplication)")
    logger.info("  6. Broadcast to WebSocket clients (if configured)")
    logger.info("")
    logger.info("Press Ctrl+C to stop...")
    logger.info("=" * 70)
    logger.info("")
    
    try:
        # Connect and run (blocking)
        consumer.connect()
    except KeyboardInterrupt:
        logger.info("\nReceived keyboard interrupt, shutting down...")
        consumer.disconnect()
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        consumer.disconnect()


if __name__ == "__main__":
    main()
