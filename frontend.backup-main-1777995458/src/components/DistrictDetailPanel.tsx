/**
 * DistrictDetailPanel — Shows per-ward, per-sensor details for a district.
 *
 * Opened by clicking a district on the map.
 * Displays a glassmorphism floating panel listing each ward with its 3 sensor values.
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
            const co2Sensor = ward.sensors.find(s => s.type === 'CO2');
            const noiseSensor = ward.sensors.find(s => s.type === 'Noise');
            const tempSensor = ward.sensors.find(s => s.type === 'Temperature');

            const co2Val = co2Sensor && telemetry[co2Sensor.id] ? telemetry[co2Sensor.id].co2 : null;
            const noiseVal = noiseSensor && telemetry[noiseSensor.id] ? telemetry[noiseSensor.id].noise : null;
            const tempVal = tempSensor && telemetry[tempSensor.id] ? telemetry[tempSensor.id].temperature : null;

            return (
              <div className="ddp-ward" key={ward.id}>
                <div className="ddp-ward-name">📍 {ward.name}</div>
                <div className="ddp-sensors">
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
