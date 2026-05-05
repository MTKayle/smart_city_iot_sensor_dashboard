/**
 * ChartView Component Usage Examples
 * 
 * This file demonstrates various ways to use the ChartView component
 * in different scenarios and configurations.
 */

import { ChartView } from './ChartView';

/**
 * Example 1: Basic Usage
 * 
 * Minimal configuration with just a sensor ID.
 * Uses default WebSocket URL.
 */
export function BasicChartViewExample() {
  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <h1>Sensor Telemetry Charts</h1>
      <ChartView sensorId="sensor-001" />
    </div>
  );
}

/**
 * Example 2: Custom WebSocket URL
 * 
 * Specify a custom WebSocket server URL for real-time updates.
 */
export function CustomWebSocketExample() {
  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <h1>Sensor Telemetry - Custom WebSocket</h1>
      <ChartView 
        sensorId="sensor-002" 
        wsUrl="ws://localhost:8000/ws"
      />
    </div>
  );
}

/**
 * Example 3: Multiple Sensors
 * 
 * Display charts for multiple sensors side by side.
 */
export function MultipleSensorsExample() {
  const sensors = ['sensor-001', 'sensor-002', 'sensor-003'];

  return (
    <div style={{ width: '100%', padding: '20px' }}>
      <h1>Multi-Sensor Dashboard</h1>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(600px, 1fr))',
        gap: '20px',
      }}>
        {sensors.map(sensorId => (
          <div key={sensorId} style={{ 
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: '16px',
          }}>
            <h2 style={{ marginTop: 0 }}>Sensor: {sensorId}</h2>
            <ChartView sensorId={sensorId} />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Example 4: Sensor Selector
 * 
 * Allow users to select which sensor to view.
 */
export function SensorSelectorExample() {
  const [selectedSensor, setSelectedSensor] = React.useState('sensor-001');
  const availableSensors = ['sensor-001', 'sensor-002', 'sensor-003', 'sensor-004'];

  return (
    <div style={{ width: '100%', padding: '20px' }}>
      <h1>Sensor Telemetry Viewer</h1>
      
      {/* Sensor Selector */}
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="sensor-select" style={{ marginRight: '10px', fontWeight: 'bold' }}>
          Select Sensor:
        </label>
        <select
          id="sensor-select"
          value={selectedSensor}
          onChange={(e) => setSelectedSensor(e.target.value)}
          style={{
            padding: '8px 12px',
            fontSize: '14px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
          }}
        >
          {availableSensors.map(sensor => (
            <option key={sensor} value={sensor}>
              {sensor}
            </option>
          ))}
        </select>
      </div>

      {/* Chart Display */}
      <ChartView sensorId={selectedSensor} />
    </div>
  );
}

/**
 * Example 5: Tabbed Interface
 * 
 * Display charts in tabs for better space utilization.
 */
export function TabbedChartExample() {
  const [activeTab, setActiveTab] = React.useState('sensor-001');
  const sensors = [
    { id: 'sensor-001', name: 'Downtown Sensor' },
    { id: 'sensor-002', name: 'Park Sensor' },
    { id: 'sensor-003', name: 'Industrial Zone' },
  ];

  return (
    <div style={{ width: '100%', padding: '20px' }}>
      <h1>Sensor Telemetry - Tabbed View</h1>
      
      {/* Tab Headers */}
      <div style={{ 
        display: 'flex', 
        gap: '4px', 
        borderBottom: '2px solid #e5e7eb',
        marginBottom: '20px',
      }}>
        {sensors.map(sensor => (
          <button
            key={sensor.id}
            onClick={() => setActiveTab(sensor.id)}
            style={{
              padding: '12px 24px',
              border: 'none',
              borderBottom: activeTab === sensor.id ? '3px solid #3b82f6' : '3px solid transparent',
              backgroundColor: activeTab === sensor.id ? '#eff6ff' : 'transparent',
              color: activeTab === sensor.id ? '#3b82f6' : '#6b7280',
              fontWeight: activeTab === sensor.id ? '600' : '400',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {sensor.name}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <ChartView sensorId={activeTab} />
    </div>
  );
}

/**
 * Example 6: Dashboard with Summary Stats
 * 
 * Combine charts with summary statistics.
 */
export function DashboardWithStatsExample() {
  const sensorId = 'sensor-001';
  
  // In a real app, these would come from the telemetry data
  const stats = {
    avgCO2: 450,
    avgNoise: 65,
    avgTemp: 26,
    lastUpdate: new Date().toLocaleString(),
  };

  return (
    <div style={{ width: '100%', padding: '20px' }}>
      <h1>Sensor Dashboard</h1>
      
      {/* Summary Stats */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '24px',
      }}>
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#eff6ff', 
          borderRadius: '8px',
          border: '1px solid #bfdbfe',
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280' }}>Avg CO2</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
            {stats.avgCO2} ppm
          </div>
        </div>
        
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#fef9c3', 
          borderRadius: '8px',
          border: '1px solid #fde047',
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280' }}>Avg Noise</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#eab308' }}>
            {stats.avgNoise} dB
          </div>
        </div>
        
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#fee2e2', 
          borderRadius: '8px',
          border: '1px solid #fca5a5',
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280' }}>Avg Temperature</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>
            {stats.avgTemp} °C
          </div>
        </div>
        
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#f3f4f6', 
          borderRadius: '8px',
          border: '1px solid #d1d5db',
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280' }}>Last Update</div>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#374151' }}>
            {stats.lastUpdate}
          </div>
        </div>
      </div>

      {/* Charts */}
      <ChartView sensorId={sensorId} />
    </div>
  );
}

/**
 * Example 7: Responsive Layout
 * 
 * Charts that adapt to different screen sizes.
 */
export function ResponsiveChartExample() {
  return (
    <div style={{ 
      width: '100%', 
      padding: '20px',
      maxWidth: '1400px',
      margin: '0 auto',
    }}>
      <h1>Responsive Sensor Charts</h1>
      <p style={{ color: '#6b7280', marginBottom: '20px' }}>
        Resize your browser window to see the responsive layout in action.
      </p>
      
      <div style={{ 
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
        gap: '20px',
      }}>
        <div style={{ 
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          overflow: 'hidden',
        }}>
          <ChartView sensorId="sensor-001" />
        </div>
      </div>
    </div>
  );
}

// Note: Import React for useState in examples that use it
import React from 'react';
