"""
MongoDB client module for Smart City IoT Dashboard.

This module provides connection pooling and operations for telemetry time-series data.
Implements automatic TTL-based data expiration and efficient indexing for queries.

Validates: Requirements 4.1, 4.2, 4.3, 4.5
"""

import os
import sys
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models import Telemetry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:admin123@mongodb:27017/smart_city?authSource=admin")
DATABASE_NAME = os.getenv("MONGO_DATABASE", "smart_city")
COLLECTION_NAME = "telemetry"

# TTL configuration (30 days in seconds)
TTL_SECONDS = 30 * 24 * 60 * 60  # 2592000 seconds

# Retry configuration
MAX_RETRIES = 5
INITIAL_BACKOFF = 1  # seconds


class MongoDBClient:
    """
    MongoDB client with connection pooling and automatic index management.
    
    Features:
    - Connection pooling for efficient resource usage
    - Automatic TTL index creation (30 days expiration)
    - Compound index on (sensorId, timestamp) for efficient queries
    - Exponential backoff retry for transient failures
    """
    
    def __init__(self):
        """Initialize MongoDB client with connection pooling."""
        self._client: Optional[MongoClient] = None
        self._db = None
        self._collection = None
        self._connect()
    
    def _connect(self):
        """
        Establish connection to MongoDB with exponential backoff retry.
        
        Implements retry logic for transient connection failures.
        Creates indexes on successful connection.
        """
        retries = 0
        backoff = INITIAL_BACKOFF
        
        while retries < MAX_RETRIES:
            try:
                logger.info(f"Attempting to connect to MongoDB (attempt {retries + 1}/{MAX_RETRIES})...")
                
                # Create client with connection pooling
                self._client = MongoClient(
                    MONGODB_URI,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    maxPoolSize=50,
                    minPoolSize=10
                )
                
                # Test connection
                self._client.admin.command('ping')
                
                # Get database and collection
                self._db = self._client[DATABASE_NAME]
                self._collection = self._db[COLLECTION_NAME]
                
                logger.info("Successfully connected to MongoDB")
                
                # Create indexes
                self._create_indexes()
                
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    logger.error(f"Failed to connect to MongoDB after {MAX_RETRIES} attempts: {e}")
                    raise
                
                logger.warning(f"MongoDB connection failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)  # Exponential backoff, max 60 seconds
    
    def _create_indexes(self):
        """
        Create required indexes for telemetry collection.
        
        Creates:
        1. TTL index on timestamp field (30 days expiration)
        2. Compound index on (sensorId, timestamp) for efficient range queries
        
        Validates: Requirements 4.2, 4.5
        """
        try:
            # Create TTL index on timestamp field
            # MongoDB will automatically delete documents older than 30 days
            self._collection.create_index(
                [("timestamp", ASCENDING)],
                name="ttl_index",
                expireAfterSeconds=TTL_SECONDS
            )
            logger.info(f"Created TTL index on timestamp field (expireAfterSeconds={TTL_SECONDS})")
            
            # Create compound index on (sensorId, timestamp) for efficient queries
            self._collection.create_index(
                [("sensorId", ASCENDING), ("timestamp", DESCENDING)],
                name="sensor_timestamp_index"
            )
            logger.info("Created compound index on (sensorId, timestamp)")
            
        except OperationFailure as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    def insert_telemetry(self, telemetry: Telemetry) -> bool:
        """
        Insert telemetry document into MongoDB collection.
        
        Args:
            telemetry: Telemetry object containing sensor measurements
        
        Returns:
            bool: True if insertion successful, False otherwise
        
        Validates: Requirement 4.1
        """
        retries = 0
        backoff = INITIAL_BACKOFF
        
        while retries < MAX_RETRIES:
            try:
                # Convert Pydantic model to dict
                doc = telemetry.model_dump()
                
                # Insert document with write concern w=1 for performance
                result = self._collection.insert_one(doc)
                
                if result.inserted_id:
                    logger.debug(f"Inserted telemetry for sensor {telemetry.sensorId}")
                    return True
                else:
                    logger.warning(f"Failed to insert telemetry for sensor {telemetry.sensorId}")
                    return False
                    
            except (ConnectionFailure, OperationFailure) as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    logger.error(f"Failed to insert telemetry after {MAX_RETRIES} attempts: {e}")
                    return False
                
                logger.warning(f"Insert operation failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                
                # Attempt to reconnect
                try:
                    self._connect()
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {reconnect_error}")
        
        return False
    
    def query_telemetry(
        self,
        sensor_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query telemetry data for a specific sensor with optional time range.
        
        Args:
            sensor_id: Sensor identifier
            start_time: Optional start of time range (inclusive)
            end_time: Optional end of time range (inclusive)
            limit: Maximum number of documents to return (default: 100)
        
        Returns:
            List of telemetry documents sorted by timestamp descending
        
        Uses compound index (sensorId, timestamp) for efficient queries.
        """
        retries = 0
        backoff = INITIAL_BACKOFF
        
        while retries < MAX_RETRIES:
            try:
                # Build query filter
                query_filter = {"sensorId": sensor_id}
                
                # Add time range filters if provided
                if start_time or end_time:
                    query_filter["timestamp"] = {}
                    if start_time:
                        query_filter["timestamp"]["$gte"] = start_time
                    if end_time:
                        query_filter["timestamp"]["$lte"] = end_time
                
                # Execute query with compound index
                cursor = self._collection.find(query_filter).sort(
                    "timestamp", DESCENDING
                ).limit(limit)
                
                # Convert cursor to list and remove MongoDB _id field
                results = []
                for doc in cursor:
                    doc.pop("_id", None)  # Remove MongoDB internal ID
                    results.append(doc)
                
                logger.debug(f"Retrieved {len(results)} telemetry documents for sensor {sensor_id}")
                return results
                
            except (ConnectionFailure, OperationFailure) as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    logger.error(f"Failed to query telemetry after {MAX_RETRIES} attempts: {e}")
                    return []
                
                logger.warning(f"Query operation failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                
                # Attempt to reconnect
                try:
                    self._connect()
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {reconnect_error}")
        
        return []
        
    def query_telemetry_aggregated(
        self,
        sensor_id: str,
        start_time: datetime,
        end_time: datetime,
        bucket_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Query and downsample telemetry data for a specific sensor over a large time range.
        
        Args:
            sensor_id: Sensor identifier
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            bucket_minutes: Size of the time bucket for aggregation
        
        Returns:
            List of aggregated telemetry documents sorted by timestamp descending
        """
        retries = 0
        backoff = INITIAL_BACKOFF
        
        while retries < MAX_RETRIES:
            try:
                pipeline = [
                    {
                        "$match": {
                            "sensorId": sensor_id,
                            "timestamp": { "$gte": start_time, "$lte": end_time }
                        }
                    },
                    {
                        "$group": {
                            "_id": {
                                "$dateTrunc": { "date": "$timestamp", "unit": "minute", "binSize": bucket_minutes }
                            },
                            "locationId": { "$first": "$locationId" },
                            "co2": { "$avg": "$co2" },
                            "noise": { "$avg": "$noise" },
                            "temperature": { "$avg": "$temperature" }
                        }
                    },
                    { "$sort": { "_id": -1 } },
                    {
                        "$project": {
                            "_id": 0,
                            "sensorId": { "$literal": sensor_id },
                            "locationId": 1,
                            "timestamp": "$_id",
                            "co2": 1,
                            "noise": 1,
                            "temperature": 1
                        }
                    }
                ]
                
                cursor = self._collection.aggregate(pipeline)
                results = list(cursor)
                
                logger.debug(f"Retrieved {len(results)} aggregated telemetry documents for sensor {sensor_id}")
                return results
                
            except (ConnectionFailure, OperationFailure) as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    logger.error(f"Failed to query aggregated telemetry after {MAX_RETRIES} attempts: {e}")
                    return []
                
                logger.warning(f"Aggregation operation failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                
                try:
                    self._connect()
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {reconnect_error}")
        
        return []
    
    def close(self):
        """Close MongoDB connection and release resources."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")


# Singleton instance
_mongodb_client: Optional[MongoDBClient] = None


def get_mongodb_client() -> MongoDBClient:
    """
    Get singleton MongoDB client instance.
    
    Returns:
        MongoDBClient: Shared client instance with connection pooling
    """
    global _mongodb_client
    if _mongodb_client is None:
        _mongodb_client = MongoDBClient()
    return _mongodb_client
