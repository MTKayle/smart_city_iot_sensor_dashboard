# Map Layer Implementation - Zoom-Based Display

## Tổng quan

MapView đã được cập nhật để hiển thị dữ liệu theo layer dựa trên zoom level với realtime data updates.

## Các Zoom Levels

### 1. ZOOM OUT (< 11)
**Hiển thị:** CHỈ clusters - KHÔNG có sensors

- Hiển thị các cluster markers với kích thước tùy thuộc vào số lượng sensors
- Màu sắc dựa trên trạng thái (critical/warning/normal)
- Số lượng sensors hiển thị trong marker
- Không có popup hover
- **Sensors hoàn toàn ẩn ở zoom level này**

### 2. ZOOM MID (11-13)
**Hiển thị:** CHỈ clusters + Aggregated Values - KHÔNG có sensors

- Hiển thị cluster markers tương tự ZOOM OUT
- **Hover để xem popup** với dữ liệu tổng hợp:
  - PM2.5 trung bình
  - Temperature trung bình
  - Humidity trung bình
  - CO2 trung bình
- Popup tự động ẩn khi di chuột ra ngoài
- **Sensors hoàn toàn ẩn ở zoom level này**

### 3. ZOOM IN (≥ 13)
**Hiển thị:** CHỈ individual sensors - KHÔNG có clusters

- Hiển thị từng sensor riêng lẻ
- **Hover để xem popup** với dữ liệu realtime:
  - PM2.5, Temperature, Humidity
  - CO2, Noise, Battery
  - Thời gian cập nhật cuối
- **Click để xem chi tiết** trong SensorDetailPanel
- Popup tự động ẩn khi di chuột ra ngoài
- **Clusters hoàn toàn ẩn ở zoom level này**

### Zoom Level Indicator
- Hiển thị ở góc trên bên trái
- 🔍 Clusters: Zoom level < 11
- 🔍 Clusters + Data: Zoom level 11-13
- 🔍 Sensors: Zoom level ≥ 13

## Realtime Data Updates

### Cập nhật mỗi 5 giây
- Dữ liệu từ WebSocket được cập nhật tự động
- Popup content được refresh khi có dữ liệu mới
- Không có flickering nhờ smooth transitions

### Smooth Animations
```css
/* Marker transitions */
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

/* Fade in animation */
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

/* Popup slide in */
@keyframes popupSlideIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

## Clustering Algorithm

### Grid-Based Clustering
```typescript
const createClusters = (sensors: SensorWithTelemetry[], gridSize: number = 0.02): ClusterData[] => {
  // Group sensors by grid cells
  // Calculate average values for each cluster
  // Determine cluster status based on averages
}
```

- Grid size: 0.02 degrees (~2.2km)
- Tự động tính toán giá trị trung bình
- Status dựa trên thresholds:
  - Critical: PM2.5 > 100 hoặc CO2 > 2000
  - Warning: PM2.5 > 50 hoặc CO2 > 1000
  - Normal: còn lại

## Tương tác người dùng

### Hover (Di chuột)
- **ZOOM MID:** Hiển thị cluster aggregated data
- **ZOOM IN:** Hiển thị sensor realtime data
- Popup tự động xuất hiện/ẩn
- Smooth animation

### Click (Nhấn chuột)
- **ZOOM IN:** Mở SensorDetailPanel
- Hiển thị chi tiết đầy đủ của sensor
- Charts và historical data
- Có thể đóng panel bằng nút X

## Màu sắc Status

```typescript
const getMarkerColor = (status: string) => {
  switch (status) {
    case 'critical': return '#EF4444'; // Red
    case 'warning': return '#F59E0B';  // Orange
    case 'normal': return '#10B981';   // Green
    default: return '#6B7280';         // Gray
  }
};
```

## Performance Optimization

### Marker Management
- Sử dụng `Map` để quản lý markers và popups
- Clear markers cũ trước khi render mới
- Tránh memory leaks

### Smooth Transitions
- CSS transitions thay vì JavaScript animations
- Hardware-accelerated transforms
- Debounced zoom events

### Realtime Updates
- Chỉ update popup content, không re-render markers
- Separate effect cho telemetry updates
- Minimal DOM manipulation

## Cấu trúc Code

```typescript
// Refs for marker management
const markersRef = useRef<Map<string, maplibregl.Marker>>(new Map());
const clusterMarkersRef = useRef<Map<string, maplibregl.Marker>>(new Map());
const popupsRef = useRef<Map<string, maplibregl.Popup>>(new Map());

// Zoom level detection
const getZoomLevel = (zoom: number): 'out' | 'mid' | 'in' => {
  if (zoom < 11) return 'out';
  if (zoom < 13) return 'mid';
  return 'in';
};

// Effect 1: Render markers based on zoom level
useEffect(() => {
  // Clear old markers
  // Render appropriate markers for current zoom level
}, [mapLoaded, layers, sensorsWithData, clusters, zoomLevel]);

// Effect 2: Update popup content for realtime data
useEffect(() => {
  // Update popup HTML with new telemetry data
}, [telemetryMap, sensorsWithData, mapLoaded, zoomLevel]);
```

## Testing

### Manual Testing
1. Zoom out → Chỉ thấy clusters
2. Zoom mid → Hover vào cluster → Thấy aggregated data
3. Zoom in → Thấy individual sensors
4. Hover vào sensor → Thấy realtime data
5. Click vào sensor → Mở detail panel
6. Đợi 5 giây → Data tự động cập nhật

### Expected Behavior
- ✅ Không có flickering khi zoom
- ✅ Popup xuất hiện/ẩn mượt mà
- ✅ Data cập nhật realtime
- ✅ Marker colors phản ánh status
- ✅ Smooth animations

## Troubleshooting

### Markers không hiển thị
- Kiểm tra `layers.sensors` và `layers.clusters` enabled
- Kiểm tra `sensorsWithData` có dữ liệu
- Kiểm tra zoom level

### Popup không hiển thị
- Kiểm tra event listeners (mouseenter/mouseleave)
- Kiểm tra popup được add vào map
- Kiểm tra z-index

### Data không update
- Kiểm tra WebSocket connection
- Kiểm tra `telemetryMap` được update
- Kiểm tra effect dependencies

## Future Enhancements

1. **Advanced Clustering**
   - Hierarchical clustering
   - Dynamic grid size based on zoom
   - Cluster splitting animation

2. **Performance**
   - Virtual markers (only render visible)
   - WebGL rendering for large datasets
   - Marker pooling

3. **Interactions**
   - Cluster expansion on click
   - Multi-sensor selection
   - Custom popup templates

4. **Animations**
   - Marker movement animation
   - Data change pulse effect
   - Zoom transition effects
