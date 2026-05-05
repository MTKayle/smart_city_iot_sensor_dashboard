import React, { useState } from 'react';
import { X, Battery, Signal, TrendingUp, TrendingDown } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SensorWithTelemetry {
  id: string
  name: string
  lat: number
  lng: number
  pm25: number
  temp: number
  humidity: number
  co2: number
  noise: number
  battery: number
  signal: number
  status: 'critical' | 'warning' | 'normal'
  lastUpdate: string
}

interface ClusterData {
  id: string
  lat: number
  lng: number
  count: number
  avgPm25: number
  avgTemp: number
  avgHumidity: number
  avgCo2: number
  status: 'critical' | 'warning' | 'normal'
}

interface SensorDetailPanelProps {
  sensor?: SensorWithTelemetry;
  cluster?: ClusterData;
  onClose: () => void;
}

const SensorDetailPanel: React.FC<SensorDetailPanelProps> = ({ sensor, cluster, onClose }) => {
  const [timeRange, setTimeRange] = useState<'1h' | '24h'>('1h');

  // Dữ liệu mẫu cho biểu đồ
  const chartData = [
    { time: '12:33', value: 45 },
    { time: '05:33', value: 52 },
    { time: '10:33', value: 68 },
    { time: '03:33', value: 85 },
    { time: '12:33', value: sensor?.pm25 || cluster?.avgPm25 || 50 },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical':
        return 'text-red-400 bg-red-400/10';
      case 'warning':
        return 'text-yellow-400 bg-yellow-400/10';
      case 'normal':
        return 'text-green-400 bg-green-400/10';
      default:
        return 'text-gray-400 bg-gray-400/10';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'critical':
        return 'NGHIÊM TRỌNG';
      case 'warning':
        return 'CẢNH BÁO';
      case 'normal':
        return 'BÌNH THƯỜNG';
      default:
        return 'KHÔNG RÕ';
    }
  };

  return (
    <div className="sensor-detail-panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">
            {sensor ? sensor.name : `Cluster (${cluster?.count} sensors)`}
          </h2>
          {sensor && <p className="panel-subtitle">ID: {sensor.id}</p>}
        </div>
        <button className="close-btn" onClick={onClose}>
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="panel-content">
        {/* Trạng thái - Chỉ hiển thị cho sensor */}
        {sensor && (
          <div className="status-section">
            <span className={`status-badge ${getStatusColor(sensor.status)}`}>
              {getStatusText(sensor.status)}
            </span>
            <div className="status-indicators">
              <div className="indicator">
                <Battery className="w-4 h-4" />
                <span>{sensor.battery}%</span>
              </div>
              <div className="indicator">
                <Signal className="w-4 h-4" />
                <span>{sensor.signal}%</span>
              </div>
            </div>
          </div>
        )}

        {/* Các chỉ số */}
        <div className="metrics-grid">
          {sensor && (
            <>
              <div className="metric-card">
                <span className="metric-label">PM2.5</span>
                <div className="metric-value-container">
                  <span className="metric-value">{sensor.pm25.toFixed(1)}</span>
                  <span className="metric-unit">µg/m³</span>
                </div>
                <TrendingUp className="w-4 h-4 text-red-400" />
              </div>

              <div className="metric-card">
                <span className="metric-label">Nhiệt Độ</span>
                <div className="metric-value-container">
                  <span className="metric-value">{sensor.temp.toFixed(1)}</span>
                  <span className="metric-unit">°C</span>
                </div>
                <TrendingDown className="w-4 h-4 text-green-400" />
              </div>

              <div className="metric-card">
                <span className="metric-label">Độ Ẩm</span>
                <div className="metric-value-container">
                  <span className="metric-value">{sensor.humidity.toFixed(1)}</span>
                  <span className="metric-unit">%</span>
                </div>
                <TrendingUp className="w-4 h-4 text-red-400" />
              </div>

              <div className="metric-card">
                <span className="metric-label">CO2</span>
                <div className="metric-value-container">
                  <span className="metric-value">{sensor.co2.toFixed(0)}</span>
                  <span className="metric-unit">ppm</span>
                </div>
                <TrendingDown className="w-4 h-4 text-green-400" />
              </div>

              <div className="metric-card">
                <span className="metric-label">Tiếng Ồn</span>
                <div className="metric-value-container">
                  <span className="metric-value">{sensor.noise.toFixed(1)}</span>
                  <span className="metric-unit">dB</span>
                </div>
                <TrendingUp className="w-4 h-4 text-yellow-400" />
              </div>
            </>
          )}

          {cluster && (
            <>
              <div className="metric-card">
                <span className="metric-label">Avg PM2.5</span>
                <div className="metric-value-container">
                  <span className="metric-value">{cluster.avgPm25.toFixed(1)}</span>
                  <span className="metric-unit">µg/m³</span>
                </div>
              </div>

              <div className="metric-card">
                <span className="metric-label">Avg Nhiệt Độ</span>
                <div className="metric-value-container">
                  <span className="metric-value">{cluster.avgTemp.toFixed(1)}</span>
                  <span className="metric-unit">°C</span>
                </div>
              </div>

              <div className="metric-card">
                <span className="metric-label">Avg Độ Ẩm</span>
                <div className="metric-value-container">
                  <span className="metric-value">{cluster.avgHumidity.toFixed(1)}</span>
                  <span className="metric-unit">%</span>
                </div>
              </div>

              <div className="metric-card">
                <span className="metric-label">Avg CO2</span>
                <div className="metric-value-container">
                  <span className="metric-value">{cluster.avgCo2.toFixed(0)}</span>
                  <span className="metric-unit">ppm</span>
                </div>
              </div>

              <div className="metric-card">
                <span className="metric-label">Số Sensors</span>
                <div className="metric-value-container">
                  <span className="metric-value">{cluster.count}</span>
                  <span className="metric-unit"></span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Biểu đồ xu hướng */}
        <div className="chart-section">
          <div className="chart-header">
            <h3 className="chart-title">Xu Hướng PM2.5 ({timeRange === '1h' ? '1 giờ' : '24 giờ'})</h3>
            <div className="time-range-selector">
              <button
                className={`time-btn ${timeRange === '1h' ? 'active' : ''}`}
                onClick={() => setTimeRange('1h')}
              >
                1h
              </button>
              <button
                className={`time-btn ${timeRange === '24h' ? 'active' : ''}`}
                onClick={() => setTimeRange('24h')}
              >
                24h
              </button>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
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
                strokeWidth={2}
                dot={{ fill: '#3B82F6', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Thông tin bổ sung */}
        <div className="info-section">
          <div className="info-item">
            <span className="info-label">Vị Trí</span>
            <span className="info-value">
              {sensor ? `${sensor.lat.toFixed(4)}, ${sensor.lng.toFixed(4)}` : 
               cluster ? `${cluster.lat.toFixed(4)}, ${cluster.lng.toFixed(4)}` : ''}
            </span>
          </div>
          {sensor && (
            <div className="info-item">
              <span className="info-label">Cập Nhật Lần Cuối</span>
              <span className="info-value">{sensor.lastUpdate}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SensorDetailPanel;
