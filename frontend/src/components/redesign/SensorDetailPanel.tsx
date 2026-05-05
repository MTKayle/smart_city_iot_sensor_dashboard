/**
 * SensorDetailPanel — Realtime, multi-metric detail view.
 *
 * Key behaviours:
 * 1. Reads current values from AppContext.telemetryMap by sensorId / cluster
 *    member IDs, so updates flow in automatically as the WebSocket pushes new
 *    telemetry.  The parent only owns the *selection*, not the data snapshot.
 * 2. 5 metric tabs (PM2.5 / CO₂ / Nhiệt Độ / Độ Ẩm / Tiếng Ồn) — clicking a
 *    tab swaps the chart to that metric without remounting the panel.
 * 3. Chart is fed by useTelemetryHistory (sensor) or useClusterHistory
 *    (cluster) — both seed from REST history then append realtime points.
 */

import React, { useState, useMemo } from 'react';
import { X, Battery, Signal, RadioTower } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { useAppContext } from '../../context/AppContext';
import {
  useTelemetryHistory,
  useClusterHistory,
} from '../../hooks/useTelemetryHistory';
import { classifySensorStatus } from '../../utils/telemetry';

type MetricKey = 'pm25' | 'co2' | 'temperature' | 'humidity' | 'noise';

interface MetricConfig {
  key: MetricKey;
  label: string;
  unit: string;
  color: string;
  icon: string;
  /** Threshold from backend ALERT_THRESHOLDS (alert_service.py). */
  threshold: number | null;
}

const METRICS: MetricConfig[] = [
  { key: 'pm25', label: 'PM2.5', unit: 'µg/m³', color: '#3B82F6', icon: '💨', threshold: 55 },
  { key: 'co2', label: 'CO₂', unit: 'ppm', color: '#10B981', icon: '🌫️', threshold: 1000 },
  { key: 'temperature', label: 'Nhiệt Độ', unit: '°C', color: '#F59E0B', icon: '🌡️', threshold: null },
  { key: 'humidity', label: 'Độ Ẩm', unit: '%', color: '#06B6D4', icon: '💧', threshold: null },
  { key: 'noise', label: 'Tiếng Ồn', unit: 'dB', color: '#EF4444', icon: '🔊', threshold: 85 },
];

export interface SensorDetailPanelProps {
  sensorId?: string | null;
  clusterId?: string | null;
  clusterMeta?: {
    memberIds: string[];
    lat: number;
    lng: number;
    count: number;
    name?: string;
  };
  onClose: () => void;
}

const fmtNum = (v: number | null | undefined, digits = 1, suffix = ''): string =>
  v === null || v === undefined || isNaN(v) ? '—' : `${v.toFixed(digits)}${suffix}`;

const getStatusColor = (status: string) => {
  switch (status) {
    case 'critical':
      return 'text-red-400 bg-red-400/10';
    case 'warning':
      return 'text-yellow-400 bg-yellow-400/10';
    case 'normal':
      return 'text-green-400 bg-green-400/10';
    default:
      return 'text-gray-400 bg-gray-400/10';
  }
};

const getStatusText = (status: string) => {
  switch (status) {
    case 'critical':
      return 'NGHIÊM TRỌNG';
    case 'warning':
      return 'CẢNH BÁO';
    case 'normal':
      return 'BÌNH THƯỜNG';
    default:
      return 'CHỜ DỮ LIỆU';
  }
};

const SensorDetailPanel: React.FC<SensorDetailPanelProps> = ({
  sensorId,
  clusterId: _clusterId,
  clusterMeta,
  onClose,
}) => {
  const { sensors, telemetryMap } = useAppContext();
  const [activeMetric, setActiveMetric] = useState<MetricKey>('pm25');

  const isSensorMode = !!sensorId;

  // ─── Sensor mode: live read from context ───
  const sensorMeta = isSensorMode
    ? sensors.find((s) => s.sensorId === sensorId)
    : undefined;
  const sensorTelemetry = isSensorMode ? telemetryMap[sensorId!] : undefined;

  // ─── Cluster mode: aggregate live ───
  const clusterAggregate = useMemo(() => {
    if (isSensorMode || !clusterMeta) return null;
    const members = clusterMeta.memberIds
      .map((id) => telemetryMap[id])
      .filter((t): t is NonNullable<typeof t> => t !== undefined);

    if (members.length === 0) {
      return {
        pm25: null, co2: null, temperature: null, humidity: null, noise: null,
        aqi: null, liveCount: 0,
      };
    }

    const avg = (k: MetricKey): number | null => {
      const vals = members
        .map((m) => {
          const flat = (m as unknown as Record<string, unknown>)[k];
          if (typeof flat === 'number') return flat;
          const nested = m.data?.[k];
          return typeof nested === 'number' ? nested : null;
        })
        .filter((v): v is number => v !== null);
      return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
    };

    const aqiVals = members
      .map((m) => m.aqi)
      .filter((v): v is number => typeof v === 'number');

    return {
      pm25: avg('pm25'),
      co2: avg('co2'),
      temperature: avg('temperature'),
      humidity: avg('humidity'),
      noise: avg('noise'),
      aqi: aqiVals.length ? aqiVals.reduce((a, b) => a + b, 0) / aqiVals.length : null,
      liveCount: members.length,
    };
  }, [isSensorMode, clusterMeta, telemetryMap]);

  // ─── Current values to display (single source of truth per mode) ───
  const current = useMemo(() => {
    if (isSensorMode && sensorTelemetry) {
      return {
        pm25: sensorTelemetry.pm25 ?? sensorTelemetry.data?.pm25 ?? null,
        co2: sensorTelemetry.co2 ?? sensorTelemetry.data?.co2 ?? null,
        temperature:
          sensorTelemetry.temperature ?? sensorTelemetry.data?.temperature ?? null,
        humidity: sensorTelemetry.humidity ?? sensorTelemetry.data?.humidity ?? null,
        noise: sensorTelemetry.noise ?? sensorTelemetry.data?.noise ?? null,
        aqi: sensorTelemetry.aqi ?? null,
        battery: sensorTelemetry.quality?.batteryLevel ?? null,
        signalDbm: sensorTelemetry.quality?.signalStrength ?? null,
        timestamp: sensorTelemetry.timestamp,
      };
    }
    if (clusterAggregate) {
      return {
        ...clusterAggregate,
        battery: null,
        signalDbm: null,
        timestamp: new Date().toISOString(),
      };
    }
    return {
      pm25: null, co2: null, temperature: null, humidity: null, noise: null,
      aqi: null, battery: null, signalDbm: null, timestamp: null as string | null,
    };
  }, [isSensorMode, sensorTelemetry, clusterAggregate]);

  // ─── History buffers (each hook is no-op when its mode is inactive) ───
  const sensorHistory = useTelemetryHistory(isSensorMode ? sensorId! : null, 60);
  const clusterHistory = useClusterHistory(
    isSensorMode ? [] : clusterMeta?.memberIds ?? [],
    60,
  );
  const history = isSensorMode ? sensorHistory : clusterHistory;

  // ─── Status badge (sensor only) ───
  const status = isSensorMode
    ? classifySensorStatus(current.pm25, current.co2)
    : null;

  // ─── Position ───
  const lat = isSensorMode
    ? sensorMeta?.latitude ?? null
    : clusterMeta?.lat ?? null;
  const lng = isSensorMode
    ? sensorMeta?.longitude ?? null
    : clusterMeta?.lng ?? null;

  // ─── Title ───
  const title = isSensorMode
    ? sensorMeta?.locationId || sensorId || 'Cảm biến'
    : clusterMeta?.name || `Cụm (${clusterMeta?.count ?? 0} cảm biến)`;
  const subtitle = isSensorMode
    ? `ID: ${sensorId}`
    : `${clusterAggregate?.liveCount ?? 0}/${clusterMeta?.memberIds.length ?? 0} đang trực tuyến`;

  // ─── Convert dBm signal → percentage display ───
  const signalPct =
    current.signalDbm === null || current.signalDbm === undefined
      ? null
      : Math.max(0, Math.min(100, Math.round(((current.signalDbm + 90) / 60) * 100)));

  const activeMetricConfig = METRICS.find((m) => m.key === activeMetric)!;

  // ─── Y-axis bounds — derive from history so the line isn't a flat blob ───
  const yDomain = useMemo<[number | string, number | string]>(() => {
    const vals = history
      .map((p) => p[activeMetric])
      .filter((v): v is number => typeof v === 'number');
    if (vals.length === 0) return ['auto', 'auto'];
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const pad = (max - min) * 0.15 || max * 0.1 || 1;
    return [Math.max(0, Math.floor(min - pad)), Math.ceil(max + pad)];
  }, [history, activeMetric]);

  return (
    <div className="sensor-detail-panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">{title}</h2>
          <p className="panel-subtitle">{subtitle}</p>
        </div>
        <button className="close-btn" onClick={onClose}>
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="panel-content">
        {/* Status / battery / signal */}
        {isSensorMode && (
          <div className="status-section">
            <span className={`status-badge ${getStatusColor(status ?? '')}`}>
              {getStatusText(status ?? '')}
            </span>
            <div className="status-indicators">
              <div className="indicator">
                <Battery className="w-4 h-4" />
                <span>{fmtNum(current.battery, 0, '%')}</span>
              </div>
              <div className="indicator">
                <Signal className="w-4 h-4" />
                <span>{fmtNum(signalPct, 0, '%')}</span>
              </div>
            </div>
          </div>
        )}

        {/* Live metric cards — all 5 + AQI */}
        <div className="metrics-grid">
          {METRICS.map((m) => {
            const value = current[m.key];
            const isActive = activeMetric === m.key;
            const exceeds =
              m.threshold !== null && typeof value === 'number' && value > m.threshold;
            return (
              <button
                key={m.key}
                onClick={() => setActiveMetric(m.key)}
                className={`metric-card ${isActive ? 'metric-card-active' : ''}`}
                style={{
                  cursor: 'pointer',
                  border: isActive ? `2px solid ${m.color}` : '2px solid transparent',
                  background: isActive
                    ? `${m.color}15`
                    : exceeds
                    ? 'rgba(239,68,68,0.08)'
                    : undefined,
                  textAlign: 'left',
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  transition: 'all 0.15s',
                }}
                title={`Xem biểu đồ ${m.label}`}
              >
                <span className="metric-label" style={{ display: 'block' }}>
                  {m.icon} {m.label}
                </span>
                <div className="metric-value-container">
                  <span
                    className="metric-value"
                    style={{ color: exceeds ? '#ef4444' : isActive ? m.color : undefined }}
                  >
                    {fmtNum(value, m.key === 'co2' ? 0 : 1)}
                  </span>
                  <span className="metric-unit">{m.unit}</span>
                </div>
                {m.threshold !== null && (
                  <span
                    style={{
                      fontSize: 10,
                      color: exceeds ? '#ef4444' : '#94a3b8',
                      display: 'block',
                      marginTop: 4,
                    }}
                  >
                    Ngưỡng: {m.threshold} {m.unit}
                    {exceeds && ' • VƯỢT'}
                  </span>
                )}
              </button>
            );
          })}

          {/* AQI badge — derived, not selectable */}
          <div className="metric-card" style={{ padding: '12px', borderRadius: '8px' }}>
            <span className="metric-label" style={{ display: 'block' }}>
              <RadioTower className="inline w-3 h-3 mr-1" />
              AQI
            </span>
            <div className="metric-value-container">
              <span
                className="metric-value"
                style={{
                  color:
                    (current.aqi ?? 0) > 150
                      ? '#ef4444'
                      : (current.aqi ?? 0) > 100
                      ? '#f59e0b'
                      : (current.aqi ?? 0) > 50
                      ? '#eab308'
                      : '#22c55e',
                }}
              >
                {fmtNum(current.aqi, 0)}
              </span>
              <span className="metric-unit">EPA</span>
            </div>
            <span style={{ fontSize: 10, color: '#94a3b8', display: 'block', marginTop: 4 }}>
              Từ PM2.5
            </span>
          </div>
        </div>

        {/* Metric switcher tabs (mirrors the metric cards but compact) */}
        <div
          className="metric-tabs"
          style={{
            display: 'flex',
            gap: 6,
            marginTop: 16,
            marginBottom: 8,
            flexWrap: 'wrap',
          }}
        >
          {METRICS.map((m) => {
            const isActive = activeMetric === m.key;
            return (
              <button
                key={m.key}
                onClick={() => setActiveMetric(m.key)}
                style={{
                  padding: '6px 12px',
                  borderRadius: 16,
                  border: `1px solid ${isActive ? m.color : 'rgba(100,116,139,0.3)'}`,
                  background: isActive ? `${m.color}25` : 'transparent',
                  color: isActive ? m.color : '#94a3b8',
                  cursor: 'pointer',
                  fontSize: 12,
                  fontWeight: isActive ? 700 : 400,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  transition: 'all 0.15s',
                }}
              >
                <span>{m.icon}</span>
                <span>{m.label}</span>
              </button>
            );
          })}
        </div>

        {/* Chart for the selected metric */}
        <div className="chart-section">
          <div className="chart-header">
            <h3 className="chart-title">
              {activeMetricConfig.icon} Xu Hướng {activeMetricConfig.label} ({activeMetricConfig.unit})
            </h3>
            <span style={{ fontSize: 11, color: '#94a3b8' }}>
              {history.length} điểm · cập nhật realtime
            </span>
          </div>
          {history.length === 0 ? (
            <div
              style={{
                height: 220,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#64748b',
                fontSize: 12,
              }}
            >
              Đang tải dữ liệu lịch sử…
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart
                data={history}
                margin={{ top: 5, right: 12, bottom: 5, left: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="time"
                  stroke="#9CA3AF"
                  style={{ fontSize: '11px' }}
                  minTickGap={20}
                />
                <YAxis
                  stroke="#9CA3AF"
                  style={{ fontSize: '11px' }}
                  domain={yDomain}
                  width={40}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: `1px solid ${activeMetricConfig.color}`,
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  labelStyle={{ color: '#9CA3AF' }}
                  formatter={(value) => {
                    const num = typeof value === 'number' ? value : Number(value);
                    return [
                      `${num.toFixed(activeMetric === 'co2' ? 0 : 1)} ${activeMetricConfig.unit}`,
                      activeMetricConfig.label,
                    ] as [string, string];
                  }}
                />
                {activeMetricConfig.threshold !== null && (
                  <ReferenceLine
                    y={activeMetricConfig.threshold}
                    stroke="#ef4444"
                    strokeDasharray="4 4"
                    strokeWidth={1}
                    label={{
                      value: `Ngưỡng ${activeMetricConfig.threshold}`,
                      position: 'right',
                      fill: '#ef4444',
                      fontSize: 10,
                    }}
                  />
                )}
                <Line
                  type="monotone"
                  dataKey={activeMetric}
                  stroke={activeMetricConfig.color}
                  strokeWidth={2}
                  dot={{ fill: activeMetricConfig.color, r: 2 }}
                  activeDot={{ r: 5 }}
                  isAnimationActive={false}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Footer info */}
        <div className="info-section">
          <div className="info-item">
            <span className="info-label">Vị Trí</span>
            <span className="info-value">
              {lat !== null && lng !== null
                ? `${lat.toFixed(4)}, ${lng.toFixed(4)}`
                : '—'}
            </span>
          </div>
          {isSensorMode && sensorMeta && (
            <>
              <div className="info-item">
                <span className="info-label">Khu vực</span>
                <span className="info-value">{sensorMeta.locationId}</span>
              </div>
              {sensorMeta.clusterId && (
                <div className="info-item">
                  <span className="info-label">Cụm</span>
                  <span className="info-value">{sensorMeta.clusterId}</span>
                </div>
              )}
            </>
          )}
          {current.timestamp && (
            <div className="info-item">
              <span className="info-label">Cập Nhật Lần Cuối</span>
              <span className="info-value">
                {new Date(current.timestamp).toLocaleTimeString('vi-VN')}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SensorDetailPanel;
