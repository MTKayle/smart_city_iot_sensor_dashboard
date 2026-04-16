"""
Unit tests for MongoDB client module.

Tests connection, insertion, querying, and index creation functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.models import Telemetry
from app.db.mongodb_client import MongoDBClient, get_mongodb_client


class TestMongoDBClient:
    """Unit tests for MongoDBClient class."""
    
    @patch('db.mongodb_client.MongoClient')
    def test_connection_success(self, mock_mongo_client):
        """Test successful MongoDB connection."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_mongo_client.return_value = mock_client_instance
        
        # Create client
        client = MongoDBClient()
        
        # Verify connection was attempted
        mock_mongo_client.assert_called_once()
        mock_client_instance.admin.command.assert_called_with('ping')
    
    @patch('db.mongodb_client.MongoClient')
    def test_insert_telemetry_success(self, mock_mongo_client):
        """Test successful telemetry insertion."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_collection = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = "test_id"
        mock_collection.insert_one.return_value = mock_result
        mock_client_instance.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_mongo_client.return_value = mock_client_instance
        
        # Create client and insert telemetry
        client = MongoDBClient()
        telemetry = Telemetry(
            sensorId="sensor_001",
            locationId="ward_001",
            co2=450.5,
            noise=65.2,
            temperature=25.3,
            timestamp=datetime.now()
        )
        
        result = client.insert_telemetry(telemetry)
        
        # Verify insertion
        assert result is True
        mock_collection.insert_one.assert_called_once()
    
    @patch('db.mongodb_client.MongoClient')
    def test_query_telemetry_with_time_range(self, mock_mongo_client):
        """Test querying telemetry with time range filters."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_collection = MagicMock()
        
        # Mock cursor
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__.return_value = iter([
            {
                "_id": "test_id",
                "sensorId": "sensor_001",
                "locationId": "ward_001",
                "co2": 450.5,
                "noise": 65.2,
                "temperature": 25.3,
                "timestamp": datetime.now()
            }
        ])
        mock_collection.find.return_value = mock_cursor
        
        mock_client_instance.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_mongo_client.return_value = mock_client_instance
        
        # Create client and query
        client = MongoDBClient()
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        results = client.query_telemetry(
            sensor_id="sensor_001",
            start_time=start_time,
            end_time=end_time,
            limit=100
        )
        
        # Verify query
        assert len(results) == 1
        assert results[0]["sensorId"] == "sensor_001"
        assert "_id" not in results[0]  # MongoDB _id should be removed
        mock_collection.find.assert_called_once()
    
    @patch('db.mongodb_client.MongoClient')
    def test_query_telemetry_without_time_range(self, mock_mongo_client):
        """Test querying telemetry without time range filters."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_collection = MagicMock()
        
        # Mock cursor
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__.return_value = iter([])
        mock_collection.find.return_value = mock_cursor
        
        mock_client_instance.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_mongo_client.return_value = mock_client_instance
        
        # Create client and query
        client = MongoDBClient()
        results = client.query_telemetry(sensor_id="sensor_001")
        
        # Verify query called with only sensorId filter
        call_args = mock_collection.find.call_args[0][0]
        assert call_args == {"sensorId": "sensor_001"}
        assert "timestamp" not in call_args
    
    @patch('db.mongodb_client.MongoClient')
    def test_index_creation(self, mock_mongo_client):
        """Test that TTL and compound indexes are created."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_collection = MagicMock()
        mock_client_instance.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_mongo_client.return_value = mock_client_instance
        
        # Create client (triggers index creation)
        client = MongoDBClient()
        
        # Verify indexes were created
        assert mock_collection.create_index.call_count == 2
        
        # Check TTL index
        ttl_call = mock_collection.create_index.call_args_list[0]
        assert ttl_call[0][0] == [("timestamp", 1)]
        assert ttl_call[1]["expireAfterSeconds"] == 30 * 24 * 60 * 60
        
        # Check compound index
        compound_call = mock_collection.create_index.call_args_list[1]
        assert compound_call[0][0] == [("sensorId", 1), ("timestamp", -1)]
    
    @patch('db.mongodb_client.MongoClient')
    def test_singleton_pattern(self, mock_mongo_client):
        """Test that get_mongodb_client returns singleton instance."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {'ok': 1}
        mock_mongo_client.return_value = mock_client_instance
        
        # Get client twice
        client1 = get_mongodb_client()
        client2 = get_mongodb_client()
        
        # Verify same instance
        assert client1 is client2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
