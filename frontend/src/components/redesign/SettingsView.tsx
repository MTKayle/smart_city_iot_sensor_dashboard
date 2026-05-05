import React, { useEffect, useState } from 'react';
import { Activity, Database, Cpu, RefreshCw } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import { fetchPipelineMetrics, checkHealth } from '../../services/api';
import type { PipelineMetrics } from '../../services/api';

const SettingsView: React.FC = () => {
  const { connectionStatus, sensors, alerts, leaderboard } = useAppContext();
  const [metrics, setMetrics] = useState<PipelineMetrics | null>(null);
  const [apiHealth, setApiHealth] = useState<string>('—');
  const [refreshing, setRefreshing] = useState(false);

  const loadOps = async () => {
    setRefreshing(true);
    try {
      const [m, h] = await Promise.allSettled([
        fetchPipelineMetrics(),
        checkHealth(),
      ]);
      if (m.status === 'fulfilled') setMetrics(m.value);
      if (h.status === 'fulfilled') setApiHealth(h.value.status);
      else setApiHealth('error');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadOps();
    const id = window.setInterval(loadOps, 15000);
    return () => window.clearInterval(id);
  }, []);

  const stat = (
    label: string,
    value: number | string,
    color = 'text-blue-400',
  ) => (
    <div className="stat-box">
      <span className="stat-label">{label}</span>
      <span className={`stat-number ${color}`}>{value}</span>
    </div>
  );

  return (
    <div className="settings-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Cài Đặt &amp; Vận Hành</h1>
          <p className="view-subtitle">Cấu hình hệ thống và giám sát pipeline</p>
        </div>
        <button
          className="filter-btn"
          onClick={loadOps}
          disabled={refreshing}
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Đang làm mới…' : 'Làm Mới'}
        </button>
      </div>

      <div className="settings-content">
        {/* Vận hành */}
        <div className="settings-section">
          <h2 className="settings-section-title">
            <Activity className="inline w-4 h-4 mr-2" />
            Trạng Thái Hệ Thống
          </h2>
          <div className="stats-row">
            {stat(
              'WebSocket',
              connectionStatus,
              connectionStatus === 'connected' ? 'text-green-400' : 'text-red-400',
            )}
            {stat(
              'API Health',
              apiHealth,
              apiHealth === 'healthy' ? 'text-green-400' : 'text-yellow-400',
            )}
            {stat('Cảm biến', sensors.length, 'text-cyan-400')}
            {stat('Khu vực xếp hạng', leaderboard.length, 'text-purple-400')}
            {stat('Cảnh báo gần đây', alerts.length, 'text-orange-400')}
          </div>
        </div>

        {/* Pipeline metrics */}
        <div className="settings-section">
          <h2 className="settings-section-title">
            <Database className="inline w-4 h-4 mr-2" />
            Pipeline Telemetry (Redis Stream)
          </h2>
          {metrics ? (
            <div className="stats-row">
              {stat('Đã enqueue', metrics.enqueued, 'text-blue-400')}
              {stat('Đã xử lý', metrics.processed, 'text-green-400')}
              {stat('Bị drop', metrics.dropped, 'text-red-400')}
              {stat(
                'Stream length',
                metrics.stream_length,
                metrics.stream_length > 5000 ? 'text-yellow-400' : 'text-cyan-400',
              )}
              {stat('Pending', metrics.pending_messages, 'text-orange-400')}
              {stat('Workers active', metrics.workers_active, 'text-green-400')}
              {stat('Mongo inserts', metrics.mongo_inserts, 'text-cyan-400')}
              {stat('Alerts created', metrics.alerts_created, 'text-yellow-400')}
              {stat('WS broadcasts', metrics.ws_broadcasts, 'text-purple-400')}
              {stat('Acked', metrics.acked, 'text-green-400')}
              {stat('Re-delivered', metrics.redelivered, 'text-orange-400')}
              {stat('Batches', metrics.batches, 'text-blue-400')}
            </div>
          ) : (
            <p className="text-gray-400" style={{ marginTop: 8 }}>
              Chưa có metrics — backend có thể chưa start pipeline.
            </p>
          )}
        </div>

        {/* Cài đặt cũ giữ nguyên */}
        <div className="settings-section">
          <h2 className="settings-section-title">
            <Cpu className="inline w-4 h-4 mr-2" />
            Hiển Thị
          </h2>
          <div className="settings-item">
            <div className="settings-item-info">
              <span className="settings-item-label">Chế Độ Tối</span>
              <span className="settings-item-description">Sử dụng giao diện tối</span>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" defaultChecked />
              <span className="toggle-slider"></span>
            </label>
          </div>
          <div className="settings-item">
            <div className="settings-item-info">
              <span className="settings-item-label">Ngôn Ngữ</span>
              <span className="settings-item-description">Chọn ngôn ngữ hiển thị</span>
            </div>
            <select className="settings-select">
              <option value="vi">Tiếng Việt</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>

        <div className="settings-section">
          <h2 className="settings-section-title">Cảnh Báo</h2>
          <div className="settings-item">
            <div className="settings-item-info">
              <span className="settings-item-label">Thông Báo Âm Thanh</span>
              <span className="settings-item-description">
                Phát âm thanh khi có cảnh báo mới
              </span>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" defaultChecked />
              <span className="toggle-slider"></span>
            </label>
          </div>
          <div className="settings-item">
            <div className="settings-item-info">
              <span className="settings-item-label">Ngưỡng PM2.5</span>
              <span className="settings-item-description">
                Giá trị ngưỡng cảnh báo PM2.5 (µg/m³). Backend hiện dùng 55 µg/m³.
              </span>
            </div>
            <input type="number" className="settings-input" defaultValue={55} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;
