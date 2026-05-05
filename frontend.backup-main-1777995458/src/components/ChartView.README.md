# ChartView Component

Time-series chart visualization component for displaying sensor telemetry data.

## Features

- **Three Line Charts**: Displays CO2 (ppm), Noise (dB), and Temperature (°C) metrics
- **Historical Data**: Fetches last 100 telemetry readings on mount
- **Real-time Updates**: Automatically updates charts when new telemetry arrives via WebSocket
- **Time Range Filtering**: Toggle between 1h, 6h, and 24h time ranges
- **Auto-scaling Y-axis**: Dynamically adjusts Y-axis range based on data with 10% padding
- **Responsive Design**: Charts adapt to container size

## Requirements Validated

- **12.1**: Display line charts for CO2, Noise, and Temperature using Chart.js
- **12.2**: Fetch and display last 100 telemetry readings for selected sensor
- **12.3**: Update charts in real-time via WebSocket
- **12.4**: Display time on X-axis and metric values on Y-axis with units
- **12.5**: Allow time range selection (1h, 6h, 24h)

## Usage

```tsx
import { ChartView } from './components/ChartView';

function App() {
  return (
    <ChartView 
      sensorId="sensor-001"
      wsUrl="ws://localhost:8000/ws"
    />
  );
}
```

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `sensorId` | `string` | Yes | - | ID of the sensor to display telemetry for |
| `wsUrl` | `string` | No | `'ws://backend:8000/ws'` | WebSocket server URL for real-time updates |

## Component States

### Loading State
Displays a loading message while fetching initial telemetry data.

### Error State
Shows error message if data fetch fails.

### Empty State
Displays helpful message when no data is available for the selected time range.

### Data Display
Shows three line charts with time range selector and data count.

## Data Flow

1. **Initial Load**: Component fetches last 100 telemetry readings via REST API
2. **Data Sorting**: Sorts readings by timestamp ascending for chronological display
3. **Time Filtering**: Filters data based on selected time range (1h/6h/24h)
4. **Chart Rendering**: Displays three separate charts with auto-scaled Y-axes
5. **Real-time Updates**: WebSocket messages add new data points (max 100 retained)

## Chart Configuration

### CO2 Chart
- **Color**: Blue (`rgb(59, 130, 246)`)
- **Unit**: ppm (parts per million)
- **Y-axis**: Auto-scaled with 10% padding

### Noise Chart
- **Color**: Yellow (`rgb(234, 179, 8)`)
- **Unit**: dB (decibels)
- **Y-axis**: Auto-scaled with 10% padding

### Temperature Chart
- **Color**: Red (`rgb(239, 68, 68)`)
- **Unit**: °C (Celsius)
- **Y-axis**: Auto-scaled with 10% padding

## Time Range Filtering

The component filters telemetry data based on the selected time range:

- **1h**: Shows data from the last 1 hour
- **6h**: Shows data from the last 6 hours
- **24h**: Shows data from the last 24 hours (default)

Time range selection is preserved during real-time updates.

## Real-time Updates

The component connects to the WebSocket server and:

1. Listens for telemetry messages
2. Filters messages by `sensorId` (ignores other sensors)
3. Appends new data points to the chart
4. Maintains a rolling window of last 100 readings
5. Automatically updates all three charts

## Performance Considerations

- **Data Limit**: Maintains maximum of 100 telemetry readings in memory
- **Efficient Filtering**: Time range filtering is performed on-demand
- **Memoization**: Chart options are created per render but could be memoized for optimization
- **WebSocket**: Single connection shared across component lifecycle

## Styling

The component uses inline styles for simplicity and portability:

- **Container**: Full width with 16px padding
- **Time Range Buttons**: Centered with hover effects
- **Charts**: Grid layout with white background and subtle shadows
- **Chart Height**: Fixed at 300px per chart

## Error Handling

- **API Errors**: Displays error message with details
- **WebSocket Errors**: Handled by `useWebSocket` hook (automatic reconnection)
- **Invalid Data**: Gracefully handles empty or malformed data

## Testing

The component includes comprehensive tests covering:

- Initial data loading
- Time range selection
- Real-time WebSocket updates
- Error handling
- Empty states
- Data sorting and limiting

Run tests with:
```bash
npm test -- ChartView.test.tsx
```

## Dependencies

- **react**: Core React library
- **chart.js**: Chart rendering engine
- **react-chartjs-2**: React wrapper for Chart.js
- **../services/api**: API client for fetching telemetry
- **../hooks/useWebSocket**: WebSocket connection management
- **../types**: TypeScript type definitions

## Future Enhancements

Potential improvements for future iterations:

- [ ] Export chart data to CSV
- [ ] Zoom and pan functionality
- [ ] Custom date range picker
- [ ] Chart type selection (line, bar, area)
- [ ] Multiple sensor comparison
- [ ] Threshold indicators on charts
- [ ] Chart annotations for alerts
- [ ] Performance optimization with memoization
