/**
 * Telemetry helpers — bridges backend nested model with UI flat reads.
 *
 * Backend WebSocket broadcasts `Telemetry` with nested `data.{co2,pm25,...}`,
 * but most UI components read `telemetry.pm25` / `telemetry.co2` etc. directly.
 * REST `/api/telemetry/{id}` already returns flat shape via `_doc_to_telemetry`,
 * so we mirror that on the WS side.
 *
 * Also computes AQI from PM2.5 (backend WS payload doesn't include AQI).
 */

import type { Telemetry } from '../types';

/**
 * EPA PM2.5 → AQI piecewise linear interpolation.
 * Mirror of backend `app/utils/aqi.py:calculate_aqi`.
 */
export function calculateAQI(pm25: number | null | undefined): {
  aqi: number;
  category: string;
} | null {
  if (pm25 === null || pm25 === undefined || isNaN(pm25) || pm25 < 0) {
    return null;
  }

  const breakpoints: Array<[number, number, number, number, string]> = [
    [0.0, 12.0, 0, 50, 'Good'],
    [12.1, 35.4, 51, 100, 'Moderate'],
    [35.5, 55.4, 101, 150, 'Unhealthy for Sensitive Groups'],
    [55.5, 150.4, 151, 200, 'Unhealthy'],
    [150.5, 250.4, 201, 300, 'Very Unhealthy'],
    [250.5, 500.4, 301, 500, 'Hazardous'],
  ];

  const c = Math.min(pm25, 500.4);
  const cTrunc = Math.trunc(c * 10) / 10;

  for (const [cLow, cHigh, iLow, iHigh, category] of breakpoints) {
    if (cTrunc >= cLow && cTrunc <= cHigh) {
      const aqi = ((iHigh - iLow) / (cHigh - cLow)) * (cTrunc - cLow) + iLow;
      return { aqi: Math.round(aqi), category };
    }
  }
  return { aqi: 500, category: 'Hazardous' };
}

/**
 * Take a raw telemetry payload (nested OR flat) and return a flat-augmented
 * version that satisfies both reading patterns.
 *
 * After calling this:
 *   t.pm25 === t.data?.pm25 (when present)
 *   t.aqi  === computed value
 */
export function normalizeTelemetry(raw: Telemetry): Telemetry {
  const nested = raw.data ?? {};

  // Coalesce nested → flat. Prefer existing flat value if backend already provided one.
  const co2 = raw.co2 ?? nested.co2 ?? undefined;
  const noise = raw.noise ?? nested.noise ?? undefined;
  const temperature = raw.temperature ?? nested.temperature ?? undefined;
  const pm25 = raw.pm25 ?? nested.pm25 ?? undefined;
  const humidity = raw.humidity ?? nested.humidity ?? undefined;

  const aqiResult = pm25 !== undefined && pm25 !== null ? calculateAQI(pm25) : null;

  return {
    ...raw,
    // Mirror nested → flat for UI components that read directly.
    co2: co2 ?? undefined,
    noise: noise ?? undefined,
    temperature: temperature ?? undefined,
    pm25: pm25 ?? undefined,
    humidity: humidity ?? undefined,
    // Keep nested data intact so chart-style consumers still work.
    data: {
      co2: co2 ?? null,
      noise: noise ?? null,
      temperature: temperature ?? null,
      pm25: pm25 ?? null,
      humidity: humidity ?? null,
    },
    // Derived AQI (backend WS payload doesn't carry this).
    aqi: aqiResult?.aqi ?? raw.aqi,
    aqi_category: aqiResult?.category ?? raw.aqi_category,
  };
}

/**
 * Classify sensor status based on PM2.5 and CO2 thresholds.
 * Used by the redesign Sensors / Map / Analytics views.
 */
export function classifySensorStatus(
  pm25: number | null | undefined,
  co2: number | null | undefined,
): 'normal' | 'warning' | 'critical' {
  const p = pm25 ?? 0;
  const c = co2 ?? 0;
  if (p >= 100 || c >= 2000) return 'critical';
  if (p >= 50 || c >= 1000) return 'warning';
  return 'normal';
}
