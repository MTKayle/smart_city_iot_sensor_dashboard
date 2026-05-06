import React, { useMemo } from 'react';
import { Flame } from 'lucide-react';
import type { HeatmapMetric } from './types';
import { METRIC_SPECS, rampColor } from '../../utils/heatmap';

interface SensorMetricSnapshot {
  pm25: number;
  temp: number;
  humidity: number;
  co2: number;
  noise: number;
}

interface HeatmapControlProps {
  selectedMetric: HeatmapMetric;
  onMetricChange: (metric: HeatmapMetric) => void;
  /** Sensors as projected by MapView — used to compute live min/avg/max stats. */
  sensors: SensorMetricSnapshot[];
  /** 0..1 — current heatmap layer opacity. */
  opacity: number;
  onOpacityChange: (opacity: number) => void;
}

const METRIC_BUTTONS: Array<{ id: HeatmapMetric }> = [
  { id: 'pm25' },
  { id: 'temp' },
  { id: 'humidity' },
  { id: 'co2' },
  { id: 'noise' },
];

const HeatmapControl: React.FC<HeatmapControlProps> = ({
  selectedMetric,
  onMetricChange,
  sensors,
  opacity,
  onOpacityChange,
}) => {
  const spec = METRIC_SPECS[selectedMetric];

  // ─── Live min / avg / max for the active metric ───
  const stats = useMemo(() => {
    const pickValue = (s: SensorMetricSnapshot): number | null => {
      switch (selectedMetric) {
        case 'pm25':     return s.pm25;
        case 'temp':     return s.temp;
        case 'humidity': return s.humidity;
        case 'co2':      return s.co2;
        case 'noise':    return s.noise;
        default:         return null;
      }
    };
    const values = sensors
      .map(pickValue)
      .filter((v): v is number => v !== null && !isNaN(v) && v !== 0);
    if (values.length === 0) return null;
    let min = values[0];
    let max = values[0];
    let sum = 0;
    for (const v of values) {
      if (v < min) min = v;
      if (v > max) max = v;
      sum += v;
    }
    return { min, max, avg: sum / values.length, count: values.length };
  }, [sensors, selectedMetric]);

  // ─── Legend gradient bar — sample the ramp at fixed intervals ───
  const legendGradient = useMemo(() => {
    const samples = 40;
    const stops: string[] = [];
    const lo = spec.stops[0].value;
    const hi = spec.stops[spec.stops.length - 1].value;
    for (let i = 0; i <= samples; i++) {
      const t = i / samples;
      const v = lo + (hi - lo) * t;
      stops.push(`${rampColor(v, spec, 1)} ${(t * 100).toFixed(1)}%`);
    }
    return `linear-gradient(to right, ${stops.join(', ')})`;
  }, [spec]);

  const fmt = (v: number) => v.toFixed(spec.digits);

  return (
    <div className="heatmap-control">
      <div className="heatmap-header">
        <Flame className="w-5 h-5 text-orange-400" />
        <span>Bản Đồ Nhiệt</span>
      </div>

      <div className="heatmap-metrics">
        {METRIC_BUTTONS.map(({ id }) => {
          const buttonSpec = METRIC_SPECS[id];
          return (
            <button
              key={id}
              className={`metric-btn ${selectedMetric === id ? 'active' : ''}`}
              onClick={() => onMetricChange(id)}
            >
              <span className="metric-label">{buttonSpec.label}</span>
              <span className="metric-unit">{buttonSpec.unit}</span>
            </button>
          );
        })}
      </div>

      {/* Live stats for the active metric */}
      <div className="heatmap-stats">
        <div className="heatmap-stat">
          <span className="heatmap-stat-label">Min</span>
          <span className="heatmap-stat-value">
            {stats ? fmt(stats.min) : '—'}
            <span className="heatmap-stat-unit"> {spec.unit}</span>
          </span>
        </div>
        <div className="heatmap-stat">
          <span className="heatmap-stat-label">TB</span>
          <span className="heatmap-stat-value">
            {stats ? fmt(stats.avg) : '—'}
            <span className="heatmap-stat-unit"> {spec.unit}</span>
          </span>
        </div>
        <div className="heatmap-stat">
          <span className="heatmap-stat-label">Max</span>
          <span className="heatmap-stat-value">
            {stats ? fmt(stats.max) : '—'}
            <span className="heatmap-stat-unit"> {spec.unit}</span>
          </span>
        </div>
      </div>

      {/* Continuous color ramp legend with breakpoint labels */}
      <div className="heatmap-legend">
        <div className="heatmap-legend-bar" style={{ background: legendGradient }} />
        <div className="heatmap-legend-ticks">
          {spec.stops.map((stop) => (
            <div
              key={stop.value}
              className="heatmap-legend-tick"
              style={{
                left: `${
                  ((stop.value - spec.stops[0].value) /
                    (spec.stops[spec.stops.length - 1].value - spec.stops[0].value)) *
                  100
                }%`,
              }}
            >
              <span className="heatmap-legend-tick-line" />
              <span className="heatmap-legend-tick-value">{fmt(stop.value)}</span>
              <span className="heatmap-legend-tick-label">{stop.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Opacity control */}
      <div className="heatmap-opacity">
        <label className="heatmap-opacity-label">
          Độ trong suốt
          <span className="heatmap-opacity-value">{Math.round(opacity * 100)}%</span>
        </label>
        <input
          type="range"
          min={20}
          max={95}
          value={Math.round(opacity * 100)}
          onChange={(e) => onOpacityChange(Number(e.target.value) / 100)}
          className="heatmap-opacity-slider"
        />
      </div>

      <p className="heatmap-footer">
        Tổng hợp từ {stats?.count ?? 0} cảm biến đang hoạt động
      </p>
    </div>
  );
};

export default HeatmapControl;
