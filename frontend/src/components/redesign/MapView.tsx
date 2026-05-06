"use client"

import { useEffect, useRef, useState, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import '../../styles/leaflet-custom.css'
import { useAppContext } from '../../context/AppContext'
import { Battery, Wifi, Clock } from 'lucide-react'
import MapLayerControl from './MapLayerControl'
import HeatmapControl from './HeatmapControl'
import SensorDetailPanel from './SensorDetailPanel'
import type { HeatmapMetric, MapLayers, MapFocusTarget } from './types'
import { METRIC_SPECS, metersToPixels, rampColor } from '../../utils/heatmap'

interface SensorWithTelemetry {
  id: string
  name: string
  lat: number
  lng: number
  pm25: number
  temp: number
  humidity: number
  co2: number
  noise: number
  battery: number
  signal: number
  status: 'critical' | 'warning' | 'normal'
  lastUpdate: string
}

interface ClusterData {
  id: string
  lat: number
  lng: number
  count: number
  avgPm25: number
  avgTemp: number
  avgHumidity: number
  avgCo2: number
  status: 'critical' | 'warning' | 'normal'
  /** Sensor IDs that make up this grid cluster — used by detail panel for live aggregation. */
  memberIds: string[]
}

// Custom marker icons
const createSensorIcon = (status: 'critical' | 'warning' | 'normal') => {
  const colors = {
    normal: '#10B981',
    warning: '#F59E0B',
    critical: '#EF4444',
  }
  
  return L.divIcon({
    html: `
      <div class="relative flex items-center justify-center">
        <div class="absolute w-8 h-8 rounded-full animate-ping opacity-40" style="background-color: ${colors[status]}"></div>
        <div class="relative w-4 h-4 rounded-full border-2 border-white shadow-lg" style="background-color: ${colors[status]}"></div>
      </div>
    `,
    className: 'custom-sensor-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  })
}

const createClusterIcon = (count: number, avgPm25: number) => {
  const color = avgPm25 > 100 ? '#EF4444' : avgPm25 > 50 ? '#F59E0B' : '#10B981'
  const size = Math.min(60, 36 + count * 4)
  
  return L.divIcon({
    html: `
      <div class="flex items-center justify-center w-full h-full rounded-full border-2 border-white/50 shadow-lg" 
           style="background-color: ${color}; width: ${size}px; height: ${size}px;">
        <span class="text-white font-bold text-sm">${count}</span>
      </div>
    `,
    className: 'custom-cluster-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
}

function MapInstanceCapture({ onMapReady }: { onMapReady: (map: L.Map) => void }) {
  const map = useMap()
  
  useEffect(() => {
    onMapReady(map)
  }, [map, onMapReady])
  
  return null
}

function ZoomHandler({ onZoomChange }: { onZoomChange: (zoom: number) => void }) {
  useMapEvents({
    zoomend: (e) => {
      onZoomChange(e.target.getZoom())
    },
  })
  
  return null
}

function MapController({
  flyTarget,
}: {
  flyTarget: { lat: number; lng: number; zoom: number } | null
}) {
  const map = useMap()

  useEffect(() => {
    if (flyTarget) {
      map.flyTo([flyTarget.lat, flyTarget.lng], flyTarget.zoom, { duration: 0.5 })
    }
  }, [flyTarget, map])

  return null
}

function SensorPopup({ sensor, onViewDetails }: { sensor: SensorWithTelemetry; onViewDetails: () => void }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return 'bg-[oklch(0.55_0.22_25)]/20 text-[oklch(0.55_0.22_25)]'
      case 'warning': return 'bg-[oklch(0.75_0.18_85)]/20 text-[oklch(0.75_0.18_85)]'
      default: return 'bg-[oklch(0.65_0.2_145)]/20 text-[oklch(0.65_0.2_145)]'
    }
  }

  return (
    <div className="min-w-220 p-1" style={{ background: 'oklch(0.16 0.01 260)', color: 'oklch(0.95 0 0)' }}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold" style={{ color: 'oklch(0.95 0 0)' }}>{sensor.name}</h3>
        <span className={`px-2 py-0-5 text-xxs font-medium rounded-full uppercase ${getStatusColor(sensor.status)}`}>
          {sensor.status}
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-2 mb-3">
        <MetricItem label="PM2.5" value={sensor.pm25} unit="µg/m³" />
        <MetricItem label="Temp" value={sensor.temp} unit="°C" />
        <MetricItem label="Humidity" value={sensor.humidity} unit="%" />
        <MetricItem label="CO2" value={sensor.co2} unit="ppm" />
        <MetricItem label="Noise" value={sensor.noise} unit="dB" />
      </div>
      
      <div className="flex items-center justify-between pt-2 border-t text-xs" style={{ borderColor: 'oklch(0.25 0.01 260)', color: 'oklch(0.65 0 0)' }}>
        <div className="flex items-center gap-1">
          <Battery className="w-3 h-3" />
          <span>{Math.round(sensor.battery)}%</span>
        </div>
        <div className="flex items-center gap-1">
          <Wifi className="w-3 h-3" />
          <span>{sensor.signal}%</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{new Date(sensor.lastUpdate).toLocaleTimeString()}</span>
        </div>
      </div>
      
      <button
        onClick={onViewDetails}
        className="w-full mt-3 py-1-5 text-xs font-medium rounded-md transition-colors"
        style={{ 
          background: 'oklch(0.65 0.22 255)', 
          color: 'oklch(0.12 0 0)' 
        }}
        onMouseEnter={(e) => e.currentTarget.style.background = 'oklch(0.6 0.22 255)'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'oklch(0.65 0.22 255)'}
      >
        View Details
      </button>
    </div>
  )
}

function MetricItem({ label, value, unit }: { label: string; value: number; unit: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-xxs" style={{ color: 'oklch(0.65 0 0)' }}>{label}</span>
      <span className="text-sm font-medium" style={{ color: 'oklch(0.95 0 0)' }}>
        {value.toFixed(1)} <span className="text-xxs" style={{ color: 'oklch(0.65 0 0)' }}>{unit}</span>
      </span>
    </div>
  )
}

function ClusterPopup({ cluster, onZoomToCluster }: { cluster: ClusterData; onZoomToCluster: () => void }) {
  return (
    <div className="min-w-200 p-1" style={{ background: 'oklch(0.16 0.01 260)', color: 'oklch(0.95 0 0)' }}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold" style={{ color: 'oklch(0.95 0 0)' }}>Sensor Cluster</h3>
        <span className="px-2 py-0-5 text-xxs font-medium rounded-full" style={{ background: 'oklch(0.65 0.22 255)/0.2', color: 'oklch(0.65 0.22 255)' }}>
          {cluster.count} sensors
        </span>
      </div>
      
      <div className="space-y-1-5 mb-3">
        <div className="flex justify-between text-sm">
          <span style={{ color: 'oklch(0.65 0 0)' }}>Avg PM2.5</span>
          <span className="font-medium">{cluster.avgPm25.toFixed(1)} µg/m³</span>
        </div>
        <div className="flex justify-between text-sm">
          <span style={{ color: 'oklch(0.65 0 0)' }}>Avg Temp</span>
          <span className="font-medium">{cluster.avgTemp.toFixed(1)}°C</span>
        </div>
        <div className="flex justify-between text-sm">
          <span style={{ color: 'oklch(0.65 0 0)' }}>Avg CO2</span>
          <span className="font-medium">{cluster.avgCo2.toFixed(0)} ppm</span>
        </div>
      </div>
      
      <button
        onClick={onZoomToCluster}
        className="w-full py-1-5 text-xs font-medium rounded-md transition-colors"
        style={{ 
          background: 'oklch(0.65 0.22 255)', 
          color: 'oklch(0.12 0 0)' 
        }}
        onMouseEnter={(e) => e.currentTarget.style.background = 'oklch(0.6 0.22 255)'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'oklch(0.65 0.22 255)'}
      >
        Zoom to Cluster
      </button>
    </div>
  )
}

/**
 * Blob-based heatmap layer.
 *
 * Approach (mirrors what leaflet.heat does, but with breakpoint-aware colors):
 *   1. For every sensor draw a radial gradient blob — strong color at the
 *      centre, fading to transparent at the influence radius.
 *   2. Composite operation `lighter` adds RGB across overlapping blobs, so
 *      hot zones intensify visually (red over yellow → vivid orange-red).
 *   3. Adaptive radius is in metres → pixels, so the spatial footprint stays
 *      meaningful at every zoom level.
 *
 * Anchoring strategy:
 *   The canvas lives directly on the map's container element (NOT inside an
 *   overlayPane). overlayPane gets translated during pan/zoom-anim, which would
 *   cause the heatmap to drift away from the markers. By staying fixed to the
 *   viewport and redrawing on every `move`/`zoom` event, container-point
 *   coordinates remain valid frame-by-frame.
 */
function HeatmapLayer({
  sensors,
  heatmapMetric,
  opacity,
}: {
  sensors: SensorWithTelemetry[]
  heatmapMetric: HeatmapMetric
  opacity: number
}) {
  const map = useMap()
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    if (sensors.length === 0) return

    const canvas = L.DomUtil.create('canvas', 'leaflet-heatmap-layer')
    canvasRef.current = canvas

    // Pin the canvas to the visible viewport — never inside a translating pane.
    canvas.style.position = 'absolute'
    canvas.style.top = '0'
    canvas.style.left = '0'
    canvas.style.pointerEvents = 'none'
    canvas.style.zIndex = '400' // above tile layer (200), below markers (600)
    canvas.style.filter = 'blur(4px)'
    canvas.style.opacity = String(opacity)

    const container = map.getContainer()
    container.appendChild(canvas)

    const spec = METRIC_SPECS[heatmapMetric]

    const pickValue = (s: SensorWithTelemetry): number | null => {
      switch (heatmapMetric) {
        case 'pm25':     return s.pm25
        case 'temp':     return s.temp
        case 'humidity': return s.humidity
        case 'co2':      return s.co2
        case 'noise':    return s.noise
        default:         return null
      }
    }

    const rgbOf = (rgba: string): [number, number, number] => {
      const m = rgba.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/)
      if (!m) return [255, 255, 255]
      return [Number(m[1]), Number(m[2]), Number(m[3])]
    }

    const drawHeatmap = () => {
      const size = map.getSize()
      // Resize only when needed — assigning width/height clears the canvas.
      if (canvas.width !== size.x) canvas.width = size.x
      if (canvas.height !== size.y) canvas.height = size.y

      const ctx = canvas.getContext('2d')
      if (!ctx) return

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const center = map.getCenter()
      const spatialPx = metersToPixels(spec.radiusMeters, center.lat, map.getZoom())
      const radiusPx = Math.max(90, Math.min(280, spatialPx))

      // Additive blending: overlapping sensor blobs intensify into hot spots.
      ctx.globalCompositeOperation = 'lighter'

      for (const s of sensors) {
        const v = pickValue(s)
        if (v === null || v === undefined || isNaN(v) || v === 0) continue

        // Container point: pixel position relative to the map's viewport,
        // matches exactly where Leaflet draws the marker for this sensor.
        const point = map.latLngToContainerPoint([s.lat, s.lng])
        const x = point.x
        const y = point.y

        // Skip sensors whose influence circle is entirely off-screen.
        if (
          x < -radiusPx ||
          x > canvas.width + radiusPx ||
          y < -radiusPx ||
          y > canvas.height + radiusPx
        ) continue

        const [r, g, b] = rgbOf(rampColor(v, spec, 1))

        const grad = ctx.createRadialGradient(x, y, 0, x, y, radiusPx)
        grad.addColorStop(0,    `rgba(${r},${g},${b},0.85)`)
        grad.addColorStop(0.35, `rgba(${r},${g},${b},0.55)`)
        grad.addColorStop(0.7,  `rgba(${r},${g},${b},0.22)`)
        grad.addColorStop(1,    `rgba(${r},${g},${b},0)`)

        ctx.fillStyle = grad
        ctx.fillRect(x - radiusPx, y - radiusPx, radiusPx * 2, radiusPx * 2)
      }

      ctx.globalCompositeOperation = 'source-over'
    }

    // Initial render.
    drawHeatmap()

    // Listen to high-frequency events (move/zoom) for smooth tracking during
    // pan and pinch-zoom gestures, plus the *end variants for animated zooms.
    map.on('move', drawHeatmap)
    map.on('zoom', drawHeatmap)
    map.on('zoomend', drawHeatmap)
    map.on('moveend', drawHeatmap)
    map.on('resize', drawHeatmap)
    map.on('viewreset', drawHeatmap)

    return () => {
      map.off('move', drawHeatmap)
      map.off('zoom', drawHeatmap)
      map.off('zoomend', drawHeatmap)
      map.off('moveend', drawHeatmap)
      map.off('resize', drawHeatmap)
      map.off('viewreset', drawHeatmap)
      if (canvas.parentNode) canvas.parentNode.removeChild(canvas)
    }
  }, [map, sensors, heatmapMetric, opacity])

  return null
}

interface MapViewProps {
  focusTarget?: MapFocusTarget | null
  onFocusConsumed?: () => void
}

const MapView: React.FC<MapViewProps> = ({ focusTarget, onFocusConsumed }) => {
  const { sensors, telemetryMap, alerts, clusters: contextClusters } = useAppContext()
  const [mounted, setMounted] = useState(false)
  const [zoomLevel, setZoomLevel] = useState(12)
  // Selection state holds IDs only — the panel reads live data from AppContext
  // so realtime updates flow through automatically.
  const [selectedSensorId, setSelectedSensorId] = useState<string | null>(null)
  const [selectedCluster, setSelectedCluster] = useState<ClusterData | null>(null)
  const [externalFlyTarget, setExternalFlyTarget] = useState<{
    lat: number
    lng: number
    zoom: number
  } | null>(null)
  // Oracle cluster the user just opened from the Clusters page — drives the
  // glowing ring on the map so the focused area is unmistakable.
  const [focusedOracleClusterId, setFocusedOracleClusterId] = useState<string | null>(null)
  // Sensor the user just navigated to from another view (Alerts → Định Vị,
  // Sensors table, Dashboard alerts). Drives a pulsing ring around the
  // marker so the target is unmistakable for a few seconds.
  const [focusedSensorId, setFocusedSensorId] = useState<string | null>(null)
  const [layers, setLayers] = useState<MapLayers>({
    sensors: true,
    clusters: true,
    alerts: true,
    heatmap: false,
  })
  const [heatmapMetric, setHeatmapMetric] = useState<HeatmapMetric>('pm25')
  const [heatmapOpacity, setHeatmapOpacity] = useState(0.85)
  const mapRef = useRef<L.Map | null>(null)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Clear selected cluster when zoom changes to sensor view
  useEffect(() => {
    if (zoomLevel >= 13 && selectedCluster) {
      setSelectedCluster(null)
    }
  }, [zoomLevel, selectedCluster])

  // External focus request from another view (e.g. ClustersView "Xem trên bản đồ"
  // or AlertsView "Định Vị"). Fly to the requested coordinates, optionally pin
  // the cluster halo or auto-select the specific sensor that triggered the
  // navigation.
  useEffect(() => {
    if (!focusTarget) return
    setExternalFlyTarget({
      lat: focusTarget.lat,
      lng: focusTarget.lng,
      zoom: focusTarget.zoom,
    })
    if (focusTarget.clusterId) {
      setFocusedOracleClusterId(focusTarget.clusterId)
    }
    // Auto-select the sensor — MapView shows SensorDetailPanel for it and the
    // marker becomes the camera anchor.
    if (focusTarget.sensorId) {
      setSelectedSensorId(focusTarget.sensorId)
      setFocusedSensorId(focusTarget.sensorId)
      // Make sure no cluster panel is also open at the same time.
      setSelectedCluster(null)
    }
    onFocusConsumed?.()
    // Release fly priority once the animation has settled so future clicks
    // (sensor, grid-cluster) regain control of the camera. The halo lives
    // longer (8s) so the user can clearly see which area was opened.
    const flyTimer = setTimeout(() => setExternalFlyTarget(null), 1000)
    const haloTimer = setTimeout(() => setFocusedOracleClusterId(null), 8000)
    const sensorHaloTimer = setTimeout(() => setFocusedSensorId(null), 10000)
    return () => {
      clearTimeout(flyTimer)
      clearTimeout(haloTimer)
      clearTimeout(sensorHaloTimer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusTarget])

  const focusedOracleCluster = useMemo(() => {
    if (!focusedOracleClusterId) return null
    return contextClusters.find((c) => c.clusterId === focusedOracleClusterId) ?? null
  }, [focusedOracleClusterId, contextClusters])
  
  // Memoize sensors with telemetry data - only process when data changes
  const sensorsWithData: SensorWithTelemetry[] = useMemo(() => {
    if (sensors.length === 0) return []
    
    return sensors.map(sensor => {
      const telemetry = telemetryMap[sensor.sensorId]
      const pm25 = telemetry?.pm25 || 0
      const co2 = telemetry?.co2 || 0
      
      let status: 'critical' | 'warning' | 'normal' = 'normal'
      if (pm25 > 100 || co2 > 2000) status = 'critical'
      else if (pm25 > 50 || co2 > 1000) status = 'warning'

      return {
        id: sensor.sensorId,
        name: sensor.locationId || sensor.sensorId,
        lat: sensor.latitude || 10.7769,
        lng: sensor.longitude || 106.7009,
        pm25: pm25,
        temp: telemetry?.temperature || 0,
        humidity: telemetry?.humidity || 0,
        co2: co2,
        noise: telemetry?.noise || 0,
        battery: 85,
        signal: 90,
        status,
        lastUpdate: telemetry ? new Date(telemetry.timestamp).toISOString() : new Date().toISOString(),
      }
    })
  }, [sensors, telemetryMap])

  // Memoize clusters
  const clusters = useMemo(() => {
    const createClusters = (sensors: SensorWithTelemetry[], gridSize: number = 0.02): ClusterData[] => {
      const clusterMap = new Map<string, SensorWithTelemetry[]>()
      
      sensors.forEach(sensor => {
        const gridLat = Math.floor(sensor.lat / gridSize) * gridSize
        const gridLng = Math.floor(sensor.lng / gridSize) * gridSize
        const key = `${gridLat},${gridLng}`
        
        if (!clusterMap.has(key)) {
          clusterMap.set(key, [])
        }
        clusterMap.get(key)!.push(sensor)
      })

      return Array.from(clusterMap.entries())
        .filter(([, group]) => group.length >= 2)
        .map(([key, group]) => {
          const [lat, lng] = key.split(',').map(Number)
          const avgPm25 = group.reduce((sum, s) => sum + s.pm25, 0) / group.length
          const avgTemp = group.reduce((sum, s) => sum + s.temp, 0) / group.length
          const avgHumidity = group.reduce((sum, s) => sum + s.humidity, 0) / group.length
          const avgCo2 = group.reduce((sum, s) => sum + s.co2, 0) / group.length
          
          let status: 'critical' | 'warning' | 'normal' = 'normal'
          if (avgPm25 > 100 || avgCo2 > 2000) status = 'critical'
          else if (avgPm25 > 50 || avgCo2 > 1000) status = 'warning'

          return {
            id: key,
            lat: lat + gridSize / 2,
            lng: lng + gridSize / 2,
            count: group.length,
            avgPm25,
            avgTemp,
            avgHumidity,
            avgCo2,
            status,
            memberIds: group.map(s => s.id),
          }
        })
    }

    return createClusters(sensorsWithData)
  }, [sensorsWithData])
  
  // Show loading state while data is being fetched
  if (!mounted || sensors.length === 0) {
    return (
      <div className="w-full h-full bg-gray-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <div className="text-gray-400">Loading map data...</div>
        </div>
      </div>
    )
  }
  
  const showClusters = zoomLevel < 13 && layers.clusters
  const showSensors = zoomLevel >= 13 && layers.sensors
  
  const alertSensorIds = new Set(
    alerts.filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH').map(a => a.sensorId)
  )

  return (
    <div className="map-view">
      <div className="map-container-wrapper">
        <MapContainer
          center={[10.7769, 106.7009]}
          zoom={12}
          className="w-full h-full"
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
          />
          
          <MapInstanceCapture onMapReady={(map) => { mapRef.current = map }} />
          <ZoomHandler onZoomChange={setZoomLevel} />
          <MapController
            flyTarget={(() => {
              if (externalFlyTarget) return externalFlyTarget
              if (selectedSensorId) {
                const s = sensorsWithData.find(x => x.id === selectedSensorId)
                if (s) return { lat: s.lat, lng: s.lng, zoom: 15 }
              }
              if (selectedCluster) {
                return { lat: selectedCluster.lat, lng: selectedCluster.lng, zoom: 14 }
              }
              return null
            })()}
          />
          {layers.heatmap && (
            <HeatmapLayer
              sensors={sensorsWithData}
              heatmapMetric={heatmapMetric}
              opacity={heatmapOpacity}
            />
          )}
          
          {/* Clusters */}
          {showClusters && clusters.map(cluster => (
            <Marker
              key={cluster.id}
              position={[cluster.lat, cluster.lng]}
              icon={createClusterIcon(cluster.count, cluster.avgPm25)}
            >
              <Popup closeButton={false} autoClose={false} closeOnClick={false}>
                <ClusterPopup 
                  cluster={cluster} 
                  onZoomToCluster={() => {
                    setSelectedCluster(cluster)
                    // Zoom to level 14 to show sensors
                    if (mapRef.current) {
                      mapRef.current.flyTo([cluster.lat, cluster.lng], 14, { duration: 0.5 })
                    }
                  }}
                />
              </Popup>
            </Marker>
          ))}
          
          {/* Individual Sensors */}
          {showSensors && sensorsWithData.map(sensor => (
            <Marker
              key={sensor.id}
              position={[sensor.lat, sensor.lng]}
              icon={createSensorIcon(sensor.status)}
            >
              <Popup closeButton={false} autoClose={false} closeOnClick={false}>
                <SensorPopup sensor={sensor} onViewDetails={() => setSelectedSensorId(sensor.id)} />
              </Popup>
            </Marker>
          ))}
          
          {/* Alert indicators */}
          {layers.alerts && sensorsWithData
            .filter(s => alertSensorIds.has(s.id))
            .map(sensor => (
              <CircleMarker
                key={`alert-${sensor.id}`}
                center={[sensor.lat, sensor.lng]}
                radius={20}
                pathOptions={{
                  color: '#EF4444',
                  fillColor: '#EF4444',
                  fillOpacity: 0.2,
                  weight: 2,
                  dashArray: '4',
                }}
              />
            ))}

          {/* Focused Oracle cluster halo — appears for ~8s after navigating
              from the Clusters page so the area is unmistakable. */}
          {focusedOracleCluster && (
            <CircleMarker
              key={`focus-${focusedOracleCluster.clusterId}`}
              center={[focusedOracleCluster.centerLat, focusedOracleCluster.centerLng]}
              radius={50}
              pathOptions={{
                color: '#3B82F6',
                fillColor: '#3B82F6',
                fillOpacity: 0.15,
                weight: 3,
                dashArray: '6 4',
                className: 'cluster-focus-halo',
              }}
            />
          )}

          {/* Focused sensor halo — appears for ~10s after navigating from an
              Alert "Định Vị" or Sensors table action. Pulsing orange ring
              makes it obvious which sensor was selected. */}
          {focusedSensorId && (() => {
            const s = sensorsWithData.find((x) => x.id === focusedSensorId)
            if (!s) return null
            return (
              <CircleMarker
                key={`sensor-focus-${s.id}`}
                center={[s.lat, s.lng]}
                radius={26}
                pathOptions={{
                  color: '#F97316',
                  fillColor: '#F97316',
                  fillOpacity: 0.18,
                  weight: 3,
                  className: 'sensor-focus-halo',
                }}
              />
            )
          })()}
        </MapContainer>

        {/* Map Controls */}
        <MapLayerControl
          layers={layers}
          onLayerToggle={(layer: keyof MapLayers) => setLayers({ ...layers, [layer]: !layers[layer] })}
        />

        {layers.heatmap && (
          <HeatmapControl
            selectedMetric={heatmapMetric}
            onMetricChange={setHeatmapMetric}
            sensors={sensorsWithData}
            opacity={heatmapOpacity}
            onOpacityChange={setHeatmapOpacity}
          />
        )}
      </div>

      {/* Sensor Detail Panel — reads live values from AppContext via IDs */}
      {(selectedSensorId || selectedCluster) && (
        <SensorDetailPanel
          sensorId={selectedSensorId}
          clusterId={selectedCluster?.id}
          clusterMeta={
            selectedCluster
              ? {
                  memberIds: selectedCluster.memberIds,
                  lat: selectedCluster.lat,
                  lng: selectedCluster.lng,
                  count: selectedCluster.count,
                  name: `Cụm ${selectedCluster.count} cảm biến`,
                }
              : undefined
          }
          onClose={() => {
            setSelectedSensorId(null)
            setSelectedCluster(null)
          }}
        />
      )}
    </div>
  )
}

export default MapView
