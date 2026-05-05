# Backend Integration - Tích Hợp Backend

## Tổng Quan

Frontend đã được tích hợp hoàn toàn với backend API và WebSocket để nhận dữ liệu thời gian thực. Tất cả mock data đã được loại bỏ.

## Các Thay Đổi Chính

### 1. AppContext - Quản Lý State Toàn Cục

**File:** `frontend/src/context/AppContext.tsx`

AppContext đã được cập nhật để:
- Load dữ liệu từ backend API khi khởi động
- Kết nối WebSocket để nhận real-time updates
- Quản lý state cho sensors, locations, alerts, và telemetry
- Tự động cập nhật UI khi có dữ liệu mới từ WebSocket

**Các API được sử dụng:**
- `fetchSensors()` - Lấy danh sách sensors
- `fetchLocations()` - Lấy danh sách locations
- `fetchAlerts()` - Lấy danh sách alerts

**WebSocket callbacks:**
- `onTelemetry` - Cập nhật telemetry data real-time
- `onAlert` - Nhận alerts mới real-time

### 2. Component Updates

#### Dashboard (`Dashboard.tsx`)
- ✅ Hiển thị số lượng sensors thực tế
- ✅ Tính toán AQI trung bình từ telemetry data
- ✅ Hiển thị nhiệt độ trung bình real-time
- ✅ Hiển thị critical alerts từ backend
- ✅ Load PM2.5 trend data từ API

#### SensorsView (`SensorsView.tsx`)
- ✅ Hiển thị danh sách sensors từ backend
- ✅ Kết hợp sensor data với telemetry real-time
- ✅ Tính toán status dựa trên PM2.5 và CO2
- ✅ Hỗ trợ tìm kiếm sensors
- ✅ Hiển thị thống kê theo status

#### MapView (`MapView.tsx`)
- ✅ Hiển thị sensors trên bản đồ với vị trí GPS thực
- ✅ Màu marker dựa trên status real-time
- ✅ Click vào marker để xem chi tiết sensor
- ✅ Tự động cập nhật khi có telemetry mới

#### AlertsView (`AlertsView.tsx`)
- ✅ Hiển thị alerts từ backend
- ✅ Phân loại theo severity (CRITICAL, HIGH, MEDIUM, LOW)
- ✅ Hiển thị thời gian và location
- ✅ Thống kê alerts theo mức độ

#### ClustersView (`ClustersView.tsx`)
- ✅ Load clusters từ backend API
- ✅ Hiển thị analytics cho mỗi cluster
- ✅ Tính toán status dựa trên PM2.5 và CO2
- ✅ Hiển thị AQI nếu có

#### AnalyticsView (`AnalyticsView.tsx`)
- ✅ Tính toán thống kê từ telemetry real-time
- ✅ Hiển thị AQI trung bình
- ✅ Phân bố sensor status
- ✅ Thống kê alerts
- ✅ PM2.5 trend chart từ API
- ✅ Cluster comparison chart

### 3. Environment Configuration

**File:** `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

Đảm bảo backend đang chạy tại `localhost:8000`.

## Cách Chạy

### 1. Khởi động Backend

```bash
cd backend
docker-compose up -d  # Khởi động Oracle, MongoDB, Mosquitto
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Khởi động IoT Simulator (tùy chọn)

```bash
cd iot-simulator
python simulator.py
```

### 3. Khởi động Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend sẽ chạy tại `http://localhost:5173`

## WebSocket Connection

WebSocket tự động kết nối khi app khởi động và:
- Reconnect tự động với exponential backoff (1s, 2s, 4s, 8s, max 60s)
- Hiển thị connection status trên Dashboard
- Nhận telemetry updates mỗi 5 giây
- Nhận alert notifications ngay lập tức

## API Endpoints Được Sử Dụng

### Sensors
- `GET /api/sensors` - Lấy danh sách sensors
- `GET /api/sensors/{sensorId}` - Chi tiết sensor
- `GET /api/sensors/{sensorId}/analytics` - Analytics cho sensor

### Telemetry
- `GET /api/telemetry/{sensorId}` - Lấy telemetry data với time range

### Locations
- `GET /api/locations` - Lấy location hierarchy

### Clusters
- `GET /api/clusters` - Lấy danh sách clusters
- `GET /api/clusters/{clusterId}/telemetry` - Analytics cho cluster

### Alerts
- `GET /api/alerts` - Lấy alerts với filters

### Leaderboard
- `GET /api/leaderboard` - Ranking locations theo Clean Score

## Xử Lý Lỗi

- API errors được catch và log ra console
- Loading states được hiển thị khi fetch data
- Fallback values (0) khi không có telemetry data
- WebSocket reconnection tự động khi mất kết nối

## Real-time Updates

Các component tự động cập nhật khi:
1. WebSocket nhận telemetry mới → `telemetryMap` được update
2. WebSocket nhận alert mới → `alerts` array được update
3. React re-render components sử dụng data này

## Kiểm Tra Tích Hợp

1. **Mở Developer Console** - Xem logs về API calls và WebSocket messages
2. **Kiểm tra Network tab** - Xem API requests và responses
3. **Kiểm tra WS tab** - Xem WebSocket messages real-time
4. **Dashboard** - Xem connection status và real-time stats

## Troubleshooting

### Backend không kết nối được
- Kiểm tra backend đang chạy: `curl http://localhost:8000/api/health`
- Kiểm tra CORS settings trong backend
- Xem logs trong backend console

### WebSocket không kết nối
- Kiểm tra WebSocket endpoint: `ws://localhost:8000/ws`
- Xem connection status trên Dashboard
- Kiểm tra browser console cho errors

### Không có dữ liệu
- Chạy IoT simulator để generate data
- Kiểm tra MongoDB có telemetry data: `docker exec -it mongodb mongosh`
- Kiểm tra Oracle có sensor registry: `docker exec -it oracle sqlplus`

## Next Steps

- [ ] Thêm error boundaries cho components
- [ ] Thêm retry logic cho failed API calls
- [ ] Thêm caching cho frequently accessed data
- [ ] Thêm pagination cho large datasets
- [ ] Thêm filters và sorting cho tables
- [ ] Thêm export data functionality

## Tài Liệu Tham Khảo

- Backend API Documentation: `backend/API_DOCUMENTATION.md`
- WebSocket Documentation: `backend/app/api/websocket.py`
- AppContext Documentation: `frontend/src/context/README.md`
