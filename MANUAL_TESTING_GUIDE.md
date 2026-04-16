# Hướng Dẫn Manual Test - Smart City IoT Dashboard

## 📋 Tổng Quan

Hướng dẫn này giúp bạn test thủ công các tính năng của Smart City IoT Dashboard qua giao diện web. Tất cả các tính năng từ Task 1-20 đã được hoàn thành và sẵn sàng để test.

---

## 🚀 Bước 1: Khởi Động Hệ Thống

### 1.1 Khởi động tất cả services

```bash
# Từ thư mục root của project
docker-compose up -d
```

### 1.2 Kiểm tra trạng thái services

```bash
# Xem logs của tất cả services
docker-compose logs -f

# Hoặc xem từng service riêng lẻ
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f iot-simulator
```

### 1.3 Đợi services khởi động hoàn tất

Các services cần thời gian khởi động:
- **MongoDB**: ~10 giây
- **Oracle**: ~30-60 giây (lần đầu có thể lâu hơn)
- **Backend**: ~5-10 giây (sau khi MongoDB và Oracle sẵn sàng)
- **Frontend**: ~5 giây
- **IoT Simulator**: ~3 giây

### 1.4 Verify services đang chạy

```bash
# Kiểm tra backend health
curl http://localhost:8000/health

# Kết quả mong đợi:
# {"status":"healthy"}

# Kiểm tra frontend
curl http://localhost:3000

# Kết quả mong đợi: HTML của React app
```

---

## 🌐 Bước 2: Truy Cập Dashboard

### 2.1 Mở trình duyệt

Truy cập: **http://localhost:3000**

### 2.2 Kiểm tra giao diện chính

Bạn sẽ thấy dashboard với layout:
- **Bên trái**: MapView - Bản đồ với các sensor markers
- **Giữa**: ChartView - Biểu đồ dữ liệu sensor
- **Bên phải trên**: Leaderboard - Bảng xếp hạng chất lượng môi trường
- **Bên phải dưới**: AlertsPanel - Danh sách cảnh báo

### 2.3 Kiểm tra connection status

Ở góc trên cùng, kiểm tra:
- ✅ **Connected**: WebSocket đang hoạt động (màu xanh)
- ❌ **Disconnected**: WebSocket bị ngắt kết nối (màu đỏ)

---

## 🗺️ Bước 3: Test MapView Component

### 3.1 Kiểm tra bản đồ hiển thị

**Mục tiêu**: Verify bản đồ Mapbox hiển thị đúng

**Các bước test**:
1. Bản đồ hiển thị khu vực thành phố (zoom level 12)
2. Có thể zoom in/out bằng scroll hoặc nút +/-
3. Có thể pan (kéo) bản đồ bằng chuột

**Kết quả mong đợi**:
- Bản đồ load mượt mà, không bị lag
- Các controls (zoom, rotate) hoạt động tốt

### 3.2 Kiểm tra sensor markers

**Mục tiêu**: Verify các sensor được hiển thị đúng vị trí

**Các bước test**:
1. Đếm số lượng markers trên bản đồ
2. Kiểm tra màu sắc của markers:
   - 🟢 **Xanh lá**: Sensor hoạt động bình thường
   - 🟡 **Vàng**: Sensor có cảnh báo mức MEDIUM
   - 🔴 **Đỏ**: Sensor có cảnh báo mức HIGH

**Kết quả mong đợi**:
- Có ít nhất 5 sensors (theo SENSOR_LIST trong .env)
- Markers hiển thị rõ ràng, có thể click được

### 3.3 Kiểm tra popup thông tin sensor

**Mục tiêu**: Verify popup hiển thị thông tin chi tiết

**Các bước test**:
1. Click vào một marker bất kỳ
2. Popup hiển thị với thông tin:
   - Sensor ID (ví dụ: sensor_001)
   - Location name (ví dụ: Ward 1, District 1)
   - Current readings:
     - CO2 (ppm)
     - Noise (dB)
     - Temperature (°C)
3. Click vào marker khác, popup chuyển sang sensor đó
4. Click ra ngoài bản đồ, popup đóng lại

**Kết quả mong đợi**:
- Popup hiển thị đầy đủ thông tin
- Dữ liệu có giá trị hợp lý:
  - CO2: 300-2000 ppm
  - Noise: 30-100 dB
  - Temperature: 15-35°C

### 3.4 Kiểm tra real-time updates

**Mục tiêu**: Verify markers cập nhật màu sắc khi có alert mới

**Các bước test**:
1. Mở popup của một sensor
2. Đợi 5-10 giây (IoT simulator publish data mỗi 5 giây)
3. Quan sát:
   - Giá trị trong popup có thay đổi không?
   - Màu marker có thay đổi nếu vượt ngưỡng không?

**Ngưỡng cảnh báo**:
- CO2 > 1000 ppm → Alert HIGH (marker đỏ)
- Noise > 85 dB → Alert HIGH (marker đỏ)

**Kết quả mong đợi**:
- Popup cập nhật giá trị mới mỗi 5 giây
- Marker chuyển màu đỏ khi có alert

---

## 📊 Bước 4: Test ChartView Component

### 4.1 Chọn sensor để xem biểu đồ

**Các bước test**:
1. Click vào một marker trên bản đồ
2. ChartView tự động load dữ liệu của sensor đó
3. Hiển thị 3 biểu đồ line chart:
   - **CO2 (ppm)**: Biểu đồ màu xanh dương
   - **Noise (dB)**: Biểu đồ màu cam
   - **Temperature (°C)**: Biểu đồ màu đỏ

**Kết quả mong đợi**:
- 3 biểu đồ hiển thị đồng thời
- Trục X: Thời gian (timestamp)
- Trục Y: Giá trị metric với đơn vị phù hợp

### 4.2 Kiểm tra time range selector

**Các bước test**:
1. Nhìn thấy 3 nút: **1h**, **6h**, **24h**
2. Click vào nút **1h**:
   - Biểu đồ hiển thị dữ liệu 1 giờ gần nhất
3. Click vào nút **6h**:
   - Biểu đồ hiển thị dữ liệu 6 giờ gần nhất
4. Click vào nút **24h**:
   - Biểu đồ hiển thị dữ liệu 24 giờ gần nhất

**Kết quả mong đợi**:
- Biểu đồ cập nhật ngay khi click
- Số lượng data points thay đổi theo time range
- Trục X scale tự động điều chỉnh

### 4.3 Kiểm tra auto-scaling Y-axis

**Các bước test**:
1. Chọn sensor có giá trị CO2 cao (>1000 ppm)
2. Chọn sensor có giá trị CO2 thấp (<500 ppm)
3. Quan sát trục Y của biểu đồ CO2

**Kết quả mong đợi**:
- Trục Y tự động scale để hiển thị tốt nhất
- Min/Max values phù hợp với data range

### 4.4 Kiểm tra real-time updates

**Các bước test**:
1. Giữ một sensor được chọn
2. Đợi 5-10 giây
3. Quan sát biểu đồ

**Kết quả mong đợi**:
- Data point mới xuất hiện ở cuối biểu đồ
- Biểu đồ tự động scroll/update
- Không bị lag hay flicker

### 4.5 Kiểm tra tooltip khi hover

**Các bước test**:
1. Di chuột qua các data points trên biểu đồ
2. Tooltip hiển thị:
   - Timestamp chính xác
   - Giá trị metric
   - Đơn vị

**Kết quả mong đợi**:
- Tooltip hiển thị mượt mà
- Thông tin chính xác và dễ đọc

---

## 🏆 Bước 5: Test Leaderboard Component

### 5.1 Kiểm tra bảng xếp hạng

**Mục tiêu**: Verify leaderboard hiển thị đúng

**Các bước test**:
1. Nhìn vào bảng Leaderboard ở góc phải trên
2. Kiểm tra các cột:
   - **Rank**: Thứ hạng (1, 2, 3, ...)
   - **Location Name**: Tên địa điểm (Ward X, District Y)
   - **Avg CO2**: Trung bình CO2 (ppm)
   - **Avg Noise**: Trung bình Noise (dB)
   - **Clean Score**: Điểm chất lượng môi trường (0-100)

**Kết quả mong đợi**:
- Bảng hiển thị ít nhất 5 locations
- Dữ liệu được sắp xếp theo Clean Score giảm dần
- Top 3 có visual indicators đặc biệt

### 5.2 Kiểm tra top 3 highlighting

**Các bước test**:
1. Quan sát 3 hàng đầu tiên
2. Kiểm tra visual indicators:
   - 🥇 **Rank 1**: Màu vàng gold hoặc icon medal
   - 🥈 **Rank 2**: Màu bạc silver
   - 🥉 **Rank 3**: Màu đồng bronze

**Kết quả mong đợi**:
- Top 3 nổi bật hơn các hàng khác
- Dễ nhận biết vị trí top

### 5.3 Kiểm tra Clean Score calculation

**Mục tiêu**: Verify công thức Clean Score đúng

**Công thức**:
```
normalized_CO2 = (avgCO2 / 2000) * 100
normalized_Noise = (avgNoise / 100) * 100
Clean Score = 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)
```

**Các bước test**:
1. Chọn một location trong leaderboard
2. Ghi lại: Avg CO2, Avg Noise, Clean Score
3. Tính toán thủ công theo công thức
4. So sánh với giá trị hiển thị

**Ví dụ**:
- Avg CO2 = 400 ppm
- Avg Noise = 60 dB
- normalized_CO2 = (400/2000)*100 = 20
- normalized_Noise = (60/100)*100 = 60
- Clean Score = 100 - (20*0.5 + 60*0.5) = 100 - 40 = 60

**Kết quả mong đợi**:
- Clean Score khớp với tính toán thủ công (±1 do làm tròn)

### 5.4 Kiểm tra click handler

**Các bước test**:
1. Click vào một hàng trong leaderboard
2. Quan sát bản đồ MapView

**Kết quả mong đợi**:
- Bản đồ tự động zoom/pan đến location được chọn
- Marker của location đó được highlight

### 5.5 Kiểm tra auto-refresh

**Các bước test**:
1. Ghi lại Clean Score của top 1
2. Đợi 60 giây
3. Kiểm tra xem dữ liệu có cập nhật không

**Kết quả mong đợi**:
- Leaderboard tự động refresh mỗi 60 giây
- Thứ hạng có thể thay đổi nếu dữ liệu mới khác

---

## 🚨 Bước 6: Test AlertsPanel Component

### 6.1 Kiểm tra danh sách alerts

**Mục tiêu**: Verify alerts hiển thị đúng

**Các bước test**:
1. Nhìn vào AlertsPanel ở góc phải dưới
2. Kiểm tra mỗi alert hiển thị:
   - **Timestamp**: Thời gian alert được tạo
   - **Sensor Location**: Vị trí sensor (Ward X, District Y)
   - **Metric Type**: Loại metric (CO2, Noise, Temperature)
   - **Value**: Giá trị vượt ngưỡng
   - **Severity Level**: Mức độ nghiêm trọng (HIGH, MEDIUM, LOW)

**Kết quả mong đợi**:
- Hiển thị tối đa 20 alerts gần nhất
- Alerts được sắp xếp theo thời gian giảm dần (mới nhất ở trên)

### 6.2 Kiểm tra color coding

**Các bước test**:
1. Quan sát màu sắc của các alerts:
   - 🔴 **Đỏ**: HIGH severity (CO2 > 1000, Noise > 85)
   - 🟠 **Cam**: MEDIUM severity
   - 🟡 **Vàng**: LOW severity

**Kết quả mong đợi**:
- Màu sắc rõ ràng, dễ phân biệt
- HIGH alerts nổi bật nhất

### 6.3 Kiểm tra filter controls

**Các bước test**:
1. Tìm filter controls (dropdown hoặc buttons)
2. Test filter by severity:
   - Chọn "HIGH" → Chỉ hiển thị HIGH alerts
   - Chọn "MEDIUM" → Chỉ hiển thị MEDIUM alerts
   - Chọn "ALL" → Hiển thị tất cả
3. Test filter by location:
   - Chọn "District 1" → Chỉ hiển thị alerts từ District 1
   - Chọn "Ward 2" → Chỉ hiển thị alerts từ Ward 2
   - Chọn "ALL" → Hiển thị tất cả locations

**Kết quả mong đợi**:
- Filter hoạt động ngay lập tức
- Số lượng alerts thay đổi theo filter

### 6.4 Kiểm tra real-time updates

**Mục tiêu**: Verify alerts mới xuất hiện real-time

**Các bước test**:
1. Đợi IoT simulator publish data mới (mỗi 5 giây)
2. Nếu có giá trị vượt ngưỡng, alert mới sẽ xuất hiện
3. Quan sát:
   - Alert mới xuất hiện ở đầu danh sách
   - Không cần refresh trang

**Kết quả mong đợi**:
- Alert mới xuất hiện trong vòng 1-2 giây
- Danh sách tự động scroll lên top

### 6.5 Kiểm tra visual notification

**Các bước test**:
1. Đợi alert mới xuất hiện
2. Kiểm tra notification:
   - Toast message ở góc màn hình
   - Badge số lượng alerts mới
   - Sound notification (nếu có)

**Kết quả mong đợi**:
- Notification rõ ràng, không làm phiền
- Có thể dismiss notification

### 6.6 Kiểm tra alert deduplication

**Mục tiêu**: Verify không tạo duplicate alerts

**Các bước test**:
1. Quan sát một sensor có alert HIGH
2. Đợi 5 giây (data mới publish)
3. Nếu sensor vẫn vượt ngưỡng, kiểm tra:
   - Có tạo alert mới không?
   - Hay vẫn giữ alert cũ?

**Kết quả mong đợi**:
- Trong vòng 5 phút, chỉ có 1 alert cho cùng sensor + metric
- Sau 5 phút, alert mới có thể được tạo

---

## 🔄 Bước 7: Test WebSocket Real-Time Updates

### 7.1 Kiểm tra connection status

**Các bước test**:
1. Mở Developer Tools (F12)
2. Vào tab Network → WS (WebSocket)
3. Tìm connection đến `ws://localhost:8000/ws`
4. Kiểm tra status: **101 Switching Protocols**

**Kết quả mong đợi**:
- WebSocket connection established
- Status indicator hiển thị "Connected"

### 7.2 Kiểm tra telemetry messages

**Các bước test**:
1. Trong WS tab, xem messages
2. Mỗi 5 giây, nhận messages dạng:
```json
{
  "type": "telemetry",
  "data": {
    "sensorId": "sensor_001",
    "co2": 450,
    "noise": 65,
    "temperature": 25,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Kết quả mong đợi**:
- Messages liên tục mỗi 5 giây
- Format JSON đúng
- Data hợp lý

### 7.3 Kiểm tra alert messages

**Các bước test**:
1. Đợi alert được trigger (CO2 > 1000 hoặc Noise > 85)
2. Xem message dạng:
```json
{
  "type": "alert",
  "data": {
    "alertId": "uuid-here",
    "sensorId": "sensor_001",
    "metricType": "CO2",
    "value": 1200,
    "level": "HIGH",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Kết quả mong đợi**:
- Alert message xuất hiện ngay khi threshold exceeded
- AlertsPanel cập nhật ngay lập tức

### 7.4 Kiểm tra reconnection logic

**Các bước test**:
1. Stop backend: `docker-compose stop backend`
2. Quan sát status indicator → "Disconnected"
3. Start backend: `docker-compose start backend`
4. Đợi 5-10 giây
5. Status indicator → "Connected"

**Kết quả mong đợi**:
- Auto-reconnect sau khi backend khởi động lại
- Không cần refresh trang
- Data tiếp tục stream

---

## 🧪 Bước 8: Test API Endpoints (Optional)

### 8.1 Test REST API bằng curl hoặc Postman

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Get locations
curl http://localhost:8000/api/locations

# 3. Get sensors
curl http://localhost:8000/api/sensors

# 4. Get telemetry for sensor
curl "http://localhost:8000/api/telemetry/sensor_001?limit=10"

# 5. Get alerts
curl http://localhost:8000/api/alerts

# 6. Get leaderboard
curl http://localhost:8000/api/leaderboard

# 7. Get analytics for sensor
curl http://localhost:8000/api/sensors/sensor_001/analytics
```

### 8.2 Kiểm tra API documentation

Truy cập: **http://localhost:8000/docs**

**Kết quả mong đợi**:
- Swagger UI hiển thị tất cả endpoints
- Có thể test API trực tiếp từ UI
- Request/Response schemas đầy đủ

---

## 🐛 Bước 9: Troubleshooting

### 9.1 Frontend không load

**Triệu chứng**: Trang trắng hoặc lỗi 404

**Giải pháp**:
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up -d --build frontend
```

### 9.2 Không có dữ liệu trên dashboard

**Triệu chứng**: Bản đồ trống, biểu đồ không có data

**Giải pháp**:
```bash
# Check backend logs
docker-compose logs backend

# Check IoT simulator logs
docker-compose logs iot-simulator

# Verify MongoDB có data
docker exec -it mongodb-store mongosh -u admin -p admin123
> use smart_city
> db.telemetry.countDocuments()
```

### 9.3 WebSocket không connect

**Triệu chứng**: Status "Disconnected", không có real-time updates

**Giải pháp**:
```bash
# Check backend WebSocket endpoint
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  http://localhost:8000/ws

# Check browser console for errors
# F12 → Console tab
```

### 9.4 Alerts không xuất hiện

**Triệu chứng**: Không có alerts dù có data vượt ngưỡng

**Giải pháp**:
```bash
# Check Oracle database
docker exec -it oracle-store sqlplus system/OraclePass123@XEPDB1
SQL> SELECT COUNT(*) FROM ALERTS;

# Check backend alert service logs
docker-compose logs backend | grep -i alert
```

### 9.5 Bản đồ không hiển thị

**Triệu chứng**: Lỗi "Mapbox token invalid"

**Giải pháp**:
1. Kiểm tra file `frontend/.env`:
```bash
VITE_MAPBOX_TOKEN=pk.your_token_here
```
2. Lấy token mới tại: https://account.mapbox.com/access-tokens/
3. Rebuild frontend:
```bash
docker-compose up -d --build frontend
```

---

## ✅ Checklist Tổng Hợp

### MapView
- [ ] Bản đồ hiển thị đúng
- [ ] Sensors markers hiển thị đúng vị trí
- [ ] Markers có màu sắc phù hợp với alert status
- [ ] Popup hiển thị thông tin chi tiết
- [ ] Real-time updates hoạt động

### ChartView
- [ ] 3 biểu đồ hiển thị đồng thời
- [ ] Time range selector hoạt động (1h, 6h, 24h)
- [ ] Auto-scaling Y-axis
- [ ] Real-time data appending
- [ ] Tooltip hiển thị đúng

### Leaderboard
- [ ] Bảng xếp hạng hiển thị đúng
- [ ] Top 3 highlighting
- [ ] Clean Score calculation đúng
- [ ] Click handler zoom map
- [ ] Auto-refresh mỗi 60s

### AlertsPanel
- [ ] Danh sách alerts hiển thị
- [ ] Color coding by severity
- [ ] Filter controls hoạt động
- [ ] Real-time alert updates
- [ ] Visual notification
- [ ] Alert deduplication

### WebSocket
- [ ] Connection established
- [ ] Telemetry messages streaming
- [ ] Alert messages received
- [ ] Auto-reconnection logic

### General
- [ ] Tất cả services khởi động thành công
- [ ] Không có errors trong console
- [ ] Performance tốt, không lag
- [ ] Responsive design (nếu có)

---

## 📊 Kết Quả Mong Đợi

Sau khi hoàn thành tất cả các bước test, bạn sẽ có:

1. ✅ Dashboard hoạt động hoàn chỉnh với real-time updates
2. ✅ Tất cả components render đúng và tương tác tốt
3. ✅ WebSocket streaming data liên tục
4. ✅ Alerts được tạo và hiển thị đúng
5. ✅ Leaderboard cập nhật định kỳ
6. ✅ Không có errors trong logs

---

## 🎯 Next Steps

Sau khi test xong, bạn có thể:

1. **Customize data**: Thay đổi SENSOR_LIST trong `.env` để thêm sensors
2. **Adjust thresholds**: Sửa ngưỡng alert trong backend code
3. **Add more features**: Implement các tasks còn lại (21-24)
4. **Performance testing**: Test với nhiều sensors hơn
5. **Security testing**: Thêm authentication/authorization

---

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Logs của services: `docker-compose logs [service-name]`
2. Browser console: F12 → Console tab
3. Network tab: F12 → Network tab
4. WebSocket tab: F12 → Network → WS

Happy Testing! 🚀
