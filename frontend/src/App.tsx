/**
 * App Component - Main application layout for Smart City IoT Dashboard (v2)
 * 
 * Implements the main dashboard layout with:
 * - Header with title and connection status indicator
 * - Grid layout: ChartView (left), Map (center), Leaderboard + AlertsPanel (right)
 * - Cluster visualization on map
 * - WebSocket integration for real-time updates
 * 
 * Requirements: FR9.1, FR9.2, FR9.3, FR9.4
 */

import { useState, useEffect, useCallback } from 'react';
import { MapView, ChartView, Leaderboard, AlertsPanel } from './components';
import { useWebSocket } from './hooks/useWebSocket';
import { fetchSensors, fetchLocations, fetchClusters } from './services/api';
import type { Sensor, Location, Alert, Telemetry, SensorCluster } from './types';
import './App.css';

function App() {
  // State management
  const [selectedSensorId, setSelectedSensorId] = useState<string | null>(null);
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [clusters, setClusters] = useState<SensorCluster[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [telemetryMap, setTelemetryMap] = useState<Record<string, Telemetry>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load initial data (sensors, locations, clusters)
   */
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const [sensorsData, locationsData] = await Promise.all([
          fetchSensors(),
          fetchLocations(),
        ]);
        
        setSensors(sensorsData);
        setLocations(locationsData);
        
        // Load clusters (non-blocking — may not exist yet)
        try {
          const clustersData = await fetchClusters();
          setClusters(clustersData);
        } catch {
          console.warn('Clusters API not available yet');
        }
        
        // Auto-select first sensor if available
        if (sensorsData.length > 0 && !selectedSensorId) {
          const sortedSensors = [...sensorsData].sort((a,b) => a.sensorId.localeCompare(b.sensorId));
          setSelectedSensorId(sortedSensors[0].sensorId);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load initial data');
        console.error('Error loading initial data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  /**
   * Handle real-time telemetry updates from WebSocket
   */
  const handleTelemetryUpdate = useCallback((telemetry: Telemetry) => {
    setTelemetryMap(prev => ({
      ...prev,
      [telemetry.sensorId]: telemetry,
    }));
  }, []);

  /**
   * Handle real-time alert updates from WebSocket
   */
  const handleAlertUpdate = useCallback((alert: Alert) => {
    setAlerts(prev => [alert, ...prev].slice(0, 100)); // Keep last 100 alerts
  }, []);

  /**
   * WebSocket connection
   */
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  const connectionStatus = useWebSocket(wsUrl, {
    onTelemetry: handleTelemetryUpdate,
    onAlert: handleAlertUpdate,
  });

  /**
   * Handle location click from Leaderboard
   */
  const handleLocationClick = useCallback((locationId: string) => {
    // Find first sensor in this location
    const sensor = sensors.find(s => s.locationId === locationId);
    if (sensor) {
      setSelectedSensorId(sensor.sensorId);
    }
  }, [sensors]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading Smart City Dashboard...</p>
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div className="app-error">
        <h2>Error Loading Dashboard</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="app cyberpunk-theme">
      {/* Background Map - Full Screen */}
      <div className="map-background">
        <MapView
          sensors={sensors}
          locations={locations}
          alerts={alerts}
          telemetry={telemetryMap}
          clusters={clusters}
        />
      </div>

      {/* Sci-Fi UI Overlay */}
      <div className="app-overlay">
        {/* Header */}
        <header className="app-header glass-panel">
          <div className="header-content">
            <h1 className="app-title">Smart City Operation Center</h1>
            <div className="connection-status">
              <span 
                className={`status-indicator ${connectionStatus}`}
                title={`WebSocket ${connectionStatus}`}
              ></span>
              <span className="status-text neon-text">
                {connectionStatus === 'connected' ? 'Connected' : 
                 connectionStatus === 'connecting' ? 'Connecting...' :
                 connectionStatus === 'error' ? 'Connection Error' :
                 'Disconnected'}
              </span>
            </div>
          </div>
        </header>

        {/* Main Dashboard Grid */}
        <main className="dashboard-grid">
          {/* Left Panel: ChartView */}
          <section className="grid-section chart-section glass-panel">
            {selectedSensorId ? (
              <ChartView
                sensorId={selectedSensorId}
                wsUrl={wsUrl}
              />
            ) : (
              <div className="no-sensor-selected">
                <p>Select a sensor from the map to view analytics</p>
              </div>
            )}
          </section>

          {/* Center Panel: Empty space to view the map */}
          <section className="grid-section center-section empty-click-through">
            {/* The map is visible here */}
          </section>

          {/* Right Panel: Leaderboard + AlertsPanel */}
          <section className="grid-section right-section">
            <div className="leaderboard-container glass-panel">
              <Leaderboard
                onLocationClick={handleLocationClick}
                refreshInterval={60000}
              />
            </div>
            <div className="alerts-container glass-panel">
              <AlertsPanel
                maxAlerts={20}
              />
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
