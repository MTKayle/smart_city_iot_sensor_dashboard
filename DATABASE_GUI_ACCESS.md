# Hướng Dẫn Xem Dữ Liệu Oracle và MongoDB

## Oracle Database

### Thông tin kết nối
- Host: `localhost`
- Port: `1521`
- Service Name: `XEPDB1`
- Username: `system`
- Password: `OraclePass123`

### Phương pháp 1: DBeaver (Khuyên dùng - Miễn phí)

1. **Download và cài đặt DBeaver**
   - Link: https://dbeaver.io/download/
   - Chọn phiên bản Community Edition (miễn phí)

2. **Tạo kết nối Oracle**
   - Mở DBeaver
   - Click "New Database Connection" (hoặc Ctrl+Shift+N)
   - Chọn "Oracle"
   - Điền thông tin:
     ```
     Host: localhost
     Port: 1521
     Database: XEPDB1
     Service name: XEPDB1
     Username: system
     Password: OraclePass123
     ```
   - Click "Test Connection" để kiểm tra
   - Click "Finish"

3. **Xem dữ liệu**
   - Expand connection → SYSTEM → Tables
   - Double-click vào table để xem data
   - Hoặc mở SQL Editor và chạy queries

### Phương pháp 2: Oracle SQL Developer (GUI chính thức)

1. **Download**
   - Link: https://www.oracle.com/database/sqldeveloper/technologies/download/
   - Cần có Java JDK 11+

2. **Tạo kết nối**
   - Click "+" để tạo connection mới
   - Điền thông tin tương tự DBeaver
   - Connection Type: Basic
   - Hostname: localhost
   - Port: 1521
   - SID: XEPDB1

### Phương pháp 3: Command Line (SQL*Plus)

```bash
# Kết nối vào container
docker exec -it oracle-store sqlplus system/OraclePass123@XEPDB1

# Các lệnh SQL hữu ích:
SELECT * FROM LOCATIONS;
SELECT * FROM SENSORS;
SELECT * FROM ALERTS ORDER BY CREATEDAT DESC FETCH FIRST 10 ROWS ONLY;
SELECT * FROM TELEMETRY_SUMMARY ORDER BY SUMMARYDATE DESC FETCH FIRST 10 ROWS ONLY;
SELECT * FROM LOCATION_HIERARCHY;

# Đếm số records
SELECT COUNT(*) FROM ALERTS;
SELECT COUNT(*) FROM SENSORS;

# Thoát
EXIT;
```

### Phương pháp 4: Scripts nhanh

```bash
# Xem tất cả tables
docker exec oracle-store bash -c "echo 'SELECT table_name FROM user_tables ORDER BY table_name;' | sqlplus -s system/OraclePass123@XEPDB1"

# Xem structure của table
docker exec oracle-store bash -c "echo 'DESC LOCATIONS;' | sqlplus -s system/OraclePass123@XEPDB1"

# Xem locations
docker exec oracle-store bash -c "echo 'SET PAGESIZE 50; SELECT * FROM LOCATIONS;' | sqlplus -s system/OraclePass123@XEPDB1"

# Xem sensors với location info
docker exec oracle-store bash -c "echo \"SELECT s.SENSORID, s.SENSORTYPE, l.NAME as LOCATION FROM SENSORS s JOIN LOCATIONS l ON s.LOCATIONID = l.LOCATIONID;\" | sqlplus -s system/OraclePass123@XEPDB1"

# Xem 10 alerts mới nhất
docker exec oracle-store bash -c "echo 'SELECT ALERTID, SENSORID, METRIC, VALUE, ALERTLEVEL, CREATEDAT FROM ALERTS ORDER BY CREATEDAT DESC FETCH FIRST 10 ROWS ONLY;' | sqlplus -s system/OraclePass123@XEPDB1"
```

## MongoDB

### Thông tin kết nối
- Host: `localhost`
- Port: `27017`
- Database: `smart_city_iot`
- Collection: `telemetry`
- No authentication required

### Phương pháp 1: MongoDB Compass (Khuyên dùng - Miễn phí)

1. **Download và cài đặt**
   - Link: https://www.mongodb.com/try/download/compass
   - Chọn phiên bản Community

2. **Kết nối**
   - Mở Compass
   - Connection string: `mongodb://localhost:27017`
   - Click "Connect"

3. **Xem dữ liệu**
   - Chọn database: `smart_city_iot`
   - Chọn collection: `telemetry`
   - Browse documents
   - Có thể filter, sort, và export data

### Phương pháp 2: Studio 3T (GUI mạnh hơn - Free trial)

1. **Download**
   - Link: https://studio3t.com/download/
   - Free trial 30 ngày, sau đó có free version giới hạn

2. **Kết nối**
   - New Connection
   - Server: localhost
   - Port: 27017

### Phương pháp 3: Command Line (mongosh)

```bash
# Kết nối vào container
docker exec -it mongodb-store mongosh

# Các lệnh MongoDB hữu ích:
use smart_city_iot

# Xem collections
show collections

# Đếm documents
db.telemetry.countDocuments()

# Xem 5 records mới nhất
db.telemetry.find().sort({timestamp: -1}).limit(5).pretty()

# Xem telemetry của sensor cụ thể
db.telemetry.find({sensorId: "sensor_001"}).sort({timestamp: -1}).limit(10).pretty()

# Xem telemetry theo metric
db.telemetry.find({metric: "CO2"}).sort({timestamp: -1}).limit(10).pretty()

# Aggregate - trung bình giá trị theo sensor
db.telemetry.aggregate([
  {$group: {_id: "$sensorId", avgValue: {$avg: "$value"}, count: {$sum: 1}}}
])

# Thoát
exit
```

### Phương pháp 4: Scripts nhanh

```bash
# Đếm telemetry records
docker exec mongodb-store mongosh --quiet --eval "use smart_city_iot; db.telemetry.countDocuments()"

# Xem 5 records mới nhất
docker exec mongodb-store mongosh --quiet --eval "use smart_city_iot; db.telemetry.find().sort({timestamp: -1}).limit(5)"

# Xem telemetry của sensor_001
docker exec mongodb-store mongosh --quiet --eval "use smart_city_iot; db.telemetry.find({sensorId: 'sensor_001'}).sort({timestamp: -1}).limit(5)"

# Đếm theo metric
docker exec mongodb-store mongosh --quiet --eval "use smart_city_iot; db.telemetry.aggregate([{\$group: {_id: '\$metric', count: {\$sum: 1}}}])"

# Xem indexes
docker exec mongodb-store mongosh --quiet --eval "use smart_city_iot; db.telemetry.getIndexes()"
```

## Queries Hữu Ích

### Oracle - Kiểm tra dữ liệu

```sql
-- Xem tổng quan hệ thống
SELECT 
    (SELECT COUNT(*) FROM LOCATIONS) as total_locations,
    (SELECT COUNT(*) FROM SENSORS) as total_sensors,
    (SELECT COUNT(*) FROM ALERTS) as total_alerts,
    (SELECT COUNT(*) FROM TELEMETRY_SUMMARY) as total_summaries
FROM DUAL;

-- Xem sensors theo location
SELECT 
    l.NAME as location_name,
    l.TYPE as location_type,
    COUNT(s.SENSORID) as sensor_count
FROM LOCATIONS l
LEFT JOIN SENSORS s ON l.LOCATIONID = s.LOCATIONID
GROUP BY l.NAME, l.TYPE
ORDER BY sensor_count DESC;

-- Xem alerts theo level
SELECT 
    ALERTLEVEL,
    COUNT(*) as count,
    MIN(CREATEDAT) as first_alert,
    MAX(CREATEDAT) as last_alert
FROM ALERTS
GROUP BY ALERTLEVEL
ORDER BY count DESC;

-- Xem location hierarchy
SELECT 
    LocationID,
    Name,
    Type,
    Path,
    HierarchyLevel
FROM LOCATION_HIERARCHY
ORDER BY HierarchyLevel, LocationID;
```

### MongoDB - Kiểm tra dữ liệu

```javascript
// Xem tổng quan
db.telemetry.aggregate([
  {
    $group: {
      _id: null,
      totalRecords: {$sum: 1},
      uniqueSensors: {$addToSet: "$sensorId"},
      metrics: {$addToSet: "$metric"},
      minTimestamp: {$min: "$timestamp"},
      maxTimestamp: {$max: "$timestamp"}
    }
  },
  {
    $project: {
      _id: 0,
      totalRecords: 1,
      uniqueSensorCount: {$size: "$uniqueSensors"},
      metrics: 1,
      minTimestamp: 1,
      maxTimestamp: 1
    }
  }
])

// Xem telemetry theo sensor
db.telemetry.aggregate([
  {
    $group: {
      _id: "$sensorId",
      count: {$sum: 1},
      avgValue: {$avg: "$value"},
      minValue: {$min: "$value"},
      maxValue: {$max: "$value"}
    }
  },
  {$sort: {count: -1}}
])

// Xem telemetry theo metric
db.telemetry.aggregate([
  {
    $group: {
      _id: "$metric",
      count: {$sum: 1},
      avgValue: {$avg: "$value"}
    }
  }
])

// Xem data rate (records per minute)
db.telemetry.aggregate([
  {
    $group: {
      _id: {
        $dateToString: {format: "%Y-%m-%d %H:%M", date: "$timestamp"}
      },
      count: {$sum: 1}
    }
  },
  {$sort: {_id: -1}},
  {$limit: 10}
])
```

## Troubleshooting

### Oracle không kết nối được
```bash
# Kiểm tra container đang chạy
docker ps | grep oracle

# Kiểm tra logs
docker logs oracle-store --tail 50

# Kiểm tra port
netstat -an | grep 1521

# Test connection
docker exec oracle-store bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s system/OraclePass123@XEPDB1"
```

### MongoDB không kết nối được
```bash
# Kiểm tra container đang chạy
docker ps | grep mongodb

# Kiểm tra logs
docker logs mongodb-store --tail 50

# Kiểm tra port
netstat -an | grep 27017

# Test connection
docker exec mongodb-store mongosh --eval "db.adminCommand('ping')"
```

## Khuyến nghị

**Cho development:**
- Oracle: Dùng DBeaver (miễn phí, dễ dùng, hỗ trợ nhiều DB)
- MongoDB: Dùng MongoDB Compass (chính thức, miễn phí, UI đẹp)

**Cho production monitoring:**
- Dùng command line scripts để tự động hóa
- Tích hợp với monitoring tools (Grafana, Prometheus)

**Cho debugging:**
- Dùng command line để nhanh chóng kiểm tra data
- Dùng GUI tools để phân tích chi tiết
