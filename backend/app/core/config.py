"""
Configuration management for Smart City IoT Dashboard.

This module loads and validates configuration from environment variables.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # MQTT Configuration
    mqtt_broker_host: str = "mosquitto"
    mqtt_broker_port: int = 1883
    
    # MongoDB Configuration
    mongodb_uri: str = "mongodb://admin:password@mongodb:27017"
    mongo_database: str = "smart_city_iot"
    mongo_username: str = "admin"
    mongo_password: str = "password"
    
    # Oracle Configuration
    oracle_user: str = "system"
    oracle_password: str = "OraclePass123"
    oracle_dsn: str = "oracle-xe:1521/XEPDB1"
    
    # Redis Configuration (durable message queue)
    redis_url: str = "redis://redis:6379/0"
    
    # API Configuration
    api_base_url: str = "http://localhost:8000"
    
    # CORS Configuration
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get singleton settings instance.
    
    Returns:
        Settings: Application settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
