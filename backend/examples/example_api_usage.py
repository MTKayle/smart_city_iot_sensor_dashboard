"""
Example usage of REST API endpoints.

This script demonstrates how to interact with the Smart City IoT Dashboard API.
Run the backend server first, then execute this script.

Usage:
    python examples/example_api_usage.py
"""

import requests
from datetime import datetime, timedelta
import json


# API base URL
BASE_URL = "http://localhost:8000/api"


def print_response(endpoint, response):
    """Pretty print API response."""
    print(f"\n{'='*80}")
    print(f"Endpoint: {endpoint}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, default=str))
    print('='*80)


def test_health_check():
    """Test health check endpoint."""
    print("\n1. Testing Health Check Endpoint")
    response = requests.get(f"{BASE_URL}/health")
    print_response("GET /api/health", response)


def test_locations():
    """Test locations endpoint."""
    print("\n2. Testing Locations Endpoint")
    response = requests.get(f"{BASE_URL}/locations")
    print_response("GET /api/locations", response)
    return response.json()


def test_sensors(location_id=None):
    """Test sensors endpoint."""
    print("\n3. Testing Sensors Endpoint")
    url = f"{BASE_URL}/sensors"
    if location_id:
        url += f"?location_id={location_id}"
    response = requests.get(url)
    print_response(f"GET /api/sensors", response)
    return response.json()


def test_telemetry(sensor_id):
    """Test telemetry endpoint."""
    print("\n4. Testing Telemetry Endpoint")
    
    # Test 1: Default (last 24 hours)
    print("\n4a. Get telemetry for last 24 hours (default)")
    response = requests.get(f"{BASE_URL}/telemetry/{sensor_id}")
    print_response(f"GET /api/telemetry/{sensor_id}", response)
    
    # Test 2: With time range
    print("\n4b. Get telemetry with custom time range")
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    response = requests.get(
        f"{BASE_URL}/telemetry/{sensor_id}",
        params={
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "limit": 50
        }
    )
    print_response(f"GET /api/telemetry/{sensor_id} (with time range)", response)
    
    # Test 3: Invalid time range (should return 400)
    print("\n4c. Test invalid time range (start > end)")
    response = requests.get(
        f"{BASE_URL}/telemetry/{sensor_id}",
        params={
            "start_time": end_time.isoformat(),
            "end_time": start_time.isoformat()
        }
    )
    print_response(f"GET /api/telemetry/{sensor_id} (invalid range)", response)


def test_analytics(sensor_id):
    """Test analytics endpoint."""
    print("\n5. Testing Analytics Endpoint")
    response = requests.get(f"{BASE_URL}/sensors/{sensor_id}/analytics")
    print_response(f"GET /api/sensors/{sensor_id}/analytics", response)


def test_alerts():
    """Test alerts endpoint."""
    print("\n6. Testing Alerts Endpoint")
    
    # Test 1: Get all alerts
    print("\n6a. Get all alerts")
    response = requests.get(f"{BASE_URL}/alerts")
    print_response("GET /api/alerts", response)
    
    # Test 2: Filter by level
    print("\n6b. Get HIGH level alerts only")
    response = requests.get(f"{BASE_URL}/alerts", params={"level": "HIGH", "limit": 10})
    print_response("GET /api/alerts?level=HIGH", response)
    
    # Test 3: Invalid level (should return 400)
    print("\n6c. Test invalid alert level")
    response = requests.get(f"{BASE_URL}/alerts", params={"level": "INVALID"})
    print_response("GET /api/alerts?level=INVALID", response)


def test_leaderboard():
    """Test leaderboard endpoint."""
    print("\n7. Testing Leaderboard Endpoint")
    response = requests.get(f"{BASE_URL}/leaderboard", params={"limit": 10})
    print_response("GET /api/leaderboard", response)


def main():
    """Run all API endpoint tests."""
    print("="*80)
    print("Smart City IoT Dashboard - REST API Examples")
    print("="*80)
    
    try:
        # 1. Health check
        test_health_check()
        
        # 2. Get locations
        locations = test_locations()
        
        # 3. Get sensors
        sensors = test_sensors()
        
        # If we have sensors, test sensor-specific endpoints
        if sensors and len(sensors) > 0:
            sensor_id = sensors[0]['sensorId']
            
            # 4. Get telemetry
            test_telemetry(sensor_id)
            
            # 5. Get analytics
            test_analytics(sensor_id)
        else:
            print("\nNo sensors found. Skipping sensor-specific tests.")
        
        # 6. Get alerts
        test_alerts()
        
        # 7. Get leaderboard
        test_leaderboard()
        
        print("\n" + "="*80)
        print("All API endpoint tests completed!")
        print("="*80)
        
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API server.")
        print("Make sure the backend server is running on http://localhost:8000")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
