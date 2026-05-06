/**
 * Heatmap utilities — color ramps + IDW interpolation.
 *
 * Breakpoints follow established standards:
 *   PM2.5  → US EPA AQI (24-hour avg, µg/m³)
 *   CO2    → ASHRAE 62.1 + WHO indoor air quality (ppm)
 *   Noise  → WHO Environmental Noise Guidelines (dB)
 *   Temp   → human-comfort / heat-stress (°C, tropical bias for HCMC)
 *   Humid. → ASHRAE indoor comfort (%)
 */

import type { HeatmapMetric } from '../components/redesign/types';

export interface BreakpointStop {
  /** The metric value at which this stop applies. */
  value: number;
  /** RGB color (0-255 triplet). */
  color: [number, number, number];
  /** Human-readable label for legend. */
  label: string;
}

export interface MetricSpec {
  metric: HeatmapMetric;
  label: string;
  unit: string;
  /** Sorted ascending by `value`. The first stop is the floor; the last is the ceiling. */
  stops: BreakpointStop[];
  /** Sensible default radius (in metres) for IDW influence. */
  radiusMeters: number;
  /** Decimal places for display. */
  digits: number;
}

const RAMP_GREEN: [number, number, number] = [16, 185, 129]; // emerald-500
const RAMP_LIME: [number, number, number] = [132, 204, 22]; // lime-500
const RAMP_YELLOW: [number, number, number] = [234, 179, 8]; // yellow-500
const RAMP_ORANGE: [number, number, number] = [249, 115, 22]; // orange-500
const RAMP_RED: [number, number, number] = [239, 68, 68]; // red-500
const RAMP_MAROON: [number, number, number] = [136, 19, 55]; // dark crimson
const RAMP_BLUE: [number, number, number] = [59, 130, 246]; // blue-500
const RAMP_CYAN: [number, number, number] = [34, 211, 238]; // cyan-400

export const METRIC_SPECS: Record<HeatmapMetric, MetricSpec> = {
  // US EPA AQI breakpoints, mapped to PM2.5 µg/m³ midpoints.
  pm25: {
    metric: 'pm25',
    label: 'PM2.5',
    unit: 'µg/m³',
    radiusMeters: 1200,
    digits: 1,
    stops: [
      { value: 0,   color: RAMP_GREEN,  label: 'Tốt' },
      { value: 12,  color: RAMP_LIME,   label: 'TB' },
      { value: 35,  color: RAMP_YELLOW, label: 'Kém' },
      { value: 55,  color: RAMP_ORANGE, label: 'Xấu' },
      { value: 150, color: RAMP_RED,    label: 'Rất xấu' },
      { value: 250, color: RAMP_MAROON, label: 'Nguy hại' },
    ],
  },

  // Tropical comfort — HCMC is warm year-round. <22 cool, 22-28 comfortable.
  temp: {
    metric: 'temp',
    label: 'Nhiệt Độ',
    unit: '°C',
    radiusMeters: 1200,
    digits: 1,
    stops: [
      { value: 18, color: RAMP_BLUE,   label: 'Mát' },
      { value: 22, color: RAMP_GREEN,  label: 'Dễ chịu' },
      { value: 28, color: RAMP_YELLOW, label: 'Ấm' },
      { value: 32, color: RAMP_ORANGE, label: 'Nóng' },
      { value: 36, color: RAMP_RED,    label: 'Rất nóng' },
      { value: 40, color: RAMP_MAROON, label: 'Cực nóng' },
    ],
  },

  // ASHRAE 55 indoor comfort: 30-60% recommended.
  humidity: {
    metric: 'humidity',
    label: 'Độ Ẩm',
    unit: '%',
    radiusMeters: 1200,
    digits: 0,
    stops: [
      { value: 20, color: RAMP_ORANGE, label: 'Khô' },
      { value: 30, color: RAMP_YELLOW, label: 'Hơi khô' },
      { value: 45, color: RAMP_GREEN,  label: 'Dễ chịu' },
      { value: 65, color: RAMP_CYAN,   label: 'Ẩm' },
      { value: 85, color: RAMP_BLUE,   label: 'Rất ẩm' },
      { value: 100,color: RAMP_MAROON, label: 'Bão hòa' },
    ],
  },

  // ASHRAE 62.1 (1000 ppm threshold), WHO outdoor ~400-450 ppm.
  co2: {
    metric: 'co2',
    label: 'CO₂',
    unit: 'ppm',
    radiusMeters: 1200,
    digits: 0,
    stops: [
      { value: 400,  color: RAMP_GREEN,  label: 'Nền' },
      { value: 800,  color: RAMP_LIME,   label: 'Tốt' },
      { value: 1000, color: RAMP_YELLOW, label: 'Khá' },
      { value: 1500, color: RAMP_ORANGE, label: 'Kém' },
      { value: 2000, color: RAMP_RED,    label: 'Rất kém' },
      { value: 5000, color: RAMP_MAROON, label: 'Nguy hại' },
    ],
  },

  // WHO Environmental Noise Guidelines: <55 dB residential, >75 dB harmful.
  noise: {
    metric: 'noise',
    label: 'Tiếng Ồn',
    unit: 'dB',
    radiusMeters: 1200,
    digits: 0,
    stops: [
      { value: 30, color: RAMP_GREEN,  label: 'Yên' },
      { value: 45, color: RAMP_LIME,   label: 'Nhẹ' },
      { value: 55, color: RAMP_YELLOW, label: 'TB' },
      { value: 70, color: RAMP_ORANGE, label: 'Ồn' },
      { value: 85, color: RAMP_RED,    label: 'Rất ồn' },
      { value: 100,color: RAMP_MAROON, label: 'Có hại' },
    ],
  },
};

/**
 * Linearly interpolate the ramp at `value`. Returns rgba string with the given alpha.
 * Values below the first stop / above the last stop are clamped to the endpoint colors.
 */
export function rampColor(value: number, spec: MetricSpec, alpha = 1): string {
  const stops = spec.stops;
  if (value <= stops[0].value) {
    const [r, g, b] = stops[0].color;
    return `rgba(${r},${g},${b},${alpha})`;
  }
  const last = stops[stops.length - 1];
  if (value >= last.value) {
    const [r, g, b] = last.color;
    return `rgba(${r},${g},${b},${alpha})`;
  }
  for (let i = 0; i < stops.length - 1; i++) {
    const a = stops[i];
    const b = stops[i + 1];
    if (value >= a.value && value <= b.value) {
      const t = (value - a.value) / (b.value - a.value);
      const r = Math.round(a.color[0] + (b.color[0] - a.color[0]) * t);
      const g = Math.round(a.color[1] + (b.color[1] - a.color[1]) * t);
      const bl = Math.round(a.color[2] + (b.color[2] - a.color[2]) * t);
      return `rgba(${r},${g},${bl},${alpha})`;
    }
  }
  return `rgba(0,0,0,${alpha})`;
}

/**
 * Inverse Distance Weighting interpolation at a query point.
 *
 * @param queryX,queryY   - container-pixel coordinates of the query
 * @param sensors          - sensors with screen-pixel positions and metric values
 * @param maxRadiusPx      - influence radius in pixels (anything farther is ignored)
 * @param power            - IDW exponent, 2 is the standard choice
 * @returns interpolated value, or null if no sensor is within radius
 */
export function idw(
  queryX: number,
  queryY: number,
  sensors: ReadonlyArray<{ x: number; y: number; v: number }>,
  maxRadiusPx: number,
  power = 2,
): number | null {
  let weightedSum = 0;
  let weightTotal = 0;
  const r2 = maxRadiusPx * maxRadiusPx;

  for (let i = 0; i < sensors.length; i++) {
    const s = sensors[i];
    const dx = s.x - queryX;
    const dy = s.y - queryY;
    const d2 = dx * dx + dy * dy;
    if (d2 > r2) continue;
    if (d2 < 1) {
      // Right on top of a sensor — return its raw value to avoid divide-by-near-zero.
      return s.v;
    }
    const w = 1 / Math.pow(d2, power / 2);
    weightedSum += w * s.v;
    weightTotal += w;
  }

  if (weightTotal === 0) return null;
  return weightedSum / weightTotal;
}

/**
 * Convert a distance in meters to pixels at the given Leaflet zoom level
 * and latitude. Uses Web Mercator scale.
 *
 *   metres-per-pixel = (cos(lat) * 2π * 6378137) / (256 * 2^zoom)
 */
export function metersToPixels(meters: number, latDeg: number, zoom: number): number {
  const earthCircumference = 40075016.686; // metres
  const metresPerPixel =
    (Math.cos((latDeg * Math.PI) / 180) * earthCircumference) / (256 * Math.pow(2, zoom));
  return meters / metresPerPixel;
}
