/**
 * AppContext - Global State Management for Smart City IoT Dashboard
 *
 * Centralized state for sensors, locations, clusters, alerts, leaderboard,
 * real-time telemetry, and pipeline metrics. Wires up the WebSocket and
 * exposes refresh + alert lifecycle actions.
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from 'react';
import type { ReactNode } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import type { ConnectionStatus } from '../hooks/useWebSocket';
import {
  fetchSensors,
  fetchLocations,
  fetchAlerts,
  fetchClusters,
  fetchLeaderboard,
  fetchPipelineMetrics,
  acknowledgeAlert as apiAcknowledgeAlert,
  resolveAlert as apiResolveAlert,
} from '../services/api';
import type {
  Sensor,
  Location,
  Alert,
  Telemetry,
  SensorCluster,
  LeaderboardEntry,
} from '../types';
import type { PipelineMetrics } from '../services/api';

interface AppState {
  sensors: Sensor[];
  locations: Location[];
  clusters: SensorCluster[];
  alerts: Alert[];
  leaderboard: LeaderboardEntry[];
  pipelineMetrics: PipelineMetrics | null;
  selectedSensorId: string | null;
  connectionStatus: ConnectionStatus;
  telemetryMap: Record<string, Telemetry>;
  loading: boolean;
  error: string | null;
}

interface AppActions {
  setSelectedSensorId: (sensorId: string | null) => void;
  addAlert: (alert: Alert) => void;
  updateTelemetry: (telemetry: Telemetry) => void;
  refreshSensors: () => Promise<void>;
  refreshLocations: () => Promise<void>;
  refreshClusters: () => Promise<void>;
  refreshAlerts: () => Promise<void>;
  refreshLeaderboard: () => Promise<void>;
  refreshPipelineMetrics: () => Promise<void>;
  acknowledgeAlert: (alertId: string) => Promise<void>;
  resolveAlert: (alertId: string) => Promise<void>;
  clearError: () => void;
}

interface AppContextValue extends AppState, AppActions {}

interface AppProviderProps {
  children: ReactNode;
  wsUrl?: string;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

export const AppProvider: React.FC<AppProviderProps> = ({ children, wsUrl }) => {
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [clusters, setClusters] = useState<SensorCluster[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [pipelineMetrics, setPipelineMetrics] = useState<PipelineMetrics | null>(null);
  const [selectedSensorId, setSelectedSensorId] = useState<string | null>(null);
  const [telemetryMap, setTelemetryMap] = useState<Record<string, Telemetry>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleTelemetryUpdate = useCallback((telemetry: Telemetry) => {
    // useWebSocket already normalised nested→flat and computed AQI.
    setTelemetryMap((prev) => ({ ...prev, [telemetry.sensorId]: telemetry }));
  }, []);

  const handleAlertUpdate = useCallback((alert: Alert) => {
    setAlerts((prev) => {
      // Replace if already exists (lifecycle update from server), else prepend.
      const idx = prev.findIndex((a) => a.alertId === alert.alertId);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = alert;
        return next;
      }
      return [alert, ...prev].slice(0, 100);
    });
  }, []);

  const wsUrlResolved =
    wsUrl ||
    (import.meta.env.VITE_WS_URL as string | undefined) ||
    'ws://localhost:8000/ws';
  const connectionStatus = useWebSocket(wsUrlResolved, {
    onTelemetry: handleTelemetryUpdate,
    onAlert: handleAlertUpdate,
  });

  const refreshSensors = useCallback(async () => {
    const data = await fetchSensors();
    setSensors(data);
  }, []);

  const refreshLocations = useCallback(async () => {
    const data = await fetchLocations();
    setLocations(data);
  }, []);

  const refreshClusters = useCallback(async () => {
    try {
      const data = await fetchClusters();
      setClusters(data);
    } catch (err) {
      console.warn('Clusters API not available:', err);
    }
  }, []);

  const refreshAlerts = useCallback(async () => {
    const data = await fetchAlerts({ limit: 100 });
    setAlerts(data);
  }, []);

  const refreshLeaderboard = useCallback(async () => {
    try {
      const data = await fetchLeaderboard(100);
      setLeaderboard(data);
    } catch (err) {
      console.warn('Leaderboard not available yet:', err);
    }
  }, []);

  const refreshPipelineMetrics = useCallback(async () => {
    try {
      const data = await fetchPipelineMetrics();
      setPipelineMetrics(data);
    } catch (err) {
      console.warn('Pipeline metrics not available:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    let cancelled = false;
    const loadInitialData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [sensorsData, locationsData] = await Promise.all([
          fetchSensors(),
          fetchLocations(),
        ]);
        if (cancelled) return;

        setSensors(sensorsData);
        setLocations(locationsData);
        if (sensorsData.length > 0) {
          setSelectedSensorId((curr) => curr ?? sensorsData[0].sensorId);
        }

        // Non-blocking secondary loads
        Promise.allSettled([
          refreshClusters(),
          refreshAlerts(),
          refreshLeaderboard(),
          refreshPipelineMetrics(),
        ]);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load initial data';
        if (!cancelled) setError(msg);
        console.error('Initial data load failed:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    loadInitialData();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-refresh leaderboard / pipeline metrics every minute
  const intervalRef = useRef<number | null>(null);
  useEffect(() => {
    intervalRef.current = window.setInterval(() => {
      refreshLeaderboard();
      refreshPipelineMetrics();
    }, 60000);
    return () => {
      if (intervalRef.current) window.clearInterval(intervalRef.current);
    };
  }, [refreshLeaderboard, refreshPipelineMetrics]);

  const addAlert = useCallback((alert: Alert) => {
    setAlerts((prev) => [alert, ...prev].slice(0, 100));
  }, []);

  const updateTelemetry = useCallback((telemetry: Telemetry) => {
    setTelemetryMap((prev) => ({ ...prev, [telemetry.sensorId]: telemetry }));
  }, []);

  const acknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      const updated = await apiAcknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.alertId === alertId ? { ...a, ...updated } : a)),
      );
    } catch (err) {
      console.error(`Failed to acknowledge alert ${alertId}:`, err);
      throw err;
    }
  }, []);

  const resolveAlert = useCallback(async (alertId: string) => {
    try {
      const updated = await apiResolveAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.alertId === alertId ? { ...a, ...updated } : a)),
      );
    } catch (err) {
      console.error(`Failed to resolve alert ${alertId}:`, err);
      throw err;
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const contextValue: AppContextValue = {
    sensors,
    locations,
    clusters,
    alerts,
    leaderboard,
    pipelineMetrics,
    selectedSensorId,
    connectionStatus,
    telemetryMap,
    loading,
    error,
    setSelectedSensorId,
    addAlert,
    updateTelemetry,
    refreshSensors,
    refreshLocations,
    refreshClusters,
    refreshAlerts,
    refreshLeaderboard,
    refreshPipelineMetrics,
    acknowledgeAlert,
    resolveAlert,
    clearError,
  };

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
};

export const useAppContext = (): AppContextValue => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export { AppContext };
