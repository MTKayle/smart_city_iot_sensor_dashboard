"""
Utility modules for Smart City IoT Dashboard.
"""

from app.utils.aqi import calculate_aqi, get_aqi_category, AQIResult
from app.utils.spatial import (
    haversine_distance,
    haversine_distance_meters,
    find_nearby_sensors,
    identify_hotspots,
)

__all__ = [
    "calculate_aqi",
    "get_aqi_category",
    "AQIResult",
    "haversine_distance",
    "haversine_distance_meters",
    "find_nearby_sensors",
    "identify_hotspots",
]
