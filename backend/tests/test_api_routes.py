"""
Unit tests for REST API routes.

Tests all API endpoints for correct behavior, error handling, and response formats.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.main import app
from app.models import Location, Sensor, Alert, Analytics, LeaderboardEntry, Telemetry, MovingAverage


# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint returns healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "smart-city-iot-backend"


class TestLocationsEndpoint:
    """Tests for locations endpoint."""
    
    @patch('app.api.routes.get_oracle_client')
    def test_get_locations_success(self, mock_get_oracle_client):
        """Test successful retrieval of location hierarchy."""
        # Mock Oracle client
        mock_oracle = Mock()
        mock_oracle.get_location_hierarchy.return_value = [
            {
                'locationid': 'city_hcm',
                'name': 'Ho Chi Minh City',
                'parentid': None,
                'type': 'City'
            },
            {
                'locationid': 'district_001',
                'name': 'District 1',
                'parentid': 'city_hcm',
                'type': 'District'
            }
        ]
        mock_get_oracle_client.return_value = mock_oracle
        
        response = client.get("/api/locations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['locationId'] == 'city_hcm'
        assert data[0]['type'] == 'City'
        assert data[1]['parentId'] == 'city_hcm'
    
    @patch('app.api.routes.get_oracle_client')
    def test_get_locations_error(self, mock_get_oracle_client):
        """Test error handling when database query fails."""
        mock_oracle = Mock()
        mock_oracle.get_location_hierarchy.side_effect = Exception("Database error")
        mock_get_oracle_client.return_value = mock_oracle
        
        response = client.get("/api/locations")
        assert response.status_code == 500
        assert "Failed to retrieve locations" in response.json()['detail']


class TestSensorsEndpoint:
    """Tests for sensors endpoint."""
    
    @patch('app.api.routes.get_oracle_client')
    def test_get_sensors_success(self, mock_get_oracle_client):
        """Test successful retrieval of sensors."""
        mock_oracle = Mock()
        mock_oracle.get_sensors.return_value = [
            {
                'sensorid': 'sensor_001',
                'locationid': 'ward_001',
                'sensortype': 'CO2',
                'registeredat': datetime(2024, 1, 1, 0, 0, 0)
            }
        ]
        mock_get_oracle_client.return_value = mock_oracle
        
        response = client.get("/api/sensors")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['sensorId'] == 'sensor_001'
        assert data[0]['sensorType'] == 'CO2'
    
    @patch('app.api.routes.get_oracle_client')
    def test_get_sensors_with_location_filter(self, mock_get_oracle_client):
        """Test sensors endpoint with location filter."""
        mock_oracle = Mock()
        mock_oracle.get_sensors.return_value = []
        mock_get_oracle_client.return_value = mock_oracle
        
        response = client.get("/api/sensors?location_id=ward_001")
        assert response.status_code == 200
        mock_oracle.get_sensors.assert_called_once_with(location_id='ward_001')


class TestTelemetryEndpoint:
    """Tests for telemetry endpoint."""
    
    @patch('app.api.routes.get_mongodb_client')
    def test_get_telemetry_success(self, mock_get_mongodb_client):
        """Test successful retrieval of telemetry data."""
        mock_mongodb = Mock()
        mock_mongodb.query_telemetry.return_value = [
            {
                'sensorId': 'sensor_001',
                'locationId': 'ward_001',
                'co2': 450.5,
                'noise': 65.2,
                'temperature': 25.3,
                'timestamp': datetime(2024, 1, 15, 10, 30, 0)
            }
        ]
        mock_get_mongodb_client.return_value = mock_mongodb
        
        response = client.get("/api/telemetry/sensor_001")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['sensorId'] == 'sensor_001'
        assert data[0]['co2'] == 450.5
    
    def test_get_telemetry_invalid_time_range(self):
        """Test validation of time range parameters."""
        start_time = datetime.utcnow()
        end_time = start_time - timedelta(hours=1)
        
        response = client.get(
            f"/api/telemetry/sensor_001?start_time={start_time.isoformat()}&end_time={end_time.isoformat()}"
        )
        assert response.status_code == 400
        assert "start_time must be less than end_time" in response.json()['detail']
    
    @patch('app.api.routes.get_mongodb_client')
    def test_get_telemetry_defaults_to_24_hours(self, mock_get_mongodb_client):
        """Test that telemetry endpoint defaults to last 24 hours."""
        mock_mongodb = Mock()
        mock_mongodb.query_telemetry.return_value = []
        mock_get_mongodb_client.return_value = mock_mongodb
        
        response = client.get("/api/telemetry/sensor_001")
        assert response.status_code == 200
        
        # Verify that query_telemetry was called with time range
        call_args = mock_mongodb.query_telemetry.call_args
        assert call_args[1]['start_time'] is not None
        assert call_args[1]['end_time'] is not None


class TestAlertsEndpoint:
    """Tests for alerts endpoint."""
    
    @patch('app.api.routes.get_oracle_client')
    def test_get_alerts_success(self, mock_get_oracle_client):
        """Test successful retrieval of alerts."""
        mock_oracle = Mock()
        mock_oracle.get_alerts.return_value = [
            {
                'alertid': 'alert_001',
                'sensorid': 'sensor_001',
                'metrictype': 'CO2',
                'value': 1250.0,
                'level': 'HIGH',
                'createdat': datetime(2024, 1, 15, 10, 30, 5)
            }
        ]
        mock_get_oracle_client.return_value = mock_oracle
        
        response = client.get("/api/alerts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['alertId'] == 'alert_001'
        assert data[0]['level'] == 'HIGH'
    
    def test_get_alerts_invalid_level(self):
        """Test validation of alert level parameter."""
        response = client.get("/api/alerts?level=INVALID")
        assert response.status_code == 400
        assert "Invalid alert level" in response.json()['detail']
    
    @patch('app.api.routes.get_oracle_client')
    def test_get_alerts_with_filters(self, mock_get_oracle_client):
        """Test alerts endpoint with filters."""
        mock_oracle = Mock()
        mock_oracle.get_alerts.return_value = []
        mock_get_oracle_client.return_value = mock_oracle
        
        response = client.get("/api/alerts?level=HIGH&location_id=ward_001&limit=50")
        assert response.status_code == 200
        mock_oracle.get_alerts.assert_called_once_with(
            level='HIGH',
            location_id='ward_001',
            limit=50
        )


class TestLeaderboardEndpoint:
    """Tests for leaderboard endpoint."""
    
    @patch('app.api.routes.get_oracle_client')
    def test_get_leaderboard_success(self, mock_get_oracle_client):
        """Test successful retrieval of leaderboard."""
        mock_oracle = Mock()
        mock_oracle.get_leaderboard.return_value = [
            {
                'locationid': 'ward_001',
                'locationname': 'Ward 1',
                'avgco2': 420.5,
                'avgnoise': 55.2,
                'avgtemperature': 26.3,
                'cleanscore': 85.5,
                'rank': 1
            }
        ]
        mock_get_oracle_client.return_value = mock_oracle
        
        response = client.get("/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['locationId'] == 'ward_001'
        assert data[0]['rank'] == 1
        assert data[0]['cleanScore'] == 85.5


class TestAnalyticsEndpoint:
    """Tests for analytics endpoint."""
    
    @patch('app.api.routes.get_analytics_service')
    def test_get_sensor_analytics_success(self, mock_get_analytics_service):
        """Test successful retrieval of sensor analytics."""
        mock_service = Mock()
        mock_analytics = Analytics(
            sensorId='sensor_001',
            co2_moving_avg=MovingAverage(
                metric='CO2',
                values=[450.5, 460.2, 455.8],
                average=455.5,
                window_size=3
            ),
            noise_moving_avg=MovingAverage(
                metric='Noise',
                values=[65.2, 67.1, 66.5],
                average=66.27,
                window_size=3
            ),
            temperature_moving_avg=MovingAverage(
                metric='Temperature',
                values=[25.3, 25.8, 25.5],
                average=25.53,
                window_size=3
            )
        )
        mock_service.calculate_moving_average.return_value = mock_analytics
        mock_get_analytics_service.return_value = mock_service
        
        response = client.get("/api/sensors/sensor_001/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data['sensorId'] == 'sensor_001'
        assert data['co2_moving_avg']['average'] == 455.5
    
    @patch('app.api.routes.get_analytics_service')
    def test_get_sensor_analytics_not_found(self, mock_get_analytics_service):
        """Test analytics endpoint when sensor has no data."""
        mock_service = Mock()
        mock_service.calculate_moving_average.return_value = None
        mock_get_analytics_service.return_value = mock_service
        
        response = client.get("/api/sensors/sensor_999/analytics")
        assert response.status_code == 404
        assert "No telemetry data found" in response.json()['detail']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
