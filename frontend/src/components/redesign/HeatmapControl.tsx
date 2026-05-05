import React from 'react';
import { Flame } from 'lucide-react';
import type { HeatmapMetric } from './types';

interface HeatmapControlProps {
  selectedMetric: HeatmapMetric;
  onMetricChange: (metric: HeatmapMetric) => void;
}

const HeatmapControl: React.FC<HeatmapControlProps> = ({ selectedMetric, onMetricChange }) => {
  const metrics = [
    { id: 'pm25', label: 'PM2.5', unit: 'µg/m³' },
    { id: 'temp', label: 'Nhiệt Độ', unit: '°C' },
    { id: 'humidity', label: 'Độ Ẩm', unit: '%' },
    { id: 'co2', label: 'CO2', unit: 'ppm' },
    { id: 'noise', label: 'Tiếng Ồn', unit: 'dB' },
  ];

  return (
    <div className="heatmap-control">
      <div className="heatmap-header">
        <Flame className="w-5 h-5 text-orange-400" />
        <span>Bản Đồ Nhiệt</span>
      </div>

      <div className="heatmap-metrics">
        {metrics.map((metric) => (
          <button
            key={metric.id}
            className={`metric-btn ${selectedMetric === metric.id ? 'active' : ''}`}
            onClick={() => onMetricChange(metric.id as HeatmapMetric)}
          >
            <span className="metric-label">{metric.label}</span>
            <span className="metric-unit">{metric.unit}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default HeatmapControl;
