"""
Example usage of Oracle client module.

This script demonstrates how to use the OracleClient for:
- Inserting locations, sensors, and alerts
- Querying location hierarchy
- Retrieving sensors and alerts

Note: This requires Oracle database to be running (via Docker Compose).
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import Location, Sensor, Alert
from app.db.oracle_client import get_oracle_client


def main():
    """Demonstrate Oracle client usage."""
    
    print("=" * 60)
    print("Oracle Client Usage Example")
    print("=" * 60)
    
    # Get singleton client instance
    client = get_oracle_client()
    print("\n✓ Connected to Oracle database")
    
    # Example 1: Insert a location
    print("\n1. Inserting a test location...")
    test_location = Location(
        locationId="test_ward_999",
        name="Test Ward 999",
        parentId="district_001",
        type="Ward"
    )
    
    success = client.insert_location(test_location)
    if success:
        print(f"   ✓ Inserted location: {test_location.locationId}")
    else:
        print(f"   ✗ Failed to insert location (may already exist)")
    
    # Example 2: Query location hierarchy
    print("\n2. Querying location hierarchy...")
    hierarchy = client.get_location_hierarchy()
    print(f"   ✓ Retrieved {len(hierarchy)} locations")
    if hierarchy:
        print(f"   Sample: {hierarchy[0]}")
    
    # Example 3: Insert a sensor
    print("\n3. Inserting a test sensor...")
    test_sensor = Sensor(
        sensorId="test_sensor_999",
        locationId="ward_001",
        sensorType="CO2",
        registeredAt=datetime.now()
    )
    
    success = client.insert_sensor(test_sensor)
    if success:
        print(f"   ✓ Inserted sensor: {test_sensor.sensorId}")
    else:
        print(f"   ✗ Failed to insert sensor (may already exist)")
    
    # Example 4: Query sensors
    print("\n4. Querying all sensors...")
    sensors = client.get_sensors()
    print(f"   ✓ Retrieved {len(sensors)} sensors")
    if sensors:
        print(f"   Sample: {sensors[0]}")
    
    # Example 5: Insert an alert
    print("\n5. Inserting a test alert...")
    test_alert = Alert(
        alertId=f"test_alert_{int(datetime.now().timestamp())}",
        sensorId="sensor_001",
        metricType="CO2",
        value=1250.0,
        level="HIGH",
        createdAt=datetime.now()
    )
    
    success = client.insert_alert(test_alert)
    if success:
        print(f"   ✓ Inserted alert: {test_alert.alertId}")
    else:
        print(f"   ✗ Failed to insert alert")
    
    # Example 6: Query alerts with filters
    print("\n6. Querying HIGH level alerts...")
    alerts = client.get_alerts(level="HIGH", limit=10)
    print(f"   ✓ Retrieved {len(alerts)} HIGH alerts")
    if alerts:
        print(f"   Sample: {alerts[0]}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nNote: Make sure Oracle database is running via Docker Compose:")
        print("  docker-compose up oracle-xe")
        sys.exit(1)
