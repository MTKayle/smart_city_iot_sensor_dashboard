/**
 * HeatmapControl Component
 * 
 * Provides heatmap configuration controls:
 * - Toggle heatmap ON/OFF
 * - Select metric for visualization (PM2.5, Temperature, Humidity, CO2, Noise)
 * - Intensity slider
 * - Radius slider
 */

import React from 'react';
import './HeatmapControl.css';

export type HeatmapMetric = 'pm25' | 'temperature' | 'humidity' | 'co2' | 'noise';

export interface HeatmapConfig {
  enabled: boolean;
  metric: HeatmapMetric;
  intensity: number;
  radius: number;
}

interface HeatmapControlProps {
  config: HeatmapConfig;
  onConfigChange: (config: Partial<HeatmapConfig>) => void;
}

const METRIC_OPTIONS: { value: HeatmapMetric; label: string; icon: string; unit: string }[] = [
  { value: 'pm25', label: 'PM2.5', icon: '💨', unit: 'μg/m³' },
  { value: 'temperature', label: 'Temperature', icon: '🌡️', unit: '°C' },
  { value: 'humidity', label: 'Humidity', icon: '💧', unit: '%' },
  { value: 'co2', label: 'CO₂', icon: '🌫️', unit: 'ppm' },
  { value: 'noise', label: 'Noise', icon: '🔊', unit: 'dB' },
];

const HeatmapControl: React.FC<HeatmapControlProps> = ({ config, onConfigChange }) => {
  // const selectedMetric = METRIC_OPTIONS.find(m => m.value === config.metric);

  return (
    <div className="heatmap-control glass-panel">
      <div className="control-header">
        <h3 className="control-title">
          <span className="icon">🔥</span>
          Heatmap
        </h3>
        <label className="heatmap-toggle">
          <input
            type="checkbox"
            checked={config.enabled}
            onChange={(e) => onConfigChange({ enabled: e.target.checked })}
          />
          <span className="toggle-slider"></span>
        </label>
      </div>

      {config.enabled && (
        <div className="heatmap-settings">
          {/* Metric Selection */}
          <div className="setting-group">
            <label className="setting-label">Metric</label>
            <div className="metric-buttons">
              {METRIC_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  className={`metric-btn ${config.metric === option.value ? 'active' : ''}`}
                  onClick={() => onConfigChange({ metric: option.value })}
                  title={`${option.label} (${option.unit})`}
                >
                  <span className="metric-icon">{option.icon}</span>
                  <span className="metric-name">{option.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Intensity Slider */}
          <div className="setting-group">
            <label className="setting-label">
              Intensity
              <span className="setting-value">{config.intensity.toFixed(1)}</span>
            </label>
            <input
              type="range"
              min="0.1"
              max="2"
              step="0.1"
              value={config.intensity}
              onChange={(e) => onConfigChange({ intensity: parseFloat(e.target.value) })}
              className="slider"
            />
          </div>

          {/* Radius Slider */}
          <div className="setting-group">
            <label className="setting-label">
              Radius
              <span className="setting-value">{config.radius}px</span>
            </label>
            <input
              type="range"
              min="10"
              max="50"
              step="5"
              value={config.radius}
              onChange={(e) => onConfigChange({ radius: parseInt(e.target.value) })}
              className="slider"
            />
          </div>

          {/* Color Legend */}
          <div className="heatmap-legend">
            <div className="legend-label">Intensity</div>
            <div className="legend-gradient"></div>
            <div className="legend-labels">
              <span>Low</span>
              <span>High</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HeatmapControl;
