# AppContext - Global State Management

## Overview

The `AppContext` provides centralized state management for the Smart City IoT Dashboard using React Context API. It manages application-wide state including sensors, locations, alerts, selected sensor, and WebSocket connection status.

## Features

- **Centralized State**: Single source of truth for global application state
- **WebSocket Integration**: Automatically updates state when real-time messages are received
- **API Integration**: Loads initial data from REST API on mount
- **Type-Safe**: Full TypeScript support with typed state and actions
- **Testable**: Comprehensive unit tests with 100% coverage

## Usage

### Wrap Your Application

```tsx
import { AppProvider } from './context';

function App() {
  return (
    <AppProvider>
      <YourComponents />
    </AppProvider>
  );
}
```

### Access State in Components

```tsx
import { useAppContext } from './context';

function MyComponent() {
  const {
    sensors,
    locations,
    alerts,
    selectedSensorId,
    connectionStatus,
    telemetryMap,
    setSelectedSensorId,
    addAlert,
    updateTelemetry,
  } = useAppContext();

  // Use state and actions...
}
```

## State Properties

### `sensors: Sensor[]`
Array of all registered sensors with location information.

### `locations: Location[]`
Array of all locations in the hierarchy (City > District > Ward).

### `alerts: Alert[]`
Array of recent alerts (limited to 100 most recent).

### `selectedSensorId: string | null`
Currently selected sensor ID for chart display.

### `connectionStatus: ConnectionStatus`
WebSocket connection status: `'connecting' | 'connected' | 'disconnected' | 'error'`

### `telemetryMap: Record<string, Telemetry>`
Map of latest telemetry data by sensor ID.

### `loading: boolean`
Indicates if initial data is being loaded.

### `error: string | null`
Error message if initial data loading failed.

## Actions

### `setSelectedSensorId(sensorId: string | null): void`
Update the currently selected sensor.

### `addAlert(alert: Alert): void`
Manually add an alert to the alerts array.

### `updateTelemetry(telemetry: Telemetry): void`
Manually update telemetry data for a sensor.

### `refreshSensors(): Promise<void>`
Reload sensors from the API.

### `refreshLocations(): Promise<void>`
Reload locations from the API.

### `refreshAlerts(): Promise<void>`
Reload alerts from the API.

### `clearError(): void`
Clear the error state.

## WebSocket Integration

The AppContext automatically integrates with the `useWebSocket` hook to handle real-time updates:

- **Telemetry Updates**: When new telemetry data is received via WebSocket, the `telemetryMap` is automatically updated
- **Alert Updates**: When new alerts are received via WebSocket, they are automatically added to the `alerts` array
- **Connection Status**: The WebSocket connection status is exposed via `connectionStatus`

### Requirements Validation

- **Requirement 10.3**: Telemetry data broadcast to WebSocket clients is received and updates state within 1 second
- **Requirement 10.4**: Alert data broadcast to WebSocket clients is received and updates state within 1 second

## Configuration

### Custom WebSocket URL

You can override the default WebSocket URL by passing the `wsUrl` prop:

```tsx
<AppProvider wsUrl="ws://custom-backend:8000/ws">
  <YourComponents />
</AppProvider>
```

If not provided, the WebSocket URL is determined by:
1. `VITE_WS_URL` environment variable
2. Default: `ws://localhost:8000/ws`

## Error Handling

The AppContext handles errors gracefully:

- **API Errors**: If initial data loading fails, the error is stored in the `error` state
- **WebSocket Errors**: Connection errors are reflected in the `connectionStatus`
- **Refresh Errors**: Refresh functions throw errors that can be caught by calling components

## Testing

The AppContext includes comprehensive unit tests covering:

- Initial data loading
- State updates
- WebSocket integration
- Error handling
- Refresh functions

Run tests:
```bash
npm test -- src/context/AppContext.test.tsx
```

## Example: Complete Integration

```tsx
import React from 'react';
import { AppProvider, useAppContext } from './context';

function Dashboard() {
  const {
    sensors,
    selectedSensorId,
    connectionStatus,
    telemetryMap,
    setSelectedSensorId,
  } = useAppContext();

  return (
    <div>
      <div>Status: {connectionStatus}</div>
      
      <select
        value={selectedSensorId || ''}
        onChange={(e) => setSelectedSensorId(e.target.value)}
      >
        {sensors.map(sensor => (
          <option key={sensor.sensorId} value={sensor.sensorId}>
            {sensor.sensorId}
          </option>
        ))}
      </select>

      {selectedSensorId && telemetryMap[selectedSensorId] && (
        <div>
          <p>CO2: {telemetryMap[selectedSensorId].co2} ppm</p>
          <p>Noise: {telemetryMap[selectedSensorId].noise} dB</p>
          <p>Temperature: {telemetryMap[selectedSensorId].temperature} °C</p>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <Dashboard />
    </AppProvider>
  );
}

export default App;
```

## Architecture

```
AppProvider
├── Loads initial data (sensors, locations, alerts)
├── Establishes WebSocket connection
├── Provides state and actions via Context
└── Handles real-time updates

Components
└── useAppContext() hook
    ├── Access state
    └── Call actions
```

## Performance Considerations

- **Memoization**: State update functions are memoized with `useCallback` to prevent unnecessary re-renders
- **Alert Limit**: Alerts array is limited to 100 entries to prevent memory issues
- **Selective Updates**: Only affected state is updated when WebSocket messages arrive
- **Lazy Loading**: Initial data is loaded only once on mount

## Future Enhancements

Potential improvements for future iterations:

- **Pagination**: Add pagination support for large datasets
- **Filtering**: Add built-in filtering for sensors and alerts
- **Caching**: Implement caching strategy for API responses
- **Optimistic Updates**: Add optimistic UI updates for better UX
- **Persistence**: Add local storage persistence for selected sensor
