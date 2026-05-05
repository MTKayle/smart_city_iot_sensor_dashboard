import React, { useMemo, useState } from 'react';
import { Trophy, RefreshCw } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import type { LeaderboardEntry } from '../../types';

type SortField =
  | 'rank'
  | 'avgCO2'
  | 'avgNoise'
  | 'avgTemperature'
  | 'avgPM25'
  | 'avgHumidity'
  | 'aqi'
  | 'cleanScore';

type SortDir = 'asc' | 'desc';

const medalIcon = (rank: number) =>
  rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : '';

const scoreColor = (score: number) =>
  score >= 80
    ? 'text-green-400'
    : score >= 60
    ? 'text-yellow-400'
    : score >= 40
    ? 'text-orange-400'
    : 'text-red-400';

const aqiInfo = (aqi: number | null | undefined) => {
  if (aqi === null || aqi === undefined) return { color: '#64748b', label: '—' };
  if (aqi <= 50) return { color: '#22c55e', label: 'Tốt' };
  if (aqi <= 100) return { color: '#eab308', label: 'Trung Bình' };
  if (aqi <= 150) return { color: '#ea580c', label: 'Kém' };
  if (aqi <= 200) return { color: '#dc2626', label: 'Xấu' };
  if (aqi <= 300) return { color: '#7e22ce', label: 'Rất Xấu' };
  return { color: '#831843', label: 'Nguy Hiểm' };
};

const LeaderboardView: React.FC = () => {
  const { leaderboard, refreshLeaderboard } = useAppContext();
  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [refreshing, setRefreshing] = useState(false);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir(field === 'rank' ? 'asc' : 'desc');
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshLeaderboard();
    } finally {
      setRefreshing(false);
    }
  };

  const sortedEntries: LeaderboardEntry[] = useMemo(() => {
    const get = (e: LeaderboardEntry, field: SortField): number => {
      switch (field) {
        case 'rank':
          return e.rank;
        case 'avgCO2':
          return e.avgCO2;
        case 'avgNoise':
          return e.avgNoise;
        case 'avgTemperature':
          return e.avgTemperature;
        case 'avgPM25':
          return e.avgPM25 ?? -1;
        case 'avgHumidity':
          return e.avgHumidity ?? -1;
        case 'aqi':
          return e.aqi ?? -1;
        case 'cleanScore':
          return e.cleanScore;
      }
    };
    return [...leaderboard].sort((a, b) => {
      const av = get(a, sortField);
      const bv = get(b, sortField);
      return sortDir === 'asc' ? av - bv : bv - av;
    });
  }, [leaderboard, sortField, sortDir]);

  const sortIcon = (f: SortField) =>
    sortField === f ? (sortDir === 'asc' ? ' ▲' : ' ▼') : '';

  return (
    <div className="leaderboard-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">
            <Trophy className="inline w-6 h-6 mr-2 text-yellow-400" />
            Bảng Xếp Hạng Khu Vực
          </h1>
          <p className="view-subtitle">
            Xếp hạng theo Clean Score — {leaderboard.length} khu vực có dữ liệu
          </p>
        </div>
        <button
          className="filter-btn"
          onClick={handleRefresh}
          disabled={refreshing}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <RefreshCw
            className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
          />
          {refreshing ? 'Đang làm mới…' : 'Làm Mới'}
        </button>
      </div>

      {leaderboard.length === 0 ? (
        <div className="alert-card">
          <p className="text-gray-400">
            Chưa có dữ liệu Clean Score. Lịch trình daily aggregation chạy lúc
            00:00 và hourly cluster aggregation chạy mỗi giờ — chờ lần kế tiếp.
          </p>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('rank')} style={{ cursor: 'pointer' }}>
                  #{sortIcon('rank')}
                </th>
                <th>Khu Vực</th>
                <th onClick={() => handleSort('avgCO2')} style={{ cursor: 'pointer' }}>
                  CO₂{sortIcon('avgCO2')}
                </th>
                <th onClick={() => handleSort('avgNoise')} style={{ cursor: 'pointer' }}>
                  Tiếng Ồn{sortIcon('avgNoise')}
                </th>
                <th
                  onClick={() => handleSort('avgTemperature')}
                  style={{ cursor: 'pointer' }}
                >
                  Nhiệt Độ{sortIcon('avgTemperature')}
                </th>
                <th onClick={() => handleSort('avgPM25')} style={{ cursor: 'pointer' }}>
                  PM2.5{sortIcon('avgPM25')}
                </th>
                <th
                  onClick={() => handleSort('avgHumidity')}
                  style={{ cursor: 'pointer' }}
                >
                  Độ Ẩm{sortIcon('avgHumidity')}
                </th>
                <th onClick={() => handleSort('aqi')} style={{ cursor: 'pointer' }}>
                  AQI{sortIcon('aqi')}
                </th>
                <th
                  onClick={() => handleSort('cleanScore')}
                  style={{ cursor: 'pointer' }}
                >
                  Clean Score{sortIcon('cleanScore')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedEntries.map((entry) => {
                const aqi = aqiInfo(entry.aqi);
                return (
                  <tr key={entry.locationId}>
                    <td>
                      <span style={{ fontWeight: 600 }}>{entry.rank}</span>
                      {entry.rank <= 3 && (
                        <span style={{ marginLeft: 4 }}>{medalIcon(entry.rank)}</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'left', fontWeight: entry.rank <= 3 ? 600 : 400 }}>
                      {entry.locationName}
                    </td>
                    <td>{entry.avgCO2.toFixed(0)}</td>
                    <td>{entry.avgNoise.toFixed(0)}</td>
                    <td>{entry.avgTemperature.toFixed(1)}°C</td>
                    <td>
                      {entry.avgPM25 !== null && entry.avgPM25 !== undefined
                        ? entry.avgPM25.toFixed(1)
                        : '—'}
                    </td>
                    <td>
                      {entry.avgHumidity !== null && entry.avgHumidity !== undefined
                        ? `${entry.avgHumidity.toFixed(0)}%`
                        : '—'}
                    </td>
                    <td>
                      {entry.aqi !== null && entry.aqi !== undefined ? (
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '2px 8px',
                            borderRadius: 4,
                            backgroundColor: `${aqi.color}20`,
                            color: aqi.color,
                            border: `1px solid ${aqi.color}40`,
                            fontWeight: 700,
                            fontSize: 12,
                          }}
                        >
                          {entry.aqi} · {aqi.label}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className={scoreColor(entry.cleanScore)} style={{ fontWeight: 700 }}>
                      {entry.cleanScore.toFixed(1)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div
        style={{
          marginTop: 16,
          fontSize: 12,
          color: '#94a3b8',
          textAlign: 'center',
        }}
      >
        Clean Score = 100 − (CO₂·0.30 + Tiếng Ồn·0.30 + PM2.5·0.40), càng cao càng sạch.
      </div>
    </div>
  );
};

export default LeaderboardView;
