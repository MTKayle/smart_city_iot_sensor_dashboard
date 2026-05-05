import React from 'react';
import { 
  LayoutDashboard, 
  Map, 
  Radio, 
  Layers, 
  AlertTriangle, 
  BarChart3, 
  Settings,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import type { ViewType } from './types';

interface SidebarProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange, collapsed, onToggleCollapse }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Tổng Quan', icon: LayoutDashboard },
    { id: 'map', label: 'Bản Đồ', icon: Map },
    { id: 'sensors', label: 'Cảm Biến', icon: Radio },
    { id: 'clusters', label: 'Cụm Vùng', icon: Layers },
    { id: 'alerts', label: 'Cảnh Báo', icon: AlertTriangle },
    { id: 'analytics', label: 'Phân Tích', icon: BarChart3 },
    { id: 'settings', label: 'Cài Đặt', icon: Settings },
  ];

  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo-container">
          <div className="logo-icon">
            <Radio className="w-6 h-6" />
          </div>
          {!collapsed && (
            <div className="logo-text">
              <div className="logo-title">SmartCity</div>
              <div className="logo-subtitle">Nền tảng IoT</div>
            </div>
          )}
        </div>
        <button className="collapse-btn" onClick={onToggleCollapse}>
          {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onViewChange(item.id as ViewType)}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="nav-icon" />
              {!collapsed && <span className="nav-label">{item.label}</span>}
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default Sidebar;
