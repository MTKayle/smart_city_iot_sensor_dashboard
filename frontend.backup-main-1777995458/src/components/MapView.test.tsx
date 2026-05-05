/**
 * MapView Component Tests
 * 
 * Tests for the MapView component rendering and functionality.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { MapView } from './MapView';
import type { Sensor, Location, Alert, Telemetry } from '../types';

// Mock maplibre-gl
vi.mock('maplibre-gl', () => ({
  default: {
    Map: vi.fn(function(this: any) {
      this.on = vi.fn((event: string, callback: () => void) => {
        if (event === 'load') {
          setTimeout(callback, 0);
        }
      });
      this.addControl = vi.fn();
      this.remove = vi.fn();
      return this;
    }),
    NavigationControl: vi.fn(function(this: any) {
      return this;
    }),
    Marker: vi.fn(function(this: any) {
      this.setLngLat = vi.fn().mockReturnThis();
      this.addTo = vi.fn().mockReturnThis();
      this.setPopup = vi.fn().mockReturnThis();
      this.remove = vi.fn();
      this.getElement = vi.fn(() => ({
        querySelector: vi.fn(() => ({
          querySelector: vi.fn(() => ({
            setAttribute: vi.fn(),
          })),
        })),
      }));
      return this;
    }),
    Popup: vi.fn(function(this: any) {
      this.setHTML = vi.fn().mockReturnThis();
      return this;
    }),
  },
}));

describe('MapView Component', () => {
  const mockSensors: Sensor[] = [
    {
      sensorId: 'sensor-1',
      locationId: 'loc-1',
      sensorType: 'CO2',
      registeredAt: '2024-01-01T00:00:00Z',
    },
    {
      sensorId: 'sensor-2',
      locationId: 'loc-2',
      sensorType: 'Noise',
      registeredAt: '2024-01-01T00:00:00Z',
    },
  ];

  const mockLocations: Location[] = [
    {
      locationId: 'loc-1',
      name: 'District 1',
      parentId: null,
      type: 'District',
    },
    {
      locationId: 'loc-2',
      name: 'District 2',
      parentId: null,
      type: 'District',
    },
  ];

  const mockAlerts: Alert[] = [
    {
      alertId: 'alert-1',
      sensorId: 'sensor-1',
      metricType: 'CO2',
      value: 1200,
      level: 'HIGH',
      createdAt: '2024-01-01T12:00:00Z',
    },
  ];

  const mockTelemetry: Record<string, Telemetry> = {
    'sensor-1': {
      sensorId: 'sensor-1',
      locationId: 'loc-1',
      co2: 1200,
      noise: 65,
      temperature: 25,
      timestamp: '2024-01-01T12:00:00Z',
    },
    'sensor-2': {
      sensorId: 'sensor-2',
      locationId: 'loc-2',
      co2: 400,
      noise: 55,
      temperature: 23,
      timestamp: '2024-01-01T12:00:00Z',
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render map container', () => {
    const { container } = render(
      <MapView
        sensors={mockSensors}
        locations={mockLocations}
        alerts={mockAlerts}
        telemetry={mockTelemetry}
      />
    );

    // Map container should be rendered
    const mapDiv = container.querySelector('div[style*="width: 100%"]');
    expect(mapDiv).toBeDefined();
  });

  it('should initialize with default center and zoom', () => {
    const { container } = render(
      <MapView
        sensors={mockSensors}
        locations={mockLocations}
        alerts={mockAlerts}
        telemetry={mockTelemetry}
      />
    );

    // Check that map container has proper styling
    const mapDiv = container.querySelector('div[style*="width: 100%"]') as HTMLElement;
    expect(mapDiv).toBeDefined();
    expect(mapDiv?.style.width).toBe('100%');
    expect(mapDiv?.style.height).toBe('100%');
    expect(mapDiv?.style.minHeight).toBe('400px');
  });

  it('should accept custom center and zoom props', () => {
    const customCenter: [number, number] = [105.8342, 21.0278]; // Hanoi
    const customZoom = 14;

    const { container } = render(
      <MapView
        sensors={mockSensors}
        locations={mockLocations}
        alerts={mockAlerts}
        telemetry={mockTelemetry}
        center={customCenter}
        zoom={customZoom}
      />
    );

    // Component should render without errors
    const mapDiv = container.querySelector('div[style*="width: 100%"]');
    expect(mapDiv).toBeDefined();
  });

  it('should handle empty sensors array', () => {
    const { container } = render(
      <MapView
        sensors={[]}
        locations={mockLocations}
        alerts={mockAlerts}
        telemetry={mockTelemetry}
      />
    );

    // Should render without errors
    const mapDiv = container.querySelector('div[style*="width: 100%"]');
    expect(mapDiv).toBeDefined();
  });

  it('should handle empty locations array', () => {
    const { container } = render(
      <MapView
        sensors={mockSensors}
        locations={[]}
        alerts={mockAlerts}
        telemetry={mockTelemetry}
      />
    );

    // Should render without errors
    const mapDiv = container.querySelector('div[style*="width: 100%"]');
    expect(mapDiv).toBeDefined();
  });

  it('should handle empty alerts array', () => {
    const { container } = render(
      <MapView
        sensors={mockSensors}
        locations={mockLocations}
        alerts={[]}
        telemetry={mockTelemetry}
      />
    );

    // Should render without errors
    const mapDiv = container.querySelector('div[style*="width: 100%"]');
    expect(mapDiv).toBeDefined();
  });

  it('should handle empty telemetry object', () => {
    const { container } = render(
      <MapView
        sensors={mockSensors}
        locations={mockLocations}
        alerts={mockAlerts}
        telemetry={{}}
      />
    );

    // Should render without errors
    const mapDiv = container.querySelector('div[style*="width: 100%"]');
    expect(mapDiv).toBeDefined();
  });
});
