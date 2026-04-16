/**
 * AppContext - Global State Management for Smart City IoT Dashboard
 * 
 * Provides centralized state management using React Context API for:
 * - Sensors list
 * - Locations hierarchy
 * - Alerts collection
 * - Selected sensor
 * - WebSocket connection status
 * - Real-time telemetry updates
 * 
 * Integrates with useWebSocket hook to automatically update state
 * when real-time messages are received from the backend.
 * 
 * Requirements: 10.3, 10.4
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import type { ConnectionStatus } from '../hooks/useWebSocket';
import { fetchSensors, fetchLocations, fetchAlerts } from '../services/api';
import type { Sensor, Location, Alert, Telemetry } from '../types';

/**
 * Global application state interface
 */
interface AppState {
  sensors: Sensor[];
  locations: Location[];
  alerts: Alert[];
  selectedSensorId: string | null;
  connectionStatus: ConnectionStatus;
  telemetryMap: Record<string, Telemetry>; // sensorId -> latest telemetry
  loading: boolean;
  error: string | null;
}

/**
 * State update functions interface
 */
interface AppActions {
  setSelectedSensorId: (sensorId: string | null) => void;
  addAlert: (alert: Alert) => void;
  updateTelemetry: (telemetry: Telemetry) => void;
  refreshSensors: () => Promise<void>;
  refreshLocations: () => Promise<void>;
  refreshAlerts: () => Promise<void>;
  clearError: () => void;
}

/**
 * Combined context value
 */
interface AppContextValue extends AppState, AppActions {}

/**
 * Context provider props
 */
interface AppProviderProps {
  children: ReactNode;
  wsUrl?: string; // Optional WebSocket URL override
}

// Create context with undefined default (will be provided by AppProvider)
const AppContext = createContext<AppContextValue | undefined>(undefined);

/**
 * AppProvider Component
 * 
 * Wraps the application and provides global state to all child components.
 * Automatically loads initial data and establishes WebSocket connection.
 * 
 * @param children - Child components to wrap
 * @param wsUrl - Optional WebSocket URL (defaults to env variable or localhost)
 */
export const AppProvider: React.FC<AppProviderProps> = ({ children, wsUrl }) => {
  // State management
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedSensorId, setSelectedSensorId] = useState<string | null>(null);
  const [telemetryMap, setTelemetryMap] = useState<Record<string, Telemetry>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Handle real-time telemetry updates from WebSocket
   * Updates telemetryMap with latest sensor reading
   * 
   * Validates: Requirement 10.3 - Broadcast telemetry within 1 second
   */
  const handleTelemetryUpdate = useCallback((telemetry: Telemetry) => {
    setTelemetryMap(prev => ({
      ...prev,
      [telemetry.sensorId]: telemetry,
    }));
  }, []);

  /**
   * Handle real-time alert updates from WebSocket
   * Adds new alert to the beginning of alerts array
   * 
   * Validates: Requirement 10.4 - Broadcast alerts within 1 second
   */
  const handleAlertUpdate = useCallback((alert: Alert) => {
    setAlerts(prev => [alert, ...prev].slice(0, 100)); // Keep last 100 alerts
  }, []);

  /**
   * WebSocket connection with callbacks
   */
  const wsUrlResolved = wsUrl || import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  const connectionStatus = useWebSocket(wsUrlResolved, {
    onTelemetry: handleTelemetryUpdate,
    onAlert: handleAlertUpdate,
  });

  /**
   * Load initial data on mount
   */
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch sensors, locations, and recent alerts in parallel
        const [sensorsData, locationsData, alertsData] = await Promise.all([
          fetchSensors(),
          fetchLocations(),
          fetchAlerts({ limit: 100 }),
        ]);

        setSensors(sensorsData);
        setLocations(locationsData);
        setAlerts(alertsData);

        // Auto-select first sensor if available
        if (sensorsData.length > 0 && !selectedSensorId) {
          setSelectedSensorId(sensorsData[0].sensorId);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load initial data';
        setError(errorMessage);
        console.error('Error loading initial data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []); // Only run on mount

  /**
   * Refresh sensors from API
   */
  const refreshSensors = useCallback(async () => {
    try {
      const sensorsData = await fetchSensors();
      setSensors(sensorsData);
    } catch (err) {
      console.error('Error refreshing sensors:', err);
      throw err;
    }
  }, []);

  /**
   * Refresh locations from API
   */
  const refreshLocations = useCallback(async () => {
    try {
      const locationsData = await fetchLocations();
      setLocations(locationsData);
    } catch (err) {
      console.error('Error refreshing locations:', err);
      throw err;
    }
  }, []);

  /**
   * Refresh alerts from API
   */
  const refreshAlerts = useCallback(async () => {
    try {
      const alertsData = await fetchAlerts({ limit: 100 });
      setAlerts(alertsData);
    } catch (err) {
      console.error('Error refreshing alerts:', err);
      throw err;
    }
  }, []);

  /**
   * Add alert manually (for testing or manual updates)
   */
  const addAlert = useCallback((alert: Alert) => {
    setAlerts(prev => [alert, ...prev].slice(0, 100));
  }, []);

  /**
   * Update telemetry manually (for testing or manual updates)
   */
  const updateTelemetry = useCallback((telemetry: Telemetry) => {
    setTelemetryMap(prev => ({
      ...prev,
      [telemetry.sensorId]: telemetry,
    }));
  }, []);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Combine state and actions into context value
  const contextValue: AppContextValue = {
    // State
    sensors,
    locations,
    alerts,
    selectedSensorId,
    connectionStatus,
    telemetryMap,
    loading,
    error,
    // Actions
    setSelectedSensorId,
    addAlert,
    updateTelemetry,
    refreshSensors,
    refreshLocations,
    refreshAlerts,
    clearError,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

/**
 * Custom hook to access AppContext
 * 
 * Throws error if used outside AppProvider.
 * 
 * @returns AppContextValue - Global state and actions
 * 
 * @example
 * const { sensors, selectedSensorId, setSelectedSensorId } = useAppContext();
 */
export const useAppContext = (): AppContextValue => {
  const context = useContext(AppContext);
  
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  
  return context;
};

// Export context for advanced usage (testing, etc.)
export { AppContext };
