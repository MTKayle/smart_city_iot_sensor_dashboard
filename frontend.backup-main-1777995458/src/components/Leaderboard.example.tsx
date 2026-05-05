/**
 * Leaderboard Component Usage Example
 * 
 * This example demonstrates how to use the Leaderboard component
 * with map integration for location zooming.
 */

import { useState, useEffect } from 'react';
import { Leaderboard } from './Leaderboard';
import { MapView } from './MapView';
import { fetchSensors, fetchLocations, fetchAlerts } from '../services/api';
import type { Sensor, Location, Alert, Telemetry } from '../types';

/**
 * Example component showing Leaderboard integration with MapView
 */
export const LeaderboardExample: React.FC = () => {
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [telemetry] = useState<Record<string, Telemetry>>({});
  const [mapCenter, setMapCenter] = useState<[number, number]>([106.6297, 10.8231]);
  const [mapZoom, setMapZoom] = useState(12);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null);

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
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setLoading(false);
      }
    };

    loadData();
  }, []);

  /**
   * Handle location click from leaderboard
   * Zooms map to the selected location
   */
  const handleLocationClick = (locationId: string) => {
    setSelectedLocation(locationId);
    
    // Find the location
    const location = locations.find(loc => loc.locationId === locationId);
    if (!location) return;

    // Generate coordinates for the location (demo implementation)
    // In production, use actual lat/lng from location data
    const coords = generateCoordinates(locationId, [106.6297, 10.8231]);
    
    // Zoom to location
    setMapCenter(coords);
    setMapZoom(15);

    // Reset selection after animation
    setTimeout(() => setSelectedLocation(null), 2000);
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading dashboard data...</p>
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
    <div style={{ 
      display: 'grid', 
      gridTemplateColumns: '2fr 1fr', 
      gap: '16px',
      padding: '16px',
      height: '100vh',
      background: '#f9fafb',
    }}>
      {/* Map Section */}
      <div style={{ 
        background: 'white',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <div style={{ 
          padding: '16px', 
          borderBottom: '1px solid #e5e7eb',
        }}>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>
            Sensor Locations
          </h2>
          {selectedLocation && (
            <p style={{ 
              margin: '8px 0 0 0', 
              fontSize: '14px', 
              color: '#3b82f6',
              fontWeight: 500,
            }}>
              Zooming to {locations.find(l => l.locationId === selectedLocation)?.name}...
            </p>
          )}
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <MapView
            sensors={sensors}
            locations={locations}
            alerts={alerts}
            telemetry={telemetry}
            center={mapCenter}
            zoom={mapZoom}
          />
        </div>
      </div>

      {/* Leaderboard Section */}
      <div style={{ 
        background: 'white',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        overflow: 'auto',
        maxHeight: '100%',
      }}>
        <Leaderboard 
          onLocationClick={handleLocationClick}
          refreshInterval={60000} // Refresh every 60 seconds
        />
      </div>
    </div>
  );
};

/**
 * Generate demo coordinates for a location
 * In production, use actual lat/lng from location data
 */
const generateCoordinates = (locationId: string, center: [number, number]): [number, number] => {
  let hash = 0;
  for (let i = 0; i < locationId.length; i++) {
    hash = ((hash << 5) - hash) + locationId.charCodeAt(i);
    hash = hash & hash;
  }
  
  const offset = 0.05;
  const lng = center[0] + (((hash % 1000) / 1000) - 0.5) * offset;
  const lat = center[1] + ((((hash >> 10) % 1000) / 1000) - 0.5) * offset;
  
  return [lng, lat];
};

/**
 * Alternative: Standalone Leaderboard Example
 */
export const LeaderboardStandaloneExample: React.FC = () => {
  const handleLocationClick = (locationId: string) => {
    console.log('Location clicked:', locationId);
    // Handle location click (e.g., navigate to detail page)
  };

  return (
    <div style={{ 
      maxWidth: '800px', 
      margin: '0 auto', 
      padding: '20px',
    }}>
      <h1 style={{ 
        fontSize: '24px', 
        fontWeight: 700, 
        marginBottom: '20px',
      }}>
        Environmental Quality Rankings
      </h1>
      <Leaderboard 
        onLocationClick={handleLocationClick}
        refreshInterval={30000} // Refresh every 30 seconds
      />
    </div>
  );
};

/**
 * Alternative: Custom Refresh Interval Example
 */
export const LeaderboardCustomRefreshExample: React.FC = () => {
  const [refreshInterval, setRefreshInterval] = useState(60000);

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ 
        marginBottom: '20px',
        display: 'flex',
        gap: '10px',
        alignItems: 'center',
      }}>
        <label htmlFor="refresh-interval">Refresh Interval:</label>
        <select
          id="refresh-interval"
          value={refreshInterval}
          onChange={(e) => setRefreshInterval(Number(e.target.value))}
          style={{
            padding: '8px',
            borderRadius: '4px',
            border: '1px solid #d1d5db',
          }}
        >
          <option value={10000}>10 seconds</option>
          <option value={30000}>30 seconds</option>
          <option value={60000}>60 seconds</option>
          <option value={120000}>2 minutes</option>
        </select>
      </div>
      <Leaderboard refreshInterval={refreshInterval} />
    </div>
  );
};

export default LeaderboardExample;
