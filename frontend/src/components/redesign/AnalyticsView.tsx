import React, { useEffect, useState, useMemo } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useAppContext } from '../../context/AppContext';
import { fetchTelemetry } from '../../services/api';
import { classifySensorStatus } from '../../utils/telemetry';

const AnalyticsView: React.FC = () => {
  const { sensors, alerts, telemetryMap, leaderboard } = useAppContext();
  const [pm25TrendData, setPm25TrendData] = useState<
    Array<{ time: string; value: number }>
  >([]);

  // Load PM2.5 trend from the first sensor that actually has data.
  useEffect(() => {
    const loadPm25Trend = async () => {
      const sourceSensor = sensors[0];
      if (!sourceSensor) return;

      try {
        const telemetryData = await fetchTelemetry(sourceSensor.sensorId, {
          limit: 24,
        });

        const chartData = telemetryData
          .slice(0, 12)
          .reverse()
          .map((t) => ({
            time: new Date(t.timestamp).toLocaleTimeString('vi-VN', {
              hour: '2-digit',
              minute: '2-digit',
            }),
            value: (t.pm25 ?? t.data?.pm25 ?? 0) as number,
          }));

        setPm25TrendData(chartData);
      } catch (error) {
        console.error('Failed to load PM2.5 trend:', error);
      }
    };

    loadPm25Trend();
  }, [sensors]);

  // ─── Averages — only over sensors with telemetry, no zero-bias ───
  const averages = useMemo(() => {
    const liveTelemetry = sensors
      .map((s) => telemetryMap[s.sensorId])
      .filter((t): t is NonNullable<typeof t> => t !== undefined);

    const avg = (vals: Array<number | undefined | null>): number => {
      const nums = vals
        .map((v) => (v === undefined || v === null ? null : Number(v)))
        .filter((v): v is number => v !== null && !isNaN(v));
      if (nums.length === 0) return 0;
      return nums.reduce((a, b) => a + b, 0) / nums.length;
    };

    return {
      pm25: avg(liveTelemetry.map((t) => t.pm25 ?? t.data?.pm25)),
      temp: avg(liveTelemetry.map((t) => t.temperature ?? t.data?.temperature)),
      humidity: avg(liveTelemetry.map((t) => t.humidity ?? t.data?.humidity)),
      noise: avg(liveTelemetry.map((t) => t.noise ?? t.data?.noise)),
      aqi: avg(liveTelemetry.map((t) => t.aqi)),
      liveCount: liveTelemetry.length,
    };
  }, [sensors, telemetryMap]);

  const aqiCategory =
    averages.aqi > 150
      ? 'Không lành mạnh'
      : averages.aqi > 100
      ? 'Không lành mạnh cho nhóm nhạy cảm'
      : averages.aqi > 50
      ? 'Trung bình'
      : 'Tốt';

  // ─── Sensor status distribution from real telemetry ───
  const statusDistribution = useMemo(() => {
    let normal = 0;
    let warning = 0;
    let critical = 0;
    sensors.forEach((s) => {
      const t = telemetryMap[s.sensorId];
      if (!t) return;
      const pm25 = t.pm25 ?? t.data?.pm25 ?? null;
      const co2 = t.co2 ?? t.data?.co2 ?? null;
      const status = classifySensorStatus(pm25, co2);
      if (status === 'critical') critical += 1;
      else if (status === 'warning') warning += 1;
      else normal += 1;
    });
    return [
      { name: 'Bình thường', value: normal, color: '#10B981' },
      { name: 'Cảnh báo', value: warning, color: '#F59E0B' },
      { name: 'Nghiêm trọng', value: critical, color: '#EF4444' },
    ];
  }, [sensors, telemetryMap]);

  // ─── Alert stats by severity (no overlap) ───
  const criticalAlerts = alerts.filter((a) => a.severity === 'CRITICAL').length;
  const highAlerts = alerts.filter((a) => a.severity === 'HIGH').length;
  const mediumAlerts = alerts.filter((a) => a.severity === 'MEDIUM').length;
  const lowAlerts = alerts.filter((a) => a.severity === 'LOW').length;
  const acknowledgedAlerts = alerts.filter((a) => a.status === 'ACKNOWLEDGED').length;
  const resolvedAlerts = alerts.filter((a) => a.status === 'RESOLVED').length;

  // ─── Bar chart: location comparison from leaderboard (real data) ───
  const locationComparisonData = useMemo(
    () =>
      leaderboard.slice(0, 6).map((entry) => ({
        name: entry.locationName,
        pm25: entry.avgPM25 ?? 0,
        noise: entry.avgNoise ?? 0,
      })),
    [leaderboard],
  );

  return (
    <div className="analytics-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Phân Tích</h1>
          <p className="view-subtitle">
            Các chỉ số môi trường và xu hướng — {averages.liveCount}/{sensors.length} cảm biến đang trực tuyến
          </p>
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-box">
          <span className="stat-label">TB PM2.5</span>
          <div className="stat-value-row">
            <span
              className={`stat-number ${
                averages.pm25 > 50 ? 'text-red-400' : 'text-green-400'
              }`}
            >
              {averages.pm25.toFixed(1)} <span className="stat-unit">µg/m³</span>
            </span>
            <div
              className={`stat-change ${averages.pm25 > 50 ? 'negative' : 'positive'}`}
            >
              {averages.pm25 > 50 ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span>Real-time</span>
            </div>
          </div>
        </div>

        <div className="stat-box">
          <span className="stat-label">TB Nhiệt Độ</span>
          <div className="stat-value-row">
            <span className="stat-number text-blue-400">
              {averages.temp.toFixed(1)} <span className="stat-unit">°C</span>
            </span>
            <div className="stat-change positive">
              <TrendingDown className="w-4 h-4" />
              <span>Real-time</span>
            </div>
          </div>
        </div>

        <div className="stat-box">
          <span className="stat-label">TB Độ Ẩm</span>
          <div className="stat-value-row">
            <span className="stat-number text-cyan-400">
              {averages.humidity.toFixed(0)} <span className="stat-unit">%</span>
            </span>
            <div className="stat-change negative">
              <TrendingUp className="w-4 h-4" />
              <span>Real-time</span>
            </div>
          </div>
        </div>

        <div className="stat-box">
          <span className="stat-label">TB Tiếng Ồn</span>
          <div className="stat-value-row">
            <span className="stat-number text-purple-400">
              {averages.noise.toFixed(0)} <span className="stat-unit">dB</span>
            </span>
            <div className="stat-change negative">
              <TrendingUp className="w-4 h-4" />
              <span>Real-time</span>
            </div>
          </div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <div className="card-header">
            <h3 className="card-title">Chỉ Số Chất Lượng Không Khí</h3>
            <p className="card-subtitle">AQI hiện tại toàn thành phố</p>
          </div>
          <div className="aqi-display">
            <div
              className={`aqi-value ${
                averages.aqi > 150
                  ? 'text-red-400'
                  : averages.aqi > 100
                  ? 'text-orange-400'
                  : 'text-green-400'
              }`}
            >
              {averages.aqi.toFixed(0)}
            </div>
            <div
              className={`aqi-label ${
                averages.aqi > 150
                  ? 'text-red-400'
                  : averages.aqi > 100
                  ? 'text-orange-400'
                  : 'text-green-400'
              }`}
            >
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

        <div className="chart-card">
          <div className="card-header">
            <h3 className="card-title">Trạng Thái Cảm Biến</h3>
            <p className="card-subtitle">Phân bố theo tình trạng (real-time)</p>
          </div>
          <div className="pie-chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={statusDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {statusDistribution.map((entry, index) => (
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

        <div className="chart-card">
          <div className="card-header">
            <h3 className="card-title">Hoạt Động Cảnh Báo</h3>
            <p className="card-subtitle">{alerts.length} cảnh báo gần đây</p>
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
              <span className="alert-stat-label">Đã Xác Nhận / Giải Quyết</span>
              <span className="alert-stat-value">
                {acknowledgedAlerts} / {resolvedAlerts}
              </span>
            </div>
          </div>
        </div>

        <div className="chart-card full-width">
          <div className="card-header">
            <h3 className="card-title">Xu Hướng PM2.5</h3>
            <p className="card-subtitle">
              {sensors[0] ? `Nguồn: ${sensors[0].sensorId}` : 'Chưa có cảm biến'}
            </p>
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

        <div className="chart-card full-width">
          <div className="card-header">
            <h3 className="card-title">So Sánh Khu Vực</h3>
            <p className="card-subtitle">Top 6 khu vực theo Clean Score</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={locationComparisonData}>
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
