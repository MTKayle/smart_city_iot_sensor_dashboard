/**
 * Unit tests for AppContext
 * 
 * Tests global state management, WebSocket integration,
 * and state update functions.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AppProvider, useAppContext } from './AppContext';
import * as api from '../services/api';
import * as useWebSocketModule from '../hooks/useWebSocket';
import type { Sensor, Location, Alert, Telemetry } from '../types';

// Mock the API module
vi.mock('../services/api');
const mockFetchSensors = vi.mocked(api.fetchSensors);
const mockFetchLocations = vi.mocked(api.fetchLocations);
const mockFetchAlerts = vi.mocked(api.fetchAlerts);

// Mock the useWebSocket hook
vi.mock('../hooks/useWebSocket');
const mockUseWebSocket = vi.mocked(useWebSocketModule.useWebSocket);

describe('AppContext', () => {
  // Sample test data
  const mockSensors: Sensor[] = [
    {
      sensorId: 'sensor_001',
      locationId: 'ward_001',
      sensorType: 'CO2',
      registeredAt: '2024-01-01T00:00:00Z',
    },
    {
      sensorId: 'sensor_002',
      locationId: 'ward_002',
      sensorType: 'Noise',
      registeredAt: '2024-01-01T00:00:00Z',
    },
  ];

  const mockLocations: Location[] = [
    {
      locationId: 'city_001',
      name: 'Test City',
      parentId: null,
      type: 'City',
    },
    {
      locationId: 'ward_001',
      name: 'Ward 1',
      parentId: 'district_001',
      type: 'Ward',
    },
  ];

  const mockAlerts: Alert[] = [
    {
      alertId: 'alert_001',
      sensorId: 'sensor_001',
      metricType: 'CO2',
      value: 1200,
      level: 'HIGH',
      createdAt: '2024-01-15T10:30:00Z',
    },
  ];

  const mockTelemetry: Telemetry = {
    sensorId: 'sensor_001',
    locationId: 'ward_001',
    co2: 450.5,
    noise: 65.2,
    temperature: 25.3,
    timestamp: '2024-01-15T10:30:00Z',
  };

  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();

    // Default mock implementations
    mockFetchSensors.mockResolvedValue(mockSensors);
    mockFetchLocations.mockResolvedValue(mockLocations);
    mockFetchAlerts.mockResolvedValue(mockAlerts);
    mockUseWebSocket.mockReturnValue('connected');
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('AppProvider initialization', () => {
    it('should load initial data on mount', async () => {
      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      // Initially loading
      expect(result.current.loading).toBe(true);

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Verify data was loaded
      expect(result.current.sensors).toEqual(mockSensors);
      expect(result.current.locations).toEqual(mockLocations);
      expect(result.current.alerts).toEqual(mockAlerts);
      expect(result.current.error).toBeNull();
    });

    it('should auto-select first sensor if available', async () => {
      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.selectedSensorId).toBe('sensor_001');
    });

    it('should handle API errors gracefully', async () => {
      const errorMessage = 'Network error';
      mockFetchSensors.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe(errorMessage);
    });

    it('should establish WebSocket connection with correct URL', () => {
      const customWsUrl = 'ws://custom:8000/ws';
      
      renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider wsUrl={customWsUrl}>{children}</AppProvider>,
      });

      expect(mockUseWebSocket).toHaveBeenCalledWith(
        customWsUrl,
        expect.objectContaining({
          onTelemetry: expect.any(Function),
          onAlert: expect.any(Function),
        })
      );
    });
  });

  describe('State management', () => {
    it('should update selectedSensorId', async () => {
      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      act(() => {
        result.current.setSelectedSensorId('sensor_002');
      });

      expect(result.current.selectedSensorId).toBe('sensor_002');
    });

    it('should add alert to alerts array', async () => {
      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const newAlert: Alert = {
        alertId: 'alert_002',
        sensorId: 'sensor_002',
        metricType: 'Noise',
        value: 95,
        level: 'HIGH',
        createdAt: '2024-01-15T11:00:00Z',
      };

      act(() => {
        result.current.addAlert(newAlert);
      });

      expect(result.current.alerts[0]).toEqual(newAlert);
      expect(result.current.alerts).toHaveLength(2);
    });

    it('should update telemetry in telemetryMap', async () => {
      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      act(() => {
        result.current.updateTelemetry(mockTelemetry);
      });

      expect(result.current.telemetryMap['sensor_001']).toEqual(mockTelemetry);
    });

    it('should clear error state', async () => {
      mockFetchSensors.mockRejectedValue(new Error('Test error'));

      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('WebSocket integration', () => {
    it('should handle real-time telemetry updates', async () => {
      let onTelemetryCallback: ((telemetry: Telemetry) => void) | undefined;

      mockUseWebSocket.mockImplementation((_url, callbacks) => {
        onTelemetryCallback = callbacks?.onTelemetry;
        return 'connected';
      });

      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Simulate WebSocket telemetry message
      act(() => {
        onTelemetryCallback?.(mockTelemetry);
      });

      expect(result.current.telemetryMap['sensor_001']).toEqual(mockTelemetry);
    });

    it('should handle real-time alert updates', async () => {
      let onAlertCallback: ((alert: Alert) => void) | undefined;

      mockUseWebSocket.mockImplementation((_url, callbacks) => {
        onAlertCallback = callbacks?.onAlert;
        return 'connected';
      });

      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const newAlert: Alert = {
        alertId: 'alert_ws_001',
        sensorId: 'sensor_001',
        metricType: 'CO2',
        value: 1500,
        level: 'HIGH',
        createdAt: '2024-01-15T12:00:00Z',
      };

      // Simulate WebSocket alert message
      act(() => {
        onAlertCallback?.(newAlert);
      });

      expect(result.current.alerts[0]).toEqual(newAlert);
    });

    it('should limit alerts to 100 entries', async () => {
      let onAlertCallback: ((alert: Alert) => void) | undefined;

      mockUseWebSocket.mockImplementation((_url, callbacks) => {
        onAlertCallback = callbacks?.onAlert;
        return 'connected';
      });

      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Add 100 alerts
      act(() => {
        for (let i = 0; i < 100; i++) {
          onAlertCallback?.({
            alertId: `alert_${i}`,
            sensorId: 'sensor_001',
            metricType: 'CO2',
            value: 1000 + i,
            level: 'HIGH',
            createdAt: new Date().toISOString(),
          });
        }
      });

      expect(result.current.alerts).toHaveLength(100);
    });

    it('should expose connection status', async () => {
      mockUseWebSocket.mockReturnValue('connecting');

      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      expect(result.current.connectionStatus).toBe('connecting');
    });
  });

  describe('Refresh functions', () => {
    it('should refresh sensors', async () => {
      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const newSensors: Sensor[] = [
        ...mockSensors,
        {
          sensorId: 'sensor_003',
          locationId: 'ward_003',
          sensorType: 'Temperature',
          registeredAt: '2024-01-02T00:00:00Z',
        },
      ];

      mockFetchSensors.mockResolvedValue(newSensors);

      await act(async () => {
        await result.current.refreshSensors();
      });

      expect(result.current.sensors).toEqual(newSensors);
    });

    it('should refresh locations', async () => {
      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const newLocations: Location[] = [
        ...mockLocations,
        {
          locationId: 'ward_002',
          name: 'Ward 2',
          parentId: 'district_001',
          type: 'Ward',
        },
      ];

      mockFetchLocations.mockResolvedValue(newLocations);

      await act(async () => {
        await result.current.refreshLocations();
      });

      expect(result.current.locations).toEqual(newLocations);
    });

    it('should refresh alerts', async () => {
      const { result } = renderHook(() => useAppContext(), {
        wrapper: ({ children }) => <AppProvider>{children}</AppProvider>,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const newAlerts: Alert[] = [
        ...mockAlerts,
        {
          alertId: 'alert_002',
          sensorId: 'sensor_002',
          metricType: 'Noise',
          value: 90,
          level: 'HIGH',
          createdAt: '2024-01-15T11:00:00Z',
        },
      ];

      mockFetchAlerts.mockResolvedValue(newAlerts);

      await act(async () => {
        await result.current.refreshAlerts();
      });

      expect(result.current.alerts).toEqual(newAlerts);
    });
  });

  describe('Error handling', () => {
    it('should throw error when useAppContext is used outside provider', () => {
      // Suppress console.error for this test
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useAppContext());
      }).toThrow('useAppContext must be used within an AppProvider');

      consoleError.mockRestore();
    });
  });
});
