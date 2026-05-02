import os
import sys
import time
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.mongodb_client import get_mongodb_client, MongoDBClient
from app.models.telemetry import Telemetry, TelemetryData, GeoLocation

def test_mongodb():
    print("--- Testing MongoDB Client ---")
    
    # 1. Test index creation on startup
    print("1. Connecting and creating indexes...")
    client = get_mongodb_client()
    
    # Check if indexes exist
    indexes = client._collection.index_information()
    print("Current indexes:")
    for name, info in indexes.items():
        print(f" - {name}: {info['key']}")
    
    assert 'ttl_expire_at' in indexes
    assert 'sensor_timestamp_unique' in indexes
    assert 'location_timestamp_index' in indexes
    assert 'cluster_timestamp_index' in indexes
    assert 'location_2dsphere' in indexes
    print("PASS: All required indexes are created.")

    # Generate some mock telemetry data
    base_time = datetime.utcnow()
    telemetries = []
    
    # Sensor 1: District 1 (Cluster North)
    for i in range(10):
        t = Telemetry(
            sensorId="s1",
            locationId="district_1",
            clusterId="cluster_north",
            data=TelemetryData(co2=400+i, temperature=25),
            location=GeoLocation(coordinates=[106.7019, 10.7756]), # HCMC District 1
            timestamp=base_time - timedelta(minutes=i)
        )
        telemetries.append(t)
        
    # Sensor 2: District 3 (Cluster Central)
    for i in range(10):
        t = Telemetry(
            sensorId="s2",
            locationId="district_3",
            clusterId="cluster_central",
            data=TelemetryData(co2=450+i, temperature=26),
            location=GeoLocation(coordinates=[106.6828, 10.7866]), # HCMC District 3
            timestamp=base_time - timedelta(minutes=i)
        )
        telemetries.append(t)
        
    print(f"\n2. Testing batch insert of {len(telemetries)} documents...")
    client._collection.delete_many({"sensorId": {"$in": ["s1", "s2"]}}) # Clean up before test
    
    result = client.batch_insert_telemetry(telemetries)
    print(f"Batch insert result: {result}")
    assert result.inserted == 20
    assert result.duplicates == 0
    assert result.errors == 0
    print("PASS: Batch insert successful.")
    
    print("\n3. Testing duplicate detection...")
    # Insert exactly the same telemetries again
    dup_result = client.batch_insert_telemetry(telemetries)
    print(f"Duplicate insert result: {dup_result}")
    assert dup_result.inserted == 0
    assert dup_result.duplicates == 20
    print("PASS: Duplicate detection successful.")

    print("\n4. Testing cluster queries...")
    cluster_docs = client.get_cluster_telemetry("cluster_north", limit=5)
    print(f"Found {len(cluster_docs)} documents for cluster_north")
    assert len(cluster_docs) == 5
    for doc in cluster_docs:
        assert doc['clusterId'] == 'cluster_north'
    print("PASS: Cluster queries working.")

    print("\n5. Testing geospatial queries...")
    # Query near District 1 [106.7019, 10.7756] within 1km (1000m)
    # Distance between District 1 and District 3 coordinates is about ~2.4km
    nearby = client.find_nearby_sensors(106.7019, 10.7756, 1000)
    print(f"Found {len(nearby)} documents near District 1 within 1km")
    
    # It should find s1 documents but not s2
    sensor_ids = set([doc['sensorId'] for doc in nearby])
    print(f"Sensors found: {sensor_ids}")
    assert 's1' in sensor_ids
    assert 's2' not in sensor_ids
    print("PASS: Geospatial queries working.")
    
    # Clean up
    client._collection.delete_many({"sensorId": {"$in": ["s1", "s2"]}})
    print("\nAll MongoDB client tests complete!")

if __name__ == "__main__":
    test_mongodb()
