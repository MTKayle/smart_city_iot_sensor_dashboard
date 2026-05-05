import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket, type WebSocketCallbacks } from './useWebSocket';
import type { Telemetry, Alert } from '../types';

/**
 * Unit tests for useWebSocket hook
 * 
 * Tests cover:
 * - Connection establishment (Requirement 10.1)
 * - Message parsing and dispatching (Requirement 10.2)
 * - Reconnection logic with exponential backoff (Requirement 10.3)
 * - Cleanup on unmount (Requirement 10.4)
 */

// Mock WebSocket
class MockWebSocket {
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  readyState: number = WebSocket.CONNECTING;
  
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(url: string) {
    this.url = url;
    // Store instance for test access
    MockWebSocket.instances.push(this);
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  send(_data: string) {
    // Mock send implementation
  }

  // Helper method to simulate receiving a message
  simulateMessage(data: string) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data }));
    }
  }

  // Helper method to simulate connection open
  simulateOpen() {
    this.readyState = WebSocket.OPEN;
    if (this.onopen) {
      this.onopen(new Event('open'));
    }
  }

  // Helper method to simulate error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }

  // Track all instances for testing
  static instances: MockWebSocket[] = [];
  static resetInstances() {
    MockWebSocket.instances = [];
  }
}

describe('useWebSocket', () => {
  beforeEach(() => {
    // Replace global WebSocket with mock
    vi.stubGlobal('WebSocket', MockWebSocket);
    MockWebSocket.resetInstances();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Connection establishment', () => {
    it('should start with connecting status', () => {
      const { result } = renderHook(() => useWebSocket());
      
      expect(result.current).toBe('connecting');
    });

    it('should connect to default URL when no URL provided', () => {
      renderHook(() => useWebSocket());
      
      expect(MockWebSocket.instances).toHaveLength(1);
      expect(MockWebSocket.instances[0].url).toBe('ws://backend:8000/ws');
    });

    it('should connect to custom URL when provided', () => {
      const customUrl = 'ws://localhost:3000/ws';
      renderHook(() => useWebSocket(customUrl));
      
      expect(MockWebSocket.instances).toHaveLength(1);
      expect(MockWebSocket.instances[0].url).toBe(customUrl);
    });

    it('should update status to connected when connection opens', async () => {
      const { result } = renderHook(() => useWebSocket());
      
      expect(result.current).toBe('connecting');
      
      // Simulate connection open
      await act(async () => {
        MockWebSocket.instances[0].simulateOpen();
      });
      
      expect(result.current).toBe('connected');
    });

    it('should update status to error when connection fails', async () => {
      const { result } = renderHook(() => useWebSocket());
      
      // Simulate error
      await act(async () => {
        MockWebSocket.instances[0].simulateError();
      });
      
      expect(result.current).toBe('error');
    });

    it('should update status to disconnected when connection closes', async () => {
      const { result } = renderHook(() => useWebSocket());
      
      // First connect
      await act(async () => {
        MockWebSocket.instances[0].simulateOpen();
      });
      expect(result.current).toBe('connected');
      
      // Then close
      await act(async () => {
        MockWebSocket.instances[0].close();
      });
      
      expect(result.current).toBe('disconnected');
    });
  });

  describe('Message parsing and dispatching', () => {
    it('should parse and dispatch telemetry messages', async () => {
      const onTelemetry = vi.fn();
      const callbacks: WebSocketCallbacks = { onTelemetry };
      
      renderHook(() => useWebSocket('ws://test', callbacks));
      
      const telemetryData: Telemetry = {
        sensorId: 'sensor-1',
        locationId: 'loc-1',
        data: {
          co2: 450,
          noise: 65,
          temperature: 22.5,
          pm25: null,
          humidity: null,
        },
        location: { type: 'Point', coordinates: [106.7, 10.78] },
        co2: 450,
        noise: 65,
        temperature: 22.5,
        timestamp: '2024-01-01T12:00:00Z'
      };
      
      const message = {
        type: 'telemetry',
        data: telemetryData
      };
      
      await act(async () => {
        MockWebSocket.instances[0].simulateMessage(JSON.stringify(message));
      });
      
      expect(onTelemetry).toHaveBeenCalledWith(telemetryData);
    });

    it('should parse and dispatch alert messages', async () => {
      const onAlert = vi.fn();
      const callbacks: WebSocketCallbacks = { onAlert };
      
      renderHook(() => useWebSocket('ws://test', callbacks));
      
      const alertData: Alert = {
        alertId: 'alert-1',
        sensorId: 'sensor-1',
        locationId: 'loc-1',
        alertType: 'THRESHOLD',
        metricType: 'CO2',
        value: 1200,
        severity: 'HIGH',
        status: 'OPEN',
        level: 'HIGH',
        createdAt: '2024-01-01T12:00:00Z'
      };
      
      const message = {
        type: 'alert',
        data: alertData
      };
      
      await act(async () => {
        MockWebSocket.instances[0].simulateMessage(JSON.stringify(message));
      });
      
      expect(onAlert).toHaveBeenCalledWith(alertData);
    });

    it('should parse and dispatch connection_ack messages', async () => {
      const onConnectionAck = vi.fn();
      const callbacks: WebSocketCallbacks = { onConnectionAck };
      
      renderHook(() => useWebSocket('ws://test', callbacks));
      
      const message = {
        type: 'connection_ack',
        message: 'Connected successfully'
      };
      
      await act(async () => {
        MockWebSocket.instances[0].simulateMessage(JSON.stringify(message));
      });
      
      expect(onConnectionAck).toHaveBeenCalledWith('Connected successfully');
    });

    it('should handle multiple message types with all callbacks', async () => {
      const onTelemetry = vi.fn();
      const onAlert = vi.fn();
      const onConnectionAck = vi.fn();
      const callbacks: WebSocketCallbacks = { onTelemetry, onAlert, onConnectionAck };
      
      renderHook(() => useWebSocket('ws://test', callbacks));
      
      await act(async () => {
        // Send connection ack
        MockWebSocket.instances[0].simulateMessage(JSON.stringify({
          type: 'connection_ack',
          message: 'Connected'
        }));
        
        // Send telemetry
        MockWebSocket.instances[0].simulateMessage(JSON.stringify({
          type: 'telemetry',
          data: {
            sensorId: 'sensor-1',
            locationId: 'loc-1',
            co2: 450,
            noise: 65,
            temperature: 22.5,
            timestamp: '2024-01-01T12:00:00Z'
          }
        }));
        
        // Send alert
        MockWebSocket.instances[0].simulateMessage(JSON.stringify({
          type: 'alert',
          data: {
            alertId: 'alert-1',
            sensorId: 'sensor-1',
            metricType: 'CO2',
            value: 1200,
            level: 'HIGH',
            createdAt: '2024-01-01T12:00:00Z'
          }
        }));
      });
      
      expect(onConnectionAck).toHaveBeenCalledTimes(1);
      expect(onTelemetry).toHaveBeenCalledTimes(1);
      expect(onAlert).toHaveBeenCalledTimes(1);
    });

    it('should not call callbacks when they are not provided', async () => {
      const { result } = renderHook(() => useWebSocket('ws://test'));
      
      // Should not throw when callbacks are not provided
      await act(async () => {
        MockWebSocket.instances[0].simulateMessage(JSON.stringify({
          type: 'telemetry',
          data: { sensorId: 'sensor-1' }
        }));
      });
      
      // Test passes if no error is thrown
      expect(result.current).toBeDefined();
    });

    it('should handle malformed JSON gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      renderHook(() => useWebSocket('ws://test'));
      
      // Send invalid JSON
      await act(async () => {
        MockWebSocket.instances[0].simulateMessage('invalid json');
      });
      
      expect(consoleErrorSpy).toHaveBeenCalled();
      consoleErrorSpy.mockRestore();
    });

    it('should handle unknown message types gracefully', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      renderHook(() => useWebSocket('ws://test'));
      
      await act(async () => {
        MockWebSocket.instances[0].simulateMessage(JSON.stringify({
          type: 'unknown_type',
          data: {}
        }));
      });
      
      expect(consoleWarnSpy).toHaveBeenCalledWith('Unknown message type:', 'unknown_type');
      consoleWarnSpy.mockRestore();
    });
  });

  describe('Reconnection logic', () => {
    it('should attempt to reconnect after disconnection', async () => {
      const { result } = renderHook(() => useWebSocket());
      
      // Connect and then close
      await act(async () => {
        MockWebSocket.instances[0].simulateOpen();
      });
      expect(result.current).toBe('connected');
      
      await act(async () => {
        MockWebSocket.instances[0].close();
      });
      expect(result.current).toBe('disconnected');
      
      // Should have 1 instance initially
      expect(MockWebSocket.instances).toHaveLength(1);
      
      // Advance timer by 1 second (initial reconnect delay)
      await act(async () => {
        vi.advanceTimersByTime(1000);
      });
      
      // Should create a new WebSocket instance
      expect(MockWebSocket.instances).toHaveLength(2);
    });

    it('should use exponential backoff for reconnection (1s, 2s, 4s, 8s)', async () => {
      renderHook(() => useWebSocket());
      
      // First connection
      expect(MockWebSocket.instances).toHaveLength(1);
      
      // Close connection - should reconnect after 1s
      await act(async () => {
        MockWebSocket.instances[0].close();
        vi.advanceTimersByTime(1000);
      });
      expect(MockWebSocket.instances).toHaveLength(2);
      
      // Close again - should reconnect after 2s
      await act(async () => {
        MockWebSocket.instances[1].close();
        vi.advanceTimersByTime(2000);
      });
      expect(MockWebSocket.instances).toHaveLength(3);
      
      // Close again - should reconnect after 4s
      await act(async () => {
        MockWebSocket.instances[2].close();
        vi.advanceTimersByTime(4000);
      });
      expect(MockWebSocket.instances).toHaveLength(4);
      
      // Close again - should reconnect after 8s
      await act(async () => {
        MockWebSocket.instances[3].close();
        vi.advanceTimersByTime(8000);
      });
      expect(MockWebSocket.instances).toHaveLength(5);
    });

    it('should cap reconnection delay at 60 seconds', async () => {
      renderHook(() => useWebSocket());
      
      // Simulate multiple disconnections to reach max delay
      // Start with 1 instance already created
      expect(MockWebSocket.instances).toHaveLength(1);
      
      for (let i = 0; i < 7; i++) {
        const currentLength = MockWebSocket.instances.length;
        
        await act(async () => {
          // Close the most recent connection
          MockWebSocket.instances[currentLength - 1].close();
          
          // Calculate expected delay (capped at 60s)
          const delay = Math.min(1000 * Math.pow(2, i), 60000);
          vi.advanceTimersByTime(delay);
        });
        
        // Should have created a new instance
        expect(MockWebSocket.instances).toHaveLength(currentLength + 1);
      }
      
      // After many reconnections, delay should be capped at 60s
      const currentLength = MockWebSocket.instances.length;
      
      await act(async () => {
        MockWebSocket.instances[currentLength - 1].close();
        // Should reconnect at 60s (capped)
        vi.advanceTimersByTime(60000);
      });
      
      expect(MockWebSocket.instances).toHaveLength(currentLength + 1);
    });

    it('should reset reconnection delay after successful connection', async () => {
      const { result } = renderHook(() => useWebSocket());
      
      // First connection and close - reconnect after 1s
      await act(async () => {
        MockWebSocket.instances[0].close();
        vi.advanceTimersByTime(1000);
      });
      expect(MockWebSocket.instances).toHaveLength(2);
      
      // Second close - reconnect after 2s
      await act(async () => {
        MockWebSocket.instances[1].close();
        vi.advanceTimersByTime(2000);
      });
      expect(MockWebSocket.instances).toHaveLength(3);
      
      // Successful connection
      await act(async () => {
        MockWebSocket.instances[2].simulateOpen();
      });
      expect(result.current).toBe('connected');
      
      // Close again - should reset to 1s delay
      await act(async () => {
        MockWebSocket.instances[2].close();
      });
      expect(result.current).toBe('disconnected');
      
      await act(async () => {
        vi.advanceTimersByTime(1000);
      });
      expect(MockWebSocket.instances).toHaveLength(4);
    });

    it('should reconnect after connection error', async () => {
      renderHook(() => useWebSocket());
      
      // Simulate error followed by close (which is the typical WebSocket behavior)
      await act(async () => {
        MockWebSocket.instances[0].simulateError();
        MockWebSocket.instances[0].close();
      });
      
      // Should not reconnect immediately
      expect(MockWebSocket.instances).toHaveLength(1);
      
      // Should reconnect after delay
      await act(async () => {
        vi.advanceTimersByTime(1000);
      });
      
      expect(MockWebSocket.instances).toHaveLength(2);
    });
  });

  describe('Cleanup on unmount', () => {
    it('should close WebSocket connection on unmount', () => {
      const { unmount } = renderHook(() => useWebSocket());
      
      const ws = MockWebSocket.instances[0];
      const closeSpy = vi.spyOn(ws, 'close');
      
      unmount();
      
      expect(closeSpy).toHaveBeenCalled();
    });

    it('should clear reconnection timeout on unmount', async () => {
      const { unmount } = renderHook(() => useWebSocket());
      
      // Close connection to trigger reconnection timer
      await act(async () => {
        MockWebSocket.instances[0].close();
      });
      
      // Unmount before reconnection happens
      unmount();
      
      // Advance time - should not create new connection
      const instanceCount = MockWebSocket.instances.length;
      await act(async () => {
        vi.advanceTimersByTime(5000);
      });
      
      expect(MockWebSocket.instances).toHaveLength(instanceCount);
    });

    it('should not attempt to reconnect after unmount', async () => {
      const { result, unmount } = renderHook(() => useWebSocket());
      
      // Connect
      await act(async () => {
        MockWebSocket.instances[0].simulateOpen();
      });
      expect(result.current).toBe('connected');
      
      // Close and unmount immediately
      await act(async () => {
        MockWebSocket.instances[0].close();
      });
      unmount();
      
      // Advance time past reconnection delay
      await act(async () => {
        vi.advanceTimersByTime(10000);
      });
      
      // Should not create new connection
      expect(MockWebSocket.instances).toHaveLength(1);
    });

    it('should not update state after unmount', async () => {
      const { result, unmount } = renderHook(() => useWebSocket());
      
      const initialStatus = result.current;
      
      unmount();
      
      // Try to trigger state updates after unmount
      await act(async () => {
        MockWebSocket.instances[0].simulateOpen();
        MockWebSocket.instances[0].simulateError();
      });
      
      // Status should not change
      expect(result.current).toBe(initialStatus);
    });
  });
});
