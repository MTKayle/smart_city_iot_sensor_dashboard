/**
 * MapView Component — HCMC District Map with real-time sensor data
 *
 * Renders MapLibre GL JS map with:
 * - District boundary polygons (color-coded by threshold status)
 * - District border lines
 * - Center markers with hover tooltips (live CO₂, Noise, Temp, PM2.5, Humidity)
 * - Cluster visualization with aggregate metrics
 * - Pulsing warning badges on districts exceeding thresholds
 * - Click to open district detail panel
 *
 * Requirements: FR9.1
 */

import { useEffect, useRef, useState, useMemo } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { Sensor, Location, Alert, Telemetry, SensorCluster } from '../types';
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
  clusters?: SensorCluster[];
  center?: [number, number];
  zoom?: number;
  styleUrl?: string | object;
}

// Use a lightweight map style without font dependencies for faster loading
const DEFAULT_STYLE = {
  version: 8,
  sources: {
    'carto-light': {
      type: 'raster',
      tiles: [
        'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
        'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
        'https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'
      ],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors, © CARTO'
    }
  },
  layers: [
    {
      id: 'carto-light-layer',
      type: 'raster',
      source: 'carto-light',
      minzoom: 0,
      maxzoom: 20
    }
  ],
  glyphs: undefined // Explicitly disable font loading
};

// ── Helper: extract metric value from v2 telemetry (nested or flat) ──
const getMetric = (t: Telemetry, metric: 'co2' | 'noise' | 'temperature' | 'pm25' | 'humidity'): number | null => {
  // Try nested data first, then flat legacy fields
  const nested = t.data?.[metric];
  if (nested !== undefined && nested !== null) return nested;
  const flat = (t as unknown as Record<string, unknown>)[metric];
  if (typeof flat === 'number') return flat;
  return null;
};

/**
 * Compute aggregated metrics for a district from real-time telemetry.
 */
const computeDistrictMetrics = (
  district: DistrictData,
  telemetry: Record<string, Telemetry>,
): DistrictMetrics => {
  let co2Sum = 0, noiseSum = 0, tempSum = 0, pm25Sum = 0, humiditySum = 0;
  let co2Count = 0, noiseCount = 0, tempCount = 0, pm25Count = 0, humidityCount = 0;
  const alertLabels: string[] = [];

  for (const ward of district.wards) {
    for (const sensor of ward.sensors) {
      const t = telemetry[sensor.id];
      if (!t) continue;

      // v2: combo sensors — read all metrics from every telemetry record
      const co2 = getMetric(t, 'co2');
      const noise = getMetric(t, 'noise');
      const temp = getMetric(t, 'temperature');
      const pm25 = getMetric(t, 'pm25');
      const humidity = getMetric(t, 'humidity');

      if (co2 !== null) { co2Sum += co2; co2Count++; }
      if (noise !== null) { noiseSum += noise; noiseCount++; }
      if (temp !== null) { tempSum += temp; tempCount++; }
      if (pm25 !== null) { pm25Sum += pm25; pm25Count++; }
      if (humidity !== null) { humiditySum += humidity; humidityCount++; }
    }
  }

  const avgCO2 = co2Count > 0 ? co2Sum / co2Count : null;
  const avgNoise = noiseCount > 0 ? noiseSum / noiseCount : null;
  const avgTemp = tempCount > 0 ? tempSum / tempCount : null;
  const avgPM25 = pm25Count > 0 ? pm25Sum / pm25Count : null;
  const avgHumidity = humidityCount > 0 ? humiditySum / humidityCount : null;

  // AQI calculation from PM2.5 average (EPA simplified)
  let aqi: number | null = null;
  if (avgPM25 !== null) {
    if (avgPM25 <= 12) aqi = Math.round((50 / 12) * avgPM25);
    else if (avgPM25 <= 35.4) aqi = Math.round(50 + ((100 - 51) / (35.4 - 12.1)) * (avgPM25 - 12.1));
    else if (avgPM25 <= 55.4) aqi = Math.round(100 + ((150 - 101) / (55.4 - 35.5)) * (avgPM25 - 35.5));
    else if (avgPM25 <= 150.4) aqi = Math.round(150 + ((200 - 151) / (150.4 - 55.5)) * (avgPM25 - 55.5));
    else aqi = Math.round(200 + ((300 - 201) / (250.4 - 150.5)) * (avgPM25 - 150.5));
  }

  // Determine status
  let status: DistrictStatus = 'gray';
  const hasData = co2Count > 0 || noiseCount > 0 || tempCount > 0 || pm25Count > 0 || humidityCount > 0;
  if (hasData) {
    status = 'green';
    if (avgCO2 !== null && avgCO2 >= THRESHOLDS.co2.warning) { status = 'yellow'; alertLabels.push(THRESHOLDS.co2.label); }
    if (avgNoise !== null && avgNoise >= THRESHOLDS.noise.warning) { status = 'yellow'; alertLabels.push(THRESHOLDS.noise.label); }
    if (avgTemp !== null && avgTemp >= THRESHOLDS.temperature.warning) { status = 'yellow'; alertLabels.push(THRESHOLDS.temperature.label); }
    if (avgPM25 !== null && avgPM25 >= THRESHOLDS.pm25.warning) { status = 'yellow'; alertLabels.push(THRESHOLDS.pm25.label); }
    if (avgHumidity !== null && avgHumidity >= THRESHOLDS.humidity.warning) { status = 'yellow'; alertLabels.push(THRESHOLDS.humidity.label); }

    if (avgCO2 !== null && avgCO2 >= THRESHOLDS.co2.danger) status = 'red';
    if (avgNoise !== null && avgNoise >= THRESHOLDS.noise.danger) status = 'red';
    if (avgTemp !== null && avgTemp >= THRESHOLDS.temperature.danger) status = 'red';
    if (avgPM25 !== null && avgPM25 >= THRESHOLDS.pm25.danger) status = 'red';
    if (avgHumidity !== null && avgHumidity >= THRESHOLDS.humidity.danger) status = 'red';
  }

  return { avgCO2, avgNoise, avgTemperature: avgTemp, avgPM25, avgHumidity, aqi, status, alerts: alertLabels };
};

/**
 * Build a tooltip HTML string for a district.
 */
const buildTooltipHTML = (district: DistrictData, metrics: DistrictMetrics): string => {
  const val = (v: number | null, unit: string) =>
    v !== null ? `${v.toFixed(1)} ${unit}` : '—';

  const cls = (v: number | null, warn: number, danger: number) =>
    v !== null && v >= danger ? 'danger' : v !== null && v >= warn ? 'warning' : 'ok';

  const co2Class = cls(metrics.avgCO2, THRESHOLDS.co2.warning, THRESHOLDS.co2.danger);
  const noiseClass = cls(metrics.avgNoise, THRESHOLDS.noise.warning, THRESHOLDS.noise.danger);
  const tempClass = cls(metrics.avgTemperature, THRESHOLDS.temperature.warning, THRESHOLDS.temperature.danger);
  const pm25Class = cls(metrics.avgPM25, THRESHOLDS.pm25.warning, THRESHOLDS.pm25.danger);
  const humidityClass = cls(metrics.avgHumidity, THRESHOLDS.humidity.warning, THRESHOLDS.humidity.danger);

  // AQI badge
  let aqiBadge = '';
  if (metrics.aqi !== null) {
    let aqiColor = '#22c55e';
    let aqiLabel = 'Tốt';
    if (metrics.aqi > 200) { aqiColor = '#7e22ce'; aqiLabel = 'Nguy hiểm'; }
    else if (metrics.aqi > 150) { aqiColor = '#dc2626'; aqiLabel = 'Xấu'; }
    else if (metrics.aqi > 100) { aqiColor = '#ea580c'; aqiLabel = 'Không tốt'; }
    else if (metrics.aqi > 50) { aqiColor = '#eab308'; aqiLabel = 'Trung bình'; }
    aqiBadge = `<div class="dt-aqi" style="margin-top:8px;padding:6px 10px;border-radius:6px;background:${aqiColor}20;border:1px solid ${aqiColor}55;text-align:center;">
      <span style="font-size:11px;color:#94a3b8;letter-spacing:0.5px;">AQI</span>
      <span style="font-size:18px;font-weight:700;color:${aqiColor};margin-left:8px;">${metrics.aqi}</span>
      <span style="font-size:11px;color:${aqiColor};margin-left:4px;">${aqiLabel}</span>
    </div>`;
  }

  return `
    <div class="district-tooltip">
      <div class="dt-header">${district.name}</div>
      <div class="dt-row"><span class="dt-icon">🌫️</span><span class="dt-label">CO₂</span><span class="dt-value ${co2Class}">${val(metrics.avgCO2, 'ppm')}</span></div>
      <div class="dt-row"><span class="dt-icon">🔊</span><span class="dt-label">Tiếng ồn</span><span class="dt-value ${noiseClass}">${val(metrics.avgNoise, 'dB')}</span></div>
      <div class="dt-row"><span class="dt-icon">🌡️</span><span class="dt-label">Nhiệt độ</span><span class="dt-value ${tempClass}">${val(metrics.avgTemperature, '°C')}</span></div>
      <div class="dt-row"><span class="dt-icon">💨</span><span class="dt-label">PM2.5</span><span class="dt-value ${pm25Class}">${val(metrics.avgPM25, 'μg/m³')}</span></div>
      <div class="dt-row"><span class="dt-icon">💧</span><span class="dt-label">Độ ẩm</span><span class="dt-value ${humidityClass}">${val(metrics.avgHumidity, '%')}</span></div>
      ${aqiBadge}
      <div class="dt-footer">Di chuột = xem tổng · Click = chi tiết</div>
    </div>
  `;
};

export const MapView: React.FC<MapViewProps> = ({
  sensors: _sensors,
  locations: _locations,
  alerts: _alerts,
  telemetry,
  clusters = [],
  center = [106.6970, 10.7900],
  zoom = 12,
  styleUrl = import.meta.env.VITE_MAP_STYLE_URL || DEFAULT_STYLE,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<Map<string, HTMLDivElement>>(new Map());
  const clusterMarkersRef = useRef<Map<string, maplibregl.Marker>>(new Map());
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
      style: styleUrl || DEFAULT_STYLE,
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
      clusterMarkersRef.current.forEach((m) => m.remove());
      clusterMarkersRef.current.clear();
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

  // ── Render cluster markers ──────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;

    // Remove old cluster markers that no longer exist
    const currentIds = new Set(clusters.map(c => c.clusterId));
    clusterMarkersRef.current.forEach((marker, id) => {
      if (!currentIds.has(id)) {
        marker.remove();
        clusterMarkersRef.current.delete(id);
      }
    });

    for (const cluster of clusters) {
      const existing = clusterMarkersRef.current.get(cluster.clusterId);
      if (existing) {
        existing.setLngLat([cluster.centerLng, cluster.centerLat]);
        continue;
      }

      // Create cluster marker
      const el = document.createElement('div');
      el.className = 'cluster-marker';
      el.innerHTML = `
        <div class="cluster-ring">
          <span class="cluster-count">${cluster.sensorCount}</span>
        </div>
      `;
      el.title = cluster.clusterName || cluster.clusterId;

      const marker = new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat([cluster.centerLng, cluster.centerLat])
        .addTo(map);

      // Cluster popup on click
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        if (popupRef.current) popupRef.current.remove();
        popupRef.current = new maplibregl.Popup({
          closeButton: true,
          closeOnClick: true,
          offset: 15,
          className: 'cluster-popup',
        })
          .setLngLat([cluster.centerLng, cluster.centerLat])
          .setHTML(`
            <div class="cluster-tooltip">
              <div class="dt-header">${cluster.clusterName || cluster.clusterId}</div>
              <div class="dt-row"><span class="dt-label">Sensors</span><span class="dt-value ok">${cluster.sensorCount}</span></div>
              <div class="dt-row"><span class="dt-label">Radius</span><span class="dt-value ok">${cluster.radius}m</span></div>
              <div class="dt-row"><span class="dt-label">Algorithm</span><span class="dt-value ok">${cluster.algorithm || '—'}</span></div>
            </div>
          `)
          .addTo(map);
      });

      clusterMarkersRef.current.set(cluster.clusterId, marker);
    }
  }, [clusters, mapLoaded]);

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
