/**
 * ChartView Component Tests
 * 
 * Tests for the ChartView component including data fetching,
 * time range filtering, and real-time updates.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChartView } from './ChartView';
import * as api from '../services/api';
import * as useWebSocketModule from '../hooks/useWebSocket';
import type { Telemetry } from '../types';

// Mock the API service
vi.mock('../services/api');

// Mock the useWebSocket hook
vi.mock('../hooks/useWebSocket');

// Mock Chart.js to avoid canvas rendering issues in tests
vi.mock('react-chartjs-2', () => ({
  Line: ({ data, options }: any) => (
    <div data-testid="line-chart">
      <div data-testid="chart-labels">{JSON.stringify(data.labels)}</div>
      <div data-testid="chart-data">{JSON.stringify(data.datasets)}</div>
      <div data-testid="chart-options">{JSON.stringify(options)}</div>
    </div>
  ),
}));

describe('ChartView', () => {
  const mockSensorId = 'sensor-001';
  
  // Create recent timestamps (within last hour)
  const now = new Date();
  const mockTelemetryData: Telemetry[] = [
    {
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 400,
      noise: 60,
      temperature: 25,
      timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(), // 30 min ago
    },
    {
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 450,
      noise: 65,
      temperature: 26,
      timestamp: new Date(now.getTime() - 20 * 60 * 1000).toISOString(), // 20 min ago
    },
    {
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 500,
      noise: 70,
      temperature: 27,
      timestamp: new Date(now.getTime() - 10 * 60 * 1000).toISOString(), // 10 min ago
    },
  ];

  let mockWebSocketCallback: ((data: Telemetry) => void) | undefined;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();

    // Mock fetchTelemetry to return test data
    vi.mocked(api.fetchTelemetry).mockResolvedValue([...mockTelemetryData]);

    // Mock useWebSocket to capture the callback
    vi.mocked(useWebSocketModule.useWebSocket).mockImplementation((_url, callbacks) => {
      mockWebSocketCallback = callbacks?.onTelemetry;
      return 'connected';
    });
  });

  afterEach(() => {
    mockWebSocketCallback = undefined;
  });

  it('should render loading state initially', () => {
    render(<ChartView sensorId={mockSensorId} />);
    expect(screen.getByText(/loading telemetry data/i)).toBeInTheDocument();
  });

  it('should fetch telemetry data on mount', async () => {
    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      expect(api.fetchTelemetry).toHaveBeenCalledWith(mockSensorId, { limit: 100 });
    });
  });

  it('should display charts after data loads', async () => {
    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      const charts = screen.getAllByTestId('line-chart');
      expect(charts).toHaveLength(3); // CO2, Noise, Temperature
    });
  });

  it('should display error message when fetch fails', async () => {
    const errorMessage = 'Network error';
    vi.mocked(api.fetchTelemetry).mockRejectedValue(new Error(errorMessage));

    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
      expect(screen.getByText(new RegExp(errorMessage, 'i'))).toBeInTheDocument();
    });
  });

  it('should display time range selector buttons', async () => {
    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '1h' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '6h' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '24h' })).toBeInTheDocument();
    });
  });

  it('should default to 24h time range', async () => {
    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      const button24h = screen.getByRole('button', { name: '24h' });
      expect(button24h).toHaveStyle({ backgroundColor: 'rgb(59, 130, 246)' });
    });
  });

  it('should change time range when button clicked', async () => {
    const user = userEvent.setup();
    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '1h' })).toBeInTheDocument();
    });

    const button1h = screen.getByRole('button', { name: '1h' });
    await user.click(button1h);

    expect(button1h).toHaveStyle({ backgroundColor: 'rgb(59, 130, 246)' });
  });

  it('should display data info with reading count', async () => {
    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      expect(screen.getByText(/showing 3 readings/i)).toBeInTheDocument();
      expect(screen.getByText(new RegExp(mockSensorId, 'i'))).toBeInTheDocument();
    });
  });

  it('should update charts when new telemetry received via WebSocket', async () => {
    render(<ChartView sensorId={mockSensorId} />);

    // Wait for initial data to load
    await waitFor(() => {
      expect(screen.getByText(/showing 3 readings/i)).toBeInTheDocument();
    });

    // Simulate WebSocket message
    const newTelemetry: Telemetry = {
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 550,
      noise: 75,
      temperature: 28,
      timestamp: new Date().toISOString(), // Now
    };

    if (mockWebSocketCallback) {
      mockWebSocketCallback(newTelemetry);
    }

    // Should now show 4 readings
    await waitFor(() => {
      expect(screen.getByText(/showing 4 readings/i)).toBeInTheDocument();
    });
  });

  it('should ignore telemetry updates for different sensors', async () => {
    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      expect(screen.getByText(/showing 3 readings/i)).toBeInTheDocument();
    });

    // Simulate WebSocket message for different sensor
    const differentSensorTelemetry: Telemetry = {
      sensorId: 'sensor-002',
      locationId: 'loc-002',
      co2: 600,
      noise: 80,
      temperature: 30,
      timestamp: new Date().toISOString(),
    };

    if (mockWebSocketCallback) {
      mockWebSocketCallback(differentSensorTelemetry);
    }

    // Should still show 3 readings
    await waitFor(() => {
      expect(screen.getByText(/showing 3 readings/i)).toBeInTheDocument();
    });
  });

  it('should display empty state when no data in time range', async () => {
    // Mock data from long ago
    const oldData: Telemetry[] = [
      {
        sensorId: 'sensor-001',
        locationId: 'loc-001',
        co2: 400,
        noise: 60,
        temperature: 25,
        timestamp: new Date('2020-01-01T10:00:00Z').toISOString(),
      },
    ];
    vi.mocked(api.fetchTelemetry).mockResolvedValue(oldData);

    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      expect(screen.getByText(/no telemetry data available/i)).toBeInTheDocument();
    });
  });

  it('should refetch data when sensorId changes', async () => {
    const { rerender } = render(<ChartView sensorId="sensor-001" />);

    await waitFor(() => {
      expect(api.fetchTelemetry).toHaveBeenCalledWith('sensor-001', { limit: 100 });
    });

    // Change sensor ID
    rerender(<ChartView sensorId="sensor-002" />);

    await waitFor(() => {
      expect(api.fetchTelemetry).toHaveBeenCalledWith('sensor-002', { limit: 100 });
    });
  });

  it('should sort telemetry data by timestamp ascending', async () => {
    const now = new Date();
    const unsortedData: Telemetry[] = [
      {
        sensorId: 'sensor-001',
        locationId: 'loc-001',
        co2: 500,
        noise: 70,
        temperature: 27,
        timestamp: new Date(now.getTime() - 10 * 60 * 1000).toISOString(), // 10 min ago
      },
      {
        sensorId: 'sensor-001',
        locationId: 'loc-001',
        co2: 400,
        noise: 60,
        temperature: 25,
        timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(), // 30 min ago
      },
    ];
    vi.mocked(api.fetchTelemetry).mockResolvedValue(unsortedData);

    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      const charts = screen.getAllByTestId('line-chart');
      expect(charts).toHaveLength(3);
    });

    // Verify data is sorted (earliest timestamp first)
    const chartData = screen.getAllByTestId('chart-data')[0];
    const datasets = JSON.parse(chartData.textContent || '[]');
    expect(datasets[0].data).toEqual([400, 500]); // CO2 values in chronological order
  });

  it('should limit data to last 100 readings when WebSocket adds new data', async () => {
    const now = new Date();
    // Create 100 initial readings
    const manyReadings: Telemetry[] = Array.from({ length: 100 }, (_, i) => ({
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 400 + i,
      noise: 60 + (i % 20),
      temperature: 25 + (i % 10),
      timestamp: new Date(now.getTime() - (100 - i) * 60 * 1000).toISOString(), // Spread over last 100 minutes
    }));
    vi.mocked(api.fetchTelemetry).mockResolvedValue(manyReadings);

    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      expect(screen.getByText(/showing 100 readings/i)).toBeInTheDocument();
    });

    // Add new reading via WebSocket
    const newTelemetry: Telemetry = {
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 600,
      noise: 80,
      temperature: 30,
      timestamp: new Date().toISOString(),
    };

    if (mockWebSocketCallback) {
      mockWebSocketCallback(newTelemetry);
    }

    // Should still show 100 readings (oldest dropped)
    await waitFor(() => {
      expect(screen.getByText(/showing 100 readings/i)).toBeInTheDocument();
    });
  });
});
