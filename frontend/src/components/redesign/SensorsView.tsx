import React, { useMemo, useState } from 'react';
import { Search, MapPin, Battery, Signal, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import { classifySensorStatus } from '../../utils/telemetry';
import { formatLocationName } from '../../utils/location';
import type { MapFocusTarget } from './types';

type SortKey = 'name' | 'status' | 'pm25' | 'temp' | 'humidity' | 'co2' | 'noise' | 'battery' | 'signal';
type SortDir = 'asc' | 'desc';

interface SensorsViewProps {
  onFocusOnMap?: (target: MapFocusTarget) => void;
}

const STATUS_RANK: Record<string, number> = {
  critical: 0,
  warning: 1,
  normal: 2,
  pending: 3,
};

const SensorsView: React.FC<SensorsViewProps> = ({ onFocusOnMap }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('status');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const { sensors, telemetryMap, locations } = useAppContext();

  // Map sensors with telemetry data — pull from quality.* when available.
  const sensorsWithData = sensors.map((sensor) => {
    const telemetry = telemetryMap[sensor.sensorId];
    const pm25 = telemetry?.pm25 ?? telemetry?.data?.pm25 ?? null;
    const co2 = telemetry?.co2 ?? telemetry?.data?.co2 ?? null;
    const temp = telemetry?.temperature ?? telemetry?.data?.temperature ?? null;
    const humidity = telemetry?.humidity ?? telemetry?.data?.humidity ?? null;
    const noise = telemetry?.noise ?? telemetry?.data?.noise ?? null;

    const status = classifySensorStatus(pm25, co2);

    // Real device-quality fields from the simulator
    const battery = telemetry?.quality?.batteryLevel ?? null;
    // Signal strength is dBm, typically -30 (great) to -90 (poor).
    // Map to 0–100% so the existing UI doesn't change.
    const signalDbm = telemetry?.quality?.signalStrength ?? null;
    const signalPct =
      signalDbm === null
        ? null
        : Math.max(0, Math.min(100, Math.round(((signalDbm + 90) / 60) * 100)));

    return {
      id: sensor.sensorId,
      name: formatLocationName(sensor.locationId, locations),
      lat: sensor.latitude ?? null,
      lng: sensor.longitude ?? null,
      status,
      pm25,
      co2,
      temp,
      humidity,
      noise,
      battery,
      signal: signalPct,
      hasTelemetry: telemetry !== undefined,
    };
  });

  const filteredSensors = useMemo(() => {
    const q = searchQuery.toLowerCase();
    const list = sensorsWithData.filter(
      (sensor) =>
        sensor.name.toLowerCase().includes(q) ||
        sensor.id.toLowerCase().includes(q),
    );

    const cmp = (a: typeof list[number], b: typeof list[number]): number => {
      const dir = sortDir === 'asc' ? 1 : -1;
      const pickNum = (v: number | null): number =>
        v === null || v === undefined || isNaN(v) ? Number.POSITIVE_INFINITY : v;

      switch (sortKey) {
        case 'name':
          return a.name.localeCompare(b.name) * dir;
        case 'status': {
          const aKey = a.hasTelemetry ? STATUS_RANK[a.status] ?? 9 : STATUS_RANK.pending;
          const bKey = b.hasTelemetry ? STATUS_RANK[b.status] ?? 9 : STATUS_RANK.pending;
          return (aKey - bKey) * dir;
        }
        case 'pm25':     return (pickNum(a.pm25)     - pickNum(b.pm25))     * dir;
        case 'temp':     return (pickNum(a.temp)     - pickNum(b.temp))     * dir;
        case 'humidity': return (pickNum(a.humidity) - pickNum(b.humidity)) * dir;
        case 'co2':      return (pickNum(a.co2)      - pickNum(b.co2))      * dir;
        case 'noise':    return (pickNum(a.noise)    - pickNum(b.noise))    * dir;
        case 'battery':  return (pickNum(a.battery)  - pickNum(b.battery))  * dir;
        case 'signal':   return (pickNum(a.signal)   - pickNum(b.signal))   * dir;
        default: return 0;
      }
    };

    return [...list].sort(cmp);
  }, [sensorsWithData, searchQuery, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortIcon = (key: SortKey) => {
    if (sortKey !== key) return <ArrowUpDown className="w-3 h-3 sort-icon" />;
    return sortDir === 'asc'
      ? <ArrowUp className="w-3 h-3 sort-icon active" />
      : <ArrowDown className="w-3 h-3 sort-icon active" />;
  };

  const handleViewOnMap = (sensor: typeof filteredSensors[number]) => {
    if (!onFocusOnMap || sensor.lat == null || sensor.lng == null) return;
    onFocusOnMap({ lat: sensor.lat, lng: sensor.lng, zoom: 15 });
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
    normal: filteredSensors.filter((s) => s.hasTelemetry && s.status === 'normal').length,
    warning: filteredSensors.filter((s) => s.hasTelemetry && s.status === 'warning').length,
    critical: filteredSensors.filter((s) => s.hasTelemetry && s.status === 'critical').length,
    pending: filteredSensors.filter((s) => !s.hasTelemetry).length,
  };

  const fmt = (v: number | null, digits = 1, suffix = '') =>
    v === null || v === undefined || isNaN(v) ? '—' : `${v.toFixed(digits)}${suffix}`;

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
              <th className="sortable" onClick={() => handleSort('name')}>
                <span className="th-content">Cảm Biến {sortIcon('name')}</span>
              </th>
              <th className="sortable" onClick={() => handleSort('status')}>
                <span className="th-content">Trạng Thái {sortIcon('status')}</span>
              </th>
              <th className="sortable" onClick={() => handleSort('pm25')}>
                <span className="th-content">PM2.5 {sortIcon('pm25')}</span>
              </th>
              <th className="sortable" onClick={() => handleSort('temp')}>
                <span className="th-content">Nhiệt Độ {sortIcon('temp')}</span>
              </th>
              <th className="sortable" onClick={() => handleSort('humidity')}>
                <span className="th-content">Độ Ẩm {sortIcon('humidity')}</span>
              </th>
              <th className="sortable" onClick={() => handleSort('co2')}>
                <span className="th-content">CO2 {sortIcon('co2')}</span>
              </th>
              <th className="sortable" onClick={() => handleSort('noise')}>
                <span className="th-content">Tiếng Ồn {sortIcon('noise')}</span>
              </th>
              <th className="sortable" onClick={() => handleSort('battery')}>
                <span className="th-content">Pin {sortIcon('battery')}</span>
              </th>
              <th className="sortable" onClick={() => handleSort('signal')}>
                <span className="th-content">Tín Hiệu {sortIcon('signal')}</span>
              </th>
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
                  {sensor.hasTelemetry ? (
                    <span className={`status-badge ${getStatusColor(sensor.status)}`}>
                      {getStatusText(sensor.status)}
                    </span>
                  ) : (
                    <span className="status-badge bg-gray-500/10 text-gray-400">
                      CHỜ DỮ LIỆU
                    </span>
                  )}
                </td>
                <td className={(sensor.pm25 ?? 0) > 50 ? 'text-red-400' : ''}>
                  {fmt(sensor.pm25, 1)}
                </td>
                <td>{fmt(sensor.temp, 1, '°C')}</td>
                <td>{fmt(sensor.humidity, 0, '%')}</td>
                <td className={(sensor.co2 ?? 0) > 1000 ? 'text-yellow-400' : ''}>
                  {fmt(sensor.co2, 0)}
                </td>
                <td>{fmt(sensor.noise, 0, ' dB')}</td>
                <td>
                  <div className="battery-cell">
                    <Battery className="w-4 h-4" />
                    <span>{fmt(sensor.battery, 0, '%')}</span>
                  </div>
                </td>
                <td>
                  <div className="signal-cell">
                    <Signal className="w-4 h-4" />
                    <span>{fmt(sensor.signal, 0, '%')}</span>
                  </div>
                </td>
                <td>
                  <button
                    className="action-btn"
                    onClick={() => handleViewOnMap(sensor)}
                    disabled={sensor.lat == null || sensor.lng == null}
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
