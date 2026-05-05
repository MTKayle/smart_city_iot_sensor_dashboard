# Leaderboard Component

Environmental quality ranking component that displays locations ordered by Clean Score with visual highlights for top performers.

## Features

- **Ranked Display**: Locations sorted by Clean Score (descending)
- **Top 3 Highlights**: Visual indicators for best-performing locations
  - 🥇 Gold background for 1st place
  - 🥈 Silver background for 2nd place
  - 🥉 Bronze background for 3rd place
- **Comprehensive Metrics**: Shows Avg CO2, Avg Noise, and Clean Score
- **Interactive Rows**: Click any location to zoom map to that area
- **Auto-Refresh**: Updates data every 60 seconds automatically
- **Color-Coded Scores**: Clean Score values colored by quality level
- **Responsive Design**: Adapts to container width

## Requirements

Validates requirements: 13.1, 13.2, 13.3, 13.4, 13.5

## Installation

No additional dependencies required beyond the base React setup.

## Usage

### Basic Usage

```tsx
import { Leaderboard } from './components/Leaderboard';

function App() {
  return <Leaderboard />;
}
```

### With Map Integration

```tsx
import { Leaderboard } from './components/Leaderboard';
import { MapView } from './components/MapView';

function Dashboard() {
  const mapRef = useRef<MapboxMap>(null);

  const handleLocationClick = (locationId: string) => {
    // Zoom map to selected location
    const location = locations.find(loc => loc.locationId === locationId);
    if (location && mapRef.current) {
      mapRef.current.flyTo({
        center: [location.longitude, location.latitude],
        zoom: 15,
      });
    }
  };

  return (
    <div>
      <MapView ref={mapRef} {...mapProps} />
      <Leaderboard onLocationClick={handleLocationClick} />
    </div>
  );
}
```

### Custom Refresh Interval

```tsx
<Leaderboard 
  refreshInterval={30000} // Refresh every 30 seconds
  onLocationClick={handleLocationClick}
/>
```

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `onLocationClick` | `(locationId: string) => void` | No | - | Callback when location row is clicked |
| `refreshInterval` | `number` | No | `60000` | Auto-refresh interval in milliseconds |

## Data Model

The component fetches data from `/api/leaderboard` endpoint which returns:

```typescript
interface LeaderboardEntry {
  locationId: string;      // Unique location identifier
  locationName: string;    // Display name
  avgCO2: number;         // Average CO2 in ppm
  avgNoise: number;       // Average noise in dB
  avgTemperature: number; // Average temperature in °C
  cleanScore: number;     // Calculated quality score (0-100)
  rank: number;           // Position in leaderboard (1-based)
}
```

## Clean Score Calculation

The Clean Score is calculated by the backend using:

```
normalized_CO2 = (avgCO2 / 2000) * 100
normalized_Noise = (avgNoise / 100) * 100
cleanScore = 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)
```

Higher scores indicate better environmental quality.

## Score Color Coding

Scores are color-coded for quick visual assessment:

- **Green** (≥80): Excellent air quality
- **Yellow** (60-79): Good air quality
- **Orange** (40-59): Moderate air quality
- **Red** (<40): Poor air quality

## Visual Highlights

### Top 3 Locations

The top 3 locations receive special visual treatment:

1. **1st Place**: Gold background (#fef3c7) + 🥇 medal
2. **2nd Place**: Silver background (#e5e7eb) + 🥈 medal
3. **3rd Place**: Bronze background (#fed7aa) + 🥉 medal

### Hover Effects

All rows have hover effects:
- Top 3: Darker shade of their highlight color
- Others: Light gray background

## Auto-Refresh Behavior

The component automatically refreshes data at the specified interval:

- Default: Every 60 seconds
- Configurable via `refreshInterval` prop
- Displays "Last updated" timestamp
- Continues refreshing until component unmounts
- Cleanup handled automatically

## Error Handling

The component handles various error states:

### Loading State
```
Loading leaderboard...
```

### Error State
```
Error: [error message]
[Retry Button]
```

### Empty State
```
No leaderboard data available
```

## Styling

The component uses inline styles for maximum portability. Key style features:

- Responsive table layout
- Box shadow for depth
- Rounded corners (8px)
- Hover transitions (0.2s)
- Centered text alignment
- Professional typography

## Performance Considerations

- **Efficient Updates**: Only re-renders when data changes
- **Interval Cleanup**: Properly cleans up timers on unmount
- **Memoization**: Consider wrapping in `React.memo()` if parent re-renders frequently
- **Data Limit**: Backend should limit results to reasonable number (e.g., top 100)

## Accessibility

Current implementation includes:

- Semantic HTML table structure
- Clickable rows with cursor pointer
- Clear visual hierarchy
- Color + text for status (not color alone)

Future improvements:

- [ ] Add ARIA labels for screen readers
- [ ] Keyboard navigation support
- [ ] Focus indicators for keyboard users
- [ ] Announce updates to screen readers

## Testing

Run tests with:

```bash
npm test -- Leaderboard.test.tsx
```

The test suite includes:
- Data rendering
- Loading/error/empty states
- Top 3 highlighting
- Click handlers
- Auto-refresh behavior
- Custom refresh intervals
- Cleanup on unmount

## Integration Example

Complete example with map integration:

```tsx
import { useState, useEffect } from 'react';
import { Leaderboard } from './components/Leaderboard';
import { MapView } from './components/MapView';
import { fetchLocations, fetchSensors, fetchAlerts } from './services/api';

function Dashboard() {
  const [locations, setLocations] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [mapCenter, setMapCenter] = useState([106.6297, 10.8231]);
  const [mapZoom, setMapZoom] = useState(12);

  useEffect(() => {
    // Load initial data
    Promise.all([
      fetchLocations(),
      fetchSensors(),
      fetchAlerts(),
    ]).then(([locs, sens, alts]) => {
      setLocations(locs);
      setSensors(sens);
      setAlerts(alts);
    });
  }, []);

  const handleLocationClick = (locationId) => {
    const location = locations.find(loc => loc.locationId === locationId);
    if (location) {
      // Zoom to location (using demo coordinates)
      setMapCenter([location.longitude, location.latitude]);
      setMapZoom(15);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px' }}>
      <MapView
        sensors={sensors}
        locations={locations}
        alerts={alerts}
        telemetry={{}}
        center={mapCenter}
        zoom={mapZoom}
      />
      <Leaderboard onLocationClick={handleLocationClick} />
    </div>
  );
}
```

## Troubleshooting

### Data not loading

1. Check API endpoint is accessible: `GET /api/leaderboard`
2. Verify CORS headers are configured
3. Check browser console for errors
4. Ensure backend is calculating Clean Scores

### Auto-refresh not working

1. Verify component is still mounted
2. Check `refreshInterval` prop value
3. Look for console errors during refresh
4. Ensure API endpoint is stable

### Click handler not firing

1. Verify `onLocationClick` prop is provided
2. Check for JavaScript errors
3. Ensure rows are not disabled by CSS
4. Test with browser dev tools

## Future Enhancements

- [ ] Sorting by different columns (CO2, Noise, etc.)
- [ ] Filtering by location type (City, District, Ward)
- [ ] Search/filter by location name
- [ ] Export leaderboard as CSV/PDF
- [ ] Historical trend indicators (↑↓)
- [ ] Pagination for large datasets
- [ ] Comparison mode (select multiple locations)
- [ ] Mobile-optimized responsive layout

## API Requirements

The backend must provide:

```
GET /api/leaderboard
Query Parameters:
  - limit (optional): Maximum entries to return

Response: LeaderboardEntry[]
Status Codes:
  - 200: Success
  - 500: Server error
```

## Related Components

- **MapView**: Displays sensor locations on map
- **ChartView**: Shows time-series data for sensors
- **AlertsPanel**: Displays recent alerts

## License

Part of the Smart City IoT Dashboard project.
