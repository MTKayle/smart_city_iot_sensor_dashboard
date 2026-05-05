# MapView Component

Interactive map visualization component for displaying IoT sensor locations with real-time status updates.

## Features

- **MapLibre GL JS Integration**: High-performance, open-source, interactive map rendering
- **No Access Token Required**: MapLibre is fully open-source, no paid token needed
- **Sensor Markers**: Visual representation of all sensor locations
- **Color-Coded Status**: Markers change color based on alert levels
  - 🟢 Green: Normal (no alerts or LOW alerts)
  - 🟡 Yellow: Warning (MEDIUM alerts)
  - 🔴 Red: High Alert (HIGH alerts)
- **Interactive Popups**: Click markers to view sensor details and current readings
- **Real-Time Updates**: Marker colors update automatically when new alerts arrive
- **Responsive Design**: Adapts to container size with minimum height of 400px

## Requirements

Validates requirements: 11.1, 11.2, 11.3, 11.4, 11.5

## Installation

The component requires `maplibre-gl` which is already installed:

```bash
npm install maplibre-gl
```

## Usage

### Basic Usage

```tsx
import { MapView } from './components/MapView';

function App() {
  return (
    <MapView
      sensors={sensors}
      locations={locations}
      alerts={alerts}
      telemetry={telemetryMap}
    />
  );
}
```

### With Custom Configuration

```tsx
<MapView
  sensors={sensors}
  locations={locations}
  alerts={alerts}
  telemetry={telemetryMap}
  center={[105.8342, 21.0278]} // Hanoi coordinates
  zoom={14}
  styleUrl="https://api.maptiler.com/maps/streets/style.json?key=YOUR_KEY"
/>
```

### With Real-Time WebSocket Updates

See `MapView.example.tsx` for a complete example with WebSocket integration.

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `sensors` | `Sensor[]` | Yes | - | Array of sensor objects |
| `locations` | `Location[]` | Yes | - | Array of location objects |
| `alerts` | `Alert[]` | Yes | - | Array of alert objects |
| `telemetry` | `Record<string, Telemetry>` | Yes | - | Map of sensor IDs to latest telemetry |
| `center` | `[number, number]` | No | `[106.6297, 10.8231]` | Map center coordinates [lng, lat] |
| `zoom` | `number` | No | `12` | Initial zoom level (0-22) |
| `styleUrl` | `string` | No | MapLibre demo tiles | Map style URL |

## Environment Variables

Configure the map style URL in your `.env` file (optional):

```env
VITE_MAP_STYLE_URL=https://demotiles.maplibre.org/style.json
```

### Free tile providers:
- **MapLibre demo**: `https://demotiles.maplibre.org/style.json`
- **MapTiler (free tier)**: `https://api.maptiler.com/maps/streets/style.json?key=YOUR_KEY`
- **Stadia Maps**: `https://tiles.stadiamaps.com/styles/alidade_smooth.json`

## Marker Colors

The component automatically determines marker colors based on alert status:

```typescript
const getMarkerColor = (sensorId: string, alerts: Alert[]): string => {
  // HIGH alerts → Red (#ef4444)
  // MEDIUM alerts → Yellow (#eab308)
  // No alerts or LOW alerts → Green (#22c55e)
};
```

## Popup Content

Clicking a marker displays:
- Sensor type (CO2, Noise, Temperature)
- Sensor ID
- Location name
- Current readings (if available):
  - CO2 level (ppm)
  - Noise level (dB)
  - Temperature (°C)
  - Timestamp of last reading

## Coordinate Generation

**Note**: The current implementation uses a demo coordinate generator that creates consistent but synthetic coordinates based on location IDs. In production, you should:

1. Add `latitude` and `longitude` fields to the `Location` model
2. Store actual GPS coordinates in the database
3. Update the component to use real coordinates:

```typescript
const location = locations.find(loc => loc.locationId === sensor.locationId);
const coords: [number, number] = [location.longitude, location.latitude];
```

## Styling

The component uses inline styles for the map container. To customize:

```tsx
<div style={{ width: '100%', height: '600px' }}>
  <MapView {...props} />
</div>
```

## Performance Considerations

- **Marker Reuse**: Existing markers are updated rather than recreated
- **Efficient Updates**: Only changed markers are modified when props update
- **Cleanup**: All markers and map resources are properly cleaned up on unmount
- **Lazy Loading**: Map tiles are loaded on-demand as users pan/zoom

## Browser Support

Requires browsers that support:
- WebGL (for MapLibre GL JS)
- ES6+ features
- Modern CSS

## Testing

Run tests with:

```bash
npm test -- MapView.test.tsx
```

The test suite includes:
- Component rendering
- Props handling
- Empty data handling
- Custom configuration

## Troubleshooting

### Map not displaying

1. Check that `maplibre-gl/dist/maplibre-gl.css` is imported
2. Ensure container has explicit height
3. Verify that the style URL is accessible

### Markers not updating

1. Verify `alerts` prop is changing (not mutated)
2. Check that sensor IDs match between sensors and alerts
3. Ensure component is receiving new props

### Performance issues

1. Limit number of sensors displayed
2. Reduce popup content complexity
3. Consider clustering for large datasets

## Future Enhancements

- [ ] Marker clustering for dense sensor networks
- [ ] Custom marker icons per sensor type
- [ ] Heatmap layer for environmental data
- [ ] Location filtering/search
- [ ] Export map as image
- [ ] Offline map support
