"use client"

import { useDashboardStore } from '@/lib/store'
import { generateTimeSeriesData } from '@/lib/mock-data'
import { useMemo } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, TrendingDown, Wind, Thermometer, Droplets, Volume2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const COLORS = ['oklch(0.65 0.22 255)', 'oklch(0.65 0.2 145)', 'oklch(0.75 0.18 85)', 'oklch(0.55 0.22 25)']

export function AnalyticsView() {
  const { sensors, clusters, alerts } = useDashboardStore()
  
  const pm25Data = useMemo(() => generateTimeSeriesData(24), [])
  const temperatureData = useMemo(() => generateTimeSeriesData(24).map(d => ({ ...d, value: 60 + Math.random() * 20 })), [])
  
  const avgPm25 = sensors.reduce((sum, s) => sum + s.pm25, 0) / sensors.length
  const avgTemp = sensors.reduce((sum, s) => sum + s.temperature, 0) / sensors.length
  const avgHumidity = sensors.reduce((sum, s) => sum + s.humidity, 0) / sensors.length
  const avgNoise = sensors.reduce((sum, s) => sum + s.noise, 0) / sensors.length
  
  const statusDistribution = [
    { name: 'Normal', value: sensors.filter(s => s.status === 'normal').length },
    { name: 'Warning', value: sensors.filter(s => s.status === 'warning').length },
    { name: 'Critical', value: sensors.filter(s => s.status === 'critical').length },
  ]
  
  const clusterComparison = clusters.slice(0, 6).map((c, i) => ({
    name: `Cluster ${i + 1}`,
    pm25: c.avgPm25,
    co2: c.avgCo2 / 20,
    noise: c.avgNoise,
  }))
  
  // Calculate AQI from PM2.5 (simplified)
  const calculateAQI = (pm25: number) => {
    if (pm25 <= 12) return Math.round((50 / 12) * pm25)
    if (pm25 <= 35.4) return Math.round(50 + ((100 - 50) / (35.4 - 12)) * (pm25 - 12))
    if (pm25 <= 55.4) return Math.round(100 + ((150 - 100) / (55.4 - 35.4)) * (pm25 - 35.4))
    if (pm25 <= 150.4) return Math.round(150 + ((200 - 150) / (150.4 - 55.4)) * (pm25 - 55.4))
    return Math.round(200 + ((300 - 200) / (250.4 - 150.4)) * (pm25 - 150.4))
  }
  
  const currentAQI = calculateAQI(avgPm25)
  const aqiCategory = currentAQI <= 50 ? 'Good' : currentAQI <= 100 ? 'Moderate' : currentAQI <= 150 ? 'Unhealthy (Sensitive)' : 'Unhealthy'
  const aqiColor = currentAQI <= 50 ? 'text-success' : currentAQI <= 100 ? 'text-warning' : 'text-destructive'

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground text-sm">Environmental metrics and trends</p>
      </div>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard
          icon={Wind}
          label="Avg PM2.5"
          value={avgPm25.toFixed(1)}
          unit="µg/m³"
          trend={Math.random() > 0.5 ? 'up' : 'down'}
          trendValue="2.3%"
        />
        <MetricCard
          icon={Thermometer}
          label="Avg Temperature"
          value={avgTemp.toFixed(1)}
          unit="°F"
          trend={Math.random() > 0.5 ? 'up' : 'down'}
          trendValue="1.2°"
        />
        <MetricCard
          icon={Droplets}
          label="Avg Humidity"
          value={avgHumidity.toFixed(0)}
          unit="%"
          trend={Math.random() > 0.5 ? 'up' : 'down'}
          trendValue="5%"
        />
        <MetricCard
          icon={Volume2}
          label="Avg Noise"
          value={avgNoise.toFixed(0)}
          unit="dB"
          trend={Math.random() > 0.5 ? 'up' : 'down'}
          trendValue="3dB"
        />
      </div>
      
      {/* Charts Row 1 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* AQI Card */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Air Quality Index</CardTitle>
            <CardDescription>Current city-wide AQI</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center py-4">
              <div className="text-center">
                <p className={cn("text-5xl font-bold", aqiColor)}>{currentAQI}</p>
                <p className={cn("text-sm font-medium mt-1", aqiColor)}>{aqiCategory}</p>
              </div>
            </div>
            <div className="h-2 rounded-full bg-secondary overflow-hidden mt-4">
              <div 
                className={cn(
                  "h-full transition-all",
                  currentAQI <= 50 ? "bg-success" : currentAQI <= 100 ? "bg-warning" : "bg-destructive"
                )}
                style={{ width: `${Math.min(currentAQI / 3, 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
              <span>Good</span>
              <span>Moderate</span>
              <span>Unhealthy</span>
            </div>
          </CardContent>
        </Card>
        
        {/* Sensor Status Distribution */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Sensor Status</CardTitle>
            <CardDescription>Distribution by health</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[180px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={70}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {statusDistribution.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={index === 0 ? 'oklch(0.65 0.2 145)' : index === 1 ? 'oklch(0.75 0.18 85)' : 'oklch(0.55 0.22 25)'} 
                      />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      background: 'oklch(0.16 0.01 260)', 
                      border: '1px solid oklch(0.25 0.01 260)',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 text-xs">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-success" />
                Normal ({statusDistribution[0].value})
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-warning" />
                Warning ({statusDistribution[1].value})
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-destructive" />
                Critical ({statusDistribution[2].value})
              </span>
            </div>
          </CardContent>
        </Card>
        
        {/* Alerts Summary */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Alert Activity</CardTitle>
            <CardDescription>Last 24 hours</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Total Alerts</span>
                <span className="text-2xl font-bold">{alerts.length}</span>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Critical</span>
                  <span className="font-medium text-destructive">
                    {alerts.filter(a => a.severity === 'critical').length}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">High</span>
                  <span className="font-medium text-chart-4">
                    {alerts.filter(a => a.severity === 'high').length}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Medium</span>
                  <span className="font-medium text-warning">
                    {alerts.filter(a => a.severity === 'medium').length}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Low</span>
                  <span className="font-medium text-chart-2">
                    {alerts.filter(a => a.severity === 'low').length}
                  </span>
                </div>
              </div>
              <div className="pt-2 border-t border-border">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Acknowledged</span>
                  <span className="font-medium">
                    {alerts.filter(a => a.acknowledged).length} / {alerts.length}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Charts Row 2 */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* PM2.5 Trend */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">PM2.5 Trend</CardTitle>
            <CardDescription>24 hour rolling average</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={pm25Data}>
                  <defs>
                    <linearGradient id="colorPm25" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="oklch(0.65 0.22 255)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="oklch(0.65 0.22 255)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis 
                    dataKey="time" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10, fill: 'oklch(0.65 0 0)' }}
                  />
                  <YAxis 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10, fill: 'oklch(0.65 0 0)' }}
                    width={40}
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
                    fill="url(#colorPm25)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        
        {/* Temperature Trend */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Temperature Trend</CardTitle>
            <CardDescription>24 hour city average</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={temperatureData}>
                  <XAxis 
                    dataKey="time" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10, fill: 'oklch(0.65 0 0)' }}
                  />
                  <YAxis 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10, fill: 'oklch(0.65 0 0)' }}
                    width={40}
                    domain={['dataMin - 5', 'dataMax + 5']}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      background: 'oklch(0.16 0.01 260)', 
                      border: '1px solid oklch(0.25 0.01 260)',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                    formatter={(value: number) => [`${value.toFixed(1)}°F`, 'Temperature']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke="oklch(0.75 0.18 85)" 
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Cluster Comparison */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Cluster Comparison</CardTitle>
          <CardDescription>Environmental metrics by area</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={clusterComparison}>
                <XAxis 
                  dataKey="name" 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 10, fill: 'oklch(0.65 0 0)' }}
                />
                <YAxis 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 10, fill: 'oklch(0.65 0 0)' }}
                  width={40}
                />
                <Tooltip 
                  contentStyle={{ 
                    background: 'oklch(0.16 0.01 260)', 
                    border: '1px solid oklch(0.25 0.01 260)',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                />
                <Bar dataKey="pm25" fill="oklch(0.65 0.22 255)" radius={[4, 4, 0, 0]} name="PM2.5" />
                <Bar dataKey="noise" fill="oklch(0.65 0.2 145)" radius={[4, 4, 0, 0]} name="Noise" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-6 mt-2 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-sm" style={{ background: 'oklch(0.65 0.22 255)' }} />
              PM2.5 (µg/m³)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-sm" style={{ background: 'oklch(0.65 0.2 145)' }} />
              Noise (dB)
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function MetricCard({ 
  icon: Icon, 
  label, 
  value, 
  unit, 
  trend, 
  trendValue 
}: { 
  icon: typeof Wind
  label: string
  value: string
  unit: string
  trend: 'up' | 'down'
  trendValue: string
}) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-muted-foreground mb-1">{label}</p>
            <p className="text-2xl font-bold">
              {value}
              <span className="text-sm text-muted-foreground ml-1">{unit}</span>
            </p>
          </div>
          <div className={cn(
            "p-2 rounded-lg",
            trend === 'up' ? "bg-destructive/10" : "bg-success/10"
          )}>
            <Icon className={cn(
              "w-4 h-4",
              trend === 'up' ? "text-destructive" : "text-success"
            )} />
          </div>
        </div>
        <div className="flex items-center gap-1 mt-2">
          {trend === 'up' ? (
            <TrendingUp className="w-3 h-3 text-destructive" />
          ) : (
            <TrendingDown className="w-3 h-3 text-success" />
          )}
          <span className={cn(
            "text-xs font-medium",
            trend === 'up' ? "text-destructive" : "text-success"
          )}>
            {trendValue}
          </span>
          <span className="text-xs text-muted-foreground">vs last hour</span>
        </div>
      </CardContent>
    </Card>
  )
}
