"""
Unit tests for Oracle client module.

Tests connection pooling, CRUD operations, and error handling.
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock cx_Oracle before importing oracle_client
sys.modules['cx_Oracle'] = MagicMock()

from app.models import Location, Sensor, Alert
from app.db.oracle_client import OracleClient, get_oracle_client


class TestOracleClient:
    """Test suite for OracleClient class."""
    
    @patch('db.oracle_client.cx_Oracle')
    def test_connection_initialization(self, mock_cx_oracle):
        """Test that connection pool is created on initialization."""
        # Setup mock
        mock_pool = MagicMock()
        mock_cx_oracle.SessionPool.return_value = mock_pool
        
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.acquire.return_value = mock_connection
        
        # Create client
        client = OracleClient()
        
        # Verify connection pool was created
        mock_cx_oracle.SessionPool.assert_called_once()
        assert client._pool is not None
    
    @patch('db.oracle_client.cx_Oracle')
    @patch('os.path.exists', return_value=False)  # Skip schema initialization
    def test_insert_location_success(self, mock_exists, mock_cx_oracle):
        """Test successful location insertion."""
        # Setup mock
        mock_pool = MagicMock()
        mock_cx_oracle.SessionPool.return_value = mock_pool
        
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.acquire.return_value = mock_connection
        
        # Create client
        client = OracleClient()
        
        # Create test location
        location = Location(
            locationId="test_001",
            name="Test Location",
            parentId=None,
            type="City"
        )
        
        # Insert location
        result = client.insert_location(location)
        
        # Verify
        assert result is True
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()
    
    @patch('db.oracle_client.cx_Oracle')
    @patch('os.path.exists', return_value=False)  # Skip schema initialization
    def test_insert_sensor_success(self, mock_exists, mock_cx_oracle):
        """Test successful sensor insertion."""
        # Setup mock
        mock_pool = MagicMock()
        mock_cx_oracle.SessionPool.return_value = mock_pool
        
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.acquire.return_value = mock_connection
        
        # Create client
        client = OracleClient()
        
        # Create test sensor
        sensor = Sensor(
            sensorId="sensor_001",
            locationId="ward_001",
            sensorType="CO2",
            registeredAt=datetime.now()
        )
        
        # Insert sensor
        result = client.insert_sensor(sensor)
        
        # Verify
        assert result is True
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()
    
    @patch('db.oracle_client.cx_Oracle')
    @patch('os.path.exists', return_value=False)  # Skip schema initialization
    def test_insert_alert_success(self, mock_exists, mock_cx_oracle):
        """Test successful alert insertion."""
        # Setup mock
        mock_pool = MagicMock()
        mock_cx_oracle.SessionPool.return_value = mock_pool
        
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.acquire.return_value = mock_connection
        
        # Create client
        client = OracleClient()
        
        # Create test alert
        alert = Alert(
            alertId="alert_001",
            sensorId="sensor_001",
            metricType="CO2",
            value=1250.0,
            level="HIGH",
            createdAt=datetime.now()
        )
        
        # Insert alert
        result = client.insert_alert(alert)
        
        # Verify
        assert result is True
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()
    
    @patch('db.oracle_client.cx_Oracle')
    def test_get_location_hierarchy(self, mock_cx_oracle):
        """Test retrieving location hierarchy."""
        # Setup mock
        mock_pool = MagicMock()
        mock_cx_oracle.SessionPool.return_value = mock_pool
        
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.acquire.return_value = mock_connection
        
        # Mock cursor description and results
        mock_cursor.description = [
            ('LOCATIONID',), ('NAME',), ('PARENTID',), ('TYPE',), ('PATH',), ('LEVEL',)
        ]
        mock_cursor.__iter__ = Mock(return_value=iter([
            ('city_hcm', 'Ho Chi Minh City', None, 'City', 'city_hcm', 0),
            ('district_001', 'District 1', 'city_hcm', 'District', 'city_hcm > district_001', 1)
        ]))
        
        # Create client
        client = OracleClient()
        
        # Get hierarchy
        results = client.get_location_hierarchy()
        
        # Verify
        assert len(results) == 2
        assert results[0]['locationid'] == 'city_hcm'
        assert results[1]['locationid'] == 'district_001'
    
    @patch('db.oracle_client.cx_Oracle')
    def test_get_sensors(self, mock_cx_oracle):
        """Test retrieving sensors."""
        # Setup mock
        mock_pool = MagicMock()
        mock_cx_oracle.SessionPool.return_value = mock_pool
        
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.acquire.return_value = mock_connection
        
        # Mock cursor description and results
        mock_cursor.description = [
            ('SENSORID',), ('LOCATIONID',), ('SENSORTYPE',), 
            ('REGISTEREDAT',), ('LOCATIONNAME',), ('LOCATIONTYPE',)
        ]
        mock_cursor.__iter__ = Mock(return_value=iter([
            ('sensor_001', 'ward_001', 'CO2', datetime.now(), 'Ward 1', 'Ward')
        ]))
        
        # Create client
        client = OracleClient()
        
        # Get sensors
        results = client.get_sensors()
        
        # Verify
        assert len(results) == 1
        assert results[0]['sensorid'] == 'sensor_001'
    
    @patch('db.oracle_client.cx_Oracle')
    def test_get_alerts_with_filters(self, mock_cx_oracle):
        """Test retrieving alerts with filters."""
        # Setup mock
        mock_pool = MagicMock()
        mock_cx_oracle.SessionPool.return_value = mock_pool
        
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.acquire.return_value = mock_connection
        
        # Mock cursor description and results
        mock_cursor.description = [
            ('ALERTID',), ('SENSORID',), ('METRICTYPE',), ('VALUE',),
            ('LEVEL',), ('CREATEDAT',), ('LOCATIONID',), ('LOCATIONNAME',)
        ]
        mock_cursor.__iter__ = Mock(return_value=iter([
            ('alert_001', 'sensor_001', 'CO2', 1250.0, 'HIGH', datetime.now(), 'ward_001', 'Ward 1')
        ]))
        
        # Create client
        client = OracleClient()
        
        # Get alerts with level filter
        results = client.get_alerts(level='HIGH')
        
        # Verify
        assert len(results) == 1
        assert results[0]['alertid'] == 'alert_001'
        assert results[0]['level'] == 'HIGH'
    
    @patch('db.oracle_client.cx_Oracle')
    @patch('os.path.exists', return_value=False)  # Skip schema initialization
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_connection_retry_on_failure(self, mock_sleep, mock_exists, mock_cx_oracle):
        """Test exponential backoff retry on connection failure."""
        # Setup mock to fail first attempt, succeed on second
        mock_pool = MagicMock()
        
        # Create a mock DatabaseError
        db_error = Exception("Connection failed")
        mock_cx_oracle.DatabaseError = Exception
        
        mock_cx_oracle.SessionPool.side_effect = [
            db_error,
            mock_pool
        ]
        
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.acquire.return_value = mock_connection
        
        # Create client (should retry and succeed)
        client = OracleClient()
        
        # Verify retry occurred
        assert mock_cx_oracle.SessionPool.call_count == 2
    
    @patch('db.oracle_client.cx_Oracle')
    def test_singleton_pattern(self, mock_cx_oracle):
        """Test that get_oracle_client returns singleton instance."""
        # Setup mock
        mock_pool = MagicMock()
        mock_cx_oracle.SessionPool.return_value = mock_pool
        
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.acquire.return_value = mock_connection
        
        # Get client twice
        client1 = get_oracle_client()
        client2 = get_oracle_client()
        
        # Verify same instance
        assert client1 is client2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
