"use client"

import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useDashboardStore } from '@/lib/store'
import type { SensorData, ClusterData } from '@/lib/types'
import { cn } from '@/lib/utils'
import { Battery, Wifi, Clock } from 'lucide-react'

// Custom marker icons
const createSensorIcon = (status: SensorData['status']) => {
  const colors = {
    normal: '#22c55e',
    warning: '#f59e0b',
    critical: '#ef4444',
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
  const color = avgPm25 > 100 ? '#ef4444' : avgPm25 > 50 ? '#f59e0b' : '#22c55e'
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

function ZoomHandler() {
  const { setZoomLevel } = useDashboardStore()
  
  useMapEvents({
    zoomend: (e) => {
      setZoomLevel(e.target.getZoom())
    },
  })
  
  return null
}

function MapController({ selectedSensor, selectedCluster }: { 
  selectedSensor: SensorData | null
  selectedCluster: ClusterData | null 
}) {
  const map = useMap()
  
  useEffect(() => {
    if (selectedSensor) {
      map.flyTo([selectedSensor.lat, selectedSensor.lng], 15, { duration: 0.5 })
    } else if (selectedCluster) {
      map.flyTo([selectedCluster.lat, selectedCluster.lng], 14, { duration: 0.5 })
    }
  }, [selectedSensor, selectedCluster, map])
  
  return null
}

function SensorPopup({ sensor }: { sensor: SensorData }) {
  const { selectSensor } = useDashboardStore()
  
  return (
    <div className="min-w-[220px] p-1">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-foreground">{sensor.name}</h3>
        <span className={cn(
          "px-2 py-0.5 text-[10px] font-medium rounded-full uppercase",
          sensor.status === 'normal' && "bg-success/20 text-success",
          sensor.status === 'warning' && "bg-warning/20 text-warning",
          sensor.status === 'critical' && "bg-destructive/20 text-destructive"
        )}>
          {sensor.status}
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-2 mb-3">
        <MetricItem label="PM2.5" value={sensor.pm25} unit="µg/m³" />
        <MetricItem label="Temp" value={sensor.temperature} unit="°F" />
        <MetricItem label="Humidity" value={sensor.humidity} unit="%" />
        <MetricItem label="CO2" value={sensor.co2} unit="ppm" />
        <MetricItem label="Noise" value={sensor.noise} unit="dB" />
      </div>
      
      <div className="flex items-center justify-between pt-2 border-t border-border text-xs text-muted-foreground">
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
          <span>{sensor.lastUpdated.toLocaleTimeString()}</span>
        </div>
      </div>
      
      <button
        onClick={() => selectSensor(sensor)}
        className="w-full mt-3 py-1.5 text-xs font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-colors"
      >
        View Details
      </button>
    </div>
  )
}

function MetricItem({ label, value, unit }: { label: string; value: number; unit: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[10px] text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">
        {value} <span className="text-muted-foreground text-[10px]">{unit}</span>
      </span>
    </div>
  )
}

function ClusterPopup({ cluster }: { cluster: ClusterData }) {
  const { selectCluster } = useDashboardStore()
  
  return (
    <div className="min-w-[200px] p-1">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-foreground">Sensor Cluster</h3>
        <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-primary/20 text-primary">
          {cluster.sensorCount} sensors
        </span>
      </div>
      
      <div className="space-y-1.5 mb-3">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Avg PM2.5</span>
          <span className="font-medium">{cluster.avgPm25} µg/m³</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Avg Temp</span>
          <span className="font-medium">{cluster.avgTemperature}°F</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Avg CO2</span>
          <span className="font-medium">{cluster.avgCo2} ppm</span>
        </div>
      </div>
      
      <button
        onClick={() => selectCluster(cluster)}
        className="w-full py-1.5 text-xs font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-colors"
      >
        Zoom to Cluster
      </button>
    </div>
  )
}

function HeatmapLayer() {
  const { sensors, heatmapMetric, layers } = useDashboardStore()
  const map = useMap()
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  
  useEffect(() => {
    if (!layers.heatmap) return
    
    const canvas = L.DomUtil.create('canvas', 'leaflet-heatmap-layer')
    canvasRef.current = canvas
    
    const pane = map.getPane('overlayPane')
    if (pane) {
      pane.appendChild(canvas)
    }
    
    const drawHeatmap = () => {
      const size = map.getSize()
      canvas.width = size.x
      canvas.height = size.y
      
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      const bounds = map.getBounds()
      const topLeft = map.latLngToContainerPoint(bounds.getNorthWest())
      
      canvas.style.transform = `translate(${topLeft.x}px, ${topLeft.y}px)`
      canvas.style.position = 'absolute'
      canvas.style.pointerEvents = 'none'
      
      sensors.forEach(sensor => {
        const point = map.latLngToContainerPoint([sensor.lat, sensor.lng])
        const x = point.x - topLeft.x
        const y = point.y - topLeft.y
        
        let value: number
        let maxValue: number
        
        switch (heatmapMetric) {
          case 'pm25':
            value = sensor.pm25
            maxValue = 150
            break
          case 'temperature':
            value = sensor.temperature
            maxValue = 100
            break
          case 'humidity':
            value = sensor.humidity
            maxValue = 100
            break
          case 'co2':
            value = sensor.co2
            maxValue = 2000
            break
          case 'noise':
            value = sensor.noise
            maxValue = 100
            break
          default:
            value = sensor.pm25
            maxValue = 150
        }
        
        const intensity = Math.min(value / maxValue, 1)
        const radius = 80
        
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius)
        
        if (intensity > 0.7) {
          gradient.addColorStop(0, `rgba(239, 68, 68, ${intensity * 0.6})`)
          gradient.addColorStop(1, 'rgba(239, 68, 68, 0)')
        } else if (intensity > 0.4) {
          gradient.addColorStop(0, `rgba(245, 158, 11, ${intensity * 0.6})`)
          gradient.addColorStop(1, 'rgba(245, 158, 11, 0)')
        } else {
          gradient.addColorStop(0, `rgba(34, 197, 94, ${intensity * 0.6})`)
          gradient.addColorStop(1, 'rgba(34, 197, 94, 0)')
        }
        
        ctx.fillStyle = gradient
        ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2)
      })
    }
    
    drawHeatmap()
    map.on('moveend', drawHeatmap)
    map.on('zoomend', drawHeatmap)
    
    return () => {
      map.off('moveend', drawHeatmap)
      map.off('zoomend', drawHeatmap)
      if (canvas.parentNode) {
        canvas.parentNode.removeChild(canvas)
      }
    }
  }, [map, sensors, heatmapMetric, layers.heatmap])
  
  return null
}

export function CityMap() {
  const { 
    sensors, 
    clusters, 
    alerts,
    layers, 
    zoomLevel, 
    selectedSensor, 
    selectedCluster 
  } = useDashboardStore()
  
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])
  
  if (!mounted) {
    return (
      <div className="w-full h-full bg-secondary flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading map...</div>
      </div>
    )
  }
  
  const showClusters = zoomLevel < 13 && layers.clusters
  const showSensors = zoomLevel >= 13 && layers.sensors
  
  const alertSensorIds = new Set(alerts.filter(a => !a.acknowledged).map(a => a.sensorId))

  return (
    <MapContainer
      center={[37.7749, -122.4194]}
      zoom={12}
      className="w-full h-full"
      zoomControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      <ZoomHandler />
      <MapController selectedSensor={selectedSensor} selectedCluster={selectedCluster} />
      <HeatmapLayer />
      
      {/* Clusters */}
      {showClusters && clusters.map(cluster => (
        <Marker
          key={cluster.id}
          position={[cluster.lat, cluster.lng]}
          icon={createClusterIcon(cluster.sensorCount, cluster.avgPm25)}
        >
          <Popup>
            <ClusterPopup cluster={cluster} />
          </Popup>
        </Marker>
      ))}
      
      {/* Individual Sensors */}
      {showSensors && sensors.map(sensor => (
        <Marker
          key={sensor.id}
          position={[sensor.lat, sensor.lng]}
          icon={createSensorIcon(sensor.status)}
        >
          <Popup>
            <SensorPopup sensor={sensor} />
          </Popup>
        </Marker>
      ))}
      
      {/* Alert indicators */}
      {layers.alerts && sensors
        .filter(s => alertSensorIds.has(s.id))
        .map(sensor => (
          <CircleMarker
            key={`alert-${sensor.id}`}
            center={[sensor.lat, sensor.lng]}
            radius={20}
            pathOptions={{
              color: '#ef4444',
              fillColor: '#ef4444',
              fillOpacity: 0.2,
              weight: 2,
              dashArray: '4',
            }}
          />
        ))}
    </MapContainer>
  )
}
