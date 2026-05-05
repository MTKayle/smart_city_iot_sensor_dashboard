# Smart City IoT Dashboard - Redesign Hoàn Chỉnh

## Tổng Quan

Đây là bản thiết kế lại hoàn toàn của giao diện Smart City IoT Dashboard với phong cách hiện đại, production-ready, lấy cảm hứng từ Uber, Google Maps, và Datadog.

## Đặc Điểm Chính

### 🎨 Thiết Kế
- **Dark Mode mặc định** - Giao diện tối chuyên nghiệp
- **Responsive Layout** - Tối ưu cho desktop
- **Clean & Minimal** - Thiết kế sạch sẽ, tối giản
- **Cards & Shadows** - Sử dụng thẻ với bóng đổ tinh tế
- **Rounded Corners** - Bo góc 8px-16px
- **Professional Color System** - Xanh dương, xanh lá, đỏ cho cảnh báo

### 🗂️ Cấu Trúc Layout

#### Sidebar (Có thể thu gọn)
- Tổng Quan (Dashboard)
- Bản Đồ (Map View) - Mặc định
- Cảm Biến (Sensors)
- Cụm Vùng (Clusters)
- Cảnh Báo (Alerts)
- Phân Tích (Analytics)
- Cài Đặt (Settings)

#### Top Navbar
- Thanh tìm kiếm (tìm cảm biến, vị trí)
- Chỉ báo trạng thái thời gian thực (TRỰC TIẾP / TRỄ)
- Chuông thông báo (cảnh báo)
- Hồ sơ người dùng

### 🗺️ Bản Đồ (Tính Năng Chính)

#### Tính Năng Bản Đồ
- Bản đồ tương tác toàn màn hình
- Hỗ trợ nhiều mức zoom
- Hiển thị markers cho cảm biến

#### Hệ Thống Lớp
Panel điều khiển lớp (floating panel góc trên bên phải):
- **Cảm Biến** - Bật/tắt hiển thị cảm biến
- **Cụm Vùng** - Bật/tắt hiển thị cụm
- **Cảnh Báo** - Bật/tắt hiển thị cảnh báo
- **Bản Đồ Nhiệt** - Bật/tắt heatmap

Hành vi theo zoom:
- **Zoom OUT** → Chỉ hiển thị cụm
- **Zoom MID** → Hiển thị cụm + giá trị tổng hợp
- **Zoom IN** → Hiển thị từng cảm biến riêng lẻ

#### Điều Khiển Bản Đồ Nhiệt
Dropdown hoặc floating panel với các chỉ số:
- PM2.5
- Nhiệt Độ
- Độ Ẩm
- CO2
- Tiếng Ồn

#### Tương Tác Cảm Biến
Khi click vào cảm biến, hiển thị popup card:
- ID Cảm Biến
- Vị Trí
- Tất cả chỉ số (5 giá trị)
- Pin / Tín hiệu
- Thời gian cập nhật cuối

#### Hiển Thị Cụm
Khi zoom out:
- Hiển thị bong bóng cụm
- Hiển thị giá trị trung bình
- Số lượng cảm biến
- Click → zoom in

#### Panel Chi Tiết Bên Phải
Khi chọn cảm biến/cụm:
- Panel chi tiết trượt từ bên phải
- Biểu đồ đường (line chart)
- Dữ liệu 1h / 24h gần nhất
- Hiển thị cảnh báo nếu có

### 🚨 Giao Diện Cảnh Báo
- Markers đỏ/vàng trên bản đồ
- Panel danh sách cảnh báo:
  - Mức độ (Thấp/Trung Bình/Cao/Nghiêm Trọng)
  - Loại (Ngưỡng / Dự Đoán / Bất Thường)
  - Click cảnh báo → highlight cảm biến trên bản đồ

### 📊 Dữ Liệu Thời Gian Thực
- Cập nhật dữ liệu mỗi 5 giây
- Animation mượt mà (không nhấp nháy)
- Sử dụng WebSocket simulation

### 📈 Hiển Thị Phân Tích
Dashboard biểu đồ:
- AQI (Chỉ số chất lượng không khí)
- Xu hướng PM2.5
- So sánh cụm
- Sử dụng cards và biểu đồ

## 🛠️ Công Nghệ

- **React** - Framework UI
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling (custom CSS variables)
- **Recharts** - Biểu đồ
- **MapLibre GL JS** - Bản đồ tương tác
- **Lucide React** - Icons

## 📁 Cấu Trúc File

```
frontend/src/
├── App.redesign.tsx              # Main app component
├── styles/
│   └── redesign.css              # Toàn bộ styles
└── components/redesign/
    ├── index.ts                  # Export tất cả components
    ├── Sidebar.tsx               # Sidebar navigation
    ├── TopNavbar.tsx             # Top navigation bar
    ├── Dashboard.tsx             # Dashboard overview
    ├── MapView.tsx               # Map view chính
    ├── MapLayerControl.tsx       # Điều khiển lớp bản đồ
    ├── HeatmapControl.tsx        # Điều khiển heatmap
    ├── SensorDetailPanel.tsx     # Panel chi tiết cảm biến
    ├── SensorsView.tsx           # Danh sách cảm biến
    ├── ClustersView.tsx          # Danh sách cụm
    ├── AlertsView.tsx            # Danh sách cảnh báo
    ├── AnalyticsView.tsx         # Phân tích & biểu đồ
    └── SettingsView.tsx          # Cài đặt
```

## 🚀 Cách Sử Dụng

### 1. Cài Đặt Dependencies

```bash
cd frontend
npm install recharts maplibre-gl lucide-react
npm install -D @types/maplibre-gl
```

### 2. Thay Thế App Component

Trong `frontend/src/main.tsx`, import App mới:

```typescript
import App from './App.redesign';
import './styles/redesign.css';
```

### 3. Chạy Development Server

```bash
npm run dev
```

## 🎨 Chi Tiết Thiết Kế

### Color System
- **Background Primary**: #0F172A (Slate 900)
- **Background Secondary**: #1E293B (Slate 800)
- **Background Tertiary**: #334155 (Slate 700)
- **Text Primary**: #F1F5F9 (Slate 100)
- **Text Secondary**: #94A3B8 (Slate 400)
- **Blue**: #3B82F6
- **Green**: #10B981
- **Yellow**: #F59E0B
- **Red**: #EF4444

### Spacing System
- XS: 4px
- SM: 8px
- MD: 16px
- LG: 24px
- XL: 32px

### Border Radius
- SM: 8px
- MD: 12px
- LG: 16px

## ✨ Tính Năng Nổi Bật

1. **Sidebar Thu Gọn** - Tiết kiệm không gian màn hình
2. **Real-time Status** - Chỉ báo trạng thái trực tiếp
3. **Interactive Map** - Bản đồ tương tác với nhiều lớp
4. **Smooth Animations** - Chuyển động mượt mà
5. **Responsive Charts** - Biểu đồ tự động điều chỉnh
6. **Detail Panels** - Panel chi tiết trượt mượt
7. **Toggle Switches** - Công tắc bật/tắt đẹp mắt
8. **Status Badges** - Huy hiệu trạng thái rõ ràng
9. **Vietnamese Language** - Toàn bộ giao diện tiếng Việt
10. **Professional Look** - Giao diện chuyên nghiệp, production-ready

## 📝 Ghi Chú

- Tất cả dữ liệu hiện tại là dữ liệu mẫu (dummy data)
- Cần tích hợp với API backend thực tế
- WebSocket cần được kết nối với backend
- Bản đồ sử dụng MapLibre GL JS với CartoDB Dark tiles
- Icons sử dụng Lucide React

## 🔄 Tích Hợp Backend

Để tích hợp với backend:

1. Thay thế dummy data bằng API calls
2. Kết nối WebSocket cho real-time updates
3. Implement authentication
4. Add error handling
5. Add loading states

## 📱 Responsive Design

Hiện tại tối ưu cho desktop. Để hỗ trợ mobile:
- Thêm hamburger menu cho sidebar
- Điều chỉnh grid layouts
- Tối ưu touch interactions
- Responsive charts

## 🎯 Next Steps

1. Tích hợp API backend
2. Thêm authentication
3. Implement WebSocket real-time
4. Thêm unit tests
5. Optimize performance
6. Add mobile responsive
7. Implement error boundaries
8. Add loading skeletons

---

**Thiết kế bởi**: Kiro AI Assistant
**Ngày**: 2026
**Phiên bản**: 1.0.0
