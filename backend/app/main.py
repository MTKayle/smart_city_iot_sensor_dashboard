"""
FastAPI application entry point for Smart City IoT Dashboard.

This module initializes the FastAPI application, registers routes,
and starts the MQTT consumer + TelemetryPipeline worker pool.

Data Flow (production):
    MQTT Broker → MQTTConsumer → AsyncQueue → Worker Pool (3) → ┐
                                                                 ├─ MongoDB (batch)
                                                                 ├─ Alert Engine → Oracle
                                                                 └─ WebSocket (broadcast)
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import get_settings, get_websocket_manager
from app.services.scheduler import get_analytics_scheduler
from app.messaging import MQTTConsumer, get_telemetry_pipeline
from app.api import routes, websocket


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global instances for lifecycle management
mqtt_consumer: MQTTConsumer = None
analytics_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Startup:
    1. Create WebSocket manager and bind event loop
    2. Create TelemetryPipeline (worker pool) and start workers
    3. Create MQTTConsumer with pipeline and start async loop
    4. Start analytics scheduler
    
    Shutdown:
    1. Disconnect MQTT consumer
    2. Stop TelemetryPipeline workers
    3. Shutdown analytics scheduler
    """
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("Starting Smart City IoT Dashboard Backend...")
    
    settings = get_settings()
    ws_manager = get_websocket_manager()
    ws_manager.loop = asyncio.get_running_loop()

    # 1. Create and start TelemetryPipeline (worker pool)
    pipeline = get_telemetry_pipeline(websocket_manager=ws_manager)
    await pipeline.start()
    logger.info("TelemetryPipeline worker pool started")

    # 2. Create MQTT consumer → routes to pipeline (NOT direct handler)
    global mqtt_consumer
    mqtt_consumer = MQTTConsumer(
        broker_host=settings.mqtt_broker_host,
        broker_port=settings.mqtt_broker_port,
        telemetry_pipeline=pipeline,
    )
    
    try:
        mqtt_consumer.connect_async()
        logger.info("MQTT consumer started → pipeline mode")
    except Exception as e:
        logger.error(f"Failed to start MQTT consumer: {e}")
    
    # 3. Start analytics scheduler
    global analytics_scheduler
    analytics_scheduler = get_analytics_scheduler()
    
    try:
        analytics_scheduler.start()
        logger.info("Analytics scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start analytics scheduler: {e}")
    
    logger.info("Backend startup complete")
    
    yield
    
    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Shutting down Smart City IoT Dashboard Backend...")
    
    if mqtt_consumer:
        mqtt_consumer.disconnect()
        logger.info("MQTT consumer disconnected")
    
    # Stop pipeline workers
    await pipeline.stop()
    logger.info("TelemetryPipeline stopped")
    
    if analytics_scheduler:
        analytics_scheduler.shutdown()
        logger.info("Analytics scheduler shutdown")
    
    logger.info("Backend shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Smart City IoT Dashboard API",
    description="REST API and WebSocket server for Smart City IoT sensor monitoring",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(routes.router)
app.include_router(websocket.router)

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        dict: Welcome message and API information
    """
    return {
        "message": "Smart City IoT Dashboard API",
        "version": "2.0.0",
        "docs": "/docs",
        "websocket": "/ws"
    }


@app.get("/pipeline/metrics")
async def pipeline_metrics():
    """
    Pipeline metrics endpoint.
    
    Returns worker pool stats: queue depth, messages processed, alerts created, etc.
    """
    pipeline = get_telemetry_pipeline()
    return pipeline.get_metrics()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
