import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useAppContext } from '../../context/AppContext';
import { fetchClusters, fetchClusterTelemetry, fetchTelemetry } from '../../services/api';
import type { ClusterAnalytics } from '../../types';

const AnalyticsView: React.FC = () => {
  const { sensors, alerts, telemetryMap } = useAppContext();
  const [pm25TrendData, setPm25TrendData] = useState<Array<{ time: string; value: number }>>([]);
  const [clusterComparisonData, setClusterComparisonData] = useState<Array<{ name: string; pm25: number; noise: number }>>([]);

  // Load PM2.5 trend data
  useEffect(() => {
    const loadPm25Trend = async () => {
      if (sensors.length === 0) return;
      
      try {
        const firstSensor = sensors[0];
        const telemetryData = await fetchTelemetry(firstSensor.sensorId, { limit: 24 });
        
        const chartData = telemetryData
          .slice(0, 6)
          .reverse()
          .map((t) => ({
            time: new Date(t.timestamp).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
            value: t.pm25 || 0,
          }));
        
        setPm25TrendData(chartData);
      } catch (error) {
        console.error('Failed to load PM2.5 trend:', error);
      }
    };

    loadPm25Trend();
  }, [sensors]);

  // Load cluster comparison data
  useEffect(() => {
    const loadClusterComparison = async () => {
      try {
        const clustersData = await fetchClusters();
        const comparisonData = await Promise.all(
          clustersData.slice(0, 6).map(async (cluster) => {
            try {
              const analytics: ClusterAnalytics = await fetchClusterTelemetry(cluster.clusterId);
              return {
                name: cluster.clusterName || cluster.clusterId,
                pm25: analytics.avgPM25 || 0,
                noise: analytics.avgNoise || 0,
              };
            } catch (error) {
              return {
                name: cluster.clusterName || cluster.clusterId,
                pm25: 0,
                noise: 0,
              };
            }
          })
        );
        
        setClusterComparisonData(comparisonData);
      } catch (error) {
        console.error('Failed to load cluster comparison:', error);
      }
    };

    loadClusterComparison();
  }, []);

  // Calculate statistics
  const avgPm25 = sensors.reduce((sum, s) => {
    const telemetry = telemetryMap[s.sensorId];
    return sum + (telemetry?.pm25 || 0);
  }, 0) / (sensors.length || 1);

  const avgTemp = sensors.reduce((sum, s) => {
    const telemetry = telemetryMap[s.sensorId];
    return sum + (telemetry?.temperature || 0);
  }, 0) / (sensors.length || 1);

  const avgHumidity = sensors.reduce((sum, s) => {
    const telemetry = telemetryMap[s.sensorId];
    return sum + (telemetry?.humidity || 0);
  }, 0) / (sensors.length || 1);

  const avgNoise = sensors.reduce((sum, s) => {
    const telemetry = telemetryMap[s.sensorId];
    return sum + (telemetry?.noise || 0);
  }, 0) / (sensors.length || 1);

  const avgAqi = sensors.reduce((sum, s) => {
    const telemetry = telemetryMap[s.sensorId];
    return sum + (telemetry?.aqi || 0);
  }, 0) / (sensors.length || 1);

  const aqiCategory = avgAqi > 150 ? 'Không lành mạnh' : 
                      avgAqi > 100 ? 'Không lành mạnh cho nhóm nhạy cảm' :
                      avgAqi > 50 ? 'Trung bình' : 'Tốt';

  // Sensor status distribution
  const normalSensors = sensors.filter(s => {
    const telemetry = telemetryMap[s.sensorId];
    if (!telemetry) return false;
    return (telemetry.pm25 || 0) < 50 && (telemetry.co2 || 0) < 1000;
  }).length;

  const warningSensors = sensors.filter(s => {
    const telemetry = telemetryMap[s.sensorId];
    if (!telemetry) return false;
    return ((telemetry.pm25 || 0) >= 50 && (telemetry.pm25 || 0) < 100) || 
           ((telemetry.co2 || 0) >= 1000 && (telemetry.co2 || 0) < 2000);
  }).length;

  const criticalSensors = sensors.filter(s => {
    const telemetry = telemetryMap[s.sensorId];
    if (!telemetry) return false;
    return (telemetry.pm25 || 0) >= 100 || (telemetry.co2 || 0) >= 2000;
  }).length;

  const sensorStatusData = [
    { name: 'Bình thường', value: normalSensors, color: '#10B981' },
    { name: 'Cảnh báo', value: warningSensors, color: '#F59E0B' },
    { name: 'Nghiêm trọng', value: criticalSensors, color: '#EF4444' },
  ];

  // Alert statistics
  const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL').length;
  const highAlerts = alerts.filter(a => a.severity === 'HIGH').length;
  const mediumAlerts = alerts.filter(a => a.severity === 'MEDIUM').length;
  const lowAlerts = alerts.filter(a => a.severity === 'LOW').length;

  return (
    <div className="analytics-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Phân Tích</h1>
          <p className="view-subtitle">Các chỉ số môi trường và xu hướng</p>
        </div>
      </div>

      {/* Thống kê tổng quan */}
      <div className="stats-row">
        <div className="stat-box">
          <span className="stat-label">TB PM2.5</span>
          <div className="stat-value-row">
            <span className={`stat-number ${avgPm25 > 50 ? 'text-red-400' : 'text-green-400'}`}>
              {avgPm25.toFixed(1)} <span className="stat-unit">µg/m³</span>
            </span>
            <div className={`stat-change ${avgPm25 > 50 ? 'negative' : 'positive'}`}>
              {avgPm25 > 50 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span>Real-time</span>
            </div>
          </div>
        </div>

        <div className="stat-box">
          <span className="stat-label">TB Nhiệt Độ</span>
          <div className="stat-value-row">
            <span className="stat-number text-blue-400">{avgTemp.toFixed(1)} <span className="stat-unit">°C</span></span>
            <div className="stat-change positive">
              <TrendingDown className="w-4 h-4" />
              <span>Real-time</span>
            </div>
          </div>
        </div>

        <div className="stat-box">
          <span className="stat-label">TB Độ Ẩm</span>
          <div className="stat-value-row">
            <span className="stat-number text-cyan-400">{avgHumidity.toFixed(0)} <span className="stat-unit">%</span></span>
            <div className="stat-change negative">
              <TrendingUp className="w-4 h-4" />
              <span>Real-time</span>
            </div>
          </div>
        </div>

        <div className="stat-box">
          <span className="stat-label">TB Tiếng Ồn</span>
          <div className="stat-value-row">
            <span className="stat-number text-purple-400">{avgNoise.toFixed(0)} <span className="stat-unit">dB</span></span>
            <div className="stat-change negative">
              <TrendingUp className="w-4 h-4" />
              <span>Real-time</span>
            </div>
          </div>
        </div>
      </div>

      {/* Biểu đồ */}
      <div className="charts-grid">
        {/* Chỉ số chất lượng không khí */}
        <div className="chart-card">
          <div className="card-header">
            <h3 className="card-title">Chỉ Số Chất Lượng Không Khí</h3>
            <p className="card-subtitle">AQI hiện tại toàn thành phố</p>
          </div>
          <div className="aqi-display">
            <div className={`aqi-value ${avgAqi > 150 ? 'text-red-400' : avgAqi > 100 ? 'text-orange-400' : 'text-green-400'}`}>
              {avgAqi.toFixed(0)}
            </div>
            <div className={`aqi-label ${avgAqi > 150 ? 'text-red-400' : avgAqi > 100 ? 'text-orange-400' : 'text-green-400'}`}>
              {aqiCategory}
            </div>
            <div className="aqi-scale">
              <div className="aqi-scale-item">
                <div className="aqi-scale-bar bg-green-500"></div>
                <span>Tốt</span>
              </div>
              <div className="aqi-scale-item">
                <div className="aqi-scale-bar bg-yellow-500"></div>
                <span>Trung bình</span>
              </div>
              <div className="aqi-scale-item active">
                <div className="aqi-scale-bar bg-red-500"></div>
                <span>Không lành mạnh</span>
              </div>
            </div>
          </div>
        </div>

        {/* Trạng thái cảm biến */}
        <div className="chart-card">
          <div className="card-header">
            <h3 className="card-title">Trạng Thái Cảm Biến</h3>
            <p className="card-subtitle">Phân bố theo tình trạng</p>
          </div>
          <div className="pie-chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={sensorStatusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {sensorStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Hoạt động cảnh báo */}
        <div className="chart-card">
          <div className="card-header">
            <h3 className="card-title">Hoạt Động Cảnh Báo</h3>
            <p className="card-subtitle">24 giờ qua</p>
          </div>
          <div className="alert-stats">
            <div className="alert-stat-item">
              <span className="alert-stat-label">Tổng Cảnh Báo</span>
              <span className="alert-stat-value">{alerts.length}</span>
            </div>
            <div className="alert-stat-item">
              <span className="alert-stat-label">Nghiêm Trọng</span>
              <span className="alert-stat-value text-red-400">{criticalAlerts}</span>
            </div>
            <div className="alert-stat-item">
              <span className="alert-stat-label">Cao</span>
              <span className="alert-stat-value text-orange-400">{highAlerts}</span>
            </div>
            <div className="alert-stat-item">
              <span className="alert-stat-label">Trung Bình</span>
              <span className="alert-stat-value text-yellow-400">{mediumAlerts}</span>
            </div>
            <div className="alert-stat-item">
              <span className="alert-stat-label">Thấp</span>
              <span className="alert-stat-value text-green-400">{lowAlerts}</span>
            </div>
            <div className="alert-stat-item">
              <span className="alert-stat-label">Đã Xác Nhận</span>
              <span className="alert-stat-value">0 / {alerts.length}</span>
            </div>
          </div>
        </div>

        {/* Xu hướng PM2.5 */}
        <div className="chart-card full-width">
          <div className="card-header">
            <h3 className="card-title">Xu Hướng PM2.5</h3>
            <p className="card-subtitle">Trung bình toàn thành phố</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={pm25TrendData}>
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
                dot={{ fill: '#3B82F6', r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* So sánh cụm */}
        <div className="chart-card full-width">
          <div className="card-header">
            <h3 className="card-title">So Sánh Cụm</h3>
            <p className="card-subtitle">Các chỉ số môi trường theo khu vực</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={clusterComparisonData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Bar dataKey="pm25" fill="#3B82F6" name="PM2.5 (µg/m³)" />
              <Bar dataKey="noise" fill="#10B981" name="Tiếng Ồn (dB)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsView;
