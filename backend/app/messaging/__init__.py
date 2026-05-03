"""
Messaging layer for Smart City IoT Dashboard.

Exports:
- MQTTConsumer: MQTT subscriber that validates and enqueues telemetry
- TelemetryPipeline: Async worker pool for parallel processing
"""

from app.messaging.mqtt_consumer import MQTTConsumer
from app.messaging.worker_pool import TelemetryPipeline, get_telemetry_pipeline

__all__ = ["MQTTConsumer", "TelemetryPipeline", "get_telemetry_pipeline"]
