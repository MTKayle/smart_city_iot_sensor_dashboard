import React, { useState } from 'react';
import { Search, Bell, User, Circle } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';

const TopNavbar: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const { alerts, connectionStatus } = useAppContext();

  // Count of alerts that still need attention.
  const openAlertCount = alerts.filter(
    (a) => (a.status || 'OPEN') === 'OPEN',
  ).length;

  const isLive = connectionStatus === 'connected';
  const statusLabel =
    connectionStatus === 'connected'
      ? 'TRỰC TIẾP'
      : connectionStatus === 'connecting'
      ? 'ĐANG KẾT NỐI'
      : connectionStatus === 'error'
      ? 'LỖI KẾT NỐI'
      : 'MẤT KẾT NỐI';

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

        <button className="notification-btn">
          <Bell className="w-5 h-5" />
          {openAlertCount > 0 && (
            <span className="notification-badge">
              {openAlertCount > 99 ? '99+' : openAlertCount}
            </span>
          )}
        </button>

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
