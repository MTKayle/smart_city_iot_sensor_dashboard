"use client"

import { useEffect } from 'react'
import dynamic from 'next/dynamic'
import { useDashboardStore } from '@/lib/store'
import { Sidebar } from './sidebar'
import { TopNavbar } from './top-navbar'
import { LayerControls } from './layer-controls'
import { DetailPanel } from './detail-panel'
import { AlertsView } from './alerts-view'
import { AnalyticsView } from './analytics-view'
import { SensorsView } from './sensors-view'
import { ClustersView } from './clusters-view'
import { DashboardView } from './dashboard-view'
import { SettingsView } from './settings-view'

// Dynamic import for the map to avoid SSR issues with Leaflet
const CityMap = dynamic(
  () => import('./city-map').then((mod) => mod.CityMap),
  { 
    ssr: false,
    loading: () => (
      <div className="w-full h-full bg-secondary flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading map...</div>
      </div>
    )
  }
)

export function DashboardLayout() {
  const { viewMode, isLive, updateData, initializeData } = useDashboardStore()
  
  // Initialize data on mount
  useEffect(() => {
    initializeData()
  }, [initializeData])
  
  // Real-time data updates
  useEffect(() => {
    if (!isLive) return
    
    const interval = setInterval(() => {
      updateData()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [isLive, updateData])

  const renderContent = () => {
    switch (viewMode) {
      case 'dashboard':
        return <DashboardView />
      case 'map':
        return (
          <div className="relative w-full h-full">
            <CityMap />
            <LayerControls />
            <DetailPanel />
          </div>
        )
      case 'sensors':
        return <SensorsView />
      case 'clusters':
        return <ClustersView />
      case 'alerts':
        return <AlertsView />
      case 'analytics':
        return <AnalyticsView />
      case 'settings':
        return <SettingsView />
      default:
        return (
          <div className="relative w-full h-full">
            <CityMap />
            <LayerControls />
            <DetailPanel />
          </div>
        )
    }
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopNavbar />
        <main className="flex-1 overflow-hidden">
          {renderContent()}
        </main>
      </div>
    </div>
  )
}
