"use client"

import { 
  LayoutDashboard, 
  Map, 
  Radio, 
  Layers, 
  AlertTriangle, 
  BarChart3, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Cpu
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useDashboardStore } from '@/lib/store'
import type { ViewMode } from '@/lib/types'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

const navItems: { id: ViewMode; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'map', label: 'Map View', icon: Map },
  { id: 'sensors', label: 'Sensors', icon: Radio },
  { id: 'clusters', label: 'Clusters', icon: Layers },
  { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const { viewMode, setViewMode, sidebarCollapsed, toggleSidebar, alerts } = useDashboardStore()
  
  const unacknowledgedAlerts = alerts.filter(a => !a.acknowledged).length

  return (
    <TooltipProvider delayDuration={0}>
      <aside 
        className={cn(
          "flex flex-col h-full bg-sidebar border-r border-sidebar-border transition-all duration-300",
          sidebarCollapsed ? "w-16" : "w-56"
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 h-16 border-b border-sidebar-border">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary">
            <Cpu className="w-5 h-5 text-primary-foreground" />
          </div>
          {!sidebarCollapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-sidebar-foreground text-sm">SmartCity</span>
              <span className="text-[10px] text-muted-foreground">IoT Platform</span>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-2 space-y-1">
          {navItems.map((item) => {
            const isActive = viewMode === item.id
            const showBadge = item.id === 'alerts' && unacknowledgedAlerts > 0
            
            const button = (
              <button
                key={item.id}
                onClick={() => setViewMode(item.id)}
                className={cn(
                  "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-lg transition-all duration-200",
                  "hover:bg-sidebar-accent",
                  isActive && "bg-sidebar-accent text-sidebar-primary"
                )}
              >
                <item.icon className={cn(
                  "w-5 h-5 flex-shrink-0",
                  isActive ? "text-sidebar-primary" : "text-muted-foreground"
                )} />
                {!sidebarCollapsed && (
                  <span className={cn(
                    "text-sm font-medium",
                    isActive ? "text-sidebar-foreground" : "text-muted-foreground"
                  )}>
                    {item.label}
                  </span>
                )}
                {showBadge && (
                  <span className={cn(
                    "absolute flex items-center justify-center text-[10px] font-bold text-destructive-foreground bg-destructive rounded-full",
                    sidebarCollapsed ? "top-0 right-0 w-4 h-4" : "ml-auto w-5 h-5"
                  )}>
                    {unacknowledgedAlerts > 9 ? '9+' : unacknowledgedAlerts}
                  </span>
                )}
              </button>
            )

            if (sidebarCollapsed) {
              return (
                <Tooltip key={item.id}>
                  <TooltipTrigger asChild>{button}</TooltipTrigger>
                  <TooltipContent side="right" className="font-medium">
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              )
            }

            return button
          })}
        </nav>

        {/* Collapse Button */}
        <div className="p-2 border-t border-sidebar-border">
          <button
            onClick={toggleSidebar}
            className="flex items-center justify-center w-full p-2 rounded-lg hover:bg-sidebar-accent transition-colors"
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-5 h-5 text-muted-foreground" />
            ) : (
              <ChevronLeft className="w-5 h-5 text-muted-foreground" />
            )}
          </button>
        </div>
      </aside>
    </TooltipProvider>
  )
}
