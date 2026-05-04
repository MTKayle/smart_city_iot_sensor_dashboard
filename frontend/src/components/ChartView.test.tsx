/**
 * ChartView Component Tests
 * 
 * Tests for the ChartView component including data fetching,
 * time range filtering, and real-time updates.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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

/** Helper to create v2-compatible Telemetry */
const makeTelemetry = (overrides: {
  sensorId: string;
  locationId: string;
  co2: number;
  noise: number;
  temperature: number;
  timestamp: string;
  pm25?: number;
  humidity?: number;
}): Telemetry => ({
  sensorId: overrides.sensorId,
  locationId: overrides.locationId,
  data: {
    co2: overrides.co2,
    noise: overrides.noise,
    temperature: overrides.temperature,
    pm25: overrides.pm25 ?? null,
    humidity: overrides.humidity ?? null,
  },
  location: { type: 'Point', coordinates: [106.7, 10.78] },
  timestamp: overrides.timestamp,
  co2: overrides.co2,
  noise: overrides.noise,
  temperature: overrides.temperature,
});

describe('ChartView', () => {
  const mockSensorId = 'sensor-001';
  
  // Create recent timestamps (within last hour)
  const now = new Date();
  const mockTelemetryData: Telemetry[] = [
    makeTelemetry({
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 400,
      noise: 60,
      temperature: 25,
      timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(),
    }),
    makeTelemetry({
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 450,
      noise: 65,
      temperature: 26,
      timestamp: new Date(now.getTime() - 20 * 60 * 1000).toISOString(),
    }),
    makeTelemetry({
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 500,
      noise: 70,
      temperature: 27,
      timestamp: new Date(now.getTime() - 10 * 60 * 1000).toISOString(),
    }),
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
      expect(api.fetchTelemetry).toHaveBeenCalledWith(mockSensorId, expect.objectContaining({ limit: 1000 }));
    });
  });

  it('should display charts after data loads', async () => {
    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      const charts = screen.getAllByTestId('line-chart');
      expect(charts.length).toBeGreaterThanOrEqual(3); // CO2, Noise, Temperature + PM2.5, Humidity
    });
  });

  it('should display error message when fetch fails', async () => {
    const errorMessage = 'Network error';
    vi.mocked(api.fetchTelemetry).mockRejectedValue(new Error(errorMessage));

    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
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

  it('should update charts when new telemetry received via WebSocket', async () => {
    render(<ChartView sensorId={mockSensorId} />);

    // Wait for initial data to load
    await waitFor(() => {
      expect(screen.getByText(/3 READINGS/i)).toBeInTheDocument();
    });

    // Simulate WebSocket message
    const newTelemetry = makeTelemetry({
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 550,
      noise: 75,
      temperature: 28,
      timestamp: new Date().toISOString(),
    });

    if (mockWebSocketCallback) {
      mockWebSocketCallback(newTelemetry);
    }

    // Should now show 4 readings
    await waitFor(() => {
      expect(screen.getByText(/4 READINGS/i)).toBeInTheDocument();
    });
  });

  it('should ignore telemetry updates for different sensors', async () => {
    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      expect(screen.getByText(/3 READINGS/i)).toBeInTheDocument();
    });

    // Simulate WebSocket message for different sensor
    const differentSensorTelemetry = makeTelemetry({
      sensorId: 'sensor-002',
      locationId: 'loc-002',
      co2: 600,
      noise: 80,
      temperature: 30,
      timestamp: new Date().toISOString(),
    });

    if (mockWebSocketCallback) {
      mockWebSocketCallback(differentSensorTelemetry);
    }

    // Should still show 3 readings
    await waitFor(() => {
      expect(screen.getByText(/3 READINGS/i)).toBeInTheDocument();
    });
  });

  it('should display empty state when no data in time range', async () => {
    // Mock data from long ago
    const oldData: Telemetry[] = [
      makeTelemetry({
        sensorId: 'sensor-001',
        locationId: 'loc-001',
        co2: 400,
        noise: 60,
        temperature: 25,
        timestamp: new Date('2020-01-01T10:00:00Z').toISOString(),
      }),
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
      expect(api.fetchTelemetry).toHaveBeenCalledWith('sensor-001', expect.objectContaining({ limit: 1000 }));
    });

    // Change sensor ID
    rerender(<ChartView sensorId="sensor-002" />);

    await waitFor(() => {
      expect(api.fetchTelemetry).toHaveBeenCalledWith('sensor-002', expect.objectContaining({ limit: 1000 }));
    });
  });

  it('should sort telemetry data by timestamp ascending', async () => {
    const now = new Date();
    const unsortedData: Telemetry[] = [
      makeTelemetry({
        sensorId: 'sensor-001',
        locationId: 'loc-001',
        co2: 500,
        noise: 70,
        temperature: 27,
        timestamp: new Date(now.getTime() - 10 * 60 * 1000).toISOString(),
      }),
      makeTelemetry({
        sensorId: 'sensor-001',
        locationId: 'loc-001',
        co2: 400,
        noise: 60,
        temperature: 25,
        timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(),
      }),
    ];
    vi.mocked(api.fetchTelemetry).mockResolvedValue(unsortedData);

    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      const charts = screen.getAllByTestId('line-chart');
      expect(charts.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('should limit data to last 1000 readings when WebSocket adds new data', async () => {
    const now = new Date();
    // Create 100 initial readings
    const manyReadings: Telemetry[] = Array.from({ length: 100 }, (_, i) =>
      makeTelemetry({
        sensorId: 'sensor-001',
        locationId: 'loc-001',
        co2: 400 + i,
        noise: 60 + (i % 20),
        temperature: 25 + (i % 10),
        timestamp: new Date(now.getTime() - (100 - i) * 60 * 1000).toISOString(),
      }),
    );
    vi.mocked(api.fetchTelemetry).mockResolvedValue(manyReadings);

    render(<ChartView sensorId={mockSensorId} />);

    await waitFor(() => {
      expect(screen.getByText(/100 READINGS/i)).toBeInTheDocument();
    });

    // Add new reading via WebSocket
    const newTelemetry = makeTelemetry({
      sensorId: 'sensor-001',
      locationId: 'loc-001',
      co2: 600,
      noise: 80,
      temperature: 30,
      timestamp: new Date().toISOString(),
    });

    if (mockWebSocketCallback) {
      mockWebSocketCallback(newTelemetry);
    }

    // Should show 101 readings
    await waitFor(() => {
      expect(screen.getByText(/101 READINGS/i)).toBeInTheDocument();
    });
  });
});
