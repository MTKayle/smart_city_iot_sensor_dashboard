import React, { useState } from 'react';
import { AppProvider } from './context/AppContext';
import Sidebar from './components/redesign/Sidebar.tsx';
import TopNavbar from './components/redesign/TopNavbar.tsx';
import Dashboard from './components/redesign/Dashboard.tsx';
import MapView from './components/redesign/MapView.tsx';
import SensorsView from './components/redesign/SensorsView.tsx';
import ClustersView from './components/redesign/ClustersView.tsx';
import AlertsView from './components/redesign/AlertsView.tsx';
import AnalyticsView from './components/redesign/AnalyticsView.tsx';
import LeaderboardView from './components/redesign/LeaderboardView.tsx';
import SettingsView from './components/redesign/SettingsView.tsx';
import './styles/redesign.css';

import type { ViewType, MapFocusTarget } from './components/redesign/types';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('map');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mapFocusTarget, setMapFocusTarget] = useState<MapFocusTarget | null>(null);

  const focusMapOn = (target: MapFocusTarget) => {
    setMapFocusTarget(target);
    setCurrentView('map');
  };

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard onNavigate={setCurrentView} onFocusOnMap={focusMapOn} />;
      case 'map':
        return (
          <MapView
            focusTarget={mapFocusTarget}
            onFocusConsumed={() => setMapFocusTarget(null)}
          />
        );
      case 'sensors':
        return <SensorsView onFocusOnMap={focusMapOn} />;
      case 'clusters':
        return <ClustersView onFocusOnMap={focusMapOn} />;
      case 'alerts':
        return <AlertsView onFocusOnMap={focusMapOn} />;
      case 'analytics':
        return <AnalyticsView />;
      case 'leaderboard':
        return <LeaderboardView />;
      case 'settings':
        return <SettingsView />;
      default:
        return (
          <MapView
            focusTarget={mapFocusTarget}
            onFocusConsumed={() => setMapFocusTarget(null)}
          />
        );
    }
  };

  return (
    <AppProvider>
      <div className="app-container">
        <Sidebar
          currentView={currentView}
          onViewChange={setCurrentView}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
        <div className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
          <TopNavbar onNavigate={setCurrentView} onFocusOnMap={focusMapOn} />
          <div className="view-container">
            {renderView()}
          </div>
        </div>
      </div>
    </AppProvider>
  );
};

export default App;
