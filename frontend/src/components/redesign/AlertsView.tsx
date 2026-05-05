import React from 'react';
import { MapPin, Check } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';

const AlertsView: React.FC = () => {
  const { alerts } = useAppContext();
  const [severityFilter, setSeverityFilter] = React.useState<string>('all');
  const [typeFilter, setTypeFilter] = React.useState<string>('all');

  // Map alerts to display format
  let displayAlerts = alerts.map(alert => ({
    id: alert.alertId,
    title: `Nồng độ ${alert.metricType} ${alert.severity === 'CRITICAL' ? 'nghiêm trọng' : 'cao'} tại ${alert.locationId}`,
    location: alert.locationId,
    time: new Date(alert.createdAt).toLocaleString('vi-VN'),
    severity: alert.severity.toLowerCase(),
    type: alert.alertType.toLowerCase(),
    metric: alert.metricType,
    value: alert.value,
    threshold: alert.metricType === 'PM2.5' ? 50 : alert.metricType === 'CO2' ? 1000 : 90,
  }));

  // Apply filters
  if (severityFilter !== 'all') {
    displayAlerts = displayAlerts.filter(a => a.severity === severityFilter);
  }
  if (typeFilter !== 'all') {
    displayAlerts = displayAlerts.filter(a => a.type === typeFilter);
  }

  const handleAcknowledge = (alertId: string) => {
    console.log('Acknowledging alert:', alertId);
    // TODO: Call API to acknowledge alert
  };

  const handleLocate = (location: string) => {
    console.log('Locating:', location);
    // TODO: Navigate to map view and center on location
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
      default:
        return 'Khác';
    }
  };

  const severityCounts = {
    critical: displayAlerts.filter(a => a.severity === 'critical').length,
    high: displayAlerts.filter(a => a.severity === 'high').length,
    medium: displayAlerts.filter(a => a.severity === 'medium' || a.severity === 'low').length,
    low: 0,
  };

  return (
    <div className="alerts-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Cảnh Báo</h1>
          <p className="view-subtitle">{displayAlerts.length} cảnh báo chưa xác nhận</p>
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

      {/* Thống kê mức độ */}
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

      {/* Danh sách cảnh báo */}
      <div className="alerts-list">
        {displayAlerts.length > 0 ? (
          displayAlerts.map((alert) => (
            <div key={alert.id} className={`alert-card ${getSeverityColor(alert.severity)}`}>
              <div className="alert-header">
                <div className="alert-badges">
                  <span className={`severity-badge ${getSeverityColor(alert.severity)}`}>
                    {getSeverityText(alert.severity)}
                  </span>
                  <span className="type-badge">{getTypeText(alert.type)}</span>
                </div>
                <div className="alert-actions">
                  <button 
                    className="alert-action-btn"
                    onClick={() => handleLocate(alert.location)}
                  >
                    <MapPin className="w-4 h-4" />
                    <span>Định Vị</span>
                  </button>
                  <button 
                    className="alert-action-btn primary"
                    onClick={() => handleAcknowledge(alert.id)}
                  >
                    <Check className="w-4 h-4" />
                    <span>Xác Nhận</span>
                  </button>
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
    </div>
  );
};

export default AlertsView;
