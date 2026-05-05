/**
 * Service exports for Smart City IoT Dashboard
 */

export {
  // Locations
  fetchLocations,
  fetchLocation,
  fetchLocationHierarchy,
  fetchLocationSensors,
  // Clusters
  fetchClusters,
  fetchCluster,
  fetchClusterSensors,
  fetchClusterTelemetry,
  fetchClusterHotspots,
  // Sensors
  fetchSensors,
  fetchSensorRegistry,
  fetchSensorById,
  fetchSensorCapabilities,
  fetchNearbySensors,
  fetchSensorHealth,
  // Telemetry / analytics
  fetchTelemetry,
  fetchAnalytics,
  // Alerts
  fetchAlerts,
  acknowledgeAlert,
  resolveAlert,
  // Leaderboard
  fetchLeaderboard,
  // Ops
  fetchPipelineMetrics,
  checkHealth,
  // Internals
  apiClient,
  ApiError,
} from './api';

export type {
  TelemetryQueryParams,
  AlertQueryParams,
  NearbySensorsResponse,
  SensorHealthResponse,
  HotspotMetric,
  HotspotCell,
  HotspotsResponse,
  PipelineMetrics,
} from './api';
