"use client"

import { useDashboardStore } from '@/lib/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Radio, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  Wind, 
  Thermometer,
  Activity,
  MapPin
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { AreaChart, Area, ResponsiveContainer } from 'recharts'
import { generateTimeSeriesData } from '@/lib/mock-data'
import { useMemo } from 'react'

export function DashboardView() {
  const { sensors, alerts, clusters, setViewMode, selectSensor } = useDashboardStore()
  
  const sparklineData = useMemo(() => generateTimeSeriesData(12), [])
  
  const avgPm25 = sensors.reduce((sum, s) => sum + s.pm25, 0) / sensors.length
  const avgTemp = sensors.reduce((sum, s) => sum + s.temperature, 0) / sensors.length
  
  const criticalAlerts = alerts.filter(a => a.severity === 'critical' && !a.acknowledged)
  const criticalSensors = sensors.filter(s => s.status === 'critical')
  
  // Calculate AQI
  const calculateAQI = (pm25: number) => {
    if (pm25 <= 12) return Math.round((50 / 12) * pm25)
    if (pm25 <= 35.4) return Math.round(50 + ((100 - 50) / (35.4 - 12)) * (pm25 - 12))
    if (pm25 <= 55.4) return Math.round(100 + ((150 - 100) / (55.4 - 35.4)) * (pm25 - 35.4))
    return Math.round(150 + ((200 - 150) / (150.4 - 55.4)) * (pm25 - 55.4))
  }
  
  const currentAQI = calculateAQI(avgPm25)
  const aqiCategory = currentAQI <= 50 ? 'Good' : currentAQI <= 100 ? 'Moderate' : 'Unhealthy'

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground text-sm">Smart City IoT Overview</p>
      </div>
      
      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Active Sensors</p>
                <p className="text-3xl font-bold">{sensors.length}</p>
              </div>
              <div className="p-2 rounded-lg bg-primary/10">
                <Radio className="w-5 h-5 text-primary" />
              </div>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Badge className="bg-success/20 text-success text-[10px]">
                {sensors.filter(s => s.status === 'normal').length} Normal
              </Badge>
              <Badge className="bg-warning/20 text-warning text-[10px]">
                {sensors.filter(s => s.status === 'warning').length} Warning
              </Badge>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Air Quality Index</p>
                <p className={cn(
                  "text-3xl font-bold",
                  currentAQI <= 50 ? "text-success" : currentAQI <= 100 ? "text-warning" : "text-destructive"
                )}>
                  {currentAQI}
                </p>
              </div>
              <div className={cn(
                "p-2 rounded-lg",
                currentAQI <= 50 ? "bg-success/10" : currentAQI <= 100 ? "bg-warning/10" : "bg-destructive/10"
              )}>
                <Wind className={cn(
                  "w-5 h-5",
                  currentAQI <= 50 ? "text-success" : currentAQI <= 100 ? "text-warning" : "text-destructive"
                )} />
              </div>
            </div>
            <p className={cn(
              "text-xs font-medium mt-2",
              currentAQI <= 50 ? "text-success" : currentAQI <= 100 ? "text-warning" : "text-destructive"
            )}>
              {aqiCategory}
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Active Alerts</p>
                <p className="text-3xl font-bold">{alerts.filter(a => !a.acknowledged).length}</p>
              </div>
              <div className="p-2 rounded-lg bg-destructive/10">
                <AlertTriangle className="w-5 h-5 text-destructive" />
              </div>
            </div>
            <Button 
              variant="link" 
              className="p-0 h-auto text-xs mt-2"
              onClick={() => setViewMode('alerts')}
            >
              View all alerts →
            </Button>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Avg Temperature</p>
                <p className="text-3xl font-bold">{avgTemp.toFixed(1)}°F</p>
              </div>
              <div className="p-2 rounded-lg bg-warning/10">
                <Thermometer className="w-5 h-5 text-warning" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
              <TrendingUp className="w-3 h-3 text-destructive" />
              <span>+2.3° from yesterday</span>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-3 gap-6">
        {/* PM2.5 Trend */}
        <Card className="col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">PM2.5 Trend</CardTitle>
            <CardDescription>City-wide average over last 12 hours</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sparklineData}>
                  <defs>
                    <linearGradient id="colorPm25Dash" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="oklch(0.65 0.22 255)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="oklch(0.65 0.22 255)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Area 
                    type="monotone" 
                    dataKey="value" 
                    stroke="oklch(0.65 0.22 255)" 
                    fillOpacity={1}
                    fill="url(#colorPm25Dash)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center justify-between text-xs text-muted-foreground mt-2">
              <span>12 hours ago</span>
              <span>Now</span>
            </div>
          </CardContent>
        </Card>
        
        {/* Critical Alerts */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Critical Alerts</CardTitle>
              <Badge variant="destructive" className="text-[10px]">
                {criticalAlerts.length}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {criticalAlerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                <Activity className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm">No critical alerts</p>
              </div>
            ) : (
              <div className="space-y-3">
                {criticalAlerts.slice(0, 4).map(alert => (
                  <div 
                    key={alert.id}
                    className="p-3 rounded-lg bg-destructive/10 border border-destructive/20"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm">{alert.sensorName}</span>
                      <span className="text-[10px] text-muted-foreground">
                        {alert.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">{alert.message}</p>
                  </div>
                ))}
                {criticalAlerts.length > 4 && (
                  <Button 
                    variant="ghost" 
                    className="w-full text-xs"
                    onClick={() => setViewMode('alerts')}
                  >
                    View {criticalAlerts.length - 4} more alerts
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Bottom Row */}
      <div className="grid grid-cols-2 gap-6 mt-6">
        {/* Critical Sensors */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Sensors Requiring Attention</CardTitle>
            <CardDescription>Sensors with critical or warning status</CardDescription>
          </CardHeader>
          <CardContent>
            {criticalSensors.length === 0 ? (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <p className="text-sm">All sensors operating normally</p>
              </div>
            ) : (
              <div className="space-y-2">
                {sensors
                  .filter(s => s.status !== 'normal')
                  .slice(0, 5)
                  .map(sensor => (
                    <div 
                      key={sensor.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors cursor-pointer"
                      onClick={() => {
                        selectSensor(sensor)
                        setViewMode('map')
                      }}
                    >
                      <div className="flex items-center gap-3">
                        <span className={cn(
                          "w-2 h-2 rounded-full",
                          sensor.status === 'critical' && "bg-destructive",
                          sensor.status === 'warning' && "bg-warning"
                        )} />
                        <div>
                          <p className="font-medium text-sm">{sensor.name}</p>
                          <p className="text-xs text-muted-foreground">
                            PM2.5: {sensor.pm25} · CO2: {sensor.co2}
                          </p>
                        </div>
                      </div>
                      <MapPin className="w-4 h-4 text-muted-foreground" />
                    </div>
                  ))}
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Cluster Summary */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Cluster Overview</CardTitle>
            <CardDescription>{clusters.length} clusters identified</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {clusters.slice(0, 4).map((cluster, i) => (
                <div 
                  key={cluster.id}
                  className="p-3 rounded-lg bg-secondary/50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">Cluster {i + 1}</span>
                    <span className="text-xs text-muted-foreground">
                      {cluster.sensorCount} sensors
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    <p>PM2.5: <span className={cn(
                      "font-medium",
                      cluster.avgPm25 > 100 ? "text-destructive" : cluster.avgPm25 > 50 ? "text-warning" : "text-foreground"
                    )}>{cluster.avgPm25}</span></p>
                    <p>Temp: <span className="text-foreground font-medium">{cluster.avgTemperature}°F</span></p>
                  </div>
                </div>
              ))}
            </div>
            {clusters.length > 4 && (
              <Button 
                variant="ghost" 
                className="w-full mt-3 text-xs"
                onClick={() => setViewMode('clusters')}
              >
                View all {clusters.length} clusters
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
