// Common types for redesign components

export type ViewType = 'dashboard' | 'map' | 'sensors' | 'clusters' | 'alerts' | 'analytics' | 'leaderboard' | 'settings';

export type SensorStatus = 'normal' | 'warning' | 'critical';

export interface Sensor {
  id: string;
  name: string;
  lat: number;
  lng: number;
  pm25: number;
  temp: number;
  humidity: number;
  co2: number;
  noise: number;
  battery: number;
  signal: number;
  status: SensorStatus;
  lastUpdate: string;
}

export interface Cluster {
  id: string;
  lat: number;
  lng: number;
  count: number;
  avgPm25: number;
  avgTemp: number;
  status: SensorStatus;
}

export interface Alert {
  id: number;
  title: string;
  location: string;
  time: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  type: 'threshold' | 'predictive' | 'anomaly';
  metric: string;
  value: number;
  threshold: number;
}

export type HeatmapMetric = 'pm25' | 'temp' | 'humidity' | 'co2' | 'noise';

/**
 * One-shot navigation request to focus the map on a coordinate.
 * The MapView consumes it on render, animates flyTo, then asks the
 * parent to clear it via `onFlyComplete`.
 */
export interface MapFocusTarget {
  lat: number;
  lng: number;
  zoom: number;
  /** Optional hint for the cluster panel that should auto-open after focusing. */
  clusterId?: string;
  /** Optional sensor ID — when set, the sensor detail panel opens automatically
      and the marker becomes the camera anchor. */
  sensorId?: string;
}

export interface MapLayers {
  sensors: boolean;
  clusters: boolean;
  alerts: boolean;
  heatmap: boolean;
}
