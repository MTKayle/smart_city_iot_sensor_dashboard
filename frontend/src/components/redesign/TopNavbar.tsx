import React, { useState } from 'react';
import { Search, Bell, User, Circle } from 'lucide-react';

const TopNavbar: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [notificationCount] = useState(9);
  const isLive = true;

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
          <span className="status-text">{isLive ? 'TRỰC TIẾP' : 'TRỄ'}</span>
        </div>

        <button className="notification-btn">
          <Bell className="w-5 h-5" />
          {notificationCount > 0 && (
            <span className="notification-badge">{notificationCount}</span>
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
