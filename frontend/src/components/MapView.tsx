/**
 * MapView Component — HCMC District Map with real-time sensor data
 *
 * Renders MapLibre GL JS map with:
 * - District boundary polygons (color-coded by threshold status)
 * - District border lines
 * - Center markers with hover tooltips (live CO2, Noise, Temp)
 * - Pulsing warning badges on districts exceeding thresholds
 * - Click to open district detail panel
 *
 * Requirements: 11.1–11.5
 */

import { useEffect, useRef, useState, useMemo } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { Sensor, Location, Alert, Telemetry } from '../types';
import {
  HCMC_DISTRICTS, HCMC_GEOJSON, THRESHOLDS,
  type DistrictData, type DistrictMetrics, type DistrictStatus,
  getDistrictFillColor, getDistrictBorderColor,
} from '../data/hcmcDistricts';
import DistrictDetailPanel from './DistrictDetailPanel';

export interface MapViewProps {
  sensors: Sensor[];
  locations: Location[];
  alerts: Alert[];
  telemetry: Record<string, Telemetry>;
  center?: [number, number];
  zoom?: number;
  styleUrl?: string;
}

const DEFAULT_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

/**
 * Compute aggregated metrics for a district from real-time telemetry.
 */
const computeDistrictMetrics = (
  district: DistrictData,
  telemetry: Record<string, Telemetry>,
): DistrictMetrics => {
  let co2Sum = 0, noiseSum = 0, tempSum = 0;
  let co2Count = 0, noiseCount = 0, tempCount = 0;
  const alerts: string[] = [];

  for (const ward of district.wards) {
    for (const sensor of ward.sensors) {
      const t = telemetry[sensor.id];
      if (!t) continue;
      if (sensor.type === 'CO2')         { co2Sum += t.co2;         co2Count++; }
      if (sensor.type === 'Noise')       { noiseSum += t.noise;     noiseCount++; }
      if (sensor.type === 'Temperature') { tempSum += t.temperature; tempCount++; }
    }
  }

  const avgCO2  = co2Count   > 0 ? co2Sum / co2Count     : null;
  const avgNoise = noiseCount > 0 ? noiseSum / noiseCount : null;
  const avgTemp  = tempCount  > 0 ? tempSum / tempCount   : null;

  // Determine status
  let status: DistrictStatus = 'gray';
  if (co2Count > 0 || noiseCount > 0 || tempCount > 0) {
    status = 'green';
    if (avgCO2 !== null && avgCO2 >= THRESHOLDS.co2.warning)           { status = 'yellow'; alerts.push(THRESHOLDS.co2.label); }
    if (avgNoise !== null && avgNoise >= THRESHOLDS.noise.warning)      { status = 'yellow'; alerts.push(THRESHOLDS.noise.label); }
    if (avgTemp !== null && avgTemp >= THRESHOLDS.temperature.warning)  { status = 'yellow'; alerts.push(THRESHOLDS.temperature.label); }
    if (avgCO2 !== null && avgCO2 >= THRESHOLDS.co2.danger)            { status = 'red'; }
    if (avgNoise !== null && avgNoise >= THRESHOLDS.noise.danger)       { status = 'red'; }
    if (avgTemp !== null && avgTemp >= THRESHOLDS.temperature.danger)   { status = 'red'; }
  }

  return { avgCO2, avgNoise, avgTemperature: avgTemp, status, alerts };
};

/**
 * Build a tooltip HTML string for a district.
 */
const buildTooltipHTML = (district: DistrictData, metrics: DistrictMetrics): string => {
  const val = (v: number | null, unit: string) =>
    v !== null ? `${v.toFixed(1)} ${unit}` : '—';

  const co2Class = metrics.avgCO2 !== null && metrics.avgCO2 >= THRESHOLDS.co2.danger ? 'danger'
    : metrics.avgCO2 !== null && metrics.avgCO2 >= THRESHOLDS.co2.warning ? 'warning' : 'ok';
  const noiseClass = metrics.avgNoise !== null && metrics.avgNoise >= THRESHOLDS.noise.danger ? 'danger'
    : metrics.avgNoise !== null && metrics.avgNoise >= THRESHOLDS.noise.warning ? 'warning' : 'ok';
  const tempClass = metrics.avgTemperature !== null && metrics.avgTemperature >= THRESHOLDS.temperature.danger ? 'danger'
    : metrics.avgTemperature !== null && metrics.avgTemperature >= THRESHOLDS.temperature.warning ? 'warning' : 'ok';

  return `
    <div class="district-tooltip">
      <div class="dt-header">${district.name}</div>
      <div class="dt-row"><span class="dt-icon">🌫️</span><span class="dt-label">CO₂</span><span class="dt-value ${co2Class}">${val(metrics.avgCO2, 'ppm')}</span></div>
      <div class="dt-row"><span class="dt-icon">🔊</span><span class="dt-label">Tiếng ồn</span><span class="dt-value ${noiseClass}">${val(metrics.avgNoise, 'dB')}</span></div>
      <div class="dt-row"><span class="dt-icon">🌡️</span><span class="dt-label">Nhiệt độ</span><span class="dt-value ${tempClass}">${val(metrics.avgTemperature, '°C')}</span></div>
      <div class="dt-footer">Di chuột = xem tổng · Click = chi tiết</div>
    </div>
  `;
};

export const MapView: React.FC<MapViewProps> = ({
  sensors: _sensors,
  locations: _locations,
  alerts: _alerts,
  telemetry,
  center = [106.6970, 10.7900],
  zoom = 12,
  styleUrl = import.meta.env.VITE_MAP_STYLE_URL || DEFAULT_STYLE,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<Map<string, HTMLDivElement>>(new Map());
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [selectedDistrict, setSelectedDistrict] = useState<DistrictData | null>(null);

  // Compute all district metrics
  const districtMetricsMap = useMemo(() => {
    const map = new Map<string, DistrictMetrics>();
    for (const d of HCMC_DISTRICTS) {
      map.set(d.id, computeDistrictMetrics(d, telemetry));
    }
    return map;
  }, [telemetry]);

  // ── Initialise map ──────────────────────────────────────────────
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: styleUrl,
      center,
      zoom,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.on('load', () => {
      // ── Add GeoJSON source ──
      map.addSource('districts', {
        type: 'geojson',
        data: HCMC_GEOJSON,
      });

      // ── Fill layer ──
      map.addLayer({
        id: 'district-fills',
        type: 'fill',
        source: 'districts',
        paint: {
          'fill-color': 'rgba(100,116,139,0.15)',
          'fill-opacity': 1,
        },
      });

      // ── Border layer ──
      map.addLayer({
        id: 'district-borders',
        type: 'line',
        source: 'districts',
        paint: {
          'line-color': '#00f3ff',
          'line-width': 1.5,
          'line-opacity': 0.7,
        },
      });

      // ── Label layer ──
      map.addLayer({
        id: 'district-labels',
        type: 'symbol',
        source: 'districts',
        layout: {
          'text-field': ['get', 'name'],
          'text-size': 11,
          'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
          'text-anchor': 'center',
          'text-allow-overlap': false,
        },
        paint: {
          'text-color': '#e0f2fe',
          'text-halo-color': 'rgba(0,0,0,0.8)',
          'text-halo-width': 1.5,
        },
      });

      setMapLoaded(true);
    });

    mapRef.current = map;

    return () => {
      markersRef.current.forEach((el) => el.remove());
      markersRef.current.clear();
      map.remove();
      mapRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Update fill / border colours based on metrics ───────────────
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;

    // Build paint expression: match district → colour
    const fillExpr: any[] = ['match', ['get', 'districtId']];
    const borderExpr: any[] = ['match', ['get', 'districtId']];

    for (const d of HCMC_DISTRICTS) {
      const m = districtMetricsMap.get(d.id)!;
      fillExpr.push(d.id, getDistrictFillColor(m.status));
      borderExpr.push(d.id, getDistrictBorderColor(m.status));
    }
    fillExpr.push('rgba(100,116,139,0.15)');   // fallback
    borderExpr.push('#64748b');                  // fallback

    map.setPaintProperty('district-fills', 'fill-color', fillExpr);
    map.setPaintProperty('district-borders', 'line-color', borderExpr);
  }, [districtMetricsMap, mapLoaded]);

  // ── Create / update center markers + warning badges ─────────────
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;

    for (const district of HCMC_DISTRICTS) {
      const metrics = districtMetricsMap.get(district.id)!;
      const existing = markersRef.current.get(district.id);

      if (existing) {
        // Update warning badge visibility
        const badge = existing.querySelector('.warning-badge') as HTMLElement;
        if (badge) {
          badge.style.display = metrics.status === 'red' ? 'flex' : 'none';
          badge.setAttribute('data-alerts', metrics.alerts.join(', '));
          const badgeText = badge.querySelector('.badge-text');
          if (badgeText) {
            badgeText.textContent = `⚠ ${metrics.alerts.join(', ')}`;
          }
        }
        // Update dot colour
        const dot = existing.querySelector('.marker-dot') as HTMLElement;
        if (dot) {
          dot.style.background = getDistrictBorderColor(metrics.status);
          dot.style.boxShadow = `0 0 12px ${getDistrictBorderColor(metrics.status)}`;
        }
        continue;
      }

      // ── Create new marker element ──
      const el = document.createElement('div');
      el.className = 'district-marker-container';

      // Dot
      const dot = document.createElement('div');
      dot.className = 'marker-dot';
      dot.style.background = getDistrictBorderColor(metrics.status);
      dot.style.boxShadow = `0 0 12px ${getDistrictBorderColor(metrics.status)}`;
      el.appendChild(dot);

      // Warning badge
      const badge = document.createElement('div');
      badge.className = 'warning-badge';
      badge.style.display = metrics.status === 'red' ? 'flex' : 'none';
      const badgeText = document.createElement('span');
      badgeText.className = 'badge-text';
      badgeText.textContent = `⚠ ${metrics.alerts.join(', ')}`;
      badge.appendChild(badgeText);
      el.appendChild(badge);

      new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat(district.center)
        .addTo(map);

      markersRef.current.set(district.id, el);
    }
  }, [districtMetricsMap, mapLoaded]);

  // ── Hover tooltip ───────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;

    const onMouseMove = (e: maplibregl.MapLayerMouseEvent) => {
      map.getCanvas().style.cursor = 'pointer';
      const feature = e.features?.[0];
      if (!feature) return;
      const distId = feature.properties?.districtId;
      const district = HCMC_DISTRICTS.find(d => d.id === distId);
      if (!district) return;
      const metrics = districtMetricsMap.get(distId);
      if (!metrics) return;

      if (popupRef.current) popupRef.current.remove();
      popupRef.current = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
        offset: 15,
        className: 'district-popup',
      })
        .setLngLat(e.lngLat)
        .setHTML(buildTooltipHTML(district, metrics))
        .addTo(map);
    };

    const onMouseLeave = () => {
      map.getCanvas().style.cursor = '';
      if (popupRef.current) {
        popupRef.current.remove();
        popupRef.current = null;
      }
    };

    const onClick = (e: maplibregl.MapLayerMouseEvent) => {
      const feature = e.features?.[0];
      if (!feature) return;
      const distId = feature.properties?.districtId;
      const district = HCMC_DISTRICTS.find(d => d.id === distId);
      if (district) setSelectedDistrict(district);
    };

    map.on('mousemove', 'district-fills', onMouseMove);
    map.on('mouseleave', 'district-fills', onMouseLeave);
    map.on('click', 'district-fills', onClick);

    return () => {
      map.off('mousemove', 'district-fills', onMouseMove);
      map.off('mouseleave', 'district-fills', onMouseLeave);
      map.off('click', 'district-fills', onClick);
    };
  }, [mapLoaded, districtMetricsMap]);

  return (
    <>
      <div
        ref={mapContainerRef}
        style={{ width: '100%', height: '100%', minHeight: '400px' }}
      />
      {selectedDistrict && (
        <DistrictDetailPanel
          district={selectedDistrict}
          telemetry={telemetry}
          onClose={() => setSelectedDistrict(null)}
        />
      )}
    </>
  );
};

export default MapView;
