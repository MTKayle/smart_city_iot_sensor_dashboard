/**
 * Smooth Data Updates Utility
 * 
 * Provides functions to smooth realtime data updates to avoid sudden jumps
 * Inspired by b_VJzFHvTPZTm implementation
 */

/**
 * Generate a random value within a range
 */
export function randomInRange(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

/**
 * Smooth update a sensor value with bounded changes
 * Prevents sudden jumps by limiting the change amount
 * 
 * @param currentValue - Current sensor value
 * @param min - Minimum allowed value
 * @param max - Maximum allowed value
 * @param maxChange - Maximum change per update
 * @returns New smoothed value
 */
export function smoothUpdate(
  currentValue: number,
  min: number,
  max: number,
  maxChange: number
): number {
  const change = randomInRange(-maxChange, maxChange);
  const newValue = currentValue + change;
  return Math.max(min, Math.min(max, newValue));
}

/**
 * Smooth update for PM2.5 values
 */
export function smoothPM25(current: number): number {
  return Math.round(smoothUpdate(current, 5, 200, 5) * 10) / 10;
}

/**
 * Smooth update for temperature values (Celsius)
 */
export function smoothTemperature(current: number): number {
  return Math.round(smoothUpdate(current, 15, 40, 1) * 10) / 10;
}

/**
 * Smooth update for humidity values
 */
export function smoothHumidity(current: number): number {
  return Math.round(smoothUpdate(current, 20, 90, 2));
}

/**
 * Smooth update for CO2 values
 */
export function smoothCO2(current: number): number {
  return Math.round(smoothUpdate(current, 350, 2000, 30));
}

/**
 * Smooth update for noise values
 */
export function smoothNoise(current: number): number {
  return Math.round(smoothUpdate(current, 30, 100, 3));
}

/**
 * Calculate sensor status based on PM2.5 and CO2 levels
 */
export function calculateStatus(
  pm25: number,
  co2: number
): 'normal' | 'warning' | 'critical' {
  if (pm25 > 100 || co2 > 1500) return 'critical';
  if (pm25 > 50 || co2 > 1000) return 'warning';
  return 'normal';
}

/**
 * Apply smooth updates to telemetry data
 * This can be used to simulate smooth realtime updates
 */
export function applySmoothUpdates(telemetry: {
  pm25?: number;
  temperature?: number;
  humidity?: number;
  co2?: number;
  noise?: number;
}): typeof telemetry {
  return {
    ...telemetry,
    pm25: telemetry.pm25 !== undefined ? smoothPM25(telemetry.pm25) : undefined,
    temperature: telemetry.temperature !== undefined ? smoothTemperature(telemetry.temperature) : undefined,
    humidity: telemetry.humidity !== undefined ? smoothHumidity(telemetry.humidity) : undefined,
    co2: telemetry.co2 !== undefined ? smoothCO2(telemetry.co2) : undefined,
    noise: telemetry.noise !== undefined ? smoothNoise(telemetry.noise) : undefined,
  };
}
