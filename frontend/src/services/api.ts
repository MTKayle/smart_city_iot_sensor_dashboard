/**
 * API Client Service for Smart City IoT Dashboard (v2)
 * 
 * Provides functions to interact with the backend REST API.
 * Covers locations, clusters, sensor registry, telemetry, alerts, analytics, and leaderboard.
 *
 * Requirements: FR8.1, FR8.2, FR8.3, FR8.4, FR8.5, FR8.6
 */

import axios, { AxiosError } from 'axios';
import type { AxiosInstance } from 'axios';
import type {
  Location,
  Sensor,
  SensorCluster,
  SensorRegistry,
  SensorCapability,
  Telemetry,
  Alert,
  Analytics,
  ClusterAnalytics,
  LeaderboardEntry,
} from '../types';

// ============================================================================
// API Error
// ============================================================================

export class ApiError extends Error {
  statusCode?: number;
  details?: unknown;

  constructor(message: string, statusCode?: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

// ============================================================================
// Axios Client
// ============================================================================

const getBaseUrl = (): string =>
  import.meta.env.VITE_API_URL || 'http://localhost:8000';

const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: getBaseUrl(),
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
  });

  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response) {
        const statusCode = error.response.status;
        const message =
          (error.response.data as { detail?: string })?.detail || error.message;
        throw new ApiError(message, statusCode, error.response.data);
      } else if (error.request) {
        throw new ApiError(
          'No response from server. Please check your connection.',
          undefined,
          error,
        );
      } else {
        throw new ApiError(error.message, undefined, error);
      }
    },
  );

  return client;
};

const apiClient = createApiClient();

// ============================================================================
// Location API
// ============================================================================

/**
 * Fetch all locations in the hierarchy.
 */
export const fetchLocations = async (): Promise<Location[]> => {
  try {
    const response = await apiClient.get<Location[]>('/api/locations');
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to fetch locations', undefined, error);
  }
};

/**
 * Fetch a single location by ID.
 */
export const fetchLocation = async (locationId: string): Promise<Location> => {
  try {
    const response = await apiClient.get<Location>(
      `/api/locations/${locationId}`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch location ${locationId}`,
      undefined,
      error,
    );
  }
};

/**
 * Fetch full hierarchy for a location (parent chain + children).
 */
export const fetchLocationHierarchy = async (
  locationId: string,
): Promise<Location[]> => {
  try {
    const response = await apiClient.get<Location[]>(
      `/api/locations/${locationId}/hierarchy`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch location hierarchy for ${locationId}`,
      undefined,
      error,
    );
  }
};

/**
 * Fetch sensors registered under a location.
 */
export const fetchLocationSensors = async (
  locationId: string,
): Promise<SensorRegistry[]> => {
  try {
    const response = await apiClient.get<SensorRegistry[]>(
      `/api/locations/${locationId}/sensors`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch sensors for location ${locationId}`,
      undefined,
      error,
    );
  }
};

// ============================================================================
// Cluster API
// ============================================================================

/**
 * Fetch all clusters.
 */
export const fetchClusters = async (): Promise<SensorCluster[]> => {
  try {
    const response = await apiClient.get<SensorCluster[]>('/api/clusters');
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to fetch clusters', undefined, error);
  }
};

/**
 * Fetch a single cluster by ID.
 */
export const fetchCluster = async (
  clusterId: string,
): Promise<SensorCluster> => {
  try {
    const response = await apiClient.get<SensorCluster>(
      `/api/clusters/${clusterId}`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch cluster ${clusterId}`,
      undefined,
      error,
    );
  }
};

/**
 * Fetch sensors in a cluster.
 */
export const fetchClusterSensors = async (
  clusterId: string,
): Promise<SensorRegistry[]> => {
  try {
    const response = await apiClient.get<SensorRegistry[]>(
      `/api/clusters/${clusterId}/sensors`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch sensors for cluster ${clusterId}`,
      undefined,
      error,
    );
  }
};

/**
 * Fetch cluster-level aggregated telemetry/analytics.
 */
export const fetchClusterTelemetry = async (
  clusterId: string,
): Promise<ClusterAnalytics> => {
  try {
    const response = await apiClient.get<ClusterAnalytics>(
      `/api/clusters/${clusterId}/telemetry`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch cluster telemetry for ${clusterId}`,
      undefined,
      error,
    );
  }
};

export type HotspotMetric = 'co2' | 'noise' | 'pm25' | 'humidity' | 'temperature';

export interface HotspotCell {
  lat: number;
  lng: number;
  value: number;
  count?: number;
  [key: string]: unknown;
}

export interface HotspotsResponse {
  metric: string;
  threshold: number | null;
  count: number;
  hotspots: HotspotCell[];
}

/**
 * Detect pollution hotspots — backend returns grid cells, not cluster analytics.
 */
export const fetchClusterHotspots = async (
  metric: HotspotMetric = 'pm25',
  threshold?: number,
  gridKm: number = 1.0,
): Promise<HotspotsResponse> => {
  try {
    const params: Record<string, number | string> = { metric, grid_km: gridKm };
    if (threshold !== undefined) params.threshold = threshold;
    const response = await apiClient.get<HotspotsResponse>(
      '/api/clusters/hotspots',
      { params },
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to fetch cluster hotspots', undefined, error);
  }
};

// ============================================================================
// Sensor Registry API
// ============================================================================

/**
 * Fetch all registered sensors (legacy + v2 compatible).
 */
export const fetchSensors = async (
  locationId?: string,
): Promise<Sensor[]> => {
  try {
    const params = locationId ? { location_id: locationId } : {};
    const response = await apiClient.get<Sensor[]>('/api/sensors', { params });
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to fetch sensors', undefined, error);
  }
};

/**
 * Fetch v2 sensor registry entries.
 */
export const fetchSensorRegistry = async (
  locationId?: string,
): Promise<SensorRegistry[]> => {
  try {
    const params = locationId ? { location_id: locationId } : {};
    const response = await apiClient.get<SensorRegistry[]>('/api/sensors', {
      params,
    });
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to fetch sensor registry', undefined, error);
  }
};

/**
 * Fetch a single sensor by ID.
 */
export const fetchSensorById = async (
  sensorId: string,
): Promise<SensorRegistry> => {
  try {
    const response = await apiClient.get<SensorRegistry>(
      `/api/sensors/${sensorId}`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch sensor ${sensorId}`,
      undefined,
      error,
    );
  }
};

/**
 * Fetch sensor capabilities (metric types it can measure).
 */
export const fetchSensorCapabilities = async (
  sensorId: string,
): Promise<SensorCapability[]> => {
  try {
    const response = await apiClient.get<SensorCapability[]>(
      `/api/sensors/${sensorId}/capabilities`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch capabilities for sensor ${sensorId}`,
      undefined,
      error,
    );
  }
};

export interface NearbySensorsResponse {
  query: { lat: number; lng: number; radius_km: number };
  count: number;
  sensors: Array<SensorRegistry & { distance_km?: number }>;
}

/**
 * Find nearby sensors by GPS coordinates.
 *
 * Backend expects `radius_km` (not `radius`) and returns
 * `{ query, count, sensors[] }` — not a bare array.
 */
export const fetchNearbySensors = async (
  lat: number,
  lng: number,
  radiusKm: number = 1.0,
  limit: number = 20,
): Promise<NearbySensorsResponse> => {
  try {
    const response = await apiClient.get<NearbySensorsResponse>(
      '/api/sensors/nearby',
      { params: { lat, lng, radius_km: radiusKm, limit } },
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to fetch nearby sensors', undefined, error);
  }
};

export interface SensorHealthResponse {
  sensorId: string;
  status: string;
  lastMaintenance: string;
  nextMaintenance: string;
  healthLogs: Array<Record<string, unknown>>;
}

/**
 * Fetch sensor health log entries.
 */
export const fetchSensorHealth = async (
  sensorId: string,
  limit: number = 10,
): Promise<SensorHealthResponse> => {
  try {
    const response = await apiClient.get<SensorHealthResponse>(
      `/api/sensors/${sensorId}/health`,
      { params: { limit } },
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch health for sensor ${sensorId}`,
      undefined,
      error,
    );
  }
};

// ============================================================================
// Telemetry API
// ============================================================================

export interface TelemetryQueryParams {
  startTime?: string;
  endTime?: string;
  limit?: number;
  /** Aggregation bucket size in minutes. Required for long ranges so the response stays under the row limit. */
  bucketMinutes?: number;
}

/**
 * Fetch telemetry data for a specific sensor.
 */
export const fetchTelemetry = async (
  sensorId: string,
  params?: TelemetryQueryParams,
): Promise<Telemetry[]> => {
  try {
    const queryParams: Record<string, string | number> = {};
    if (params?.startTime) queryParams.start_time = params.startTime;
    if (params?.endTime) queryParams.end_time = params.endTime;
    if (params?.limit) queryParams.limit = params.limit;
    if (params?.bucketMinutes) queryParams.bucket_minutes = params.bucketMinutes;

    const response = await apiClient.get<Telemetry[]>(
      `/api/telemetry/${sensorId}`,
      { params: queryParams },
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch telemetry for sensor ${sensorId}`,
      undefined,
      error,
    );
  }
};

/**
 * One row of the Oracle TELEMETRY_SUMMARY table — pre-aggregated metrics
 * for a (location, granularity, time-bucket) tuple.
 */
export interface LocationHistoryPoint {
  timeBucket: string;
  avgPM25: number | null;
  maxPM25: number | null;
  avgCO2: number | null;
  maxCO2: number | null;
  minCO2: number | null;
  avgNoise: number | null;
  maxNoise: number | null;
  minNoise: number | null;
  avgTemperature: number | null;
  maxTemperature: number | null;
  minTemperature: number | null;
  avgHumidity: number | null;
  aqi: number | null;
  cleanScore: number | null;
  dataPoints: number;
}

export type HistoryGranularity = 'HOURLY' | 'DAILY' | 'WEEKLY';

/**
 * Fetch Oracle TELEMETRY_SUMMARY rows for a location at the given granularity.
 *
 * Used by the Analytics & Compare views — these are *real* aggregated values
 * from Oracle, not synthetic mock data.
 */
export const fetchLocationHistory = async (
  locationId: string,
  params: {
    granularity: HistoryGranularity;
    startTime?: string;
    endTime?: string;
  },
): Promise<LocationHistoryPoint[]> => {
  try {
    const queryParams: Record<string, string> = {
      granularity: params.granularity,
    };
    if (params.startTime) queryParams.start_time = params.startTime;
    if (params.endTime) queryParams.end_time = params.endTime;
    const response = await apiClient.get<LocationHistoryPoint[]>(
      `/api/locations/${locationId}/history`,
      { params: queryParams },
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch history for location ${locationId}`,
      undefined,
      error,
    );
  }
};

// ============================================================================
// Analytics API
// ============================================================================

/**
 * Fetch analytics (moving averages + AQI) for a specific sensor.
 */
export const fetchAnalytics = async (sensorId: string): Promise<Analytics> => {
  try {
    const response = await apiClient.get<Analytics>(
      `/api/sensors/${sensorId}/analytics`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to fetch analytics for sensor ${sensorId}`,
      undefined,
      error,
    );
  }
};

// ============================================================================
// Alert API
// ============================================================================

export interface AlertQueryParams {
  level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  alertType?: 'THRESHOLD' | 'PREDICTIVE' | 'ANOMALY' | 'CLUSTER';
  locationId?: string;
  status?: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  limit?: number;
}

/**
 * Fetch recent alerts with optional filters.
 */
export const fetchAlerts = async (
  params?: AlertQueryParams,
): Promise<Alert[]> => {
  try {
    const queryParams: Record<string, string | number> = {};
    if (params?.level) queryParams.level = params.level;
    if (params?.alertType) queryParams.alert_type = params.alertType;
    if (params?.locationId) queryParams.location_id = params.locationId;
    if (params?.status) queryParams.status = params.status;
    if (params?.limit) queryParams.limit = params.limit;

    const response = await apiClient.get<Alert[]>('/api/alerts', {
      params: queryParams,
    });
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to fetch alerts', undefined, error);
  }
};

// ============================================================================
// Leaderboard API
// ============================================================================

export interface LeaderboardRefreshResult {
  refreshedAt: string;
  granularity: 'HOURLY' | 'DAILY' | 'WEEKLY';
  days: number;
  entries: LeaderboardEntry[];
}

/**
 * Force-refresh: triggers the MongoDB → Oracle aggregator on the rolling
 * window then returns the freshly-aggregated leaderboard. Use this from the
 * UI's "Làm Mới" button so the user gets up-to-the-minute data without
 * waiting for the next scheduled run.
 */
export const triggerLeaderboardRefresh = async (
  granularity: 'HOURLY' | 'DAILY' | 'WEEKLY' = 'HOURLY',
  days = 2,
): Promise<LeaderboardRefreshResult> => {
  try {
    const response = await apiClient.post<LeaderboardRefreshResult>(
      '/api/leaderboard/refresh',
      null,
      { params: { granularity, days } },
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to refresh leaderboard', undefined, error);
  }
};

/**
 * Fetch leaderboard of locations ranked by environmental quality.
 */
export const fetchLeaderboard = async (
  limit?: number,
): Promise<LeaderboardEntry[]> => {
  try {
    const params = limit ? { limit } : {};
    const response = await apiClient.get<LeaderboardEntry[]>(
      '/api/leaderboard',
      { params },
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to fetch leaderboard', undefined, error);
  }
};

/**
 * Acknowledge an alert (lifecycle: OPEN → ACKNOWLEDGED).
 */
export const acknowledgeAlert = async (alertId: string): Promise<Alert> => {
  try {
    const response = await apiClient.post<Alert>(
      `/api/alerts/${alertId}/acknowledge`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to acknowledge alert ${alertId}`,
      undefined,
      error,
    );
  }
};

/**
 * Resolve an alert (lifecycle: ACKNOWLEDGED → RESOLVED).
 */
export const resolveAlert = async (alertId: string): Promise<Alert> => {
  try {
    const response = await apiClient.post<Alert>(
      `/api/alerts/${alertId}/resolve`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to resolve alert ${alertId}`,
      undefined,
      error,
    );
  }
};

// ============================================================================
// Pipeline / Ops
// ============================================================================

export interface PipelineMetrics {
  enqueued: number;
  dropped: number;
  processed: number;
  batches: number;
  mongo_inserts: number;
  alerts_created: number;
  ws_broadcasts: number;
  acked: number;
  redelivered: number;
  stream_length: number;
  pending_messages: number;
  workers_active: number;
}

/**
 * Fetch worker-pool / Redis Stream pipeline metrics.
 */
export const fetchPipelineMetrics = async (): Promise<PipelineMetrics> => {
  try {
    const response = await apiClient.get<PipelineMetrics>('/pipeline/metrics');
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to fetch pipeline metrics', undefined, error);
  }
};

// ============================================================================
// Health Check
// ============================================================================

export const checkHealth = async (): Promise<{
  status: string;
  service: string;
}> => {
  try {
    const response = await apiClient.get<{ status: string; service: string }>(
      '/api/health',
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Failed to check API health', undefined, error);
  }
};

// Export the API client instance for advanced usage
export { apiClient };
