"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Bell, Map, Database, Shield, Save } from 'lucide-react'

export function SettingsView() {
  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground text-sm">Configure your dashboard preferences</p>
      </div>
      
      <div className="max-w-3xl space-y-6">
        {/* Notifications */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-primary" />
              <CardTitle className="text-base">Notifications</CardTitle>
            </div>
            <CardDescription>Configure how you receive alerts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Critical Alerts</Label>
                <p className="text-xs text-muted-foreground">Receive notifications for critical sensor alerts</p>
              </div>
              <Switch defaultChecked />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <Label>Warning Alerts</Label>
                <p className="text-xs text-muted-foreground">Receive notifications for warning-level alerts</p>
              </div>
              <Switch defaultChecked />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <Label>Email Notifications</Label>
                <p className="text-xs text-muted-foreground">Send alert summaries to your email</p>
              </div>
              <Switch />
            </div>
            <div className="pt-2">
              <Label>Notification Email</Label>
              <Input 
                type="email" 
                placeholder="admin@smartcity.io" 
                className="mt-2 max-w-sm"
              />
            </div>
          </CardContent>
        </Card>
        
        {/* Map Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Map className="w-5 h-5 text-primary" />
              <CardTitle className="text-base">Map Settings</CardTitle>
            </div>
            <CardDescription>Customize map appearance and behavior</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Auto-center on Alerts</Label>
                <p className="text-xs text-muted-foreground">Automatically pan to new critical alerts</p>
              </div>
              <Switch defaultChecked />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <Label>Show Cluster Animations</Label>
                <p className="text-xs text-muted-foreground">Animate cluster transitions on zoom</p>
              </div>
              <Switch defaultChecked />
            </div>
            <Separator />
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <Label>Default Zoom Level</Label>
                <Select defaultValue="12">
                  <SelectTrigger className="mt-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">City Wide (10)</SelectItem>
                    <SelectItem value="12">District (12)</SelectItem>
                    <SelectItem value="14">Neighborhood (14)</SelectItem>
                    <SelectItem value="16">Street (16)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Map Style</Label>
                <Select defaultValue="dark">
                  <SelectTrigger className="mt-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="satellite">Satellite</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Data Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-primary" />
              <CardTitle className="text-base">Data Settings</CardTitle>
            </div>
            <CardDescription>Configure data refresh and storage</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Refresh Interval</Label>
                <Select defaultValue="5">
                  <SelectTrigger className="mt-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 second</SelectItem>
                    <SelectItem value="5">5 seconds</SelectItem>
                    <SelectItem value="10">10 seconds</SelectItem>
                    <SelectItem value="30">30 seconds</SelectItem>
                    <SelectItem value="60">1 minute</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Data Retention</Label>
                <Select defaultValue="30">
                  <SelectTrigger className="mt-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7">7 days</SelectItem>
                    <SelectItem value="30">30 days</SelectItem>
                    <SelectItem value="90">90 days</SelectItem>
                    <SelectItem value="365">1 year</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <Label>Data Compression</Label>
                <p className="text-xs text-muted-foreground">Compress historical data to save storage</p>
              </div>
              <Switch defaultChecked />
            </div>
          </CardContent>
        </Card>
        
        {/* Thresholds */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              <CardTitle className="text-base">Alert Thresholds</CardTitle>
            </div>
            <CardDescription>Set custom alert thresholds for metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>PM2.5 Warning (µg/m³)</Label>
                <Input type="number" defaultValue="50" className="mt-2" />
              </div>
              <div>
                <Label>PM2.5 Critical (µg/m³)</Label>
                <Input type="number" defaultValue="100" className="mt-2" />
              </div>
              <div>
                <Label>CO2 Warning (ppm)</Label>
                <Input type="number" defaultValue="1000" className="mt-2" />
              </div>
              <div>
                <Label>CO2 Critical (ppm)</Label>
                <Input type="number" defaultValue="1500" className="mt-2" />
              </div>
              <div>
                <Label>Temperature High (°F)</Label>
                <Input type="number" defaultValue="95" className="mt-2" />
              </div>
              <div>
                <Label>Noise High (dB)</Label>
                <Input type="number" defaultValue="85" className="mt-2" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Save Button */}
        <div className="flex justify-end pt-4 pb-8">
          <Button>
            <Save className="w-4 h-4 mr-2" />
            Save Settings
          </Button>
        </div>
      </div>
    </div>
  )
}
