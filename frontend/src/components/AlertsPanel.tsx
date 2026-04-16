/**
 * AlertsPanel Component - Real-time alert monitoring
 * 
 * Displays a list of recent alerts with filtering capabilities.
 * Updates in real-time via WebSocket and shows visual notifications for new alerts.
 * 
 * Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
 */

import { useEffect, useState, useCallback } from 'react';
import { fetchAlerts, fetchLocations } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { Alert, Location } from '../types';

/**
 * AlertsPanel component props
 */
export interface AlertsPanelProps {
  maxAlerts?: number; // Maximum number of alerts to display (default: 20)
  onAlertClick?: (alert: Alert) => void;
}

/**
 * Get color based on alert severity level
 */
const getSeverityColor = (level: Alert['level']): string => {
  switch (level) {
    case 'HIGH':
      return '#ff003c'; // Cyberpunk red
    case 'MEDIUM':
      return '#fb923c'; // Neon orange
    case 'LOW':
      return '#facc15'; // Neon yellow
    default:
      return '#94a3b8'; // gray
  }
};

/**
 * Get background color for alert items
 */
const getSeverityBackground = (level: Alert['level']): string => {
  switch (level) {
    case 'HIGH':
      return 'rgba(255, 0, 60, 0.15)'; // light red
    case 'MEDIUM':
      return 'rgba(251, 146, 60, 0.15)'; // light orange
    case 'LOW':
      return 'rgba(250, 204, 21, 0.15)'; // light yellow
    default:
      return 'rgba(148, 163, 184, 0.15)'; // light gray
  }
};

/**
 * Format timestamp to readable format
 */
const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  
  return date.toLocaleString();
};

/**
 * AlertsPanel Component
 * 
 * Displays recent alerts with filtering by severity and location.
 * Updates in real-time via WebSocket and shows notifications for new alerts.
 */
export const AlertsPanel: React.FC<AlertsPanelProps> = ({
  maxAlerts = 20,
  onAlertClick,
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filter states
  const [selectedLevel, setSelectedLevel] = useState<Alert['level'] | 'ALL'>('ALL');
  const [selectedLocation, setSelectedLocation] = useState<string>('ALL');
  
  // New alert notification state
  const [newAlertCount, setNewAlertCount] = useState(0);
  const [showNotification, setShowNotification] = useState(false);

  /**
   * Load locations for filter dropdown
   */
  const loadLocations = async () => {
    try {
      const data = await fetchLocations();
      setLocations(data);
    } catch (err) {
      console.error('Error fetching locations:', err);
    }
  };

  /**
   * Load alerts with current filters
   */
  const loadAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: { level?: Alert['level']; locationId?: string; limit: number } = {
        limit: maxAlerts,
      };
      
      if (selectedLevel !== 'ALL') {
        params.level = selectedLevel;
      }
      if (selectedLocation !== 'ALL') {
        params.locationId = selectedLocation;
      }
      
      const data = await fetchAlerts(params);
      setAlerts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
      console.error('Error fetching alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle new alert from WebSocket
   */
  const handleNewAlert = useCallback((alert: Alert) => {
    setAlerts((prevAlerts) => {
      // Add new alert to the top of the list
      const updatedAlerts = [alert, ...prevAlerts];
      
      // Limit to maxAlerts
      return updatedAlerts.slice(0, maxAlerts);
    });
    
    // Show notification
    setNewAlertCount((prev) => prev + 1);
    setShowNotification(true);
    
    // Hide notification after 3 seconds
    setTimeout(() => {
      setShowNotification(false);
      setNewAlertCount(0);
    }, 3000);
  }, [maxAlerts]);

  /**
   * Set up WebSocket connection for real-time updates
   */
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  useWebSocket(wsUrl, {
    onAlert: handleNewAlert,
  });

  /**
   * Load initial data on mount
   */
  useEffect(() => {
    loadLocations();
    loadAlerts();
  }, []);

  /**
   * Reload alerts when filters change
   */
  useEffect(() => {
    if (!loading) {
      loadAlerts();
    }
  }, [selectedLevel, selectedLocation]);

  /**
   * Handle alert click
   */
  const handleAlertClick = (alert: Alert) => {
    if (onAlertClick) {
      onAlertClick(alert);
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        color: '#6b7280',
      }}>
        Loading alerts...
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        color: '#ef4444',
      }}>
        <p>Error: {error}</p>
        <button
          onClick={loadAlerts}
          style={{
            marginTop: '16px',
            padding: '8px 16px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', padding: '16px', position: 'relative' }}>
      {/* New Alert Notification */}
      {showNotification && (
        <div style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          backgroundColor: '#ef4444',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          zIndex: 1000,
          animation: 'slideIn 0.3s ease-out',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <span style={{ fontSize: '20px' }}>🚨</span>
          <span style={{ fontWeight: '600' }}>
            {newAlertCount} new alert{newAlertCount > 1 ? 's' : ''}
          </span>
        </div>
      )}

      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <h2 style={{ 
          margin: 0, 
          fontSize: '20px', 
          fontWeight: '700',
          color: '#e0f2fe',
          textTransform: 'uppercase',
          letterSpacing: '1px',
          textShadow: '0 0 10px rgba(0, 243, 255, 0.5)'
        }}>
          Live Anomalies
        </h2>
        <div style={{
          backgroundColor: 'rgba(255, 0, 60, 0.2)',
          border: '1px solid #ff003c',
          color: '#ff003c',
          padding: '4px 12px',
          borderRadius: '12px',
          fontSize: '14px',
          fontWeight: '700',
          boxShadow: '0 0 10px rgba(255, 0, 60, 0.3)'
        }}>
          {alerts.length} ALERTS
        </div>
      </div>

      {/* Filter Controls */}
      <div style={{ 
        display: 'flex', 
        gap: '12px',
        marginBottom: '16px',
        flexWrap: 'wrap',
      }}>
        {/* Severity Filter */}
        <div style={{ flex: '1', minWidth: '150px' }}>
          <label style={{ 
             display: 'block',
             fontSize: '11px',
             fontWeight: '700',
             color: '#00f3ff',
             marginBottom: '4px',
             textTransform: 'uppercase',
             letterSpacing: '1px'
          }}>
            Severity
          </label>
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value as Alert['level'] | 'ALL')}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid rgba(0, 243, 255, 0.3)',
              borderRadius: '4px',
              fontSize: '14px',
              backgroundColor: 'rgba(2, 6, 23, 0.5)',
              color: '#e0f2fe',
              cursor: 'pointer',
              outline: 'none'
            }}
          >
            <option value="ALL">All Levels</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        {/* Location Filter */}
        <div style={{ flex: '1', minWidth: '150px' }}>
          <label style={{ 
             display: 'block',
             fontSize: '11px',
             fontWeight: '700',
             color: '#00f3ff',
             marginBottom: '4px',
             textTransform: 'uppercase',
             letterSpacing: '1px'
          }}>
            Location
          </label>
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid rgba(0, 243, 255, 0.3)',
              borderRadius: '4px',
              fontSize: '14px',
              backgroundColor: 'rgba(2, 6, 23, 0.5)',
              color: '#e0f2fe',
              cursor: 'pointer',
              outline: 'none'
            }}
          >
            <option value="ALL">All Locations</option>
            {locations
              .filter((loc) => loc.type === 'Ward')
              .map((loc) => (
                <option key={loc.locationId} value={loc.locationId}>
                  {loc.name}
                </option>
              ))}
          </select>
        </div>
      </div>

      {/* Alerts List */}
      <div style={{ 
        backgroundColor: 'transparent',
        borderRadius: '0',
        overflow: 'hidden',
        maxHeight: '600px',
        overflowY: 'auto',
      }}>
        {alerts.length === 0 ? (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '200px',
            color: '#94a3b8',
          }}>
            SYSTEM NORMAL. NO ANOMALIES.
          </div>
        ) : (
          <div>
            {alerts.map((alert) => (
              <div
                key={alert.alertId}
                onClick={() => handleAlertClick(alert)}
                style={{
                  padding: '16px',
                  borderBottom: '1px solid rgba(0, 243, 255, 0.2)',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: 'transparent',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(0, 243, 255, 0.1)';
                  e.currentTarget.style.boxShadow = 'inset 0 0 10px rgba(0, 243, 255, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: '12px',
                }}>
                  {/* Alert Content */}
                  <div style={{ flex: 1 }}>
                    {/* Severity Badge */}
                    <div style={{ 
                      display: 'inline-block',
                      backgroundColor: getSeverityBackground(alert.level),
                      border: `1px solid ${getSeverityColor(alert.level)}`,
                      color: getSeverityColor(alert.level),
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '700',
                      letterSpacing: '1px',
                      marginBottom: '8px',
                      boxShadow: `0 0 10px ${getSeverityBackground(alert.level)}`
                    }}>
                      {alert.level}
                    </div>

                    {/* Alert Details */}
                    <div style={{ 
                      fontSize: '14px',
                      color: '#e0f2fe',
                      marginBottom: '4px',
                    }}>
                      <span style={{ fontWeight: '600', color: '#00f3ff' }}>{alert.metricType}</span>
                      {' '}exceeded threshold: {' '}
                      <span style={{ 
                        fontWeight: '700',
                        color: getSeverityColor(alert.level),
                        textShadow: `0 0 5px ${getSeverityColor(alert.level)}`
                      }}>
                        {alert.value.toFixed(1)}
                        {alert.metricType === 'CO2' ? ' ppm' : 
                         alert.metricType === 'Noise' ? ' dB' : ' °C'}
                      </span>
                    </div>

                    {/* Location and Sensor */}
                    <div style={{ 
                      fontSize: '11px',
                      color: '#94a3b8',
                      textTransform: 'uppercase',
                      letterSpacing: '1px'
                    }}>
                      SENSOR: {alert.sensorId}
                    </div>
                  </div>

                  {/* Timestamp */}
                  <div style={{ 
                    fontSize: '11px',
                    color: '#00f3ff',
                    whiteSpace: 'nowrap',
                    opacity: 0.8
                  }}>
                    {formatTimestamp(alert.createdAt)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info */}
      <div style={{ 
        marginTop: '12px', 
        textAlign: 'center', 
        color: '#00f3ff',
        fontSize: '11px',
        letterSpacing: '1px',
        opacity: 0.7
      }}>
        SHOWING {alerts.length} ALERTS. LIVE FEED ACTIVE.
      </div>

      {/* CSS Animation */}
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default AlertsPanel;
