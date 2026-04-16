/**
 * TypeScript type definitions for Smart City IoT Dashboard
 * 
 * These interfaces match the Pydantic models from the backend.
 * Requirements: 9.1, 9.2, 9.3, 9.4
 */

/**
 * Telemetry data model representing sensor measurements.
 * 
 * Validates:
 * - co2: Non-negative values (>= 0)
 * - noise: Values between 0-120 dB
 * - temperature: Values between -50°C and 60°C
 */
export interface Telemetry {
  sensorId: string;
  locationId: string;
  co2: number;
  noise: number;
  temperature: number;
  timestamp: string; // ISO8601 date string
}

/**
 * Location data model representing geographic hierarchy.
 * 
 * Supports three-level hierarchy: City > District > Ward
 */
export interface Location {
  locationId: string;
  name: string;
  parentId: string | null;
  type: "City" | "District" | "Ward";
}

/**
 * Sensor registry data model representing IoT device registration.
 */
export interface Sensor {
  sensorId: string;
  locationId: string;
  sensorType: "CO2" | "Noise" | "Temperature";
  registeredAt: string; // ISO8601 date string
}

/**
 * Alert data model representing threshold violations.
 * 
 * Alerts are generated when:
 * - CO2 > 1000 ppm (HIGH)
 * - Noise > 85 dB (HIGH)
 */
export interface Alert {
  alertId: string;
  sensorId: string;
  metricType: "CO2" | "Noise" | "Temperature";
  value: number;
  level: "LOW" | "MEDIUM" | "HIGH";
  createdAt: string; // ISO8601 date string
}

/**
 * Moving average data model for a single metric.
 * 
 * Calculates the average of the last N readings (where N = min(10, total_readings)).
 */
export interface MovingAverage {
  metric: string;
  values: number[];
  average: number;
  window_size: number;
}

/**
 * Analytics data model containing moving averages for all metrics.
 */
export interface Analytics {
  sensorId: string;
  co2_moving_avg: MovingAverage;
  noise_moving_avg: MovingAverage;
  temperature_moving_avg: MovingAverage;
}

/**
 * Leaderboard entry data model for location environmental quality ranking.
 * 
 * Clean Score calculation:
 * - normalized_CO2 = (avgCO2 / 2000) * 100
 * - normalized_Noise = (avgNoise / 100) * 100
 * - cleanScore = 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)
 */
export interface LeaderboardEntry {
  locationId: string;
  locationName: string;
  avgCO2: number;
  avgNoise: number;
  avgTemperature: number;
  cleanScore: number;
  rank: number;
}
