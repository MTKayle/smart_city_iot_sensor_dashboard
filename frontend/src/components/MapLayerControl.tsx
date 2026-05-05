/**
 * MapLayerControl Component
 * 
 * Provides layer visibility controls for the map:
 * - Sensor Layer (individual markers)
 * - Cluster Layer (grouped sensors)
 * - Heatmap Layer (intensity visualization)
 * - Alert Layer (problematic areas)
 * - District Boundaries
 */

import React from 'react';
import './MapLayerControl.css';

export interface LayerVisibility {
  sensors: boolean;
  clusters: boolean;
  heatmap: boolean;
  alerts: boolean;
  districts: boolean;
}

interface MapLayerControlProps {
  layers: LayerVisibility;
  onLayerToggle: (layer: keyof LayerVisibility) => void;
}

const MapLayerControl: React.FC<MapLayerControlProps> = ({ layers, onLayerToggle }) => {
  return (
    <div className="map-layer-control glass-panel">
      <h3 className="control-title">
        <span className="icon">🗺️</span>
        Map Layers
      </h3>
      
      <div className="layer-toggles">
        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={layers.sensors}
            onChange={() => onLayerToggle('sensors')}
          />
          <span className="toggle-slider"></span>
          <span className="layer-label">
            <span className="layer-icon">📍</span>
            Sensors
          </span>
        </label>

        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={layers.clusters}
            onChange={() => onLayerToggle('clusters')}
          />
          <span className="toggle-slider"></span>
          <span className="layer-label">
            <span className="layer-icon">🎯</span>
            Clusters
          </span>
        </label>

        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={layers.heatmap}
            onChange={() => onLayerToggle('heatmap')}
          />
          <span className="toggle-slider"></span>
          <span className="layer-label">
            <span className="layer-icon">🔥</span>
            Heatmap
          </span>
        </label>

        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={layers.alerts}
            onChange={() => onLayerToggle('alerts')}
          />
          <span className="toggle-slider"></span>
          <span className="layer-label">
            <span className="layer-icon">⚠️</span>
            Alerts
          </span>
        </label>

        <label className="layer-toggle">
          <input
            type="checkbox"
            checked={layers.districts}
            onChange={() => onLayerToggle('districts')}
          />
          <span className="toggle-slider"></span>
          <span className="layer-label">
            <span className="layer-icon">🏙️</span>
            Districts
          </span>
        </label>
      </div>
    </div>
  );
};

export default MapLayerControl;
