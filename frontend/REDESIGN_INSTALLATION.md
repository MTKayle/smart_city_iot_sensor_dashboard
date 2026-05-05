# Hướng Dẫn Cài Đặt Redesign

## Bước 1: Cài Đặt Dependencies

Chạy lệnh sau trong thư mục `frontend`:

```bash
npm install maplibre-gl recharts lucide-react
```

Hoặc nếu dùng yarn:

```bash
yarn add maplibre-gl recharts lucide-react
```

## Bước 2: Cài Đặt Type Definitions (nếu dùng TypeScript)

```bash
npm install -D @types/maplibre-gl
```

## Bước 3: Kiểm Tra package.json

Đảm bảo các dependencies sau đã được thêm vào `package.json`:

```json
{
  "dependencies": {
    "maplibre-gl": "^4.0.0",
    "recharts": "^2.10.0",
    "lucide-react": "^0.300.0"
  },
  "devDependencies": {
    "@types/maplibre-gl": "^3.0.0"
  }
}
```

## Bước 4: Import CSS của MapLibre

CSS của MapLibre đã được import trong component, nhưng đảm bảo rằng nó được load:

```typescript
import 'maplibre-gl/dist/maplibre-gl.css';
```

## Bước 5: Cập Nhật main.tsx

Thay đổi import trong `frontend/src/main.tsx`:

```typescript
import App from './App.redesign';
import './styles/redesign.css';
```

## Bước 6: Chạy Development Server

```bash
npm run dev
```

## Lỗi Thường Gặp

### Lỗi: Cannot find module 'lucide-react'

**Giải pháp**: Cài đặt lại dependencies:
```bash
npm install lucide-react
```

### Lỗi: Cannot find module 'maplibre-gl'

**Giải pháp**: Cài đặt maplibre-gl:
```bash
npm install maplibre-gl
npm install -D @types/maplibre-gl
```

### Lỗi: Cannot find module 'recharts'

**Giải pháp**: Cài đặt recharts:
```bash
npm install recharts
```

### Bản đồ không hiển thị

**Giải pháp**: 
1. Kiểm tra console để xem có lỗi CSS không
2. Đảm bảo CSS của maplibre đã được import
3. Kiểm tra network tab để xem tiles có load được không

### Markers không hiển thị

**Giải pháp**:
1. Kiểm tra dữ liệu sensors và clusters có đúng format không
2. Kiểm tra zoom level (sensors chỉ hiển thị khi zoom >= 13)
3. Kiểm tra layers toggle có bật không

## Kiểm Tra Cài Đặt

Sau khi cài đặt xong, bạn có thể kiểm tra bằng cách:

1. Mở browser console (F12)
2. Không có lỗi import
3. Bản đồ hiển thị đúng
4. Sidebar và navbar hoạt động
5. Có thể toggle giữa các views

## Cấu Trúc File Cần Thiết

```
frontend/src/
├── App.redesign.tsx              ✓ Main app
├── styles/
│   └── redesign.css              ✓ Styles
└── components/redesign/
    ├── Sidebar.tsx               ✓
    ├── TopNavbar.tsx             ✓
    ├── Dashboard.tsx             ✓
    ├── MapView.tsx               ✓
    ├── MapLayerControl.tsx       ✓
    ├── HeatmapControl.tsx        ✓
    ├── SensorDetailPanel.tsx     ✓
    ├── SensorsView.tsx           ✓
    ├── ClustersView.tsx          ✓
    ├── AlertsView.tsx            ✓
    ├── AnalyticsView.tsx         ✓
    └── SettingsView.tsx          ✓
```

## Next Steps

Sau khi cài đặt thành công:

1. Tích hợp với API backend
2. Kết nối WebSocket cho real-time data
3. Thêm authentication
4. Implement error handling
5. Add loading states
6. Optimize performance

---

**Lưu ý**: Đây là bản redesign hoàn toàn mới, không ảnh hưởng đến code hiện tại. Bạn có thể giữ cả hai phiên bản và chuyển đổi bằng cách thay đổi import trong `main.tsx`.
