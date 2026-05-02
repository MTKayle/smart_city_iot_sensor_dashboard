// backend/app/db/mongodb_indexes.js
// MongoDB Indexes Script for Telemetry Collection
// Run this script using: mongosh mongodb://admin:admin123@localhost:27017/smart_city?authSource=admin backend/app/db/mongodb_indexes.js

db = db.getSiblingDB('smart_city');
collection = db.getCollection('telemetry');

print("Creating indexes for telemetry collection...");

// 1. TTL Index for automatic data expiration based on expireAt field
print("1. Creating TTL index on expireAt...");
collection.createIndex(
  { "expireAt": 1 },
  { expireAfterSeconds: 0, name: "ttl_expire_at" }
);

// 2. Compound indexes for efficient querying by entity and time
print("2. Creating compound indexes...");
collection.createIndex(
  { "sensorId": 1, "timestamp": -1 },
  { name: "sensor_timestamp" }
);

collection.createIndex(
  { "locationId": 1, "timestamp": -1 },
  { name: "location_timestamp" }
);

collection.createIndex(
  { "clusterId": 1, "timestamp": -1 },
  { name: "cluster_timestamp" }
);

// 3. Geospatial index for spatial queries
print("3. Creating geospatial index on location (2dsphere)...");
collection.createIndex(
  { "location": "2dsphere" },
  { name: "location_2dsphere" }
);

print("Index creation completed successfully.");
print("Current indexes on telemetry collection:");
printjson(collection.getIndexes());
