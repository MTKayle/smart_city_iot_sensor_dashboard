/**
 * TypeScript type definitions for Smart City IoT Dashboard (v2)
 * 
 * These interfaces match the Pydantic models from the backend v2 schema.
 * Supports multi-metric combo sensors, spatial clustering, and advanced alerts.
 * Requirements: FR3.1, FR3.2, FR3.3, FR3.4, FR3.5, FR3.6
 */

// ============================================================================
// Alert Enums
// ============================================================================

export type AlertType = 'THRESHOLD' | 'PREDICTIVE' | 'ANOMALY' | 'CLUSTER';
export type AlertSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';

// ============================================================================
// Telemetry Types
// ============================================================================

/**
 * Sensor measurement data (combo sensor — multiple metrics per reading)
 */
export interface TelemetryData {
  co2?: number | null;
  noise?: number | null;
  temperature?: number | null;
  pm25?: number | null;
  humidity?: number | null;
}

/**
 * GeoJSON Point for spatial queries
 */
export interface GeoLocation {
  type: string;
  coordinates: [number, number]; // [longitude, latitude]
}

/**
 * Device health / data quality metrics
 */
export interface DataQuality {
  batteryLevel?: number | null;
  signalStrength?: number | null;
}

/**
 * Enhanced Telemetry document (v2 schema).
 *
 * Multi-metric combo reading with geolocation, clustering, and device health.
 */
export interface Telemetry {
  sensorId: string;
  locationId: string;
  clusterId?: string | null;

  data: TelemetryData;
  location: GeoLocation;
  quality?: DataQuality | null;

  timestamp: string;   // ISO 8601
  receivedAt?: string; // ISO 8601
  expireAt?: string;   // ISO 8601

  // ── Legacy flat-field aliases (for backward compatibility) ──
  co2?: number;
  noise?: number;
  temperature?: number;
  pm25?: number;
  humidity?: number;
}

// ============================================================================
// Location Types (Oracle — City/District/Ward hierarchy)
// ============================================================================

/**
 * Location in the three-level hierarchy: City > District > Ward
 */
export interface Location {
  locationId: string;
  name: string;
  parentId: string | null;
  type: 'City' | 'District' | 'Ward';

  centerLat?: number | null;
  centerLng?: number | null;
  geometry?: string | null;  // GeoJSON
  area?: number | null;      // km²
  population?: number | null;

  createdAt?: string;
  updatedAt?: string;
}

// ============================================================================
// Sensor Cluster (Oracle)
// ============================================================================

/**
 * Spatial cluster grouping co-located sensors for aggregate analysis.
 */
export interface SensorCluster {
  clusterId: string;
  locationId: string;

  clusterName?: string | null;
  centerLat: number;
  centerLng: number;
  radius: number; // meters

  sensorCount: number;
  algorithm?: string | null; // GRID | DBSCAN | KMEANS

  createdAt?: string;
  updatedAt?: string;
}

// ============================================================================
// Sensor Registry (Oracle)
// ============================================================================

/**
 * Enhanced sensor registration with GPS position and maintenance info.
 */
export interface SensorRegistry {
  sensorId: string;
  locationId: string;
  clusterId?: string | null;

  latitude: number;
  longitude: number;
  altitude?: number | null;

  sensorModel?: string | null;
  firmwareVersion?: string | null;
  status: 'Active' | 'Offline' | 'Maintenance' | 'Decommissioned';

  installDate: string;         // date
  lastMaintenance?: string | null;
  nextMaintenance?: string | null;
  registeredAt?: string;
  updatedAt?: string;
}

// ============================================================================
// Sensor Capability (Oracle)
// ============================================================================

/**
 * What a sensor can measure (one row per metric type).
 */
export interface SensorCapability {
  capabilityId: string;
  sensorId: string;
  metricType: string; // CO2 | Noise | Temperature | PM2.5 | Humidity
  unit: string;       // ppm | dB | °C | μg/m³ | %

  minRange?: number | null;
  maxRange?: number | null;
  accuracy?: number | null;

  calibrationDate?: string | null;
  nextCalibration?: string | null;
  isActive: boolean;
}

// ============================================================================
// Legacy Sensor Type (backward compat)
// ============================================================================

export interface Sensor {
  sensorId: string;
  locationId: string;
  sensorType: 'CO2' | 'Noise' | 'Temperature';
  registeredAt: string;
}

// ============================================================================
// Alert (v2 — supports THRESHOLD / PREDICTIVE / ANOMALY / CLUSTER)
// ============================================================================

/**
 * Alert document with extended type system, confidence scoring,
 * and lifecycle status tracking.
 */
export interface Alert {
  alertId: string;
  sensorId?: string | null;
  clusterId?: string | null;
  locationId: string;

  alertType: AlertType;
  metricType: string;         // CO2, Noise, Temperature, PM2.5, Humidity

  value: number;
  threshold?: number | null;
  predictedValue?: number | null;
  confidenceScore?: number | null; // 0 – 1

  severity: AlertSeverity;
  status: AlertStatus;
  message?: string | null;

  createdAt: string;             // ISO 8601
  acknowledgedAt?: string | null;
  resolvedAt?: string | null;

  // ── Legacy aliases ──
  level?: AlertSeverity; // backward compat
}

// ============================================================================
// Analytics
// ============================================================================

/**
 * Moving average data model for a single metric.
 */
export interface MovingAverage {
  metric: string;
  values: number[];
  average: number;
  window_size: number;
}

/**
 * Per-sensor analytics with moving averages for all 5 metrics + AQI.
 */
export interface Analytics {
  sensorId: string;
  co2_moving_avg: MovingAverage;
  noise_moving_avg: MovingAverage;
  temperature_moving_avg: MovingAverage;
  pm25_moving_avg?: MovingAverage | null;
  humidity_moving_avg?: MovingAverage | null;
  aqi?: number | null;
  aqi_category?: string | null;
}

/**
 * Cluster-level aggregated analytics.
 */
export interface ClusterAnalytics {
  clusterId: string;
  clusterName?: string | null;
  locationId?: string | null;
  sensorCount: number;
  readingCount: number;

  avgCO2?: number | null;
  avgNoise?: number | null;
  avgTemperature?: number | null;
  avgPM25?: number | null;
  avgHumidity?: number | null;
  aqi?: number | null;
  aqi_category?: string | null;
  cleanScore?: number | null;
}

// ============================================================================
// Leaderboard
// ============================================================================

/**
 * Leaderboard entry with extended metrics (PM2.5, Humidity, AQI).
 *
 * cleanScore = 100 - (normalized_CO2 * 0.30 + normalized_Noise * 0.30 + normalized_PM25 * 0.40)
 */
export interface LeaderboardEntry {
  locationId: string;
  locationName: string;
  avgCO2: number;
  avgNoise: number;
  avgTemperature: number;
  avgPM25?: number | null;
  avgHumidity?: number | null;
  aqi?: number | null;
  aqi_category?: string | null;
  cleanScore: number;
  rank: number;
}
