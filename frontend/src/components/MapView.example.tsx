/**
 * MapView Component Usage Example
 * 
 * This example demonstrates how to use the MapView component
 * with real-time WebSocket updates for alerts and telemetry.
 */

import { useState, useEffect } from 'react';
import { MapView } from './MapView';
import { useWebSocket } from '../hooks/useWebSocket';
import { fetchSensors, fetchLocations, fetchAlerts, fetchTelemetry } from '../services/api';
import type { Sensor, Location, Alert, Telemetry } from '../types';

/**
 * Example component showing MapView integration
 */
export const MapViewExample: React.FC = () => {
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [telemetry, setTelemetry] = useState<Record<string, Telemetry>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load initial data from API
   */
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Fetch all required data in parallel
        const [sensorsData, locationsData, alertsData] = await Promise.all([
          fetchSensors(),
          fetchLocations(),
          fetchAlerts({ limit: 100 }),
        ]);

        setSensors(sensorsData);
        setLocations(locationsData);
        setAlerts(alertsData);

        // Fetch latest telemetry for each sensor
        const telemetryPromises = sensorsData.map(sensor =>
          fetchTelemetry(sensor.sensorId, { limit: 1 })
            .then(data => ({ sensorId: sensor.sensorId, data: data[0] }))
            .catch(() => ({ sensorId: sensor.sensorId, data: null }))
        );

        const telemetryResults = await Promise.all(telemetryPromises);
        const telemetryMap: Record<string, Telemetry> = {};
        
        telemetryResults.forEach(result => {
          if (result.data) {
            telemetryMap[result.sensorId] = result.data;
          }
        });

        setTelemetry(telemetryMap);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setLoading(false);
      }
    };

    loadData();
  }, []);

  /**
   * Set up WebSocket connection for real-time updates
   */
  const wsStatus = useWebSocket(
    import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
    {
      onTelemetry: (data: Telemetry) => {
        // Update telemetry for the sensor
        setTelemetry(prev => ({
          ...prev,
          [data.sensorId]: data,
        }));
      },
      onAlert: (data: Alert) => {
        // Add new alert to the beginning of the list
        setAlerts(prev => [data, ...prev].slice(0, 100)); // Keep last 100 alerts
      },
      onConnectionAck: (message: string) => {
        console.log('WebSocket connected:', message);
      },
    }
  );

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading map data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: 'red' }}>
        <p>Error: {error}</p>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '600px' }}>
      <div style={{ 
        padding: '10px', 
        background: '#f3f4f6', 
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>
          Sensor Map
        </h2>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <span style={{ fontSize: '14px', color: '#6b7280' }}>
            WebSocket: {wsStatus}
          </span>
          <div style={{ display: 'flex', gap: '15px', fontSize: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ 
                width: '12px', 
                height: '12px', 
                borderRadius: '50%', 
                background: '#22c55e' 
              }} />
              <span>Normal</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ 
                width: '12px', 
                height: '12px', 
                borderRadius: '50%', 
                background: '#eab308' 
              }} />
              <span>Warning</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ 
                width: '12px', 
                height: '12px', 
                borderRadius: '50%', 
                background: '#ef4444' 
              }} />
              <span>High Alert</span>
            </div>
          </div>
        </div>
      </div>
      <div style={{ height: 'calc(100% - 60px)' }}>
        <MapView
          sensors={sensors}
          locations={locations}
          alerts={alerts}
          telemetry={telemetry}
          center={[106.6297, 10.8231]} // Ho Chi Minh City
          zoom={12}
        />
      </div>
    </div>
  );
};

export default MapViewExample;
