import React, { useEffect, useState } from 'react';
import { Radio, Wind, AlertTriangle, Thermometer, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAppContext } from '../../context/AppContext';
import { fetchTelemetry } from '../../services/api';
import type { Telemetry } from '../../types';

import type { ViewType } from './types';

interface DashboardProps {
  onNavigate?: (view: ViewType) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onNavigate }) => {
  const { sensors, alerts, telemetryMap, connectionStatus } = useAppContext();
  const [pm25Data, setPm25Data] = useState<Array<{ time: string; value: number }>>([]);

  // Load PM2.5 trend data from first sensor
  useEffect(() => {
    const loadPm25Trend = async () => {
      if (sensors.length === 0) return;
      
      try {
        const firstSensor = sensors[0];
        const telemetryData = await fetchTelemetry(firstSensor.sensorId, { limit: 24 });
        
        const chartData = telemetryData
          .slice(0, 8)
          .reverse()
          .map((t: Telemetry) => ({
            time: new Date(t.timestamp).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
            value: (t.pm25 ?? t.data?.pm25 ?? 0) as number,
          }));
        
        setPm25Data(chartData);
      } catch (error) {
        console.error('Failed to load PM2.5 trend:', error);
      }
    };

    loadPm25Trend();
  }, [sensors]);

  // Read flat field with nested fallback (WS now normalises but keep defensive).
  const pickPm25 = (t?: Telemetry) => (t?.pm25 ?? t?.data?.pm25 ?? null);
  const pickCo2 = (t?: Telemetry) => (t?.co2 ?? t?.data?.co2 ?? null);
  const pickTemp = (t?: Telemetry) => (t?.temperature ?? t?.data?.temperature ?? null);

  const activeSensors = sensors.filter((s) => s.status === 'Active').length;
  const normalSensors = sensors.filter((s) => {
    const t = telemetryMap[s.sensorId];
    if (!t) return false;
    return (pickPm25(t) ?? 0) < 50 && (pickCo2(t) ?? 0) < 1000;
  }).length;
  const warningSensors = sensors.filter((s) => {
    const t = telemetryMap[s.sensorId];
    if (!t) return false;
    const pm25 = pickPm25(t) ?? 0;
    const co2 = pickCo2(t) ?? 0;
    return (pm25 >= 50 && pm25 < 100) || (co2 >= 1000 && co2 < 2000);
  }).length;

  // Average AQI / temperature only over sensors that actually have telemetry.
  const liveTelemetry = sensors
    .map((s) => telemetryMap[s.sensorId])
    .filter((t): t is Telemetry => t !== undefined);

  const avgOver = (vals: Array<number | null | undefined>): number => {
    const nums = vals.filter(
      (v): v is number => typeof v === 'number' && !isNaN(v),
    );
    return nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : 0;
  };

  const avgAqi = avgOver(liveTelemetry.map((t) => t.aqi ?? null));
  const avgTemp = avgOver(liveTelemetry.map((t) => pickTemp(t)));

  const aqiCategory =
    avgAqi > 150
      ? 'Không lành mạnh'
      : avgAqi > 100
      ? 'Không lành mạnh cho nhóm nhạy cảm'
      : avgAqi > 50
      ? 'Trung bình'
      : 'Tốt';

  // Get critical alerts (HIGH or CRITICAL severity)
  const criticalAlerts = alerts
    .filter(a => a.severity === 'HIGH' || a.severity === 'CRITICAL')
    .slice(0, 2)
    .map(a => ({
      id: a.alertId,
      location: a.locationId,
      message: `${a.metricType} ${a.value.toFixed(1)} vượt ngưỡng`,
      time: new Date(a.createdAt).toLocaleTimeString('vi-VN'),
    }));

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h1 className="view-title">Tổng Quan</h1>
        <p className="view-subtitle">Tổng quan hệ thống IoT thành phố thông minh</p>
      </div>

      {/* Connection Status */}
      {connectionStatus !== 'connected' && (
        <div className="alert alert-warning mb-4">
          WebSocket: {connectionStatus === 'connecting' ? 'Đang kết nối...' : 
                      connectionStatus === 'disconnected' ? 'Mất kết nối' : 'Lỗi kết nối'}
        </div>
      )}

      {/* Thẻ thống kê */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Cảm Biến Hoạt Động</span>
            <Radio className="stat-icon text-blue-400" />
          </div>
          <div className="stat-value">{activeSensors}</div>
          <div className="stat-badges">
            <span className="badge badge-success">{normalSensors} Bình thường</span>
            <span className="badge badge-warning">{warningSensors} Cảnh báo</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Chỉ Số Chất Lượng Không Khí</span>
            <Wind className={`stat-icon ${avgAqi > 150 ? 'text-red-400' : avgAqi > 100 ? 'text-orange-400' : 'text-green-400'}`} />
          </div>
          <div className={`stat-value ${avgAqi > 150 ? 'text-red-400' : avgAqi > 100 ? 'text-orange-400' : 'text-green-400'}`}>
            {avgAqi.toFixed(0)}
          </div>
          <div className="stat-footer">
            <span className={`stat-status ${avgAqi > 150 ? 'text-red-400' : avgAqi > 100 ? 'text-orange-400' : 'text-green-400'}`}>
              {aqiCategory}
            </span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Cảnh Báo Đang Hoạt Động</span>
            <AlertTriangle className="stat-icon text-yellow-400" />
          </div>
          <div className="stat-value">{alerts.length}</div>
          <div className="stat-footer">
            <a 
              href="#" 
              className="stat-link"
              onClick={(e) => {
                e.preventDefault();
                onNavigate?.('alerts');
              }}
            >
              Xem tất cả cảnh báo →
            </a>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Nhiệt Độ Trung Bình</span>
            <Thermometer className="stat-icon text-orange-400" />
          </div>
          <div className="stat-value">{avgTemp.toFixed(1)}°C</div>
          <div className="stat-footer">
            <TrendingUp className="w-4 h-4 text-green-400" />
            <span className="stat-change text-green-400">Cập nhật real-time</span>
          </div>
        </div>
      </div>

      {/* Biểu đồ và cảnh báo */}
      <div className="dashboard-content">
        <div className="chart-card">
          <div className="card-header">
            <h3 className="card-title">Xu Hướng PM2.5</h3>
            <p className="card-subtitle">Trung bình toàn thành phố trong 12 giờ qua</p>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={pm25Data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3B82F6"
                  strokeWidth={3}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="alerts-card">
          <div className="card-header">
            <h3 className="card-title">Cảnh Báo Nghiêm Trọng</h3>
            <span className="alert-count">{criticalAlerts.length}</span>
          </div>
          <div className="alerts-list">
            {criticalAlerts.length > 0 ? (
              criticalAlerts.map((alert) => (
                <div key={alert.id} className="alert-item">
                  <div className="alert-content">
                    <h4 className="alert-location">{alert.location}</h4>
                    <p className="alert-message">{alert.message}</p>
                  </div>
                  <span className="alert-time">{alert.time}</span>
                </div>
              ))
            ) : (
              <div className="alert-item">
                <p className="text-gray-400">Không có cảnh báo nghiêm trọng</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
