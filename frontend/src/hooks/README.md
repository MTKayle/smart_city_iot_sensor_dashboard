# WebSocket Hook Tests

## Overview
Comprehensive unit tests for the `useWebSocket` hook covering all requirements (10.1, 10.2, 10.3, 10.4).

## Test Coverage

### Connection Establishment (Requirement 10.1)
- ✅ Starts with 'connecting' status
- ✅ Connects to default URL (ws://backend:8000/ws)
- ✅ Connects to custom URL when provided
- ✅ Updates status to 'connected' on successful connection
- ✅ Updates status to 'error' on connection failure
- ✅ Updates status to 'disconnected' when connection closes

### Message Parsing and Dispatching (Requirement 10.2)
- ✅ Parses and dispatches telemetry messages
- ✅ Parses and dispatches alert messages
- ✅ Parses and dispatches connection_ack messages
- ✅ Handles multiple message types with all callbacks
- ✅ Handles missing callbacks gracefully
- ✅ Handles malformed JSON gracefully
- ✅ Handles unknown message types gracefully

### Reconnection Logic (Requirement 10.3)
- ✅ Attempts to reconnect after disconnection
- ✅ Uses exponential backoff (1s, 2s, 4s, 8s)
- ✅ Caps reconnection delay at 60 seconds
- ✅ Resets reconnection delay after successful connection
- ✅ Reconnects after connection error

### Cleanup on Unmount (Requirement 10.4)
- ✅ Closes WebSocket connection on unmount
- ✅ Clears reconnection timeout on unmount
- ✅ Does not attempt to reconnect after unmount
- ✅ Does not update state after unmount

## Running Tests

```bash
# Run tests once
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui
```

## Test Implementation Details

### Mock WebSocket
Tests use a custom `MockWebSocket` class that simulates WebSocket behavior:
- Tracks all instances for verification
- Provides helper methods to simulate events (open, close, error, message)
- Maintains connection state

### Fake Timers
Tests use Vitest's fake timers to control time-based behavior:
- Allows testing of exponential backoff without waiting
- Enables precise control over reconnection timing
- Wrapped in `act()` to handle React state updates

### React Testing Library
Tests use `@testing-library/react` for hook testing:
- `renderHook()` to render hooks in isolation
- `act()` to wrap state updates
- Proper cleanup after each test
