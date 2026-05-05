"use client"

import { X, Battery, Wifi, Clock, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react'
import { useDashboardStore } from '@/lib/store'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { generateTimeSeriesData } from '@/lib/mock-data'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { useMemo } from 'react'

export function DetailPanel() {
  const { 
    selectedSensor, 
    selectedCluster, 
    detailPanelOpen, 
    setDetailPanelOpen,
    selectSensor,
    selectCluster,
    alerts 
  } = useDashboardStore()
  
  const timeSeriesData = useMemo(() => generateTimeSeriesData(24), [])
  
  const sensorAlerts = selectedSensor 
    ? alerts.filter(a => a.sensorId === selectedSensor.id)
    : []
  
  const handleClose = () => {
    setDetailPanelOpen(false)
    selectSensor(null)
    selectCluster(null)
  }
  
  if (!detailPanelOpen || (!selectedSensor && !selectedCluster)) {
    return null
  }

  return (
    <div className={cn(
      "absolute top-0 right-0 h-full w-96 bg-card border-l border-border z-[1001]",
      "transform transition-transform duration-300 ease-out",
      detailPanelOpen ? "translate-x-0" : "translate-x-full"
    )}>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h2 className="font-semibold text-lg">
              {selectedSensor ? selectedSensor.name : `Cluster (${selectedCluster?.sensorCount} sensors)`}
            </h2>
            {selectedSensor && (
              <p className="text-xs text-muted-foreground">ID: {selectedSensor.id}</p>
            )}
          </div>
          <Button variant="ghost" size="icon" onClick={handleClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Status & Quick Stats */}
          {selectedSensor && (
            <>
              <div className="flex items-center gap-3">
                <Badge className={cn(
                  "uppercase",
                  selectedSensor.status === 'normal' && "bg-success/20 text-success border-success/30",
                  selectedSensor.status === 'warning' && "bg-warning/20 text-warning border-warning/30",
                  selectedSensor.status === 'critical' && "bg-destructive/20 text-destructive border-destructive/30"
                )}>
                  {selectedSensor.status}
                </Badge>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Battery className="w-3 h-3" />
                    {Math.round(selectedSensor.battery)}%
                  </span>
                  <span className="flex items-center gap-1">
                    <Wifi className="w-3 h-3" />
                    {selectedSensor.signal}%
                  </span>
                </div>
              </div>
              
              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-3">
                <MetricCard 
                  label="PM2.5" 
                  value={selectedSensor.pm25} 
                  unit="µg/m³"
                  trend={Math.random() > 0.5 ? 'up' : 'down'}
                  status={selectedSensor.pm25 > 100 ? 'critical' : selectedSensor.pm25 > 50 ? 'warning' : 'normal'}
                />
                <MetricCard 
                  label="Temperature" 
                  value={selectedSensor.temperature} 
                  unit="°F"
                  trend={Math.random() > 0.5 ? 'up' : 'down'}
                />
                <MetricCard 
                  label="Humidity" 
                  value={selectedSensor.humidity} 
                  unit="%"
                  trend={Math.random() > 0.5 ? 'up' : 'down'}
                />
                <MetricCard 
                  label="CO2" 
                  value={selectedSensor.co2} 
                  unit="ppm"
                  trend={Math.random() > 0.5 ? 'up' : 'down'}
                  status={selectedSensor.co2 > 1500 ? 'critical' : selectedSensor.co2 > 1000 ? 'warning' : 'normal'}
                />
                <MetricCard 
                  label="Noise" 
                  value={selectedSensor.noise} 
                  unit="dB"
                  trend={Math.random() > 0.5 ? 'up' : 'down'}
                />
              </div>
            </>
          )}
          
          {selectedCluster && (
            <div className="grid grid-cols-2 gap-3">
              <MetricCard label="Avg PM2.5" value={selectedCluster.avgPm25} unit="µg/m³" />
              <MetricCard label="Avg Temp" value={selectedCluster.avgTemperature} unit="°F" />
              <MetricCard label="Avg Humidity" value={selectedCluster.avgHumidity} unit="%" />
              <MetricCard label="Avg CO2" value={selectedCluster.avgCo2} unit="ppm" />
              <MetricCard label="Avg Noise" value={selectedCluster.avgNoise} unit="dB" />
              <MetricCard label="Sensors" value={selectedCluster.sensorCount} unit="" />
            </div>
          )}
          
          {/* Chart */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-sm">PM2.5 Trend (24h)</h3>
              <div className="flex gap-1">
                <Button variant="ghost" size="sm" className="h-6 px-2 text-xs">1h</Button>
                <Button variant="secondary" size="sm" className="h-6 px-2 text-xs">24h</Button>
              </div>
            </div>
            <div className="h-40 bg-secondary/50 rounded-lg p-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeSeriesData}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="oklch(0.65 0.22 255)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="oklch(0.65 0.22 255)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis 
                    dataKey="time" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10, fill: 'oklch(0.65 0 0)' }}
                    interval="preserveStartEnd"
                  />
                  <YAxis 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10, fill: 'oklch(0.65 0 0)' }}
                    width={30}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      background: 'oklch(0.16 0.01 260)', 
                      border: '1px solid oklch(0.25 0.01 260)',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="value" 
                    stroke="oklch(0.65 0.22 255)" 
                    fillOpacity={1}
                    fill="url(#colorValue)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* Alerts for this sensor */}
          {selectedSensor && sensorAlerts.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium text-sm flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-warning" />
                Active Alerts ({sensorAlerts.length})
              </h3>
              <div className="space-y-2">
                {sensorAlerts.map(alert => (
                  <div 
                    key={alert.id}
                    className={cn(
                      "p-3 rounded-lg border",
                      alert.severity === 'critical' && "bg-destructive/10 border-destructive/30",
                      alert.severity === 'high' && "bg-chart-4/10 border-chart-4/30",
                      alert.severity === 'medium' && "bg-warning/10 border-warning/30",
                      alert.severity === 'low' && "bg-chart-2/10 border-chart-2/30"
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <Badge variant="outline" className="text-[10px] uppercase">
                        {alert.severity}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground">
                        {alert.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm">{alert.message}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {alert.metric}: {alert.value} (threshold: {alert.threshold})
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Last Updated */}
          {selectedSensor && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground pt-2 border-t border-border">
              <Clock className="w-3 h-3" />
              <span>Last updated: {selectedSensor.lastUpdated.toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function MetricCard({ 
  label, 
  value, 
  unit, 
  trend,
  status = 'normal'
}: { 
  label: string
  value: number
  unit: string
  trend?: 'up' | 'down'
  status?: 'normal' | 'warning' | 'critical'
}) {
  return (
    <div className={cn(
      "p-3 rounded-lg bg-secondary",
      status === 'warning' && "ring-1 ring-warning/50",
      status === 'critical' && "ring-1 ring-destructive/50"
    )}>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <div className="flex items-end justify-between">
        <p className="text-xl font-semibold">
          {value}
          <span className="text-xs text-muted-foreground ml-1">{unit}</span>
        </p>
        {trend && (
          <span className={cn(
            "flex items-center text-xs",
            trend === 'up' ? "text-destructive" : "text-success"
          )}>
            {trend === 'up' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          </span>
        )}
      </div>
    </div>
  )
}
