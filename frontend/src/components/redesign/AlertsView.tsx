import React from 'react';
import { MapPin, Check, CheckCircle2, Eye } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import { formatLocationName } from '../../utils/location';
import type { Alert as ApiAlert } from '../../types';
import type { MapFocusTarget } from './types';
import PredictiveDetailModal from './alerts/PredictiveDetailModal';

const formatThreshold = (alert: ApiAlert): string => {
  if (alert.threshold !== null && alert.threshold !== undefined) {
    return alert.threshold.toFixed(1);
  }
  // Fallback table mirroring backend ALERT_THRESHOLDS in alert_service.py
  switch (alert.metricType) {
    case 'CO2':
      return '1000';
    case 'Noise':
      return '85';
    case 'PM25':
    case 'PM2.5':
      return '55';
    case 'Humidity':
      return '90';
    default:
      return '—';
  }
};

interface AlertsViewProps {
  onFocusOnMap?: (target: MapFocusTarget) => void;
}

const AlertsView: React.FC<AlertsViewProps> = ({ onFocusOnMap }) => {
  const { alerts, sensors, locations, acknowledgeAlert, resolveAlert } = useAppContext();
  const [severityFilter, setSeverityFilter] = React.useState<string>('all');
  const [typeFilter, setTypeFilter] = React.useState<string>('all');
  const [busyId, setBusyId] = React.useState<string | null>(null);
  const [predictiveDetailAlert, setPredictiveDetailAlert] = React.useState<ApiAlert | null>(null);

  // Map alerts to display format
  let displayAlerts = alerts.map((alert) => {
    const locationName = formatLocationName(alert.locationId, locations);
    return {
      raw: alert,
      id: alert.alertId,
      sensorId: alert.sensorId ?? null,
      locationId: alert.locationId,
      title: `Nồng độ ${alert.metricType} ${
        alert.severity === 'CRITICAL' ? 'nghiêm trọng' : 'cao'
      } tại ${locationName}`,
      location: locationName,
      time: new Date(alert.createdAt).toLocaleString('vi-VN'),
      severity: (alert.severity || 'LOW').toLowerCase(),
      type: (alert.alertType || 'THRESHOLD').toLowerCase(),
      status: (alert.status || 'OPEN').toLowerCase(),
      metric: alert.metricType,
      value: alert.value,
      threshold: formatThreshold(alert),
    };
  });

  if (severityFilter !== 'all') {
    displayAlerts = displayAlerts.filter((a) => a.severity === severityFilter);
  }
  if (typeFilter !== 'all') {
    displayAlerts = displayAlerts.filter((a) => a.type === typeFilter);
  }

  const handleAcknowledge = async (alertId: string) => {
    setBusyId(alertId);
    try {
      await acknowledgeAlert(alertId);
    } finally {
      setBusyId(null);
    }
  };

  const handleResolve = async (alertId: string) => {
    setBusyId(alertId);
    try {
      await resolveAlert(alertId);
    } finally {
      setBusyId(null);
    }
  };

  const handleLocate = (sensorId: string | null, locationId: string) => {
    if (!onFocusOnMap) return;
    // Prefer the sensor coordinates (precise pin) if we have them.
    if (sensorId) {
      const sensor = sensors.find((s) => s.sensorId === sensorId);
      if (sensor && sensor.latitude != null && sensor.longitude != null) {
        // Pass sensorId so MapView opens the detail panel for THIS sensor.
        onFocusOnMap({
          lat: sensor.latitude,
          lng: sensor.longitude,
          zoom: 17,
          sensorId,
        });
        return;
      }
    }
    // Fall back to the location's center coordinates if available.
    const loc = locations.find((l) => l.locationId === locationId);
    if (loc && loc.centerLat != null && loc.centerLng != null) {
      onFocusOnMap({
        lat: loc.centerLat,
        lng: loc.centerLng,
        zoom: loc.type === 'Ward' ? 15 : 13,
      });
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500/10 text-red-400 border-red-500';
      case 'high':
        return 'bg-orange-500/10 text-orange-400 border-orange-500';
      case 'medium':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500';
      case 'low':
        return 'bg-green-500/10 text-green-400 border-green-500';
      default:
        return 'bg-gray-500/10 text-gray-400 border-gray-500';
    }
  };

  const getSeverityText = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'Nghiêm Trọng';
      case 'high':
        return 'Cao';
      case 'medium':
        return 'Trung Bình';
      case 'low':
        return 'Thấp';
      default:
        return 'Không Rõ';
    }
  };

  const getTypeText = (type: string) => {
    switch (type) {
      case 'threshold':
        return 'Ngưỡng';
      case 'predictive':
        return 'Dự Đoán';
      case 'anomaly':
        return 'Bất Thường';
      case 'cluster':
        return 'Cụm';
      default:
        return 'Khác';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'open':
        return 'CHƯA XỬ LÝ';
      case 'acknowledged':
        return 'ĐÃ XÁC NHẬN';
      case 'resolved':
        return 'ĐÃ GIẢI QUYẾT';
      default:
        return status.toUpperCase();
    }
  };

  // Distinct counts (no overlap)
  const severityCounts = {
    critical: displayAlerts.filter((a) => a.severity === 'critical').length,
    high: displayAlerts.filter((a) => a.severity === 'high').length,
    medium: displayAlerts.filter((a) => a.severity === 'medium').length,
    low: displayAlerts.filter((a) => a.severity === 'low').length,
  };

  const openCount = displayAlerts.filter((a) => a.status === 'open').length;

  return (
    <div className="alerts-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Cảnh Báo</h1>
          <p className="view-subtitle">
            {openCount} chưa xử lý / {displayAlerts.length} tổng
          </p>
        </div>
        <div className="filter-controls">
          <select
            className="filter-btn"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="all">Tất Cả Mức Độ</option>
            <option value="critical">Nghiêm Trọng</option>
            <option value="high">Cao</option>
            <option value="medium">Trung Bình</option>
            <option value="low">Thấp</option>
          </select>
          <select
            className="filter-btn"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="all">Tất Cả Loại</option>
            <option value="threshold">Ngưỡng</option>
            <option value="predictive">Dự Đoán</option>
            <option value="anomaly">Bất Thường</option>
            <option value="cluster">Cụm</option>
          </select>
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-box">
          <span className="stat-label">Nghiêm Trọng</span>
          <span className="stat-number text-red-400">{severityCounts.critical}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Cao</span>
          <span className="stat-number text-orange-400">{severityCounts.high}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Trung Bình</span>
          <span className="stat-number text-yellow-400">{severityCounts.medium}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Thấp</span>
          <span className="stat-number text-green-400">{severityCounts.low}</span>
        </div>
      </div>

      <div className="alerts-list">
        {displayAlerts.length > 0 ? (
          displayAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-card ${getSeverityColor(alert.severity)}`}
              style={alert.status !== 'open' ? { opacity: 0.7 } : undefined}
            >
              <div className="alert-header">
                <div className="alert-badges">
                  <span className={`severity-badge ${getSeverityColor(alert.severity)}`}>
                    {getSeverityText(alert.severity)}
                  </span>
                  <span className="type-badge">{getTypeText(alert.type)}</span>
                  <span
                    className="type-badge"
                    style={{
                      color:
                        alert.status === 'resolved'
                          ? '#22c55e'
                          : alert.status === 'acknowledged'
                          ? '#3b82f6'
                          : '#f87171',
                    }}
                  >
                    {getStatusText(alert.status)}
                  </span>
                </div>
                <div className="alert-actions">
                  {alert.type === 'predictive' && (
                    <button
                      className="alert-action-btn predictive-detail-btn"
                      onClick={() => setPredictiveDetailAlert(alert.raw)}
                      title="Xem chi tiết phân tích dự đoán"
                    >
                      <Eye className="w-4 h-4" />
                      <span>Xem Chi Tiết</span>
                    </button>
                  )}
                  <button
                    className="alert-action-btn"
                    onClick={() => handleLocate(alert.sensorId, alert.locationId)}
                  >
                    <MapPin className="w-4 h-4" />
                    <span>Định Vị</span>
                  </button>
                  {alert.status === 'open' && (
                    <button
                      className="alert-action-btn primary"
                      onClick={() => handleAcknowledge(alert.id)}
                      disabled={busyId === alert.id}
                    >
                      <Check className="w-4 h-4" />
                      <span>{busyId === alert.id ? 'Đang xử lý…' : 'Xác Nhận'}</span>
                    </button>
                  )}
                  {alert.status === 'acknowledged' && (
                    <button
                      className="alert-action-btn primary"
                      onClick={() => handleResolve(alert.id)}
                      disabled={busyId === alert.id}
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>{busyId === alert.id ? 'Đang xử lý…' : 'Giải Quyết'}</span>
                    </button>
                  )}
                </div>
              </div>

              <h3 className="alert-title">{alert.title}</h3>

              <div className="alert-details">
                <div className="alert-detail-item">
                  <MapPin className="w-4 h-4 text-gray-400" />
                  <span>{alert.location}</span>
                </div>
                <div className="alert-detail-item">
                  <span className="text-gray-400">⏰</span>
                  <span>{alert.time}</span>
                </div>
                <div className="alert-detail-item">
                  <span className="text-gray-400">{alert.metric}:</span>
                  <span className="font-semibold">{alert.value.toFixed(1)}</span>
                  <span className="text-gray-400">(ngưỡng: {alert.threshold})</span>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="alert-card">
            <p className="text-gray-400">Không có cảnh báo nào</p>
          </div>
        )}
      </div>

      {predictiveDetailAlert && (
        <PredictiveDetailModal
          alert={predictiveDetailAlert}
          onClose={() => setPredictiveDetailAlert(null)}
        />
      )}
    </div>
  );
};

export default AlertsView;
