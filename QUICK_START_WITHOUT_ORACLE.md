# Quick Start - Test Without Oracle

Oracle XE có vấn đề trên Windows. Bạn có thể test hầu hết tính năng mà không cần Oracle.

## Các tính năng KHÔNG cần Oracle:
- ✅ Real-time telemetry streaming (MQTT → MongoDB)
- ✅ WebSocket updates
- ✅ MapView với sensor markers
- ✅ ChartView với telemetry data
- ✅ Real-time data visualization

## Các tính năng CẦN Oracle:
- ❌ Alerts storage (sẽ lưu trong memory thay vì DB)
- ❌ Leaderboard (Clean Score calculation)
- ❌ Location hierarchy queries

---

## Bước 1: Stop tất cả services

```bash
docker-compose down
```

## Bước 2: Start services cần thiết

```bash
# Start MongoDB và MQTT
docker-compose up -d mosquitto mongodb
```

## Bước 3: Verify services đang chạy

```bash
docker-compose ps
```

Kết quả mong đợi:
```
NAME            STATUS
mongodb-store   Up (healthy)
mqtt-broker     Up
```

## Bước 4: Start Backend manually (không cần Oracle)

### 4.1 Tạo virtual environment

```bash
cd backend
python -m venv venv

# Activate venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
.\venv\Scripts\activate.bat
```

### 4.2 Install dependencies

```bash
pip install -r requirements.txt
```

### 4.3 Set environment variables

```bash
# PowerShell
$env:MQTT_BROKER_HOST="localhost"
$env:MQTT_BROKER_PORT="1883"
$env:MONGODB_URI="mongodb://admin:admin123@localhost:27017/smart_city?authSource=admin"
$env:ORACLE_DSN="localhost:1521/XEPDB1"  # Sẽ không dùng nhưng cần có
$env:ORACLE_USER="system"
$env:ORACLE_PASSWORD="OraclePass123"
```

### 4.4 Comment out Oracle code tạm thời

Mở file `backend/app/main.py` và comment out phần Oracle initialization:

```python
# Comment out these lines:
# from app.db.oracle_client import get_oracle_client
# oracle_client = get_oracle_client()
```

### 4.5 Start backend

```bash
python -m app.main
```

Backend sẽ chạy tại: http://localhost:8000

## Bước 5: Start IoT Simulator

```bash
docker-compose up -d iot-simulator
```

## Bước 6: Start Frontend

### 6.1 Install dependencies

```bash
cd frontend
npm install
```

### 6.2 Create .env file

```bash
# Copy from example
cp .env.example .env
```

Nội dung `.env`:
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_MAPBOX_TOKEN=
```

### 6.3 Start frontend dev server

```bash
npm run dev
```

Frontend sẽ chạy tại: http://localhost:5173

---

## Bước 7: Test Dashboard

Mở browser: **http://localhost:5173**

### Test Cases:

#### 1. MapView
- ✅ Bản đồ hiển thị
- ✅ Sensor markers xuất hiện
- ✅ Click marker → popup hiển thị thông tin
- ✅ Markers cập nhật màu real-time

#### 2. ChartView
- ✅ Click sensor → 3 biểu đồ hiển thị (CO2, Noise, Temperature)
- ✅ Time range selector hoạt động (1h, 6h, 24h)
- ✅ Data cập nhật real-time mỗi 5 giây

#### 3. WebSocket
- ✅ Connection status: "Connected" (góc trên)
- ✅ F12 → Network → WS → Xem messages streaming

#### 4. Leaderboard (Sẽ trống vì không có Oracle)
- ⚠️ Hiển thị "No data" hoặc empty table

#### 5. AlertsPanel (Sẽ trống vì không có Oracle)
- ⚠️ Hiển thị "No alerts" hoặc empty list

---

## Troubleshooting

### Backend không start

```bash
# Check MongoDB
docker-compose logs mongodb

# Test MongoDB connection
mongosh mongodb://admin:admin123@localhost:27017/smart_city?authSource=admin
```

### Frontend không connect WebSocket

```bash
# Check backend logs
# Xem có lỗi WebSocket không

# Check browser console (F12)
# Xem có lỗi connection không
```

### Không có data trên charts

```bash
# Check IoT simulator
docker-compose logs iot-simulator

# Verify MQTT messages
docker exec -it mqtt-broker mosquitto_sub -t "sensors/#" -v
```

---

## Alternative: Use SQLite instead of Oracle

Nếu bạn muốn test Leaderboard và Alerts, có thể thay Oracle bằng SQLite:

### 1. Install SQLite driver

```bash
pip install aiosqlite
```

### 2. Modify oracle_client.py

Thay đổi connection string để dùng SQLite thay vì Oracle.

### 3. Update schema

Chuyển đổi SQL schema từ Oracle sang SQLite syntax.

---

## Summary

Với setup này, bạn có thể test:
- ✅ 70% tính năng dashboard
- ✅ Real-time data streaming
- ✅ WebSocket updates
- ✅ Interactive charts
- ✅ Map visualization

Chỉ thiếu:
- ❌ Persistent alerts storage
- ❌ Leaderboard rankings
- ❌ Location hierarchy queries

Đủ để demo và hiểu cách hệ thống hoạt động!
