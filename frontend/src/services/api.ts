/**
 * API Client Service for Smart City IoT Dashboard
 * 
 * This module provides functions to interact with the backend REST API.
 * Uses axios for HTTP requests with error handling and response validation.
 * 
 * Requirements: 9.1, 9.2, 9.3, 9.4
 */

import axios, { AxiosError } from 'axios';
import type { AxiosInstance } from 'axios';
import type {
  Location,
  Sensor,
  Telemetry,
  Alert,
  Analytics,
  LeaderboardEntry,
} from '../types';

/**
 * API Error class for structured error handling
 */
export class ApiError extends Error {
  statusCode?: number;
  details?: unknown;

  constructor(
    message: string,
    statusCode?: number,
    details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

/**
 * Get base URL from environment variable or default to localhost
 */
const getBaseUrl = (): string => {
  // Vite uses import.meta.env for environment variables
  return import.meta.env.VITE_API_URL || 'http://localhost:8000';
};

/**
 * Create axios instance with base configuration
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: getBaseUrl(),
    timeout: 30000, // 30 second timeout
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response) {
        // Server responded with error status
        const statusCode = error.response.status;
        const message = (error.response.data as { detail?: string })?.detail || error.message;
        throw new ApiError(message, statusCode, error.response.data);
      } else if (error.request) {
        // Request made but no response received
        throw new ApiError('No response from server. Please check your connection.', undefined, error);
      } else {
        // Error setting up the request
        throw new ApiError(error.message, undefined, error);
      }
    }
  );

  return client;
};

// Create singleton API client instance
const apiClient = createApiClient();

/**
 * Fetch all locations in the hierarchy.
 * 
 * Retrieves the complete location hierarchy (City > District > Ward)
 * with parent-child relationships.
 * 
 * @returns Promise<Location[]> - Array of all locations
 * @throws ApiError - If request fails
 * 
 * Validates: Requirements 9.1, 1.3
 */
export const fetchLocations = async (): Promise<Location[]> => {
  try {
    const response = await apiClient.get<Location[]>('/api/locations');
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Failed to fetch locations', undefined, error);
  }
};

/**
 * Fetch all registered sensors with location information.
 * 
 * Retrieves sensors with their location hierarchy information.
 * Optionally filters by location ID.
 * 
 * @param locationId - Optional location filter
 * @returns Promise<Sensor[]> - Array of registered sensors
 * @throws ApiError - If request fails
 * 
 * Validates: Requirements 9.2, 2.4
 */
export const fetchSensors = async (locationId?: string): Promise<Sensor[]> => {
  try {
    const params = locationId ? { location_id: locationId } : {};
    const response = await apiClient.get<Sensor[]>('/api/sensors', { params });
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Failed to fetch sensors', undefined, error);
  }
};

/**
 * Telemetry query parameters
 */
export interface TelemetryQueryParams {
  startTime?: string; // ISO 8601 format
  endTime?: string; // ISO 8601 format
  limit?: number; // Max records to return (default: 100, max: 1000)
}

/**
 * Fetch telemetry data for a specific sensor.
 * 
 * Retrieves telemetry data with optional time range filter.
 * Defaults to last 24 hours if no time range specified.
 * 
 * @param sensorId - Sensor identifier
 * @param params - Optional query parameters (time range, limit)
 * @returns Promise<Telemetry[]> - Array of telemetry records ordered by timestamp descending
 * @throws ApiError - If request fails or parameters are invalid
 * 
 * Validates: Requirement 9.3
 */
export const fetchTelemetry = async (
  sensorId: string,
  params?: TelemetryQueryParams
): Promise<Telemetry[]> => {
  try {
    const queryParams: Record<string, string | number> = {};
    
    if (params?.startTime) {
      queryParams.start_time = params.startTime;
    }
    if (params?.endTime) {
      queryParams.end_time = params.endTime;
    }
    if (params?.limit) {
      queryParams.limit = params.limit;
    }

    const response = await apiClient.get<Telemetry[]>(
      `/api/telemetry/${sensorId}`,
      { params: queryParams }
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(`Failed to fetch telemetry for sensor ${sensorId}`, undefined, error);
  }
};

/**
 * Fetch analytics (moving averages) for a specific sensor.
 * 
 * Retrieves moving averages for the last 10 telemetry readings
 * for CO2, Noise, and Temperature metrics.
 * 
 * @param sensorId - Sensor identifier
 * @returns Promise<Analytics> - Analytics data with moving averages
 * @throws ApiError - If request fails or sensor has no data
 * 
 * Validates: Requirement 7.4
 */
export const fetchAnalytics = async (sensorId: string): Promise<Analytics> => {
  try {
    const response = await apiClient.get<Analytics>(
      `/api/sensors/${sensorId}/analytics`
    );
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(`Failed to fetch analytics for sensor ${sensorId}`, undefined, error);
  }
};

/**
 * Alert query parameters
 */
export interface AlertQueryParams {
  level?: 'LOW' | 'MEDIUM' | 'HIGH'; // Alert level filter
  locationId?: string; // Location ID filter
  limit?: number; // Max alerts to return (default: 100, max: 1000)
}

/**
 * Fetch recent alerts with optional filters.
 * 
 * Retrieves alerts ordered by creation time descending.
 * Supports filtering by alert level and location.
 * 
 * @param params - Optional query parameters (level, location, limit)
 * @returns Promise<Alert[]> - Array of recent alerts
 * @throws ApiError - If request fails or parameters are invalid
 * 
 * Validates: Requirement 9.4
 */
export const fetchAlerts = async (params?: AlertQueryParams): Promise<Alert[]> => {
  try {
    const queryParams: Record<string, string | number> = {};
    
    if (params?.level) {
      queryParams.level = params.level;
    }
    if (params?.locationId) {
      queryParams.location_id = params.locationId;
    }
    if (params?.limit) {
      queryParams.limit = params.limit;
    }

    const response = await apiClient.get<Alert[]>('/api/alerts', { params: queryParams });
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Failed to fetch alerts', undefined, error);
  }
};

/**
 * Fetch leaderboard of locations ranked by environmental quality.
 * 
 * Retrieves locations ordered by Clean Score descending
 * (highest score = cleanest location).
 * 
 * @param limit - Maximum number of entries to return (default: 100, max: 1000)
 * @returns Promise<LeaderboardEntry[]> - Array of leaderboard entries with rank numbers
 * @throws ApiError - If request fails
 * 
 * Validates: Requirement 8.4
 */
export const fetchLeaderboard = async (limit?: number): Promise<LeaderboardEntry[]> => {
  try {
    const params = limit ? { limit } : {};
    const response = await apiClient.get<LeaderboardEntry[]>('/api/leaderboard', { params });
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Failed to fetch leaderboard', undefined, error);
  }
};

/**
 * Health check endpoint to verify API connectivity.
 * 
 * @returns Promise<{ status: string; service: string }> - Health status
 * @throws ApiError - If request fails
 */
export const checkHealth = async (): Promise<{ status: string; service: string }> => {
  try {
    const response = await apiClient.get<{ status: string; service: string }>('/api/health');
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Failed to check API health', undefined, error);
  }
};

// Export the API client instance for advanced usage
export { apiClient };
