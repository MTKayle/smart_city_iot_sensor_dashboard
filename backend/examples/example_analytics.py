"""
Example script demonstrating analytics service usage.

This script shows how to:
1. Insert sample telemetry data into MongoDB
2. Calculate moving averages using the analytics service
3. Handle edge cases (fewer than 10 readings)

Run: python -m backend.examples.example_analytics
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.telemetry import Telemetry
from app.services.analytics_service import get_analytics_service
from app.db.mongodb_client import get_mongodb_client


def main():
    """Demonstrate analytics service functionality."""
    
    print("=" * 60)
    print("Analytics Service Example")
    print("=" * 60)
    
    # Get service instances
    mongodb_client = get_mongodb_client()
    analytics_service = get_analytics_service()
    
    sensor_id = "test_sensor_analytics_001"
    location_id = "test_ward_001"
    
    print(f"\n1. Inserting sample telemetry data for sensor: {sensor_id}")
    print("-" * 60)
    
    # Insert 15 sample telemetry readings
    base_time = datetime.now()
    sample_data = [
        {"co2": 450.5, "noise": 65.2, "temperature": 25.3},
        {"co2": 460.2, "noise": 67.1, "temperature": 25.8},
        {"co2": 455.8, "noise": 66.5, "temperature": 25.5},
        {"co2": 470.1, "noise": 68.3, "temperature": 26.1},
        {"co2": 465.3, "noise": 67.8, "temperature": 25.9},
        {"co2": 458.9, "noise": 66.9, "temperature": 25.6},
        {"co2": 462.4, "noise": 67.5, "temperature": 25.7},
        {"co2": 467.2, "noise": 68.1, "temperature": 26.0},
        {"co2": 461.5, "noise": 67.2, "temperature": 25.8},
        {"co2": 459.7, "noise": 66.8, "temperature": 25.7},
        {"co2": 463.1, "noise": 67.4, "temperature": 25.9},
        {"co2": 468.5, "noise": 68.5, "temperature": 26.2},
        {"co2": 456.3, "noise": 66.1, "temperature": 25.4},
        {"co2": 464.8, "noise": 67.6, "temperature": 25.9},
        {"co2": 461.2, "noise": 67.0, "temperature": 25.8},
    ]
    
    for i, data in enumerate(sample_data):
        telemetry = Telemetry(
            sensorId=sensor_id,
            locationId=location_id,
            co2=data["co2"],
            noise=data["noise"],
            temperature=data["temperature"],
            timestamp=base_time - timedelta(minutes=15-i)  # Oldest to newest
        )
        
        success = mongodb_client.insert_telemetry(telemetry)
        if success:
            print(f"  ✓ Inserted reading {i+1}: CO2={data['co2']}, Noise={data['noise']}, Temp={data['temperature']}")
        else:
            print(f"  ✗ Failed to insert reading {i+1}")
    
    print(f"\n2. Calculating moving averages (window size = 10)")
    print("-" * 60)
    
    # Calculate moving averages
    analytics = analytics_service.calculate_moving_average(sensor_id)
    
    if analytics:
        print(f"\n✓ Analytics calculated successfully for sensor: {analytics.sensorId}")
        print(f"\nCO2 Moving Average:")
        print(f"  - Average: {analytics.co2_moving_avg.average} ppm")
        print(f"  - Window Size: {analytics.co2_moving_avg.window_size}")
        print(f"  - Values: {analytics.co2_moving_avg.values[:5]}... (showing first 5)")
        
        print(f"\nNoise Moving Average:")
        print(f"  - Average: {analytics.noise_moving_avg.average} dB")
        print(f"  - Window Size: {analytics.noise_moving_avg.window_size}")
        print(f"  - Values: {analytics.noise_moving_avg.values[:5]}... (showing first 5)")
        
        print(f"\nTemperature Moving Average:")
        print(f"  - Average: {analytics.temperature_moving_avg.average} °C")
        print(f"  - Window Size: {analytics.temperature_moving_avg.window_size}")
        print(f"  - Values: {analytics.temperature_moving_avg.values[:5]}... (showing first 5)")
    else:
        print("✗ Failed to calculate analytics")
    
    print(f"\n3. Testing edge case: sensor with fewer than 10 readings")
    print("-" * 60)
    
    # Test with a sensor that has only 3 readings
    sensor_id_small = "test_sensor_small_001"
    
    for i in range(3):
        telemetry = Telemetry(
            sensorId=sensor_id_small,
            locationId=location_id,
            co2=400.0 + i * 10,
            noise=60.0 + i * 2,
            temperature=24.0 + i * 0.5,
            timestamp=base_time - timedelta(minutes=3-i)
        )
        mongodb_client.insert_telemetry(telemetry)
    
    analytics_small = analytics_service.calculate_moving_average(sensor_id_small)
    
    if analytics_small:
        print(f"\n✓ Analytics calculated for sensor with limited data: {analytics_small.sensorId}")
        print(f"  - Window Size: {analytics_small.co2_moving_avg.window_size} (expected: 3)")
        print(f"  - CO2 Average: {analytics_small.co2_moving_avg.average} ppm")
        print(f"  - Noise Average: {analytics_small.noise_moving_avg.average} dB")
        print(f"  - Temperature Average: {analytics_small.temperature_moving_avg.average} °C")
    else:
        print("✗ Failed to calculate analytics for small dataset")
    
    print(f"\n4. Testing edge case: sensor with no data")
    print("-" * 60)
    
    analytics_none = analytics_service.calculate_moving_average("nonexistent_sensor")
    
    if analytics_none is None:
        print("✓ Correctly returned None for sensor with no data")
    else:
        print("✗ Expected None but got analytics object")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
