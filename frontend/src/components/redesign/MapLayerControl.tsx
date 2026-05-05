import React from 'react';
import { Layers, Radio, AlertTriangle, Flame } from 'lucide-react';
import type { MapLayers } from './types';

interface MapLayerControlProps {
  layers: MapLayers;
  onLayerToggle: (layer: keyof MapLayers) => void;
}

const MapLayerControl: React.FC<MapLayerControlProps> = ({ layers, onLayerToggle }) => {
  return (
    <div className="map-layer-control">
      <div className="layer-control-header">
        <Layers className="w-5 h-5" />
        <span>Lớp Bản Đồ</span>
      </div>

      <div className="layer-control-items">
        <div className="layer-item">
          <div className="layer-info">
            <Radio className="w-4 h-4 text-blue-400" />
            <span>Cảm Biến</span>
          </div>
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={layers.sensors}
              onChange={() => onLayerToggle('sensors')}
            />
            <span className="toggle-slider"></span>
          </label>
        </div>

        <div className="layer-item">
          <div className="layer-info">
            <Layers className="w-4 h-4 text-green-400" />
            <span>Cụm Vùng</span>
          </div>
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={layers.clusters}
              onChange={() => onLayerToggle('clusters')}
            />
            <span className="toggle-slider"></span>
          </label>
        </div>

        <div className="layer-item">
          <div className="layer-info">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span>Cảnh Báo</span>
          </div>
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={layers.alerts}
              onChange={() => onLayerToggle('alerts')}
            />
            <span className="toggle-slider"></span>
          </label>
        </div>

        <div className="layer-item">
          <div className="layer-info">
            <Flame className="w-4 h-4 text-orange-400" />
            <span>Bản Đồ Nhiệt</span>
          </div>
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={layers.heatmap}
              onChange={() => onLayerToggle('heatmap')}
            />
            <span className="toggle-slider"></span>
          </label>
        </div>
      </div>

      <div className="layer-legend">
        <div className="legend-title">Chú Thích</div>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-dot bg-green-500"></div>
            <span>Bình thường</span>
          </div>
          <div className="legend-item">
            <div className="legend-dot bg-yellow-500"></div>
            <span>Cảnh báo</span>
          </div>
          <div className="legend-item">
            <div className="legend-dot bg-red-500"></div>
            <span>Nghiêm trọng</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapLayerControl;
