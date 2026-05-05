"use client"

import { AlertTriangle, Check, MapPin, Clock, Filter } from 'lucide-react'
import { useDashboardStore } from '@/lib/store'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useState } from 'react'

export function AlertsView() {
  const { alerts, acknowledgeAlert, selectSensor, sensors, setViewMode } = useDashboardStore()
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  
  const filteredAlerts = alerts.filter(alert => {
    if (severityFilter !== 'all' && alert.severity !== severityFilter) return false
    if (typeFilter !== 'all' && alert.type !== typeFilter) return false
    return true
  })
  
  const criticalCount = alerts.filter(a => a.severity === 'critical' && !a.acknowledged).length
  const highCount = alerts.filter(a => a.severity === 'high' && !a.acknowledged).length
  const mediumCount = alerts.filter(a => a.severity === 'medium' && !a.acknowledged).length
  const lowCount = alerts.filter(a => a.severity === 'low' && !a.acknowledged).length
  
  const handleLocate = (sensorId: string) => {
    const sensor = sensors.find(s => s.id === sensorId)
    if (sensor) {
      selectSensor(sensor)
      setViewMode('map')
    }
  }

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Alerts</h1>
          <p className="text-muted-foreground text-sm">
            {alerts.filter(a => !a.acknowledged).length} unacknowledged alerts
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-32 h-9">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-32 h-9">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="threshold">Threshold</SelectItem>
                <SelectItem value="predictive">Predictive</SelectItem>
                <SelectItem value="anomaly">Anomaly</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Critical" count={criticalCount} color="destructive" />
        <StatCard label="High" count={highCount} color="chart-4" />
        <StatCard label="Medium" count={mediumCount} color="warning" />
        <StatCard label="Low" count={lowCount} color="chart-2" />
      </div>
      
      {/* Alert List */}
      <div className="flex-1 overflow-y-auto space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <AlertTriangle className="w-12 h-12 mb-4 opacity-50" />
            <p>No alerts match your filters</p>
          </div>
        ) : (
          filteredAlerts.map(alert => (
            <div 
              key={alert.id}
              className={cn(
                "p-4 rounded-xl border bg-card transition-all",
                alert.acknowledged && "opacity-60",
                !alert.acknowledged && alert.severity === 'critical' && "border-destructive/50 bg-destructive/5",
                !alert.acknowledged && alert.severity === 'high' && "border-chart-4/50 bg-chart-4/5",
                !alert.acknowledged && alert.severity === 'medium' && "border-warning/50 bg-warning/5",
                !alert.acknowledged && alert.severity === 'low' && "border-chart-2/50 bg-chart-2/5"
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={cn(
                      "uppercase text-[10px]",
                      alert.severity === 'critical' && "bg-destructive/20 text-destructive",
                      alert.severity === 'high' && "bg-chart-4/20 text-chart-4",
                      alert.severity === 'medium' && "bg-warning/20 text-warning",
                      alert.severity === 'low' && "bg-chart-2/20 text-chart-2"
                    )}>
                      {alert.severity}
                    </Badge>
                    <Badge variant="outline" className="text-[10px]">
                      {alert.type}
                    </Badge>
                    {alert.acknowledged && (
                      <Badge variant="secondary" className="text-[10px]">
                        Acknowledged
                      </Badge>
                    )}
                  </div>
                  
                  <h3 className="font-medium mb-1">{alert.message}</h3>
                  
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {alert.sensorName}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {alert.timestamp.toLocaleString()}
                    </span>
                    <span>
                      {alert.metric}: <span className="text-foreground font-medium">{alert.value}</span> 
                      {' '}(threshold: {alert.threshold})
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 ml-4">
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => handleLocate(alert.sensorId)}
                  >
                    <MapPin className="w-4 h-4 mr-1" />
                    Locate
                  </Button>
                  {!alert.acknowledged && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => acknowledgeAlert(alert.id)}
                    >
                      <Check className="w-4 h-4 mr-1" />
                      Acknowledge
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function StatCard({ 
  label, 
  count, 
  color 
}: { 
  label: string
  count: number
  color: string 
}) {
  return (
    <div className={cn(
      "p-4 rounded-xl border bg-card",
      `border-${color}/30`
    )}>
      <p className="text-sm text-muted-foreground mb-1">{label}</p>
      <p className={cn("text-3xl font-bold", `text-${color}`)}>{count}</p>
    </div>
  )
}
