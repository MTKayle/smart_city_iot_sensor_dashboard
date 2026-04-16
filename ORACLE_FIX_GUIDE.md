# Hướng Dẫn Fix Oracle XE trên Windows

Oracle XE crash với "Break signaled" thường do thiếu resources hoặc config không phù hợp với Windows.

## Nguyên nhân chính:
1. **Thiếu RAM** - Oracle XE cần tối thiểu 2GB RAM
2. **Shared memory issues** trên Windows
3. **Volume permissions** trên Windows
4. **Healthcheck timeout** quá ngắn

---

## Giải pháp 1: Tăng Resources cho Docker Desktop (Khuyên dùng)

### Bước 1: Mở Docker Desktop Settings

1. Click icon Docker Desktop trong system tray
2. Settings → Resources

### Bước 2: Tăng Memory và CPU

- **Memory**: Tối thiểu 4GB (khuyên dùng 6GB)
- **CPUs**: Tối thiểu 2 cores
- **Swap**: 1GB
- **Disk image size**: 60GB

### Bước 3: Apply & Restart

Click "Apply & Restart"

---

## Giải pháp 2: Sửa docker-compose.yml

### Bước 1: Tăng resources cho Oracle container

Thêm resource limits vào docker-compose.yml:

```yaml
oracle-xe:
  image: gvenzl/oracle-xe:21-slim
  container_name: oracle-store
  ports:
    - "1521:1521"
  environment:
    ORACLE_PASSWORD: ${ORACLE_PASSWORD}
    ORACLE_DATABASE: ${ORACLE_DATABASE}
  volumes:
    - oracle-data:/opt/oracle/oradata
    - ./backend/app/db/sql/oracle_schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
    - ./backend/app/db/sql/oracle_seed.sql:/docker-entrypoint-initdb.d/02_seed.sql
  networks:
    - smart-city-network
  # Thêm phần này:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2'
      reservations:
        memory: 1G
        cpus: '1'
  # Tăng timeout cho healthcheck
  healthcheck:
    test: ["CMD", "healthcheck.sh"]
    interval: 30s
    timeout: 30s  # Tăng từ 10s lên 30s
    retries: 10   # Tăng từ 5 lên 10
    start_period: 120s  # Thêm start_period
  restart: unless-stopped
  # Thêm shared memory size
  shm_size: 1gb
```

### Bước 2: Apply changes

```bash
docker-compose down
docker-compose up -d
```

---

## Giải pháp 3: Xóa volume cũ và start lại

Oracle có thể bị corrupt data từ lần start trước.

```bash
# Stop tất cả
docker-compose down

# Xóa Oracle volume
docker volume rm smart_city_iot_sensor_dashboard_oracle-data

# Start lại
docker-compose up -d
```

---

## Giải pháp 4: Dùng Oracle XE 18c thay vì 21c

Image 21c có thể không stable trên Windows. Thử 18c:

```yaml
oracle-xe:
  image: gvenzl/oracle-xe:18-slim  # Đổi từ 21-slim sang 18-slim
  # ... rest of config
```

---

## Giải pháp 5: Disable init scripts tạm thời

Init scripts có thể gây crash. Test không có scripts trước:

```yaml
oracle-xe:
  image: gvenzl/oracle-xe:21-slim
  container_name: oracle-store
  ports:
    - "1521:1521"
  environment:
    ORACLE_PASSWORD: ${ORACLE_PASSWORD}
    ORACLE_DATABASE: ${ORACLE_DATABASE}
  volumes:
    - oracle-data:/opt/oracle/oradata
    # Comment out init scripts:
    # - ./backend/app/db/sql/oracle_schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
    # - ./backend/app/db/sql/oracle_seed.sql:/docker-entrypoint-initdb.d/02_seed.sql
  # ... rest of config
```

Sau khi Oracle start thành công, chạy scripts manually:

```bash
# Copy scripts vào container
docker cp backend/app/db/sql/oracle_schema.sql oracle-store:/tmp/
docker cp backend/app/db/sql/oracle_seed.sql oracle-store:/tmp/

# Execute scripts
docker exec -it oracle-store sqlplus system/OraclePass123@XEPDB1 @/tmp/oracle_schema.sql
docker exec -it oracle-store sqlplus system/OraclePass123@XEPDB1 @/tmp/oracle_seed.sql
```

---

## Giải pháp 6: Check Docker Desktop WSL2 backend

Nếu dùng WSL2 backend:

### Bước 1: Verify WSL2

```powershell
wsl --list --verbose
```

### Bước 2: Tăng memory cho WSL2

Tạo file `.wslconfig` trong `C:\Users\<YourUsername>\`:

```ini
[wsl2]
memory=6GB
processors=4
swap=2GB
```

### Bước 3: Restart WSL

```powershell
wsl --shutdown
```

Sau đó restart Docker Desktop.

---

## Giải pháp 7: Dùng PostgreSQL thay vì Oracle (Recommended)

PostgreSQL nhẹ hơn và stable hơn trên Windows:

### Bước 1: Thay Oracle bằng PostgreSQL trong docker-compose.yml

```yaml
postgres:
  image: postgres:15-alpine
  container_name: postgres-store
  ports:
    - "5432:5432"
  environment:
    POSTGRES_USER: ${POSTGRES_USER:-postgres}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    POSTGRES_DB: ${POSTGRES_DB:-smart_city}
  volumes:
    - postgres-data:/var/lib/postgresql/data
    - ./backend/app/db/sql/postgres_schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
    - ./backend/app/db/sql/postgres_seed.sql:/docker-entrypoint-initdb.d/02_seed.sql
  networks:
    - smart-city-network
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
  restart: unless-stopped

volumes:
  postgres-data:  # Thay oracle-data
```

### Bước 2: Convert SQL scripts

Oracle SQL → PostgreSQL SQL (tôi có thể giúp convert nếu cần)

### Bước 3: Update backend code

Thay `oracledb` bằng `psycopg2` hoặc `asyncpg`

---

## Verification Steps

Sau khi apply fix, verify Oracle đang chạy:

### 1. Check container status

```bash
docker-compose ps
```

Kết quả mong đợi:
```
NAME           STATUS
oracle-store   Up (healthy)
```

### 2. Check logs

```bash
docker-compose logs oracle-xe
```

Kết quả mong đợi (không có "Break signaled"):
```
DATABASE IS READY TO USE!
```

### 3. Test connection

```bash
docker exec -it oracle-store sqlplus system/OraclePass123@XEPDB1
```

Nếu connect thành công, gõ:
```sql
SELECT * FROM v$version;
EXIT;
```

### 4. Verify tables

```bash
docker exec -it oracle-store sqlplus system/OraclePass123@XEPDB1 <<EOF
SELECT table_name FROM user_tables;
EXIT;
EOF
```

Kết quả mong đợi:
```
LOCATIONS
SENSOR_REGISTRY
ALERTS
TELEMETRY_SUMMARY
```

---

## Recommended Solution Order

Thử theo thứ tự này:

1. ✅ **Giải pháp 1**: Tăng Docker Desktop resources (dễ nhất)
2. ✅ **Giải pháp 3**: Xóa volume cũ
3. ✅ **Giải pháp 2**: Sửa docker-compose với shm_size và healthcheck
4. ✅ **Giải pháp 5**: Disable init scripts tạm thời
5. ✅ **Giải pháp 7**: Dùng PostgreSQL (stable nhất)

---

## Nếu vẫn không được

Hãy gửi cho tôi:

```bash
# System info
docker info

# Oracle logs đầy đủ
docker-compose logs oracle-xe > oracle_logs.txt

# Docker Desktop version
docker --version
```

Tôi sẽ phân tích và đưa ra giải pháp cụ thể hơn.

---

## Quick Fix Script

Tôi tạo script tự động fix:

```bash
# fix_oracle.sh
#!/bin/bash

echo "Stopping all containers..."
docker-compose down

echo "Removing Oracle volume..."
docker volume rm smart_city_iot_sensor_dashboard_oracle-data

echo "Starting Oracle with increased resources..."
docker-compose up -d oracle-xe

echo "Waiting for Oracle to start (this may take 2-3 minutes)..."
sleep 180

echo "Checking Oracle status..."
docker-compose ps oracle-xe

echo "Checking Oracle logs..."
docker-compose logs oracle-xe | tail -20

echo "Done! Check if Oracle is healthy above."
```

Chạy:
```bash
bash fix_oracle.sh
```
