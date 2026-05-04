db = db.getSiblingDB('smartcity');
print('Total telemetry records:', db.telemetry.countDocuments({}));
print('Unique sensors:', db.telemetry.distinct('sensorId').length);
print('Sample sensor IDs:');
printjson(db.telemetry.distinct('sensorId').slice(0, 10));
