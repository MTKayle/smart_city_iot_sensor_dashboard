import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Search, Bell, User, Circle, MapPin, ArrowRight } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import { formatLocationName } from '../../utils/location';
import type { ViewType, MapFocusTarget } from './types';

interface TopNavbarProps {
  onNavigate?: (view: ViewType) => void;
  onFocusOnMap?: (target: MapFocusTarget) => void;
}

const SEVERITY_PRIORITY: Record<string, number> = {
  CRITICAL: 0,
  HIGH:     1,
  MEDIUM:   2,
  LOW:      3,
};

const TopNavbar: React.FC<TopNavbarProps> = ({ onNavigate, onFocusOnMap }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [hasNewAlert, setHasNewAlert] = useState(false);

  const dropdownRef = useRef<HTMLDivElement>(null);
  const lastCountRef = useRef<number>(0);

  const { alerts, sensors, locations, connectionStatus } = useAppContext();

  // ─── Open / unacknowledged alerts only — those needing attention ───
  const openAlerts = useMemo(
    () => alerts.filter((a) => (a.status || 'OPEN') === 'OPEN'),
    [alerts],
  );

  // Top 6 alerts by severity then recency for the dropdown.
  const dropdownAlerts = useMemo(() => {
    return [...openAlerts]
      .sort((a, b) => {
        const sa = SEVERITY_PRIORITY[a.severity] ?? 9;
        const sb = SEVERITY_PRIORITY[b.severity] ?? 9;
        if (sa !== sb) return sa - sb;
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      })
      .slice(0, 6);
  }, [openAlerts]);

  const criticalCount = openAlerts.filter((a) => a.severity === 'CRITICAL').length;
  const highCount = openAlerts.filter((a) => a.severity === 'HIGH').length;

  // Pulse the badge whenever the count grows (= a brand-new alert arrived).
  useEffect(() => {
    const prev = lastCountRef.current;
    if (openAlerts.length > prev) {
      setHasNewAlert(true);
      const timer = setTimeout(() => setHasNewAlert(false), 4000);
      lastCountRef.current = openAlerts.length;
      return () => clearTimeout(timer);
    }
    lastCountRef.current = openAlerts.length;
  }, [openAlerts.length]);

  // Close dropdown on outside click.
  useEffect(() => {
    if (!dropdownOpen) return;
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [dropdownOpen]);

  const isLive = connectionStatus === 'connected';
  const statusLabel =
    connectionStatus === 'connected'  ? 'TRỰC TIẾP'
    : connectionStatus === 'connecting' ? 'ĐANG KẾT NỐI'
    : connectionStatus === 'error'    ? 'LỖI KẾT NỐI'
    : 'MẤT KẾT NỐI';

  const goToAlerts = () => {
    setDropdownOpen(false);
    onNavigate?.('alerts');
  };

  const locateAlert = (sensorId: string | null | undefined, locationId: string) => {
    if (!onFocusOnMap) {
      goToAlerts();
      return;
    }
    if (sensorId) {
      const s = sensors.find((x) => x.sensorId === sensorId);
      if (s && s.latitude != null && s.longitude != null) {
        onFocusOnMap({
          lat: s.latitude,
          lng: s.longitude,
          zoom: 17,
          sensorId,
        });
        setDropdownOpen(false);
        return;
      }
    }
    const loc = locations.find((l) => l.locationId === locationId);
    if (loc && loc.centerLat != null && loc.centerLng != null) {
      onFocusOnMap({
        lat: loc.centerLat,
        lng: loc.centerLng,
        zoom: loc.type === 'Ward' ? 15 : 13,
      });
      setDropdownOpen(false);
    }
  };

  const severityClass = (sev: string): string => {
    switch (sev) {
      case 'CRITICAL': return 'critical';
      case 'HIGH':     return 'high';
      case 'MEDIUM':   return 'medium';
      case 'LOW':      return 'low';
      default:         return 'low';
    }
  };

  const severityLabel = (sev: string): string => {
    switch (sev) {
      case 'CRITICAL': return 'Nghiêm trọng';
      case 'HIGH':     return 'Cao';
      case 'MEDIUM':   return 'TB';
      case 'LOW':      return 'Thấp';
      default:         return sev;
    }
  };

  // Time-ago formatter — keeps the dropdown compact.
  const timeAgo = (iso: string): string => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'vừa xong';
    if (mins < 60) return `${mins} phút trước`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} giờ trước`;
    const days = Math.floor(hrs / 24);
    return `${days} ngày trước`;
  };

  return (
    <div className="top-navbar">
      <div className="search-container">
        <Search className="search-icon" />
        <input
          type="text"
          placeholder="Tìm kiếm cảm biến, vị trí..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="navbar-actions">
        <div className={`status-indicator ${isLive ? 'live' : 'delay'}`}>
          <Circle className="status-dot" />
          <span className="status-text">{statusLabel}</span>
        </div>

        <div className="notification-wrap" ref={dropdownRef}>
          <button
            className={`notification-btn ${hasNewAlert ? 'has-new' : ''}`}
            onClick={() => setDropdownOpen((v) => !v)}
            title={openAlerts.length > 0
              ? `${openAlerts.length} cảnh báo chưa xử lý`
              : 'Không có cảnh báo mới'}
            aria-haspopup="true"
            aria-expanded={dropdownOpen}
          >
            <Bell className="w-5 h-5" />
            {openAlerts.length > 0 && (
              <span className={`notification-badge ${hasNewAlert ? 'pulse' : ''}`}>
                {openAlerts.length > 99 ? '99+' : openAlerts.length}
              </span>
            )}
          </button>

          {dropdownOpen && (
            <div className="notification-dropdown" role="menu">
              <div className="notification-dropdown-header">
                <div>
                  <div className="notification-dropdown-title">Cảnh Báo</div>
                  <div className="notification-dropdown-subtitle">
                    {openAlerts.length > 0
                      ? `${openAlerts.length} chưa xử lý · ${criticalCount} nghiêm trọng · ${highCount} cao`
                      : 'Không có cảnh báo nào đang mở'}
                  </div>
                </div>
                <button
                  className="notification-view-all"
                  onClick={goToAlerts}
                  title="Xem tất cả cảnh báo"
                >
                  Xem tất cả
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>

              <div className="notification-list">
                {dropdownAlerts.length === 0 ? (
                  <div className="notification-empty">
                    Mọi thứ đang ổn — không có cảnh báo mở.
                  </div>
                ) : (
                  dropdownAlerts.map((alert) => (
                    <div
                      key={alert.alertId}
                      className={`notification-item severity-${severityClass(alert.severity)}`}
                      onClick={goToAlerts}
                    >
                      <div className="notification-item-row">
                        <span className={`notification-pill severity-${severityClass(alert.severity)}`}>
                          {severityLabel(alert.severity)}
                        </span>
                        <span className="notification-metric">{alert.metricType}</span>
                        <span className="notification-time">{timeAgo(alert.createdAt)}</span>
                      </div>
                      <div className="notification-title">
                        {alert.metricType} ={' '}
                        <strong>{alert.value.toFixed(1)}</strong>
                        {alert.threshold !== null && alert.threshold !== undefined && (
                          <span className="notification-threshold"> (ngưỡng {alert.threshold.toFixed(0)})</span>
                        )}
                      </div>
                      <div className="notification-location">
                        <MapPin className="w-3 h-3" />
                        {formatLocationName(alert.locationId, locations)}
                        <button
                          className="notification-locate-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            locateAlert(alert.sensorId, alert.locationId);
                          }}
                          title="Xem trên bản đồ"
                        >
                          Định vị
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {openAlerts.length > dropdownAlerts.length && (
                <div className="notification-dropdown-footer">
                  Còn {openAlerts.length - dropdownAlerts.length} cảnh báo khác —{' '}
                  <button className="notification-link" onClick={goToAlerts}>
                    xem trang Cảnh Báo
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        <button className="user-profile">
          <div className="user-avatar">
            <User className="w-5 h-5" />
          </div>
          <span className="user-name">Người Dùng</span>
        </button>
      </div>
    </div>
  );
};

export default TopNavbar;
