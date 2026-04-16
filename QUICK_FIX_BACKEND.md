# Quick Fix - Chạy Backend Không Cần Oracle

Backend đang crash vì không connect được Oracle. Đây là cách fix nhanh để test được ngay.

## Option 1: Comment out Oracle dependency trong docker-compose

### Sửa docker-compose.yml

Tìm phần `backend` và sửa `depends_on`:

```yaml
backend:
  # ... other config
  depends_on:
    mosquitto:
      condition: service_started
    mongodb:
      condition: service_healthy
    # Comment out Oracle dependency:
    # oracle-xe:
    #   condition: service_healthy
```

### Restart

```bash
docker-compose down
docker-compose up -d mosquitto mongodb backend iot-simulator frontend
```

## Option 2: Mock Oracle trong code (Recommended)

Sửa backend code để handle Oracle connection failure gracefully.

### Chạy lệnh này:

```bash
# Stop backend
docker-compose stop backend

# Start lại backend với restart policy
docker-compose up -d backend

# Xem logs
docker-compose logs -f backend
```

## Option 3: Dùng environment variable để disable Oracle

Thêm vào `.env`:

```
ORACLE_ENABLED=false
```

Sau đó sửa code backend để check biến này trước khi connect Oracle.

## Verify Backend Running

```bash
# Check status
docker-compose ps backend

# Should show: Up

# Test API
curl http://localhost:8000/

# Should return JSON with API info
```

## Test Frontend Connection

Sau khi backend chạy, refresh frontend:

```
http://localhost:3000
```

Nếu vẫn lỗi, check browser console (F12) để xem error message cụ thể.
