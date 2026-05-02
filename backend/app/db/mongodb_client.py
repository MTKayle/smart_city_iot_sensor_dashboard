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
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, GEOSPHERE, InsertOne
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError, BulkWriteError

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models import Telemetry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:admin123@localhost:27017/smart_city?authSource=admin")
DATABASE_NAME = os.getenv("MONGO_DATABASE", "smart_city")
COLLECTION_NAME = "telemetry"

# Retry configuration
MAX_RETRIES = 5
INITIAL_BACKOFF = 1  # seconds

class BatchInsertResult:
    def __init__(self, inserted: int = 0, duplicates: int = 0, errors: int = 0):
        self.inserted = inserted
        self.duplicates = duplicates
        self.errors = errors
        
    def __repr__(self):
        return f"BatchInsertResult(inserted={self.inserted}, duplicates={self.duplicates}, errors={self.errors})"


class MongoDBClient:
    """
    MongoDB client with connection pooling and automatic index management.
    
    Features:
    - Connection pooling for efficient resource usage
    - Automatic TTL index creation (30 days expiration)
    - Compound indexes for efficient queries
    - Geospatial indexes for location-based queries
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
                self.create_indexes()
                
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    logger.error(f"Failed to connect to MongoDB after {MAX_RETRIES} attempts: {e}")
                    raise
                
                logger.warning(f"MongoDB connection failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)  # Exponential backoff, max 60 seconds
    
    def create_indexes(self):
        """
        Create required indexes for telemetry collection.
        
        Creates:
        1. TTL index on expireAt field (30 days expiration)
        2. Compound index on (sensorId, timestamp)
        3. Compound index on (locationId, timestamp)
        4. Compound index on (clusterId, timestamp)
        5. Geospatial index on location (2dsphere)
        6. Unique index on (sensorId, timestamp) to prevent duplicates
        """
        try:
            # 1. TTL index on expireAt field
            self._collection.create_index(
                [("expireAt", ASCENDING)],
                name="ttl_expire_at",
                expireAfterSeconds=0
            )
            logger.info("Created TTL index on expireAt field")
            
            # 2. Compound index on (sensorId, timestamp) & Unique constraint
            self._collection.create_index(
                [("sensorId", ASCENDING), ("timestamp", DESCENDING)],
                name="sensor_timestamp_unique",
                unique=True
            )
            logger.info("Created compound/unique index on (sensorId, timestamp)")

            # 3. Compound index on (locationId, timestamp)
            self._collection.create_index(
                [("locationId", ASCENDING), ("timestamp", DESCENDING)],
                name="location_timestamp_index"
            )
            logger.info("Created compound index on (locationId, timestamp)")

            # 4. Compound index on (clusterId, timestamp)
            self._collection.create_index(
                [("clusterId", ASCENDING), ("timestamp", DESCENDING)],
                name="cluster_timestamp_index"
            )
            logger.info("Created compound index on (clusterId, timestamp)")

            # 5. Geospatial index on location field (2dsphere)
            self._collection.create_index(
                [("location", GEOSPHERE)],
                name="location_2dsphere"
            )
            logger.info("Created geospatial index on location field (2dsphere)")
            
        except OperationFailure as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    def insert_telemetry(self, telemetry: Telemetry) -> bool:
        retries = 0
        backoff = INITIAL_BACKOFF
        while retries < MAX_RETRIES:
            try:
                doc = telemetry.model_dump()
                result = self._collection.insert_one(doc)
                if result.inserted_id:
                    return True
                return False
            except OperationFailure as e:
                # E11000 duplicate key error
                if e.code == 11000:
                    logger.warning(f"Duplicate telemetry skipped for sensor {telemetry.sensorId} at {telemetry.timestamp}")
                    return False
            except ConnectionFailure as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    return False
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                try:
                    self._connect()
                except Exception:
                    pass
        return False

    def batch_insert_telemetry(self, telemetries: List[Telemetry], batch_size: int = 100) -> BatchInsertResult:
        """
        Batch insert telemetry documents with error handling.
        """
        result = BatchInsertResult()
        
        if not telemetries:
            return result
            
        retries = 0
        backoff = INITIAL_BACKOFF
        
        while retries < MAX_RETRIES:
            try:
                operations = []
                for tel in telemetries:
                    operations.append(InsertOne(tel.model_dump()))
                
                if operations:
                    # ordered=False allows to continue on duplicate key errors
                    bulk_result = self._collection.bulk_write(operations, ordered=False)
                    result.inserted = bulk_result.inserted_count
                return result
                
            except BulkWriteError as bwe:
                # Handle Duplicate key errors (E11000)
                write_errors = bwe.details.get('writeErrors', [])
                result.inserted = bwe.details.get('nInserted', 0)
                
                for err in write_errors:
                    if err.get('code') == 11000:
                        result.duplicates += 1
                    else:
                        result.errors += 1
                        
                logger.warning(f"Batch insert completed with {result.duplicates} duplicates and {result.errors} errors.")
                return result
                
            except (ConnectionFailure, OperationFailure) as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    logger.error(f"Failed to batch insert telemetry after {MAX_RETRIES} attempts: {e}")
                    result.errors = len(telemetries)
                    return result
                
                logger.warning(f"Batch insert operation failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                
                try:
                    self._connect()
                except Exception:
                    pass
        
        return result
    
    def query_telemetry(
        self,
        sensor_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        query_filter = {"sensorId": sensor_id}
        if start_time or end_time:
            query_filter["timestamp"] = {}
            if start_time:
                query_filter["timestamp"]["$gte"] = start_time
            if end_time:
                query_filter["timestamp"]["$lte"] = end_time
                
        cursor = self._collection.find(query_filter).sort("timestamp", DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            doc.pop("_id", None)
            results.append(doc)
        return results

    def query_telemetry_aggregated(
        self,
        sensor_id: str,
        start_time: datetime,
        end_time: datetime,
        bucket_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Query and downsample telemetry data using time-based aggregation.
        """
        pipeline = [
            {
                "$match": {
                    "sensorId": sensor_id,
                    "timestamp": {"$gte": start_time, "$lte": end_time}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateTrunc": {"date": "$timestamp", "unit": "minute", "binSize": bucket_minutes}
                    },
                    "locationId": {"$first": "$locationId"},
                    "co2": {"$avg": "$data.co2"},
                    "noise": {"$avg": "$data.noise"},
                    "temperature": {"$avg": "$data.temperature"}
                }
            },
            {"$sort": {"_id": -1}},
            {
                "$project": {
                    "_id": 0,
                    "sensorId": {"$literal": sensor_id},
                    "locationId": 1,
                    "timestamp": "$_id",
                    "co2": 1,
                    "noise": 1,
                    "temperature": 1
                }
            }
        ]

        cursor = self._collection.aggregate(pipeline)
        return list(cursor)

    def get_cluster_telemetry(
        self,
        cluster_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query telemetry data for a specific cluster.
        """
        query_filter = {"clusterId": cluster_id}
        if start_time or end_time:
            query_filter["timestamp"] = {}
            if start_time:
                query_filter["timestamp"]["$gte"] = start_time
            if end_time:
                query_filter["timestamp"]["$lte"] = end_time
                
        cursor = self._collection.find(query_filter).sort("timestamp", DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            doc.pop("_id", None)
            results.append(doc)
        return results

    def find_nearby_sensors(self, longitude: float, latitude: float, max_distance_meters: float, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Geospatial query to find latest telemetry from sensors near a point.
        """
        query_filter = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude]
                    },
                    "$maxDistance": max_distance_meters
                }
            }
        }
        
        # We might want only the latest telemetry per sensor, but standard find will just return matching docs
        cursor = self._collection.find(query_filter).limit(limit)
        results = []
        for doc in cursor:
            doc.pop("_id", None)
            results.append(doc)
        return results
    
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
    """
    global _mongodb_client
    if _mongodb_client is None:
        _mongodb_client = MongoDBClient()
    return _mongodb_client
