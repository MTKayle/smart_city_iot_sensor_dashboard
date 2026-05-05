/**
 * App Component Tests
 * 
 * Basic tests to verify the App component renders correctly
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';
import * as apiModule from './services/api';
import * as useWebSocketModule from './hooks/useWebSocket';

// Mock the API module
vi.mock('./services/api');

// Mock the useWebSocket hook
vi.mock('./hooks/useWebSocket');

// Mock the child components
vi.mock('./components', () => ({
  MapView: () => <div data-testid="map-view">MapView</div>,
  ChartView: () => <div data-testid="chart-view">ChartView</div>,
  Leaderboard: () => <div data-testid="leaderboard">Leaderboard</div>,
  AlertsPanel: () => <div data-testid="alerts-panel">AlertsPanel</div>,
}));

describe('App Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();

    // Mock API responses
    vi.mocked(apiModule.fetchSensors).mockResolvedValue([
      {
        sensorId: 'sensor_001',
        locationId: 'ward_001',
        sensorType: 'CO2',
        registeredAt: '2024-01-01T00:00:00Z',
      },
    ]);

    vi.mocked(apiModule.fetchLocations).mockResolvedValue([
      {
        locationId: 'ward_001',
        name: 'Ward 1',
        parentId: 'district_001',
        type: 'Ward',
      },
    ]);

    // Mock WebSocket hook
    vi.mocked(useWebSocketModule.useWebSocket).mockReturnValue('connected');
  });

  it('renders loading state initially', () => {
    render(<App />);
    expect(screen.getByText('Loading Smart City Dashboard...')).toBeInTheDocument();
  });

  it('renders the app title', async () => {
    render(<App />);
    
    // Wait for loading to complete
    await screen.findByText('Smart City IoT Sensor Dashboard');
    
    expect(screen.getByText('Smart City IoT Sensor Dashboard')).toBeInTheDocument();
  });

  it('renders connection status indicator', async () => {
    render(<App />);
    
    // Wait for loading to complete
    await screen.findByText('Smart City IoT Sensor Dashboard');
    
    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('renders all dashboard components', async () => {
    render(<App />);
    
    // Wait for loading to complete
    await screen.findByText('Smart City IoT Sensor Dashboard');
    
    expect(screen.getByTestId('map-view')).toBeInTheDocument();
    expect(screen.getByTestId('chart-view')).toBeInTheDocument();
    expect(screen.getByTestId('leaderboard')).toBeInTheDocument();
    expect(screen.getByTestId('alerts-panel')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    // Mock API error
    vi.mocked(apiModule.fetchSensors).mockRejectedValue(new Error('API Error'));
    
    render(<App />);
    
    // Wait for error state
    await screen.findByText('Error Loading Dashboard');
    
    expect(screen.getByText('API Error')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });
});
