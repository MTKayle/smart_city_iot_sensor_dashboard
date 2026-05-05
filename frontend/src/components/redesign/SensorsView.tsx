import React, { useState } from 'react';
import { Search, MapPin, Battery, Signal } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';

const SensorsView: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const { sensors, telemetryMap } = useAppContext();

  // Map sensors with telemetry data
  const sensorsWithData = sensors.map(sensor => {
    const telemetry = telemetryMap[sensor.sensorId];
    const pm25 = telemetry?.pm25 || 0;
    const co2 = telemetry?.co2 || 0;
    
    let status = 'normal';
    if (pm25 > 100 || co2 > 2000) status = 'critical';
    else if (pm25 > 50 || co2 > 1000) status = 'warning';

    return {
      id: sensor.sensorId,
      name: sensor.locationId || sensor.sensorId,
      status,
      pm25: pm25,
      temp: telemetry?.temperature || 0,
      humidity: telemetry?.humidity || 0,
      co2: co2,
      battery: 85, // Mock - backend doesn't provide this yet
      signal: 90,  // Mock - backend doesn't provide this yet
    };
  });

  // Filter by search query
  const filteredSensors = sensorsWithData.filter(sensor =>
    sensor.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    sensor.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleViewOnMap = (sensorId: string) => {
    console.log('View sensor on map:', sensorId);
    // TODO: Navigate to map view and center on sensor
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical':
        return 'bg-red-500/10 text-red-400';
      case 'warning':
        return 'bg-yellow-500/10 text-yellow-400';
      case 'normal':
        return 'bg-green-500/10 text-green-400';
      default:
        return 'bg-gray-500/10 text-gray-400';
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

  const statusCounts = {
    total: filteredSensors.length,
    normal: filteredSensors.filter(s => s.status === 'normal').length,
    warning: filteredSensors.filter(s => s.status === 'warning').length,
    critical: filteredSensors.filter(s => s.status === 'critical').length,
  };

  return (
    <div className="sensors-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Cảm Biến</h1>
          <p className="view-subtitle">{sensors.length} cảm biến đã triển khai</p>
        </div>
        <div className="search-box">
          <Search className="search-icon" />
          <input
            type="text"
            placeholder="Tìm kiếm cảm biến..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      {/* Thống kê */}
      <div className="stats-row">
        <div className="stat-box">
          <span className="stat-label">Tổng Số Cảm Biến</span>
          <span className="stat-number text-blue-400">{statusCounts.total}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Bình Thường</span>
          <span className="stat-number text-green-400">{statusCounts.normal}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Cảnh Báo</span>
          <span className="stat-number text-yellow-400">{statusCounts.warning}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Nghiêm Trọng</span>
          <span className="stat-number text-red-400">{statusCounts.critical}</span>
        </div>
      </div>

      {/* Bảng cảm biến */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Cảm Biến ↕</th>
              <th>Trạng Thái</th>
              <th>PM2.5 ↕</th>
              <th>Nhiệt Độ ↕</th>
              <th>Độ Ẩm ↕</th>
              <th>CO2 ↕</th>
              <th>Pin</th>
              <th>Tín Hiệu</th>
              <th>Hành Động</th>
            </tr>
          </thead>
          <tbody>
            {filteredSensors.map((sensor) => (
              <tr key={sensor.id}>
                <td>
                  <div className="sensor-cell">
                    <div className="sensor-name">{sensor.name}</div>
                    <div className="sensor-id">{sensor.id}</div>
                  </div>
                </td>
                <td>
                  <span className={`status-badge ${getStatusColor(sensor.status)}`}>
                    {getStatusText(sensor.status)}
                  </span>
                </td>
                <td className={sensor.pm25 > 50 ? 'text-red-400' : ''}>{sensor.pm25.toFixed(1)}</td>
                <td>{sensor.temp.toFixed(1)}°C</td>
                <td>{sensor.humidity.toFixed(0)}%</td>
                <td className={sensor.co2 > 1000 ? 'text-yellow-400' : ''}>{sensor.co2.toFixed(0)}</td>
                <td>
                  <div className="battery-cell">
                    <Battery className="w-4 h-4" />
                    <span>{sensor.battery}%</span>
                  </div>
                </td>
                <td>
                  <div className="signal-cell">
                    <Signal className="w-4 h-4" />
                    <span>{sensor.signal}%</span>
                  </div>
                </td>
                <td>
                  <button 
                    className="action-btn"
                    onClick={() => handleViewOnMap(sensor.id)}
                    title="Xem trên bản đồ"
                  >
                    <MapPin className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SensorsView;
