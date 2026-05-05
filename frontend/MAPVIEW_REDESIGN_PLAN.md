# MapView Redesign Plan - Based on b_VJzFHvTPZTm

## Phân tích Implementation Tốt (b_VJzFHvTPZTm)

### 1. Zoom Logic ✅
```typescript
const showClusters = zoomLevel < 13 && layers.clusters
const showSensors = zoomLevel >= 13 && layers.sensors
```
- **Rõ ràng**: Chỉ dùng một điều kiện đơn giản
- **Không overlap**: Clusters và sensors không bao giờ hiển thị cùng lúc
- **Threshold cố định**: zoom < 13 = clusters, zoom >= 13 = sensors

### 2. State Management với Zustand ✅
```typescript
interface DashboardState {
  sensors: SensorData[]
  clusters: ClusterData[]
  zoomLevel: number
  layers: LayerState
  selectedSensor: SensorData | null
  isLive: boolean
}
```
- **Centralized state**: Tất cả state ở một nơi
- **Type-safe**: Full TypeScript support
- **Easy updates**: Simple actions

### 3. Realtime Data Updates ✅
```typescript
export function updateSensorData(sensor: SensorData): SensorData {
  const pm25 = Math.max(5, Math.min(200, sensor.pm25 + randomInRange(-5, 5)))
  const co2 = Math.max(350, Math.min(2000, sensor.co2 + randomInRange(-30, 30)))
  return { ...sensor, pm25, co2, lastUpdated: new Date(), status: generateSensorStatus(pm25, co2) }
}
```
- **Smooth changes**: Chỉ thay đổi nhỏ mỗi lần update
- **Bounded values**: Min/max để tránh giá trị bất thường
- **Status recalculation**: Tự động update status

### 4. Marker Icons với Animation ✅
```typescript
const createSensorIcon = (status: SensorData['status']) => {
  return L.divIcon({
    html: `
      <div class="relative flex items-center justify-center">
        <div class="absolute w-8 h-8 rounded-full animate-ping opacity-40" 
             style="background-color: ${colors[status]}"></div>
        <div class="relative w-4 h-4 rounded-full border-2 border-white shadow-lg" 
             style="background-color: ${colors[status]}"></div>
      </div>
    `,
  })
}
```
- **Pulse animation**: Hiệu ứng ping cho markers
- **Status colors**: Màu sắc theo trạng thái
- **Clean HTML**: Đơn giản, dễ maintain

### 5. Detail Panel Slide-in ✅
```typescript
<div className={cn(
  "absolute top-0 right-0 h-full w-96 bg-card border-l",
  "transform transition-transform duration-300",
  detailPanelOpen ? "translate-x-0" : "translate-x-full"
)}>
```
- **Smooth transition**: CSS transform
- **Fixed width**: 384px (w-96)
- **Overlay**: Absolute positioning

### 6. Heatmap với Canvas ✅
```typescript
const drawHeatmap = () => {
  sensors.forEach(sensor => {
    const point = map.latLngToContainerPoint([sensor.lat, sensor.lng])
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius)
    // Color based on intensity
    ctx.fillStyle = gradient
    ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2)
  })
}
```
- **Canvas rendering**: Performance tốt
- **Radial gradient**: Smooth color transitions
- **Dynamic colors**: Dựa trên intensity

## Plan Áp Dụng vào Redesign

### Phase 1: Fix Zoom Logic ✅ (Đã làm)
- [x] Sử dụng `useMemo` cho zoomLevel
- [x] Điều kiện rõ ràng: `zoomLevel === 'out'`, `'mid'`, `'in'`
- [x] Không overlap giữa clusters và sensors

### Phase 2: Improve Markers (TODO)
- [ ] Thêm pulse animation cho sensor markers
- [ ] Cải thiện cluster markers với size động
- [ ] Smooth color transitions

### Phase 3: Realtime Updates (TODO)
- [ ] Implement smooth data updates (không jump đột ngột)
- [ ] Bounded value changes
- [ ] Auto status recalculation

### Phase 4: Detail Panel (TODO)
- [ ] Slide-in animation từ bên phải
- [ ] Charts với Recharts
- [ ] Metric cards với trends

### Phase 5: Heatmap (TODO)
- [ ] Canvas-based heatmap layer
- [ ] Metric selector
- [ ] Smooth color gradients

## Code Changes Needed

### 1. MapView.tsx
```typescript
// Current (có vấn đề)
const sensorsWithData = sensors.map(...)  // Re-calculate mỗi render
const clusters = createClusters(...)      // Re-calculate mỗi render

// New (tốt hơn) - ĐÃ FIX
const sensorsWithData = useMemo(() => sensors.map(...), [sensors, telemetryMap])
const clusters = useMemo(() => createClusters(...), [sensorsWithData])
```

### 2. Zoom Logic
```typescript
// Current
const getZoomLevel = (zoom: number): 'out' | 'mid' | 'in' => {
  if (zoom < 11) return 'out'
  if (zoom < 13) return 'mid'
  return 'in'
}

// Recommendation: Giữ nguyên, đã tốt
```

### 3. Marker Rendering
```typescript
// Current: Tạo markers trong useEffect
useEffect(() => {
  // Clear và re-create tất cả markers
}, [zoomLevel, sensorsWithData, clusters])

// Recommendation: Giữ nguyên approach này, nhưng thêm animations
```

## Comparison

| Feature | Current Redesign | b_VJzFHvTPZTm | Status |
|---------|------------------|---------------|--------|
| Zoom Logic | ✅ Good | ✅ Good | Equal |
| State Management | React useState | Zustand | Could improve |
| Marker Animation | ❌ None | ✅ Pulse | Need to add |
| Detail Panel | ✅ Has | ✅ Slide-in | Could improve |
| Heatmap | ❌ Basic | ✅ Canvas | Need to improve |
| Realtime Updates | ✅ WebSocket | ✅ Mock updates | Equal |
| Performance | ✅ useMemo | ✅ Good | Equal |

## Recommendations

### High Priority
1. ✅ **Fix marker jumping** - DONE với useMemo
2. **Add pulse animation** cho sensor markers
3. **Improve detail panel** với slide-in animation

### Medium Priority
4. **Canvas-based heatmap** thay vì basic implementation
5. **Smooth data updates** với bounded changes
6. **Better cluster visualization** với dynamic sizing

### Low Priority
7. Consider Zustand cho state management (optional)
8. Add more chart types trong detail panel
9. Implement alert indicators như b_VJzFHvTPZTm

## Next Steps

1. Review plan này với team
2. Implement pulse animation cho markers
3. Improve detail panel với better animations
4. Test performance với nhiều sensors
5. Add canvas-based heatmap

## Notes

- b_VJzFHvTPZTm sử dụng Leaflet thay vì MapLibre
- Chúng ta đang dùng MapLibre (tốt hơn cho production)
- Có thể học UI/UX patterns nhưng giữ MapLibre
- Zustand là optional, React Context + useState cũng đủ tốt
