/**
 * AlertsPanel Component — Real-time alert monitoring (v2)
 *
 * Displays a list of recent alerts with filtering capabilities.
 * Supports alert types: THRESHOLD, PREDICTIVE, ANOMALY, CLUSTER.
 * Displays confidence scores for ML-based alerts.
 * Updates in real-time via WebSocket.
 *
 * Requirements: FR9.4
 */

import { useEffect, useState, useCallback } from 'react';
import { fetchAlerts, fetchLocations } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { Alert, AlertType, AlertSeverity, Location } from '../types';

export interface AlertsPanelProps {
  maxAlerts?: number;
  onAlertClick?: (alert: Alert) => void;
}

// ── Alert type configuration ──
interface AlertTypeConfig {
  label: string;
  icon: string;
  color: string;
  bgColor: string;
  description: string;
}

const ALERT_TYPE_CONFIG: Record<AlertType, AlertTypeConfig> = {
  THRESHOLD: {
    label: 'THRESHOLD',
    icon: '⚡',
    color: '#ff003c',
    bgColor: 'rgba(255, 0, 60, 0.12)',
    description: 'Exceeded threshold limit',
  },
  PREDICTIVE: {
    label: 'PREDICTIVE',
    icon: '🔮',
    color: '#c084fc',
    bgColor: 'rgba(192, 132, 252, 0.12)',
    description: 'ML prediction alert',
  },
  ANOMALY: {
    label: 'ANOMALY',
    icon: '🔬',
    color: '#f59e0b',
    bgColor: 'rgba(245, 158, 11, 0.12)',
    description: 'Anomaly detected',
  },
  CLUSTER: {
    label: 'CLUSTER',
    icon: '🔗',
    color: '#06b6d4',
    bgColor: 'rgba(6, 182, 212, 0.12)',
    description: 'Cluster-wide alert',
  },
};

/**
 * Get color based on severity level
 */
const getSeverityColor = (level: AlertSeverity): string => {
  switch (level) {
    case 'CRITICAL': return '#dc2626';
    case 'HIGH': return '#ff003c';
    case 'MEDIUM': return '#fb923c';
    case 'LOW': return '#facc15';
    default: return '#94a3b8';
  }
};

const getSeverityBg = (level: AlertSeverity): string => {
  switch (level) {
    case 'CRITICAL': return 'rgba(220, 38, 38, 0.15)';
    case 'HIGH': return 'rgba(255, 0, 60, 0.15)';
    case 'MEDIUM': return 'rgba(251, 146, 60, 0.15)';
    case 'LOW': return 'rgba(250, 204, 21, 0.15)';
    default: return 'rgba(148, 163, 184, 0.15)';
  }
};

/**
 * Get the severity from either severity or legacy level field.
 */
const getAlertSeverity = (alert: Alert): AlertSeverity => {
  return alert.severity || alert.level || 'LOW';
};

/**
 * Get the alert type, defaulting to THRESHOLD for legacy alerts.
 */
const getAlertType = (alert: Alert): AlertType => {
  return alert.alertType || 'THRESHOLD';
};

/**
 * Format timestamp
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
 * Get metric unit
 */
const getMetricUnit = (metric: string): string => {
  const units: Record<string, string> = {
    CO2: 'ppm', Noise: 'dB', Temperature: '°C', 'PM2.5': 'μg/m³', Humidity: '%',
  };
  return units[metric] || '';
};

// ── Confidence bar component ──
const ConfidenceBar: React.FC<{ score: number; color: string }> = ({ score, color }) => (
  <div style={{
    display: 'flex', alignItems: 'center', gap: '6px',
    marginTop: '6px',
  }}>
    <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
      Confidence
    </span>
    <div style={{
      flex: 1, height: '4px', backgroundColor: 'rgba(255,255,255,0.05)',
      borderRadius: '2px', overflow: 'hidden',
    }}>
      <div style={{
        width: `${score * 100}%`,
        height: '100%',
        backgroundColor: color,
        borderRadius: '2px',
        transition: 'width 0.3s ease',
        boxShadow: `0 0 6px ${color}50`,
      }} />
    </div>
    <span style={{ fontSize: '10px', fontWeight: '700', color, fontVariantNumeric: 'tabular-nums' }}>
      {(score * 100).toFixed(0)}%
    </span>
  </div>
);

export const AlertsPanel: React.FC<AlertsPanelProps> = ({
  maxAlerts = 20,
  onAlertClick,
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [selectedSeverity, setSelectedSeverity] = useState<AlertSeverity | 'ALL'>('ALL');
  const [selectedType, setSelectedType] = useState<AlertType | 'ALL'>('ALL');
  const [selectedLocation, setSelectedLocation] = useState<string>('ALL');

  // Notification
  const [newAlertCount, setNewAlertCount] = useState(0);
  const [showNotification, setShowNotification] = useState(false);

  const loadLocations = async () => {
    try {
      const data = await fetchLocations();
      setLocations(data);
    } catch (err) {
      console.error('Error fetching locations:', err);
    }
  };

  const loadAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: { level?: AlertSeverity; alertType?: AlertType; locationId?: string; limit: number } = {
        limit: maxAlerts,
      };

      if (selectedSeverity !== 'ALL') params.level = selectedSeverity;
      if (selectedType !== 'ALL') params.alertType = selectedType;
      if (selectedLocation !== 'ALL') params.locationId = selectedLocation;

      const data = await fetchAlerts(params);
      setAlerts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const handleNewAlert = useCallback((alert: Alert) => {
    setAlerts((prev) => [alert, ...prev].slice(0, maxAlerts));
    setNewAlertCount((prev) => prev + 1);
    setShowNotification(true);
    setTimeout(() => {
      setShowNotification(false);
      setNewAlertCount(0);
    }, 3000);
  }, [maxAlerts]);

  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  useWebSocket(wsUrl, { onAlert: handleNewAlert });

  useEffect(() => {
    loadLocations();
    loadAlerts();
  }, []);

  useEffect(() => {
    if (!loading) loadAlerts();
  }, [selectedSeverity, selectedType, selectedLocation]);

  const handleAlertClick = (alert: Alert) => {
    if (onAlertClick) onAlertClick(alert);
  };

  // ── Count by type ──
  const typeCounts = alerts.reduce((acc, a) => {
    const type = getAlertType(a);
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // ── Render states ──
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px', color: '#64748b' }}>
        Loading alerts...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '400px', color: '#ef4444' }}>
        <p>Error: {error}</p>
        <button
          onClick={loadAlerts}
          style={{
            marginTop: '16px', padding: '8px 16px',
            backgroundColor: 'transparent', color: '#00f3ff',
            border: '1px solid #00f3ff', borderRadius: '6px',
            cursor: 'pointer', fontSize: '13px',
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', padding: '12px', position: 'relative' }}>
      {/* Notification Toast */}
      {showNotification && (
        <div style={{
          position: 'absolute', top: '12px', right: '12px', zIndex: 1000,
          backgroundColor: 'rgba(220, 38, 38, 0.9)', color: 'white',
          padding: '10px 14px', borderRadius: '8px',
          boxShadow: '0 4px 20px rgba(220, 38, 38, 0.4)',
          animation: 'slideIn 0.3s ease-out',
          display: 'flex', alignItems: 'center', gap: '8px',
          border: '1px solid rgba(255,255,255,0.2)',
        }}>
          <span style={{ fontSize: '18px' }}>🚨</span>
          <span style={{ fontWeight: '600', fontSize: '13px' }}>
            {newAlertCount} new alert{newAlertCount > 1 ? 's' : ''}
          </span>
        </div>
      )}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <h2 style={{
          margin: 0, fontSize: '16px', fontWeight: '700', color: '#e0f2fe',
          textTransform: 'uppercase', letterSpacing: '1px',
          textShadow: '0 0 10px rgba(0, 243, 255, 0.5)',
        }}>
          ⚡ Live Alerts
        </h2>
        <div style={{
          backgroundColor: 'rgba(255, 0, 60, 0.2)', border: '1px solid #ff003c',
          color: '#ff003c', padding: '3px 10px', borderRadius: '12px',
          fontSize: '12px', fontWeight: '700', boxShadow: '0 0 8px rgba(255, 0, 60, 0.3)',
        }}>
          {alerts.length}
        </div>
      </div>

      {/* Alert Type Summary Pills */}
      <div style={{
        display: 'flex', gap: '6px', marginBottom: '10px',
        flexWrap: 'wrap',
      }}>
        {(Object.entries(ALERT_TYPE_CONFIG) as [AlertType, AlertTypeConfig][]).map(([type, cfg]) => {
          const count = typeCounts[type] || 0;
          const isActive = selectedType === type;
          return (
            <button
              key={type}
              onClick={() => setSelectedType(isActive ? 'ALL' : type)}
              style={{
                padding: '3px 8px',
                border: `1px solid ${isActive ? cfg.color : 'rgba(100,116,139,0.3)'}`,
                borderRadius: '12px',
                backgroundColor: isActive ? cfg.bgColor : 'transparent',
                color: isActive ? cfg.color : '#64748b',
                cursor: 'pointer',
                fontSize: '10px',
                fontWeight: isActive ? '700' : '400',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <span>{cfg.icon}</span>
              <span>{cfg.label}</span>
              {count > 0 && (
                <span style={{
                  backgroundColor: cfg.color + '30',
                  padding: '0 4px', borderRadius: '6px',
                  fontSize: '9px', fontWeight: '700', color: cfg.color,
                }}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Filter Controls */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
        {/* Severity Filter */}
        <div style={{ flex: '1', minWidth: '120px' }}>
          <label style={{
            display: 'block', fontSize: '10px', fontWeight: '700',
            color: '#00f3ff', marginBottom: '3px',
            textTransform: 'uppercase', letterSpacing: '0.5px',
          }}>
            Severity
          </label>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value as AlertSeverity | 'ALL')}
            style={{
              width: '100%', padding: '6px 8px',
              border: '1px solid rgba(0, 243, 255, 0.2)',
              borderRadius: '4px', fontSize: '12px',
              backgroundColor: 'rgba(2, 6, 23, 0.5)',
              color: '#e0f2fe', cursor: 'pointer', outline: 'none',
            }}
          >
            <option value="ALL">All</option>
            <option value="CRITICAL">🔴 Critical</option>
            <option value="HIGH">🟡 High</option>
            <option value="MEDIUM">🟠 Medium</option>
            <option value="LOW">🟢 Low</option>
          </select>
        </div>

        {/* Location Filter */}
        <div style={{ flex: '1', minWidth: '120px' }}>
          <label style={{
            display: 'block', fontSize: '10px', fontWeight: '700',
            color: '#00f3ff', marginBottom: '3px',
            textTransform: 'uppercase', letterSpacing: '0.5px',
          }}>
            Location
          </label>
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            style={{
              width: '100%', padding: '6px 8px',
              border: '1px solid rgba(0, 243, 255, 0.2)',
              borderRadius: '4px', fontSize: '12px',
              backgroundColor: 'rgba(2, 6, 23, 0.5)',
              color: '#e0f2fe', cursor: 'pointer', outline: 'none',
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
        overflow: 'hidden', maxHeight: '500px', overflowY: 'auto',
      }}>
        {alerts.length === 0 ? (
          <div style={{
            display: 'flex', flexDirection: 'column',
            justifyContent: 'center', alignItems: 'center',
            height: '150px', color: '#94a3b8',
          }}>
            <span style={{ fontSize: '24px', marginBottom: '8px' }}>✅</span>
            <span style={{ fontSize: '12px', letterSpacing: '1px', textTransform: 'uppercase' }}>
              System normal — No alerts
            </span>
          </div>
        ) : (
          <div>
            {alerts.map((alert) => {
              const alertType = getAlertType(alert);
              const severity = getAlertSeverity(alert);
              const typeConfig = ALERT_TYPE_CONFIG[alertType];
              const isMLAlert = alertType === 'PREDICTIVE' || alertType === 'ANOMALY';

              return (
                <div
                  key={alert.alertId}
                  onClick={() => handleAlertClick(alert)}
                  style={{
                    padding: '12px',
                    borderBottom: '1px solid rgba(0, 243, 255, 0.1)',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    backgroundColor: 'transparent',
                    borderLeft: `3px solid ${typeConfig.color}`,
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(0, 243, 255, 0.06)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  {/* Top row: type badge + severity + timestamp */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                    <div style={{ flex: 1 }}>
                      {/* Type + Severity badges */}
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '6px' }}>
                        {/* Alert Type Badge */}
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: '3px',
                          backgroundColor: typeConfig.bgColor,
                          border: `1px solid ${typeConfig.color}40`,
                          color: typeConfig.color,
                          padding: '2px 6px', borderRadius: '4px',
                          fontSize: '9px', fontWeight: '700', letterSpacing: '0.5px',
                        }}>
                          {typeConfig.icon} {typeConfig.label}
                        </span>

                        {/* Severity Badge */}
                        <span style={{
                          display: 'inline-block',
                          backgroundColor: getSeverityBg(severity),
                          border: `1px solid ${getSeverityColor(severity)}`,
                          color: getSeverityColor(severity),
                          padding: '2px 6px', borderRadius: '4px',
                          fontSize: '9px', fontWeight: '700', letterSpacing: '0.5px',
                          boxShadow: `0 0 6px ${getSeverityBg(severity)}`,
                        }}>
                          {severity}
                        </span>

                        {/* Status badge */}
                        {alert.status && alert.status !== 'OPEN' && (
                          <span style={{
                            display: 'inline-block',
                            backgroundColor: alert.status === 'RESOLVED' ? 'rgba(34,197,94,0.15)' : 'rgba(59,130,246,0.15)',
                            color: alert.status === 'RESOLVED' ? '#22c55e' : '#3b82f6',
                            padding: '2px 6px', borderRadius: '4px',
                            fontSize: '9px', fontWeight: '600',
                          }}>
                            {alert.status}
                          </span>
                        )}
                      </div>

                      {/* Alert message */}
                      <div style={{ fontSize: '13px', color: '#e0f2fe', marginBottom: '4px' }}>
                        <span style={{ fontWeight: '600', color: '#00f3ff' }}>{alert.metricType}</span>
                        {alertType === 'THRESHOLD' && (
                          <>
                            {' exceeded threshold: '}
                            <span style={{
                              fontWeight: '700', color: getSeverityColor(severity),
                              textShadow: `0 0 5px ${getSeverityColor(severity)}`,
                            }}>
                              {alert.value.toFixed(1)} {getMetricUnit(alert.metricType)}
                            </span>
                            {alert.threshold !== null && alert.threshold !== undefined && (
                              <span style={{ fontSize: '11px', color: '#94a3b8', marginLeft: '4px' }}>
                                (limit: {alert.threshold.toFixed(1)})
                              </span>
                            )}
                          </>
                        )}
                        {alertType === 'PREDICTIVE' && (
                          <>
                            {' predicted to reach '}
                            <span style={{
                              fontWeight: '700', color: typeConfig.color,
                              textShadow: `0 0 5px ${typeConfig.color}`,
                            }}>
                              {alert.predictedValue?.toFixed(1) || alert.value.toFixed(1)} {getMetricUnit(alert.metricType)}
                            </span>
                          </>
                        )}
                        {alertType === 'ANOMALY' && (
                          <>
                            {' anomaly detected: '}
                            <span style={{
                              fontWeight: '700', color: typeConfig.color,
                              textShadow: `0 0 5px ${typeConfig.color}`,
                            }}>
                              {alert.value.toFixed(1)} {getMetricUnit(alert.metricType)}
                            </span>
                          </>
                        )}
                        {alertType === 'CLUSTER' && (
                          <>
                            {' cluster-wide alert: '}
                            <span style={{
                              fontWeight: '700', color: typeConfig.color,
                              textShadow: `0 0 5px ${typeConfig.color}`,
                            }}>
                              {alert.value.toFixed(1)} {getMetricUnit(alert.metricType)}
                            </span>
                          </>
                        )}
                      </div>

                      {/* Custom message */}
                      {alert.message && (
                        <div style={{
                          fontSize: '11px', color: '#94a3b8', fontStyle: 'italic',
                          marginBottom: '4px',
                        }}>
                          {alert.message}
                        </div>
                      )}

                      {/* Sensor / Cluster ID */}
                      <div style={{
                        fontSize: '10px', color: '#64748b',
                        textTransform: 'uppercase', letterSpacing: '0.5px',
                        display: 'flex', gap: '8px', flexWrap: 'wrap',
                      }}>
                        {alert.sensorId && <span>SENSOR: {alert.sensorId}</span>}
                        {alert.clusterId && <span>CLUSTER: {alert.clusterId}</span>}
                      </div>

                      {/* Confidence Bar (for PREDICTIVE / ANOMALY) */}
                      {isMLAlert && alert.confidenceScore !== null && alert.confidenceScore !== undefined && (
                        <ConfidenceBar score={alert.confidenceScore} color={typeConfig.color} />
                      )}
                    </div>

                    {/* Timestamp */}
                    <div style={{
                      fontSize: '10px', color: '#00f3ff',
                      whiteSpace: 'nowrap', opacity: 0.7,
                    }}>
                      {formatTimestamp(alert.createdAt)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{
        marginTop: '8px', textAlign: 'center', color: '#00f3ff',
        fontSize: '10px', letterSpacing: '1px', opacity: 0.6,
      }}>
        SHOWING {alerts.length} ALERTS · LIVE FEED ACTIVE
      </div>

      {/* CSS Animation */}
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default AlertsPanel;
