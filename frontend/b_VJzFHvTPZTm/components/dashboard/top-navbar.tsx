"use client"

import { Search, Bell, User, Circle } from 'lucide-react'
import { useDashboardStore } from '@/lib/store'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'

export function TopNavbar() {
  const { isLive, toggleLive, alerts, setViewMode } = useDashboardStore()
  const unacknowledgedAlerts = alerts.filter(a => !a.acknowledged)
  const criticalAlerts = unacknowledgedAlerts.filter(a => a.severity === 'critical')

  return (
    <header className="flex items-center justify-between h-16 px-6 bg-card border-b border-border">
      {/* Search */}
      <div className="relative w-80">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Search sensors, locations..."
          className="pl-10 bg-secondary border-0 focus-visible:ring-1"
        />
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-4">
        {/* Live Status */}
        <button
          onClick={toggleLive}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all",
            isLive 
              ? "bg-success/20 text-success" 
              : "bg-muted text-muted-foreground"
          )}
        >
          <Circle className={cn(
            "w-2 h-2 fill-current",
            isLive && "animate-pulse"
          )} />
          {isLive ? 'LIVE' : 'PAUSED'}
        </button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="w-5 h-5" />
              {unacknowledgedAlerts.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center w-4 h-4 text-[10px] font-bold text-destructive-foreground bg-destructive rounded-full">
                  {unacknowledgedAlerts.length > 9 ? '9+' : unacknowledgedAlerts.length}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel className="flex items-center justify-between">
              <span>Notifications</span>
              {criticalAlerts.length > 0 && (
                <Badge variant="destructive" className="text-[10px]">
                  {criticalAlerts.length} Critical
                </Badge>
              )}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {unacknowledgedAlerts.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">
                No new notifications
              </div>
            ) : (
              <>
                {unacknowledgedAlerts.slice(0, 5).map((alert) => (
                  <DropdownMenuItem key={alert.id} className="flex flex-col items-start gap-1 py-3 cursor-pointer">
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        "w-2 h-2 rounded-full",
                        alert.severity === 'critical' && "bg-destructive",
                        alert.severity === 'high' && "bg-chart-4",
                        alert.severity === 'medium' && "bg-warning",
                        alert.severity === 'low' && "bg-chart-2"
                      )} />
                      <span className="font-medium text-sm">{alert.sensorName}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">{alert.message}</span>
                  </DropdownMenuItem>
                ))}
                {unacknowledgedAlerts.length > 5 && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      className="justify-center text-primary cursor-pointer"
                      onClick={() => setViewMode('alerts')}
                    >
                      View all {unacknowledgedAlerts.length} alerts
                    </DropdownMenuItem>
                  </>
                )}
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 pl-2 pr-3">
              <Avatar className="w-8 h-8">
                <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                  JD
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium hidden md:inline">John Doe</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="w-4 h-4 mr-2" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setViewMode('settings')}>
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive">
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
