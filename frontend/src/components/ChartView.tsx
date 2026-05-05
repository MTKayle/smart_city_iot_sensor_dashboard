/**
 * ChartView Component — Time-series chart visualization for 5 sensor metrics
 *
 * Displays line charts for CO₂, Noise, Temperature, PM2.5, and Humidity.
 * Fetches historical data and updates in real-time via WebSocket.
 *
 * Requirements: FR9.2
 */

import { useEffect, useState, useRef, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
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
  Legend,
  Filler,
);

type TimeRange = '1h' | '6h' | '24h';

export interface ChartViewProps {
  sensorId: string;
  wsUrl?: string;
}

// ── Metric configs ──
interface MetricConfig {
  key: string;
  label: string;
  unit: string;
  color: string;
  bgColor: string;
  icon: string;
  extractFn: (t: Telemetry) => number | null;
}

const METRICS: MetricConfig[] = [
  {
    key: 'co2', label: 'CO₂', unit: 'ppm', icon: '🌫️',
    color: '#00f3ff', bgColor: 'rgba(0, 243, 255, 0.08)',
    extractFn: (t) => t.data?.co2 ?? t.co2 ?? null,
  },
  {
    key: 'noise', label: 'Noise', unit: 'dB', icon: '🔊',
    color: '#facc15', bgColor: 'rgba(250, 204, 21, 0.08)',
    extractFn: (t) => t.data?.noise ?? t.noise ?? null,
  },
  {
    key: 'temperature', label: 'Temperature', unit: '°C', icon: '🌡️',
    color: '#ff003c', bgColor: 'rgba(255, 0, 60, 0.08)',
    extractFn: (t) => t.data?.temperature ?? t.temperature ?? null,
  },
  {
    key: 'pm25', label: 'PM2.5', unit: 'μg/m³', icon: '💨',
    color: '#c084fc', bgColor: 'rgba(192, 132, 252, 0.08)',
    extractFn: (t) => t.data?.pm25 ?? t.pm25 ?? null,
  },
  {
    key: 'humidity', label: 'Humidity', unit: '%', icon: '💧',
    color: '#00ff9d', bgColor: 'rgba(0, 255, 157, 0.08)',
    extractFn: (t) => t.data?.humidity ?? t.humidity ?? null,
  },
];

/**
 * ChartView Component — Renders 5 line charts with real-time updates.
 */
export const ChartView: React.FC<ChartViewProps> = ({
  sensorId,
  wsUrl = 'ws://backend:8000/ws',
}) => {
  const [telemetryData, setTelemetryData] = useState<Telemetry[]>([]);
  const [timeRange, setTimeRange] = useState<TimeRange>('24h');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeMetrics, setActiveMetrics] = useState<Set<string>>(
    new Set(METRICS.map(m => m.key)),
  );
  const dataRef = useRef<Telemetry[]>([]);

  // ── Fetch historical telemetry ──
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
          startTime,
        });

        const sortedData = data.sort(
          (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
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

  // ── Real-time WS updates ──
  const handleTelemetryUpdate = (newTelemetry: Telemetry) => {
    if (newTelemetry.sensorId !== sensorId) return;

    setTelemetryData(prevData => {
      const updatedData = [...prevData, newTelemetry].slice(-1000);
      dataRef.current = updatedData;
      return updatedData;
    });
  };

  useWebSocket(wsUrl, { onTelemetry: handleTelemetryUpdate });

  // ── Filter data by time range ──
  const filteredData = useMemo(() => {
    const now = new Date();
    const timeRangeMs: Record<TimeRange, number> = {
      '1h': 60 * 60 * 1000,
      '6h': 6 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
    };
    const cutoff = new Date(now.getTime() - timeRangeMs[timeRange]);
    return telemetryData.filter(t => new Date(t.timestamp) >= cutoff);
  }, [telemetryData, timeRange]);

  // ── Labels ──
  const labels = filteredData.map(t => {
    const d = new Date(t.timestamp);
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  });

  // ── Y-axis auto-scaling ──
  const getYRange = (values: (number | null)[]): { min: number; max: number } => {
    const valid = values.filter((v): v is number => v !== null);
    if (valid.length === 0) return { min: 0, max: 100 };
    const mn = Math.min(...valid);
    const mx = Math.max(...valid);
    const pad = (mx - mn) * 0.1 || 10;
    return { min: Math.max(0, Math.floor(mn - pad)), max: Math.ceil(mx + pad) };
  };

  // ── Chart options factory ──
  const createChartOptions = (
    yRange: { min: number; max: number },
    _metricLabel: string,
    metricColor: string,
  ): ChartOptions<'line'> => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    color: '#e0f2fe',
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(2, 6, 23, 0.92)',
        titleColor: metricColor,
        bodyColor: '#e0f2fe',
        borderColor: metricColor,
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
      },
    },
    scales: {
      x: {
        display: true,
        ticks: { maxRotation: 45, minRotation: 45, color: '#64748b', font: { size: 10 } },
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
      },
      y: {
        display: true,
        min: yRange.min,
        max: yRange.max,
        ticks: { precision: 0, color: '#64748b', font: { size: 10 } },
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
      },
    },
    interaction: { mode: 'nearest', axis: 'x', intersect: false },
  });

  // ── Toggle metric visibility ──
  const toggleMetric = (key: string) => {
    setActiveMetrics(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size <= 1) return prev; // Must keep at least 1
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  // ── Render states ──
  if (loading) {
    return (
      <div className="chart-loading">
        <div className="chart-loading-spinner" />
        <span>Loading telemetry data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chart-error">
        <span>⚠️ {error}</span>
      </div>
    );
  }

  if (filteredData.length === 0) {
    return (
      <div className="chart-empty">
        <p>No telemetry data available.</p>
        <p style={{ fontSize: '12px', marginTop: '4px' }}>
          Try a different time range or wait for new data.
        </p>
      </div>
    );
  }

  const visibleMetrics = METRICS.filter(m => activeMetrics.has(m.key));

  return (
    <div style={{ width: '100%', padding: '12px' }}>
      {/* ── Time Range Selector ── */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', justifyContent: 'center' }}>
        {(['1h', '6h', '24h'] as TimeRange[]).map(range => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            style={{
              padding: '6px 14px',
              border: `1px solid ${timeRange === range ? '#00f3ff' : 'rgba(0, 243, 255, 0.2)'}`,
              borderRadius: '6px',
              backgroundColor: timeRange === range ? 'rgba(0, 243, 255, 0.15)' : 'transparent',
              color: timeRange === range ? '#00f3ff' : '#64748b',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: timeRange === range ? '700' : '400',
              transition: 'all 0.2s',
              boxShadow: timeRange === range ? '0 0 8px rgba(0, 243, 255, 0.3)' : 'none',
              textTransform: 'uppercase',
              letterSpacing: '1px',
            }}
          >
            {range}
          </button>
        ))}
      </div>

      {/* ── Metric Toggle Pills ── */}
      <div style={{
        display: 'flex', gap: '6px', marginBottom: '16px',
        justifyContent: 'center', flexWrap: 'wrap',
      }}>
        {METRICS.map(m => {
          const isActive = activeMetrics.has(m.key);
          return (
            <button
              key={m.key}
              onClick={() => toggleMetric(m.key)}
              style={{
                padding: '4px 10px',
                border: `1px solid ${isActive ? m.color : 'rgba(100,116,139,0.3)'}`,
                borderRadius: '16px',
                backgroundColor: isActive ? `${m.color}20` : 'transparent',
                color: isActive ? m.color : '#64748b',
                cursor: 'pointer',
                fontSize: '11px',
                fontWeight: isActive ? '600' : '400',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <span>{m.icon}</span>
              <span>{m.label}</span>
            </button>
          );
        })}
      </div>

      {/* ── Charts Grid ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {visibleMetrics.map(m => {
          const values = filteredData.map(m.extractFn);
          const yRange = getYRange(values);

          // Latest value for header display
          const latestVal = values[values.length - 1];
          const validValues = values.filter((v): v is number => v !== null);

          const chartData = {
            labels,
            datasets: [{
              label: `${m.label} (${m.unit})`,
              data: validValues.length > 0 ? values.map(v => v ?? undefined) : [],
              borderColor: m.color,
              backgroundColor: m.bgColor,
              tension: 0.35,
              pointRadius: 1,
              pointHoverRadius: 4,
              pointBackgroundColor: m.color,
              borderWidth: 2,
              fill: true,
            }],
          };

          return (
            <div
              key={m.key}
              style={{
                padding: '12px',
                borderRadius: '8px',
                border: `1px solid ${m.color}20`,
                background: `linear-gradient(180deg, ${m.color}08 0%, transparent 100%)`,
              }}
            >
              {/* Metric header */}
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                marginBottom: '8px', paddingBottom: '6px',
                borderBottom: `1px solid ${m.color}20`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '14px' }}>{m.icon}</span>
                  <span style={{
                    fontSize: '13px', fontWeight: '700', color: m.color,
                    textTransform: 'uppercase', letterSpacing: '0.5px',
                  }}>
                    {m.label}
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{
                    fontSize: '18px', fontWeight: '700', color: m.color,
                    textShadow: `0 0 8px ${m.color}50`,
                    fontVariantNumeric: 'tabular-nums',
                  }}>
                    {latestVal !== null && latestVal !== undefined ? latestVal.toFixed(1) : '—'}
                  </span>
                  <span style={{ fontSize: '11px', color: '#64748b', marginLeft: '4px' }}>
                    {m.unit}
                  </span>
                </div>
              </div>

              {/* Chart */}
              <div style={{ height: '150px' }}>
                {validValues.length > 0 ? (
                  <Line data={chartData} options={createChartOptions(yRange, m.label, m.color)} />
                ) : (
                  <div style={{
                    display: 'flex', justifyContent: 'center', alignItems: 'center',
                    height: '100%', color: '#64748b', fontSize: '12px',
                  }}>
                    No {m.label} data available
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Data Info */}
      <div style={{
        marginTop: '12px', textAlign: 'center', color: '#64748b',
        fontSize: '11px', letterSpacing: '0.5px',
      }}>
        SHOWING {filteredData.length} READINGS · SENSOR {sensorId}
      </div>
    </div>
  );
};

export default ChartView;
