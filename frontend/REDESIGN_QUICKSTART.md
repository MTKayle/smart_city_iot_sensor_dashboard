# Quick Start - Redesign Dashboard

## 🚀 Bắt Đầu Nhanh (5 phút)

### 1. Cài Đặt Dependencies

```bash
cd frontend
npm install maplibre-gl recharts lucide-react
```

### 2. Thay Đổi Import

Mở file `frontend/src/main.tsx` và thay đổi:

```typescript
// Thay đổi từ:
import App from './App';
import './App.css';

// Sang:
import App from './App.redesign';
import './styles/redesign.css';
```

### 3. Chạy

```bash
npm run dev
```

### 4. Mở Browser

Truy cập: `http://localhost:5173`

## ✅ Kiểm Tra

Bạn sẽ thấy:
- ✅ Sidebar bên trái (có thể thu gọn)
- ✅ Top navbar với search bar
- ✅ Bản đồ tối màu (dark theme)
- ✅ Tất cả text bằng Tiếng Việt
- ✅ Smooth animations

## 🎯 Các View Có Sẵn

1. **Tổng Quan** - Dashboard với stats và charts
2. **Bản Đồ** - Interactive map với layers (mặc định)
3. **Cảm Biến** - Danh sách sensors dạng bảng
4. **Cụm Vùng** - Clusters dạng cards
5. **Cảnh Báo** - Alert list với filters
6. **Phân Tích** - Analytics dashboard
7. **Cài Đặt** - Settings

## 🗺️ Map Features

### Zoom Levels
- **Zoom < 13**: Hiển thị clusters (bong bóng lớn)
- **Zoom >= 13**: Hiển thị individual sensors (chấm nhỏ)

### Layer Controls (góc trên bên phải)
- Toggle Cảm Biến
- Toggle Cụm Vùng
- Toggle Cảnh Báo
- Toggle Bản Đồ Nhiệt

### Heatmap Metrics (góc dưới bên phải, khi bật)
- PM2.5
- Nhiệt Độ
- Độ Ẩm
- CO2
- Tiếng Ồn

## 🎨 Customization

### Thay Đổi Colors

Edit `frontend/src/styles/redesign.css`:

```css
:root {
  --blue: #3B82F6;    /* Màu chính */
  --green: #10B981;   /* Success */
  --yellow: #F59E0B;  /* Warning */
  --red: #EF4444;     /* Danger */
}
```

### Thay Đổi Map Style

Edit `frontend/src/components/redesign/MapView.tsx`:

```typescript
// Thay đổi từ dark sang light
tiles: [
  'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
  // ...
]
```

### Thay Đổi Default View

Edit `frontend/src/App.redesign.tsx`:

```typescript
// Thay đổi từ 'map' sang view khác
const [currentView, setCurrentView] = useState<ViewType>('dashboard');
```

## 🔧 Troubleshooting

### Lỗi: Module not found

```bash
# Cài lại dependencies
npm install
```

### Map không hiển thị

1. Kiểm tra console (F12)
2. Xem network tab có load tiles không
3. Thử refresh (Ctrl+R)

### Sidebar không toggle

1. Kiểm tra console có lỗi không
2. Thử click vào icon mũi tên

### Charts không hiển thị

```bash
# Cài lại recharts
npm install recharts
```

## 📱 Responsive

Hiện tại tối ưu cho **desktop**. Để xem trên mobile:
- Sidebar sẽ tự động thu gọn
- Charts sẽ stack vertically
- Tables có horizontal scroll

## 🔗 Tích Hợp API

### Thay Dummy Data

Edit các file view và thay thế dummy data:

```typescript
// Thay vì:
const sensors = [/* dummy data */];

// Dùng:
const { data: sensors } = useQuery('sensors', fetchSensors);
```

### WebSocket Real-time

```typescript
// Trong MapView.tsx
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws');
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Update sensors/telemetry
  };
  return () => ws.close();
}, []);
```

## 📚 Tài Liệu Đầy Đủ

- [REDESIGN_README.md](./REDESIGN_README.md) - Tài liệu chi tiết
- [REDESIGN_INSTALLATION.md](./REDESIGN_INSTALLATION.md) - Hướng dẫn cài đặt
- [REDESIGN_CHANGES.md](./REDESIGN_CHANGES.md) - Các thay đổi

## 💡 Tips

1. **Sidebar**: Click icon mũi tên để thu gọn/mở rộng
2. **Map**: Scroll để zoom, drag để di chuyển
3. **Sensors**: Click marker trên map để xem chi tiết
4. **Charts**: Hover để xem tooltip
5. **Search**: Gõ để tìm sensor hoặc location

## 🎉 Hoàn Thành!

Bạn đã sẵn sàng sử dụng redesign dashboard. Enjoy! 🚀

---

**Cần trợ giúp?** Xem [REDESIGN_README.md](./REDESIGN_README.md) để biết thêm chi tiết.
