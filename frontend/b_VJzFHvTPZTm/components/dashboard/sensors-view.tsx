"use client"

import { useDashboardStore } from '@/lib/store'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Search, MapPin, Battery, Wifi, ArrowUpDown } from 'lucide-react'
import { useState, useMemo } from 'react'

export function SensorsView() {
  const { sensors, selectSensor, setViewMode } = useDashboardStore()
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<string>('name')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  
  const filteredSensors = useMemo(() => {
    let result = sensors.filter(s => 
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.id.toLowerCase().includes(search.toLowerCase())
    )
    
    result.sort((a, b) => {
      const aVal = a[sortBy as keyof typeof a]
      const bVal = b[sortBy as keyof typeof b]
      
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
      }
      return 0
    })
    
    return result
  }, [sensors, search, sortBy, sortOrder])
  
  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('asc')
    }
  }
  
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
          <h1 className="text-2xl font-bold">Sensors</h1>
          <p className="text-muted-foreground text-sm">
            {sensors.length} sensors deployed
          </p>
        </div>
        
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search sensors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 bg-secondary border-0"
          />
        </div>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard 
          label="Total Sensors" 
          value={sensors.length} 
          color="primary"
        />
        <StatCard 
          label="Normal" 
          value={sensors.filter(s => s.status === 'normal').length} 
          color="success"
        />
        <StatCard 
          label="Warning" 
          value={sensors.filter(s => s.status === 'warning').length} 
          color="warning"
        />
        <StatCard 
          label="Critical" 
          value={sensors.filter(s => s.status === 'critical').length} 
          color="destructive"
        />
      </div>
      
      {/* Table */}
      <div className="flex-1 overflow-hidden rounded-xl border border-border bg-card">
        <div className="overflow-y-auto h-full">
          <Table>
            <TableHeader className="sticky top-0 bg-card">
              <TableRow>
                <TableHead className="w-[200px]">
                  <button 
                    className="flex items-center gap-1 hover:text-foreground"
                    onClick={() => handleSort('name')}
                  >
                    Sensor
                    <ArrowUpDown className="w-3 h-3" />
                  </button>
                </TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">
                  <button 
                    className="flex items-center gap-1 hover:text-foreground ml-auto"
                    onClick={() => handleSort('pm25')}
                  >
                    PM2.5
                    <ArrowUpDown className="w-3 h-3" />
                  </button>
                </TableHead>
                <TableHead className="text-right">
                  <button 
                    className="flex items-center gap-1 hover:text-foreground ml-auto"
                    onClick={() => handleSort('temperature')}
                  >
                    Temp
                    <ArrowUpDown className="w-3 h-3" />
                  </button>
                </TableHead>
                <TableHead className="text-right">
                  <button 
                    className="flex items-center gap-1 hover:text-foreground ml-auto"
                    onClick={() => handleSort('humidity')}
                  >
                    Humidity
                    <ArrowUpDown className="w-3 h-3" />
                  </button>
                </TableHead>
                <TableHead className="text-right">
                  <button 
                    className="flex items-center gap-1 hover:text-foreground ml-auto"
                    onClick={() => handleSort('co2')}
                  >
                    CO2
                    <ArrowUpDown className="w-3 h-3" />
                  </button>
                </TableHead>
                <TableHead className="text-right">Battery</TableHead>
                <TableHead className="text-right">Signal</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSensors.map((sensor) => (
                <TableRow key={sensor.id} className="hover:bg-secondary/50">
                  <TableCell>
                    <div>
                      <p className="font-medium">{sensor.name}</p>
                      <p className="text-xs text-muted-foreground">{sensor.id}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={cn(
                      "uppercase text-[10px]",
                      sensor.status === 'normal' && "bg-success/20 text-success",
                      sensor.status === 'warning' && "bg-warning/20 text-warning",
                      sensor.status === 'critical' && "bg-destructive/20 text-destructive"
                    )}>
                      {sensor.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    <span className={cn(
                      sensor.pm25 > 100 && "text-destructive",
                      sensor.pm25 > 50 && sensor.pm25 <= 100 && "text-warning"
                    )}>
                      {sensor.pm25}
                    </span>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {sensor.temperature}°F
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {sensor.humidity}%
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    <span className={cn(
                      sensor.co2 > 1500 && "text-destructive",
                      sensor.co2 > 1000 && sensor.co2 <= 1500 && "text-warning"
                    )}>
                      {sensor.co2}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Battery className={cn(
                        "w-3 h-3",
                        sensor.battery < 20 && "text-destructive",
                        sensor.battery >= 20 && sensor.battery < 50 && "text-warning",
                        sensor.battery >= 50 && "text-success"
                      )} />
                      <span className="font-mono text-sm">{Math.round(sensor.battery)}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Wifi className={cn(
                        "w-3 h-3",
                        sensor.signal < 30 && "text-destructive",
                        sensor.signal >= 30 && sensor.signal < 60 && "text-warning",
                        sensor.signal >= 60 && "text-success"
                      )} />
                      <span className="font-mono text-sm">{sensor.signal}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleLocate(sensor.id)}
                    >
                      <MapPin className="w-4 h-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}

function StatCard({ 
  label, 
  value, 
  color 
}: { 
  label: string
  value: number
  color: string 
}) {
  return (
    <div className={cn(
      "p-4 rounded-xl border bg-card"
    )}>
      <p className="text-sm text-muted-foreground mb-1">{label}</p>
      <p className={cn("text-3xl font-bold", `text-${color}`)}>{value}</p>
    </div>
  )
}
