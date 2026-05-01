# Hướng Dẫn Xem Giao Diện Oracle Database

## Thông Tin Kết Nối

```
Host: localhost
Port: 1521
Service Name: XEPDB1
Username: system
Password: OraclePass123
```

## Phương Pháp 1: Oracle SQL Developer (Khuyên dùng)

### Tải về
1. Truy cập: https://www.oracle.com/database/sqldeveloper/technologies/download/
2. Tải phiên bản phù hợp với hệ điều hành (Windows/Mac/Linux)
3. Giải nén và chạy file `sqldeveloper.exe` (Windows) hoặc `sqldeveloper.sh` (Linux/Mac)

### Kết nối
1. Mở SQL Developer
2. Click vào dấu `+` (New Connection) ở góc trái trên
3. Điền thông tin:
   - **Connection Name**: Smart City Oracle
   - **Username**: system
   - **Password**: OraclePass123
   - **Save Password**: ✓ (check)
   - **Hostname**: localhost
   - **Port**: 1521
   - **Service name**: XEPDB1 (chọn Service name, không phải SID)
4. Click **Test** để kiểm tra kết nối
5. Nếu thành công, click **Connect**

### Xem Dữ Liệu
- Mở cây thư mục bên trái: **SYSTEM** → **Tables**
- Các bảng của project:
  - `LOCATIONS` - Thông tin địa điểm (City, District, Ward)
  - `SENSORS` - Danh sách cảm biến
  - `ALERTS` - Cảnh báo từ cảm biến
  - `TELEMETRY_SUMMARY` - Tổng hợp dữ liệu telemetry
- Click phải vào bảng → **View Data** để xem nội dung

## Phương Pháp 2: DBeaver (Miễn phí, đa nền tảng)

### Tải về
1. Truy cập: https://dbeaver.io/download/
2. Tải phiên bản Community Edition (miễn phí)
3. Cài đặt như phần mềm thông thường

### Kết nối
1. Mở DBeaver
2. Click **Database** → **New Database Connection**
3. Chọn **Oracle** trong danh sách
4. Điền thông tin:
   - **Host**: localhost
   - **Port**: 1521
   - **Database**: XEPDB1
   - **Authentication**: Database Native
   - **Username**: system
   - **Password**: OraclePass123
5. Click **Test Connection**
6. Nếu thiếu driver, DBeaver sẽ tự động tải về
7. Click **Finish**

### Xem Dữ Liệu
- Mở cây thư mục bên trái: **XEPDB1** → **Schemas** → **SYSTEM** → **Tables**
- Double-click vào bảng để xem dữ liệu

## Phương Pháp 3: SQL*Plus qua Command Line

### Kết nối
```bash
docker exec -it oracle-store sqlplus system/OraclePass123@XEPDB1
```

### Các Lệnh Hữu Ích

**Xem danh sách bảng:**
```sql
SELECT table_name FROM user_tables ORDER BY table_name;
```

**Xem cấu trúc bảng:**
```sql
DESC LOCATIONS;
DESC SENSORS;
DESC ALERTS;
DESC TELEMETRY_SUMMARY;
```

**Xem dữ liệu:**
```sql
-- Xem tất cả locations
SELECT * FROM LOCATIONS;

-- Xem tất cả sensors
SELECT * FROM SENSORS;

-- Xem 10 alerts gần nhất
SELECT * FROM ALERTS ORDER BY CreatedAt DESC FETCH FIRST 10 ROWS ONLY;

-- Xem hierarchy view
SELECT * FROM LOCATION_HIERARCHY ORDER BY HierarchyLevel, LocationID;
```

**Đếm số records:**
```sql
SELECT 'LOCATIONS' as TableName, COUNT(*) as RecordCount FROM LOCATIONS
UNION ALL
SELECT 'SENSORS', COUNT(*) FROM SENSORS
UNION ALL
SELECT 'ALERTS', COUNT(*) FROM ALERTS
UNION ALL
SELECT 'TELEMETRY_SUMMARY', COUNT(*) FROM TELEMETRY_SUMMARY;
```

**Thoát SQL*Plus:**
```sql
EXIT;
```

## Phương Pháp 4: Web-based Tools

### Oracle APEX (Nếu đã cài đặt)
- URL: http://localhost:8080/apex
- Workspace: INTERNAL
- Username: ADMIN
- Password: (password bạn đã set khi cài Oracle)

**Lưu ý:** Oracle XE Docker image mặc định không có APEX, cần cài thêm.

## Phương Pháp 5: VS Code Extension

### Cài đặt Extension
1. Mở VS Code
2. Tìm extension: **Oracle Developer Tools for VS Code**
3. Cài đặt extension

### Kết nối
1. Mở Command Palette (Ctrl+Shift+P)
2. Gõ: **Oracle: New Connection**
3. Điền thông tin kết nối tương tự như trên

## Cấu Trúc Database của Project

### Bảng LOCATIONS
```
LocationID (PK) | Name              | ParentID | Type
city_hcm        | Ho Chi Minh City  | NULL     | City
district_001    | District 1        | city_hcm | District
ward_001        | Ward 1            | district_001 | Ward
...
```

### Bảng SENSORS
```
SensorID (PK) | LocationID | SensorType   | RegisteredAt
sensor_001    | ward_001   | CO2          | 2026-04-12...
sensor_002    | ward_001   | Noise        | 2026-04-12...
sensor_003    | ward_001   | Temperature  | 2026-04-12...
...
```

### Bảng ALERTS
```
AlertID (PK) | SensorID   | Metric | Value  | AlertLevel | CreatedAt
uuid...      | sensor_001 | CO2    | 1500   | HIGH       | 2026-04-12...
...
```

### View LOCATION_HIERARCHY
```
LocationID | Name              | ParentID | Type     | Path                    | HierarchyLevel
city_hcm   | Ho Chi Minh City  | NULL     | City     | > city_hcm              | 0
district_001| District 1       | city_hcm | District | > city_hcm > district_001| 1
ward_001   | Ward 1            | district_001| Ward  | > city_hcm > district_001 > ward_001| 2
...
```

## Troubleshooting

### Không kết nối được
1. Kiểm tra Oracle container đang chạy:
   ```bash
   docker ps | grep oracle
   ```

2. Kiểm tra Oracle đã healthy:
   ```bash
   docker ps
   # Cột STATUS phải hiển thị "healthy"
   ```

3. Kiểm tra port 1521 đang mở:
   ```bash
   netstat -an | grep 1521
   ```

### Lỗi "ORA-12541: TNS:no listener"
- Oracle chưa khởi động xong, đợi thêm vài phút
- Kiểm tra logs: `docker logs oracle-store`

### Lỗi "ORA-01017: invalid username/password"
- Kiểm tra lại username: `system`
- Kiểm tra lại password: `OraclePass123`
- Đảm bảo dùng Service Name: `XEPDB1` (không phải SID)

## Khuyến Nghị

Đối với người mới bắt đầu, tôi khuyên dùng **DBeaver** vì:
- Miễn phí và mã nguồn mở
- Giao diện thân thiện, dễ sử dụng
- Hỗ trợ nhiều loại database (Oracle, MySQL, PostgreSQL, MongoDB...)
- Tự động tải driver
- Có tính năng ER Diagram để xem mối quan hệ giữa các bảng

Đối với người có kinh nghiệm với Oracle, dùng **SQL Developer** vì:
- Công cụ chính thức từ Oracle
- Nhiều tính năng chuyên sâu cho Oracle
- Hỗ trợ PL/SQL debugging
- Tối ưu hóa query
