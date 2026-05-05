/**
 * DistrictDetailPanel — Shows per-ward, per-sensor details for a district.
 *
 * Opened by clicking a district on the map.
 * Displays a glassmorphism floating panel listing each ward with 5 sensor metrics
 * (CO₂, Noise, Temperature, PM2.5, Humidity) plus an AQI summary.
 */

import type { Telemetry } from '../types';
import { type DistrictData, THRESHOLDS } from '../data/hcmcDistricts';

interface Props {
  district: DistrictData;
  telemetry: Record<string, Telemetry>;
  onClose: () => void;
}

const statusColor = (value: number | null, warn: number, danger: number): string => {
  if (value === null) return '#94a3b8';
  if (value >= danger) return '#ef4444';
  if (value >= warn) return '#eab308';
  return '#22c55e';
};

/** Extract metric from v2 telemetry (nested data or flat field) */
const getVal = (t: Telemetry | undefined, metric: 'co2' | 'noise' | 'temperature' | 'pm25' | 'humidity'): number | null => {
  if (!t) return null;
  const nested = t.data?.[metric];
  if (nested !== undefined && nested !== null) return nested;
  const flat = (t as unknown as Record<string, unknown>)[metric];
  if (typeof flat === 'number') return flat;
  return null;
};

const DistrictDetailPanel: React.FC<Props> = ({ district, telemetry, onClose }) => {
  return (
    <div className="ddp-overlay" onClick={onClose}>
      <div className="ddp-panel glass-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="ddp-header">
          <h2 className="ddp-title">{district.name}</h2>
          <button className="ddp-close" onClick={onClose}>✕</button>
        </div>

        <div className="ddp-subtitle">{district.nameEn} — {district.wards.length} phường · {district.wards.length * 3} sensors</div>

        {/* Ward list */}
        <div className="ddp-wards">
          {district.wards.map(ward => {
            // Find any telemetry for the ward's sensors
            const wardTelemetry = ward.sensors
              .map(s => telemetry[s.id])
              .filter(Boolean);

            // Aggregate values across all sensors in the ward
            const aggregateMetric = (metric: 'co2' | 'noise' | 'temperature' | 'pm25' | 'humidity'): number | null => {
              const values = wardTelemetry.map(t => getVal(t, metric)).filter((v): v is number => v !== null);
              if (values.length === 0) return null;
              return values.reduce((a, b) => a + b, 0) / values.length;
            };

            const co2Val = aggregateMetric('co2');
            const noiseVal = aggregateMetric('noise');
            const tempVal = aggregateMetric('temperature');
            const pm25Val = aggregateMetric('pm25');
            const humidityVal = aggregateMetric('humidity');

            return (
              <div className="ddp-ward" key={ward.id}>
                <div className="ddp-ward-name">📍 {ward.name}</div>
                <div className="ddp-sensors" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
                  <div className="ddp-sensor">
                    <span className="ddp-sensor-label">🌫️ CO₂</span>
                    <span
                      className="ddp-sensor-value"
                      style={{ color: statusColor(co2Val, THRESHOLDS.co2.warning, THRESHOLDS.co2.danger) }}
                    >
                      {co2Val !== null ? `${co2Val.toFixed(1)} ppm` : '—'}
                    </span>
                  </div>
                  <div className="ddp-sensor">
                    <span className="ddp-sensor-label">🔊 Tiếng ồn</span>
                    <span
                      className="ddp-sensor-value"
                      style={{ color: statusColor(noiseVal, THRESHOLDS.noise.warning, THRESHOLDS.noise.danger) }}
                    >
                      {noiseVal !== null ? `${noiseVal.toFixed(1)} dB` : '—'}
                    </span>
                  </div>
                  <div className="ddp-sensor">
                    <span className="ddp-sensor-label">🌡️ Nhiệt độ</span>
                    <span
                      className="ddp-sensor-value"
                      style={{ color: statusColor(tempVal, THRESHOLDS.temperature.warning, THRESHOLDS.temperature.danger) }}
                    >
                      {tempVal !== null ? `${tempVal.toFixed(1)} °C` : '—'}
                    </span>
                  </div>
                  <div className="ddp-sensor">
                    <span className="ddp-sensor-label">💨 PM2.5</span>
                    <span
                      className="ddp-sensor-value"
                      style={{ color: statusColor(pm25Val, THRESHOLDS.pm25.warning, THRESHOLDS.pm25.danger) }}
                    >
                      {pm25Val !== null ? `${pm25Val.toFixed(1)} μg` : '—'}
                    </span>
                  </div>
                  <div className="ddp-sensor">
                    <span className="ddp-sensor-label">💧 Độ ẩm</span>
                    <span
                      className="ddp-sensor-value"
                      style={{ color: statusColor(humidityVal, THRESHOLDS.humidity.warning, THRESHOLDS.humidity.danger) }}
                    >
                      {humidityVal !== null ? `${humidityVal.toFixed(1)} %` : '—'}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="ddp-legend">
          <span className="ddp-leg-item"><span style={{color:'#22c55e'}}>●</span> Bình thường</span>
          <span className="ddp-leg-item"><span style={{color:'#eab308'}}>●</span> Cảnh báo</span>
          <span className="ddp-leg-item"><span style={{color:'#ef4444'}}>●</span> Vượt ngưỡng</span>
        </div>
      </div>
    </div>
  );
};

export default DistrictDetailPanel;
