"use client"

import { useDashboardStore } from '@/lib/store'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MapPin, Layers } from 'lucide-react'

export function ClustersView() {
  const { clusters, selectCluster, setViewMode } = useDashboardStore()
  
  const handleViewOnMap = (clusterId: string) => {
    const cluster = clusters.find(c => c.id === clusterId)
    if (cluster) {
      selectCluster(cluster)
      setViewMode('map')
    }
  }
  
  const getHealthColor = (avgPm25: number) => {
    if (avgPm25 > 100) return 'destructive'
    if (avgPm25 > 50) return 'warning'
    return 'success'
  }

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Clusters</h1>
          <p className="text-muted-foreground text-sm">
            {clusters.length} sensor clusters identified
          </p>
        </div>
      </div>
      
      {/* Grid */}
      <div className="flex-1 overflow-y-auto">
        {clusters.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <Layers className="w-12 h-12 mb-4 opacity-50" />
            <p>No clusters available</p>
            <p className="text-sm">Zoom out on the map to see clusters</p>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {clusters.map((cluster, index) => {
              const healthColor = getHealthColor(cluster.avgPm25)
              
              return (
                <Card key={cluster.id} className="relative overflow-hidden">
                  <div className={cn(
                    "absolute top-0 left-0 w-1 h-full",
                    `bg-${healthColor}`
                  )} />
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center justify-between text-base">
                      <span>Cluster {index + 1}</span>
                      <span className="text-xs font-normal text-muted-foreground bg-secondary px-2 py-1 rounded-full">
                        {cluster.sensorCount} sensors
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-2">
                        <MetricItem 
                          label="Avg PM2.5" 
                          value={cluster.avgPm25} 
                          unit="µg/m³"
                          status={healthColor}
                        />
                        <MetricItem 
                          label="Avg Temp" 
                          value={cluster.avgTemperature} 
                          unit="°F"
                        />
                        <MetricItem 
                          label="Avg Humidity" 
                          value={cluster.avgHumidity} 
                          unit="%"
                        />
                        <MetricItem 
                          label="Avg CO2" 
                          value={cluster.avgCo2} 
                          unit="ppm"
                          status={cluster.avgCo2 > 1500 ? 'destructive' : cluster.avgCo2 > 1000 ? 'warning' : undefined}
                        />
                        <MetricItem 
                          label="Avg Noise" 
                          value={cluster.avgNoise} 
                          unit="dB"
                        />
                      </div>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => handleViewOnMap(cluster.id)}
                      >
                        <MapPin className="w-4 h-4 mr-2" />
                        View on Map
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

function MetricItem({ 
  label, 
  value, 
  unit,
  status
}: { 
  label: string
  value: number
  unit: string
  status?: string
}) {
  return (
    <div className="bg-secondary/50 rounded-lg p-2">
      <p className="text-[10px] text-muted-foreground">{label}</p>
      <p className={cn(
        "text-sm font-semibold",
        status && `text-${status}`
      )}>
        {value}
        <span className="text-muted-foreground text-[10px] ml-1">{unit}</span>
      </p>
    </div>
  )
}
