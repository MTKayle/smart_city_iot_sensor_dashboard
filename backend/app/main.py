"""
FastAPI application entry point for Smart City IoT Dashboard.

This module initializes the FastAPI application, registers routes,
and starts the MQTT consumer for telemetry processing.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import get_settings, get_websocket_manager
from app.services import get_telemetry_service
from app.services.scheduler import get_analytics_scheduler
from app.messaging import MQTTConsumer
from app.api import routes, websocket


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# MQTT consumer instance (global for lifecycle management)
mqtt_consumer: MQTTConsumer = None

# Analytics scheduler instance (global for lifecycle management)
analytics_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize services and start MQTT consumer
    - Shutdown: Disconnect MQTT consumer
    """
    # Startup
    logger.info("Starting Smart City IoT Dashboard Backend...")
    
    settings = get_settings()
    ws_manager = get_websocket_manager()
    import asyncio
    ws_manager.loop = asyncio.get_running_loop()
    telemetry_service = get_telemetry_service(websocket_manager=ws_manager)
    
    # Initialize and start MQTT consumer
    global mqtt_consumer
    mqtt_consumer = MQTTConsumer(
        broker_host=settings.mqtt_broker_host,
        broker_port=settings.mqtt_broker_port,
        telemetry_handler=telemetry_service.process_telemetry
    )
    
    try:
        mqtt_consumer.connect_async()
        logger.info("MQTT consumer started successfully")
    except Exception as e:
        logger.error(f"Failed to start MQTT consumer: {e}")
    
    # Initialize and start analytics scheduler
    global analytics_scheduler
    analytics_scheduler = get_analytics_scheduler()
    
    try:
        analytics_scheduler.start()
        logger.info("Analytics scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start analytics scheduler: {e}")
    
    logger.info("Backend startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Smart City IoT Dashboard Backend...")
    
    if mqtt_consumer:
        mqtt_consumer.disconnect()
        logger.info("MQTT consumer disconnected")
    
    if analytics_scheduler:
        analytics_scheduler.shutdown()
        logger.info("Analytics scheduler shutdown")
    
    logger.info("Backend shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Smart City IoT Dashboard API",
    description="REST API and WebSocket server for Smart City IoT sensor monitoring",
    version="1.0.0",
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
        "version": "1.0.0",
        "docs": "/docs",
        "websocket": "/ws"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
