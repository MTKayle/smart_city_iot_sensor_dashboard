"use client"

import { Radio, Layers, AlertTriangle, Thermometer, Droplets, Wind, Volume2, Flame } from 'lucide-react'
import { useDashboardStore } from '@/lib/store'
import { cn } from '@/lib/utils'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { HeatmapMetric } from '@/lib/types'

const heatmapOptions: { value: HeatmapMetric; label: string; icon: typeof Thermometer }[] = [
  { value: 'pm25', label: 'PM2.5', icon: Wind },
  { value: 'temperature', label: 'Temperature', icon: Thermometer },
  { value: 'humidity', label: 'Humidity', icon: Droplets },
  { value: 'co2', label: 'CO2', icon: Flame },
  { value: 'noise', label: 'Noise', icon: Volume2 },
]

export function LayerControls() {
  const { layers, toggleLayer, heatmapMetric, setHeatmapMetric } = useDashboardStore()

  return (
    <div className="absolute top-4 right-4 z-[1000] w-56 bg-card/95 backdrop-blur-sm border border-border rounded-xl shadow-xl p-4 space-y-4">
      <div className="flex items-center gap-2 pb-2 border-b border-border">
        <Layers className="w-4 h-4 text-primary" />
        <h3 className="font-semibold text-sm">Map Layers</h3>
      </div>
      
      {/* Layer Toggles */}
      <div className="space-y-3">
        <LayerToggle
          icon={Radio}
          label="Sensors"
          checked={layers.sensors}
          onToggle={() => toggleLayer('sensors')}
        />
        <LayerToggle
          icon={Layers}
          label="Clusters"
          checked={layers.clusters}
          onToggle={() => toggleLayer('clusters')}
        />
        <LayerToggle
          icon={AlertTriangle}
          label="Alerts"
          checked={layers.alerts}
          onToggle={() => toggleLayer('alerts')}
        />
      </div>
      
      {/* Heatmap Section */}
      <div className="pt-3 border-t border-border space-y-3">
        <LayerToggle
          icon={Thermometer}
          label="Heatmap"
          checked={layers.heatmap}
          onToggle={() => toggleLayer('heatmap')}
        />
        
        {layers.heatmap && (
          <Select value={heatmapMetric} onValueChange={(v) => setHeatmapMetric(v as HeatmapMetric)}>
            <SelectTrigger className="h-9 text-xs bg-secondary border-0">
              <SelectValue placeholder="Select metric" />
            </SelectTrigger>
            <SelectContent>
              {heatmapOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div className="flex items-center gap-2">
                    <option.icon className="w-3 h-3" />
                    <span>{option.label}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>
      
      {/* Legend */}
      <div className="pt-3 border-t border-border">
        <p className="text-[10px] text-muted-foreground mb-2">Legend</p>
        <div className="flex items-center gap-3 text-[10px]">
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-success" />
            <span>Normal</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-warning" />
            <span>Warning</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-destructive" />
            <span>Critical</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function LayerToggle({ 
  icon: Icon, 
  label, 
  checked, 
  onToggle 
}: { 
  icon: typeof Radio
  label: string
  checked: boolean
  onToggle: () => void 
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon className={cn(
          "w-4 h-4",
          checked ? "text-primary" : "text-muted-foreground"
        )} />
        <Label className="text-sm cursor-pointer" onClick={onToggle}>
          {label}
        </Label>
      </div>
      <Switch checked={checked} onCheckedChange={onToggle} />
    </div>
  )
}
