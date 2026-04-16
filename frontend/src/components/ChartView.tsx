/**
 * ChartView Component - Time-series chart visualization for sensor telemetry
 * 
 * Displays three line charts for CO2, Noise, and Temperature metrics.
 * Fetches historical data and updates in real-time via WebSocket.
 * 
 * Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
 */

import { useEffect, useState, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  type ChartOptions,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { fetchTelemetry } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { Telemetry } from '../types';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

/**
 * Time range options for filtering data
 */
type TimeRange = '1h' | '6h' | '24h';

/**
 * ChartView component props
 */
export interface ChartViewProps {
  sensorId: string;
  wsUrl?: string;
}

/**
 * ChartView Component
 * 
 * Renders three line charts showing CO2, Noise, and Temperature trends.
 * Fetches last 100 telemetry readings on mount and updates in real-time.
 */
export const ChartView: React.FC<ChartViewProps> = ({
  sensorId,
  wsUrl = 'ws://backend:8000/ws',
}) => {
  const [telemetryData, setTelemetryData] = useState<Telemetry[]>([]);
  const [timeRange, setTimeRange] = useState<TimeRange>('24h');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const dataRef = useRef<Telemetry[]>([]);

  /**
   * Fetch initial telemetry data on mount or when sensorId changes
   */
  useEffect(() => {
    const loadTelemetry = async () => {
      try {
        setLoading(true);
        setError(null);

        const now = new Date();
        const timeRangeMs: Record<TimeRange, number> = {
          '1h': 60 * 60 * 1000,
          '6h': 6 * 60 * 60 * 1000,
          '24h': 24 * 60 * 60 * 1000,
        };
        const startTime = new Date(now.getTime() - timeRangeMs[timeRange]).toISOString();

        const data = await fetchTelemetry(sensorId, { 
          limit: 1000,
          startTime: startTime 
        });
        
        // Sort by timestamp ascending for chart display
        const sortedData = data.sort((a, b) => 
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        );
        setTelemetryData(sortedData);
        dataRef.current = sortedData;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load telemetry data');
        console.error('Error fetching telemetry:', err);
      } finally {
        setLoading(false);
      }
    };

    loadTelemetry();
  }, [sensorId, timeRange]);

  /**
   * Handle real-time telemetry updates via WebSocket
   */
  const handleTelemetryUpdate = (newTelemetry: Telemetry) => {
    // Only update if telemetry is for the selected sensor
    if (newTelemetry.sensorId !== sensorId) return;

    setTelemetryData(prevData => {
      // Add new data point and keep last 1000 readings to support 24h view
      const updatedData = [...prevData, newTelemetry].slice(-1000);
      dataRef.current = updatedData;
      return updatedData;
    });
  };

  // Connect to WebSocket for real-time updates
  useWebSocket(wsUrl, {
    onTelemetry: handleTelemetryUpdate,
  });

  /**
   * Filter data based on selected time range
   */
  const getFilteredData = (): Telemetry[] => {
    const now = new Date();
    const timeRangeMs: Record<TimeRange, number> = {
      '1h': 60 * 60 * 1000,
      '6h': 6 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
    };

    const cutoffTime = new Date(now.getTime() - timeRangeMs[timeRange]);
    return telemetryData.filter(t => new Date(t.timestamp) >= cutoffTime);
  };

  const filteredData = getFilteredData();

  /**
   * Prepare chart data
   */
  const labels = filteredData.map(t => {
    const date = new Date(t.timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false,
    });
  });

  /**
   * Calculate auto-scaling Y-axis range with padding
   */
  const getYAxisRange = (values: number[]): { min: number; max: number } => {
    if (values.length === 0) return { min: 0, max: 100 };
    
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.1 || 10; // 10% padding or minimum 10 units
    
    return {
      min: Math.max(0, Math.floor(min - padding)),
      max: Math.ceil(max + padding),
    };
  };

  // CO2 Chart Data
  const co2Values = filteredData.map(t => t.co2);
  const co2Range = getYAxisRange(co2Values);
  const co2Data = {
    labels,
    datasets: [
      {
        label: 'CO2 (ppm)',
        data: co2Values,
        borderColor: '#00f3ff', // Neon Cyan
        backgroundColor: 'rgba(0, 243, 255, 0.1)',
        tension: 0.3,
        pointRadius: 2,
        pointHoverRadius: 5,
        pointBackgroundColor: '#00f3ff',
      },
    ],
  };

  // Noise Chart Data
  const noiseValues = filteredData.map(t => t.noise);
  const noiseRange = getYAxisRange(noiseValues);
  const noiseData = {
    labels,
    datasets: [
      {
        label: 'Noise (dB)',
        data: noiseValues,
        borderColor: '#facc15', // Neon Yellow
        backgroundColor: 'rgba(250, 204, 21, 0.1)',
        tension: 0.3,
        pointRadius: 2,
        pointHoverRadius: 5,
        pointBackgroundColor: '#facc15',
      },
    ],
  };

  // Temperature Chart Data
  const temperatureValues = filteredData.map(t => t.temperature);
  const temperatureRange = getYAxisRange(temperatureValues);
  const temperatureData = {
    labels,
    datasets: [
      {
        label: 'Temperature (°C)',
        data: temperatureValues,
        borderColor: '#ff003c', // Cyberpunk Red
        backgroundColor: 'rgba(255, 0, 60, 0.1)',
        tension: 0.3,
        pointRadius: 2,
        pointHoverRadius: 5,
        pointBackgroundColor: '#ff003c',
      },
    ],
  };

  /**
   * Chart options with auto-scaling Y-axis and dark theme
   */
  const createChartOptions = (yAxisRange: { min: number; max: number }): ChartOptions<'line'> => ({
    responsive: true,
    maintainAspectRatio: false,
    color: '#e0f2fe',
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: { color: '#e0f2fe' }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(2, 6, 23, 0.9)',
        titleColor: '#00f3ff',
        bodyColor: '#e0f2fe',
        borderColor: '#00f3ff',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Time',
          color: '#94a3b8'
        },
        ticks: {
          maxRotation: 45,
          minRotation: 45,
          color: '#94a3b8'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.05)'
        }
      },
      y: {
        display: true,
        min: yAxisRange.min,
        max: yAxisRange.max,
        ticks: {
          precision: 0,
          color: '#94a3b8'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.05)'
        }
      },
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false,
    },
  });

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        color: '#6b7280',
      }}>
        Loading telemetry data...
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        color: '#ef4444',
      }}>
        Error: {error}
      </div>
    );
  }

  /**
   * Render empty state
   */
  if (filteredData.length === 0) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        color: '#6b7280',
      }}>
        <p>No telemetry data available for the selected time range.</p>
        <p style={{ fontSize: '14px', marginTop: '8px' }}>
          Try selecting a different time range or wait for new data.
        </p>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', padding: '16px' }}>
      {/* Time Range Selector */}
      <div style={{ 
        display: 'flex', 
        gap: '8px', 
        marginBottom: '24px',
        justifyContent: 'center',
      }}>
        {(['1h', '6h', '24h'] as TimeRange[]).map(range => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            style={{
              padding: '8px 16px',
              border: `1px solid ${timeRange === range ? '#00f3ff' : 'rgba(0, 243, 255, 0.3)'}`,
              borderRadius: '6px',
              backgroundColor: timeRange === range ? 'rgba(0, 243, 255, 0.2)' : 'rgba(2, 6, 23, 0.5)',
              color: timeRange === range ? '#00f3ff' : '#94a3b8',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: timeRange === range ? '600' : '400',
              transition: 'all 0.2s',
              boxShadow: timeRange === range ? '0 0 10px rgba(0, 243, 255, 0.5)' : 'none',
            }}
            onMouseEnter={(e) => {
              if (timeRange !== range) e.currentTarget.style.backgroundColor = 'rgba(0, 243, 255, 0.1)';
            }}
            onMouseLeave={(e) => {
              if (timeRange !== range) e.currentTarget.style.backgroundColor = 'rgba(2, 6, 23, 0.5)';
            }}
          >
            {range}
          </button>
        ))}
      </div>

      {/* Charts Grid */}
      <div style={{ 
        display: 'grid', 
        gap: '24px',
        gridTemplateColumns: '1fr',
      }}>
        {/* CO2 Chart */}
        <div style={{ 
          padding: '16px', 
          height: '300px',
        }}>
          <Line data={co2Data} options={createChartOptions(co2Range)} />
        </div>

        {/* Noise Chart */}
        <div style={{ 
          padding: '16px', 
          height: '300px',
        }}>
          <Line data={noiseData} options={createChartOptions(noiseRange)} />
        </div>

        {/* Temperature Chart */}
        <div style={{ 
          padding: '16px', 
          height: '300px',
        }}>
          <Line data={temperatureData} options={createChartOptions(temperatureRange)} />
        </div>
      </div>

      {/* Data Info */}
      <div style={{ 
        marginTop: '16px', 
        textAlign: 'center', 
        color: '#6b7280',
        fontSize: '14px',
      }}>
        Showing {filteredData.length} readings for sensor {sensorId}
      </div>
    </div>
  );
};

export default ChartView;
