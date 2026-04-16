/**
 * Service exports for Smart City IoT Dashboard
 */

export {
  fetchLocations,
  fetchSensors,
  fetchTelemetry,
  fetchAnalytics,
  fetchAlerts,
  fetchLeaderboard,
  checkHealth,
  apiClient,
  ApiError,
} from './api';

export type {
  TelemetryQueryParams,
  AlertQueryParams,
} from './api';
