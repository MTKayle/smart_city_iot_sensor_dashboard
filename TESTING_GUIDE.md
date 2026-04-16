# Hướng Dẫn Test Frontend và Backend

## 📋 Mục Lục
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Integration Testing](#integration-testing)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Backend Testing

### Cài Đặt Môi Trường Test

```bash
cd backend

# Cài đặt dependencies
pip install -r requirements.txt

# Cài đặt pytest và coverage tools
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Cấu Hình Environment Variables

Tạo file `.env` trong thư mục `backend/`:

```bash
# Database
MONGODB_URI=mongodb://admin:password@localhost:27017
ORACLE_USER=system
ORACLE_PASSWORD=oracle
ORACLE_DSN=localhost:1521/XEPDB1

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_TOPIC=sensors/telemetry

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### Chạy Tests

#### 1. Chạy Tất Cả Tests

```bash
cd backend
pytest tests/
```

#### 2. Chạy Test Cụ Thể

```bash
# Test models
pytest tests/test_models.py

# Test MongoDB
pytest tests/test_mongodb.py

# Test Oracle
pytest tests/test_oracle.py

# Test MQTT Consumer
pytest tests/test_mqtt_consumer.py

# Test API Routes
pytest tests/test_api_routes.py

# Test WebSocket
pytest tests/test_websocket.py

# Test Scheduler
pytest tests/test_scheduler.py
```

#### 3. Chạy Test Với Coverage

```bash
# Xem coverage report
pytest --cov=app tests/

# Tạo HTML coverage report
pytest --cov=app --cov-report=html tests/

# Mở report trong browser
# File sẽ được tạo tại: htmlcov/index.html
```

#### 4. Chạy Test Với Output Chi Tiết

```bash
# Verbose mode
pytest -v tests/

# Show print statements
pytest -s tests/

# Kết hợp cả hai
pytest -vs tests/
```

### Các Test Files Quan Trọng

| File | Mô Tả |
|------|-------|
| `test_models.py` | Test Pydantic models validation |
| `test_mongodb.py` | Test MongoDB operations |
| `test_oracle.py` | Test Oracle database operations |
| `test_mqtt_consumer.py` | Test MQTT message consumption |
| `test_mqtt_integration.py` | Test MQTT end-to-end flow |
| `test_api_routes.py` | Test REST API endpoints |
| `test_websocket.py` | Test WebSocket connections |
| `test_scheduler.py` | Test scheduled tasks |
| `test_broadcast_integration.py` | Test real-time broadcast |

### Chạy Integration Tests

```bash
# Đảm bảo các services đang chạy
docker-compose up -d mongodb oracle mosquitto

# Chạy integration tests
pytest tests/test_mqtt_integration.py
pytest tests/test_broadcast_integration.py
```

---

## ⚛️ Frontend Testing

### Cài Đặt Môi Trường Test

```bash
cd frontend

# Cài đặt dependencies
npm install

# Dependencies đã bao gồm:
# - vitest: Test runner
# - @testing-library/react: React testing utilities
# - @testing-library/jest-dom: Custom matchers
# - jsdom: DOM implementation
```

### Cấu Hình Environment Variables

Tạo file `.env` trong thư mục `frontend/`:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_MAPBOX_TOKEN=pk.your_mapbox_token_here
```

### Chạy Tests

#### 1. Chạy Tất Cả Tests (Single Run)

```bash
cd frontend
npm test
```

#### 2. Chạy Tests Ở Watch Mode

```bash
npm run test:watch
```

#### 3. Chạy Tests Với UI

```bash
npm run test:ui
```

Sau đó mở browser tại: `http://localhost:51204/__vitest__/`

#### 4. Chạy Test Cụ Thể

```bash
# Test một file cụ thể
npm test -- src/components/MapView.test.tsx

# Test với pattern matching
npm test -- MapView

# Test với coverage
npm test -- --coverage
```

### Các Test Files Quan Trọng

| File | Mô Tả |
|------|-------|
| `App.test.tsx` | Test main App component |
| `components/MapView.test.tsx` | Test MapView component |
| `components/ChartView.test.tsx` | Test ChartView component |
| `components/Leaderboard.test.tsx` | Test Leaderboard component |
| `context/AppContext.test.tsx` | Test React Context |
| `hooks/useWebSocket.test.ts` | Test WebSocket hook |

### Cấu Trúc Test Frontend

```typescript
// Example: Component test
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import MyComponent from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

---

## 🔄 Integration Testing

### Chạy Full Stack Test

#### 1. Khởi Động Tất Cả Services

```bash
# Từ thư mục root
docker-compose up -d
```

Services sẽ chạy:
- MongoDB: `localhost:27017`
- Oracle: `localhost:1521`
- MQTT Broker: `localhost:1883`
- Backend API: `localhost:8000`
- Frontend: `localhost:5173`

#### 2. Verify Services

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:5173

# Check MQTT
docker-compose logs mosquitto
```

#### 3. Chạy End-to-End Tests

```bash
# Backend integration tests
cd backend
pytest tests/test_mqtt_integration.py
pytest tests/test_broadcast_integration.py

# Frontend tests với backend running
cd frontend
npm test
```

### Test Workflow Hoàn Chỉnh

```bash
# 1. Start infrastructure
docker-compose up -d mongodb oracle mosquitto

# 2. Run backend tests
cd backend
pytest tests/

# 3. Start backend
python -m app.main &

# 4. Run frontend tests
cd ../frontend
npm test

# 5. Manual testing
npm run dev
# Mở browser: http://localhost:5173
```

---

## 🐛 Troubleshooting

### Backend Issues

#### Import Errors

```bash
# Thêm backend vào PYTHONPATH
export PYTHONPATH=$PWD/backend:$PYTHONPATH

# Hoặc chạy từ thư mục backend
cd backend
python -m pytest tests/
```

#### Database Connection Errors

```bash
# Check MongoDB
docker-compose logs mongodb
mongosh mongodb://admin:password@localhost:27017

# Check Oracle
docker-compose logs oracle
sqlplus system/oracle@localhost:1521/XEPDB1
```

#### MQTT Connection Errors

```bash
# Check MQTT broker
docker-compose logs mosquitto

# Test MQTT connection
mosquitto_sub -h localhost -p 1883 -t "sensors/#"
```

### Frontend Issues

#### Environment Variables Not Loading

```bash
# Đảm bảo file .env tồn tại
ls -la frontend/.env

# Restart dev server
npm run dev
```

#### Test Failures

```bash
# Clear cache và chạy lại
rm -rf node_modules/.vite
npm test
```

#### WebSocket Connection Issues

```bash
# Check backend WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  http://localhost:8000/ws
```

### Common Test Commands

```bash
# Backend: Chạy test với verbose output
cd backend
pytest -vv tests/

# Backend: Chạy test và dừng ở failure đầu tiên
pytest -x tests/

# Backend: Chạy test với pdb debugger
pytest --pdb tests/

# Frontend: Chạy test với UI
cd frontend
npm run test:ui

# Frontend: Chạy test với coverage
npm test -- --coverage

# Frontend: Watch mode cho một file
npm run test:watch -- MapView
```

---

## 📊 Test Coverage Goals

### Backend
- Unit Tests: >80% coverage
- Integration Tests: Critical paths covered
- API Tests: All endpoints tested

### Frontend
- Component Tests: >70% coverage
- Hook Tests: All custom hooks tested
- Integration Tests: Key user flows tested

---

## 🚀 Quick Start Commands

### Backend Testing
```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
pytest tests/ --cov=app
```

### Frontend Testing
```bash
cd frontend
npm install
npm test
```

### Full Stack Testing
```bash
docker-compose up -d
cd backend && pytest tests/
cd ../frontend && npm test
```
