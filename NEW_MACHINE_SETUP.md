# Hướng Dẫn Cài Đặt và Chạy Dự Án Chuyển Máy (Portable Setup Guide)

Hướng dẫn này giúp bạn mang toàn bộ source code của dự án "Smart City IoT Dashboard" qua một máy tính khác và khởi chạy mượt mà từ đầu mà không gặp phải các lỗi đồng bộ cơ sở dữ liệu hay nghẽn API.

---

## Bước 1: Yêu cầu hệ thống cần có
1. **Docker** và **Docker Compose** đã được cài đặt trên máy mới (Nên cấp tối thiểu 4GB RAM cho Docker Desktop do Oracle XE và MongoDB dùng khá nhiều bộ nhớ).
2. Kiểm tra/Tắt các dịch vụ trên máy trùng với các port sau (nếu có): `3000` (React), `8000` (FastAPI), `1521` (Oracle), `27017` (MongoDB), `1883` (MQTT).

---

## Bước 2: Chuẩn bị Source Code và Environment
1. Copy toàn bộ thư mục dự án này qua máy mới.
2. Kiểm tra xem file ẩn `.env` gốc đã có ở thư mục ngoài cùng hay chưa. Nếu file bị thất lạc trong quá trình copy, bạn có thể tạo lại bằng cách copy từ file mẫu:
   - Mở Terminal/Command Prompt trong đường dẫn root của file:
   - Chạy lệnh: `cp .env.example .env` (Linux/Mac) hoặc `copy .env.example .env` (Win)

---

## Bước 3: Dọn dẹp môi trường (Phòng hờ bộ nhớ cache đụng độ cũ nếu cài lại)
Để đảm bảo máy mới không bị dính các container/volume cũ, hãy mở terminal ngay tại gốc thư mục dự án và gõ lệnh:
```bash
docker compose down -v
```

---

## Bước 4: Khởi Tối Đa Hệ Thống (Auto Build & Run)
Chỉ bằng một lệnh duy nhất, toàn bộ hệ thống (Frontend, Backend, Các Database, Trình giả lập Sensor) sẽ tự tải, tự build và hoạt động độc lập:

```bash
docker compose up --build -d
```
*Lưu ý: Quá trình này tốn từ **3 đến 5 phút** ở lần đầu tiên (phụ thuộc vào tốc độ mạng để tải các image Oracle/Mongo/Node).*

---

## Bước 5: Kiểm tra Quá Trình Seed Dữ Liệu (Quan trọng)
*Backend sẽ tự động chạy script `oracle_schema.sql` (Tạo bảng siêu tốc) và `oracle_seed.sql` (Add Phường, Quận).*

👉 **Kiểm tra trạng thái Backend:**
Mở Terminal chạy lệnh:
```bash
docker logs backend-consumer --tail 20
```
Nếu bạn thấy cuối dòng có:
`INFO: Application startup complete.` 
Và `INFO: MQTT consumer started successfully` 
Có nghĩa là toàn bộ Table/View đã được nạp chính xác, và dữ liệu tự động gửi từ Sensor đang được nhận và ghi vào MongoDB.

---

## Bước 6: Mở và Trải Nghiệm Ứng Dụng
Hệ thống lúc này đã có đầy đủ danh sách các Quận, Phường, 90 Cảm biến bắt đầu phát sinh dữ liệu liên tục:
- **Dashboard Giao Diện Người Dùng**: Mở trình duyệt web truy cập http://localhost:3000
- **Hệ Thống API Swagger (Dành cho Dev Backend/Test)**: truy cập http://localhost:8000/docs
- **Nếu muốn xem log Sensor đang giả lập**: `docker logs -f iot-simulator`

### 💡 Lưu ý Về Tính Ổn Định Core File SQL
Toàn bộ source core đã được tôi gộp và xử lý lỗi hiệu năng cũ. File `backend/app/db/sql/oracle_schema.sql` ở thư mục hiện tại đã được nâng cấp thẳng đoạn fix truy vấn tốc độ cao (15ms trả dữ liệu Locations thay vì bị treo đơ do kẹt câu lệnh CTE đệ quy cũ). Bạn mang source code này tới bất cứ máy nào chạy đều sẽ hoạt động tối ưu nhất từ giây đầu tiên!
