import React, { useEffect, useMemo, useState } from 'react';
import { Trophy, RefreshCw, Search, Filter, RotateCcw, Check, AlertTriangle } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import { triggerLeaderboardRefresh } from '../../services/api';
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
type ScopeFilter = 'all' | 'City' | 'District' | 'Ward';

const ALL = '__ALL__';

const medalIcon = (rank: number) =>
  rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : '';

const scoreColor = (score: number) =>
  score >= 80 ? 'text-green-400'
  : score >= 60 ? 'text-yellow-400'
  : score >= 40 ? 'text-orange-400'
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

const SCOPE_OPTIONS: Array<{ id: ScopeFilter; label: string; emoji: string }> = [
  { id: 'all',      label: 'Tất cả',     emoji: '🌐' },
  { id: 'City',     label: 'Thành phố',  emoji: '🏙' },
  { id: 'District', label: 'Quận',       emoji: '🏘' },
  { id: 'Ward',     label: 'Phường',     emoji: '📍' },
];

const LeaderboardView: React.FC = () => {
  const { leaderboard, refreshLeaderboard, locations } = useAppContext();

  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshAt, setLastRefreshAt] = useState<Date | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [refreshSuccess, setRefreshSuccess] = useState(false);

  // ─── Filter state ───
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>('all');
  const [districtId, setDistrictId] = useState<string>(ALL);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const districts = useMemo(
    () => locations.filter((l) => l.type === 'District'),
    [locations],
  );

  // Resetting district filter when scope changes to a level where it doesn't apply.
  useEffect(() => {
    if (scopeFilter === 'City') {
      // City scope ignores district — clear it.
      setDistrictId(ALL);
    }
  }, [scopeFilter]);

  // Build a quick lookup: locationId → (type, parentId).
  const locationMeta = useMemo(() => {
    const map = new Map<string, { type: string; parentId: string | null }>();
    for (const l of locations) {
      map.set(l.locationId, { type: l.type, parentId: l.parentId ?? null });
    }
    return map;
  }, [locations]);

  // ─── Filter pipeline ───
  // Steps: scope filter → district filter → search → re-rank.
  const filteredEntries = useMemo(() => {
    let list: LeaderboardEntry[] = [...leaderboard];

    // 1. Scope: City | District | Ward | all
    if (scopeFilter !== 'all') {
      list = list.filter((e) => {
        const meta = locationMeta.get(e.locationId);
        return meta?.type === scopeFilter;
      });
    }

    // 2. District: only meaningful when scope is District or Ward (or all)
    if (districtId !== ALL) {
      list = list.filter((e) => {
        const meta = locationMeta.get(e.locationId);
        if (!meta) return false;
        if (meta.type === 'District') return e.locationId === districtId;
        if (meta.type === 'Ward')     return meta.parentId === districtId;
        // City never matches a district filter.
        return false;
      });
    }

    // 3. Search by name (case-insensitive, accent-insensitive).
    if (searchQuery.trim()) {
      const norm = (s: string) =>
        s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
      const q = norm(searchQuery.trim());
      list = list.filter((e) => norm(e.locationName).includes(q));
    }

    return list;
  }, [leaderboard, scopeFilter, districtId, searchQuery, locationMeta]);

  // Re-rank within the filtered subset so #1 is the visible top.
  const rerankedEntries = useMemo(() => {
    return [...filteredEntries]
      .sort((a, b) => b.cleanScore - a.cleanScore)
      .map((e, i) => ({ ...e, rank: i + 1 }));
  }, [filteredEntries]);

  // ─── Sort by user choice ───
  const sortedEntries = useMemo(() => {
    const get = (e: LeaderboardEntry, field: SortField): number => {
      switch (field) {
        case 'rank':           return e.rank;
        case 'avgCO2':         return e.avgCO2;
        case 'avgNoise':       return e.avgNoise;
        case 'avgTemperature': return e.avgTemperature;
        case 'avgPM25':        return e.avgPM25 ?? -1;
        case 'avgHumidity':    return e.avgHumidity ?? -1;
        case 'aqi':            return e.aqi ?? -1;
        case 'cleanScore':     return e.cleanScore;
      }
    };
    return [...rerankedEntries].sort((a, b) => {
      const av = get(a, sortField);
      const bv = get(b, sortField);
      return sortDir === 'asc' ? av - bv : bv - av;
    });
  }, [rerankedEntries, sortField, sortDir]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir(field === 'rank' ? 'asc' : 'desc');
    }
  };

  // Force-refresh: trigger the aggregator on the server, then re-fetch.
  // This guarantees the user sees up-to-the-minute data instead of whatever
  // the scheduler computed last.
  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshError(null);
    setRefreshSuccess(false);
    try {
      const result = await triggerLeaderboardRefresh('HOURLY', 2);
      setLastRefreshAt(new Date(result.refreshedAt));
      // Re-fetch via context so AppContext.leaderboard updates everywhere.
      await refreshLeaderboard();
      setRefreshSuccess(true);
      // Auto-hide the success indicator after 3s.
      setTimeout(() => setRefreshSuccess(false), 3000);
    } catch (err) {
      console.error('Leaderboard refresh failed:', err);
      setRefreshError('Không thể làm mới — kiểm tra kết nối backend');
      setTimeout(() => setRefreshError(null), 5000);
    } finally {
      setRefreshing(false);
    }
  };

  const formatLastRefresh = (d: Date): string => {
    return d.toLocaleTimeString('vi-VN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  };

  const sortIcon = (f: SortField) =>
    sortField === f ? (sortDir === 'asc' ? ' ▲' : ' ▼') : '';

  const isFiltered = scopeFilter !== 'all' || districtId !== ALL || searchQuery.trim() !== '';

  const districtFilterDisabled = scopeFilter === 'City';

  // Append the type label for clarity once filters are mixed.
  const renderLocationName = (entry: LeaderboardEntry): string => {
    const meta = locationMeta.get(entry.locationId);
    if (!meta) return entry.locationName;
    if (meta.type === 'Ward' && meta.parentId) {
      const parent = locations.find((l) => l.locationId === meta.parentId);
      return parent ? `${entry.locationName}, ${parent.name}` : entry.locationName;
    }
    return entry.locationName;
  };

  return (
    <div className="leaderboard-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">
            <Trophy className="inline w-6 h-6 mr-2 text-yellow-400" />
            Bảng Xếp Hạng Khu Vực
          </h1>
          <p className="view-subtitle">
            Xếp hạng theo Clean Score —{' '}
            {isFiltered
              ? `${rerankedEntries.length} / ${leaderboard.length} khu vực`
              : `${leaderboard.length} khu vực có dữ liệu`}
          </p>
        </div>
        <div className="leaderboard-refresh-block">
          <button
            className={`leaderboard-refresh-btn ${refreshSuccess ? 'success' : ''} ${refreshError ? 'error' : ''}`}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshSuccess ? (
              <Check className="w-4 h-4" />
            ) : refreshError ? (
              <AlertTriangle className="w-4 h-4" />
            ) : (
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            )}
            <span>
              {refreshing
                ? 'Đang aggregate Mongo → Oracle…'
                : refreshSuccess
                ? 'Đã làm mới'
                : refreshError
                ? 'Lỗi'
                : 'Làm Mới'}
            </span>
          </button>
          {lastRefreshAt && !refreshing && !refreshError && (
            <span className="leaderboard-refresh-time">
              Cập nhật lúc {formatLastRefresh(lastRefreshAt)}
            </span>
          )}
          {refreshError && (
            <span className="leaderboard-refresh-error">{refreshError}</span>
          )}
        </div>
      </div>

      {/* ─── Filter bar ─── */}
      <div className="leaderboard-filter-bar">
        <div className="leaderboard-filter-group">
          <Filter className="filter-icon" />
          <span className="filter-label">Cấp</span>
          <div className="leaderboard-scope-pills">
            {SCOPE_OPTIONS.map((opt) => (
              <button
                key={opt.id}
                className={`leaderboard-scope-pill ${scopeFilter === opt.id ? 'active' : ''}`}
                onClick={() => setScopeFilter(opt.id)}
              >
                <span className="leaderboard-scope-emoji">{opt.emoji}</span>
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="leaderboard-filter-group">
          <span className="filter-label">Quận</span>
          <select
            className="filter-select"
            value={districtId}
            onChange={(e) => setDistrictId(e.target.value)}
            disabled={districtFilterDisabled}
            title={districtFilterDisabled ? 'Cấp Thành phố không lọc theo quận' : ''}
          >
            <option value={ALL}>Tất cả quận</option>
            {districts.map((d) => (
              <option key={d.locationId} value={d.locationId}>
                {d.name}
              </option>
            ))}
          </select>
        </div>

        <div className="leaderboard-filter-group leaderboard-search-group">
          <Search className="filter-icon" />
          <input
            type="text"
            className="leaderboard-search"
            placeholder="Tìm theo tên (Bến, Nguyễn, Phường…)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {isFiltered && (
          <button
            className="filter-reset-btn"
            onClick={() => {
              setScopeFilter('all');
              setDistrictId(ALL);
              setSearchQuery('');
            }}
          >
            <RotateCcw className="w-4 h-4" />
            <span>Đặt lại</span>
          </button>
        )}
      </div>

      {sortedEntries.length === 0 ? (
        <div className="alert-card" style={{ marginTop: 'var(--spacing-lg)' }}>
          <p className="text-gray-400">
            {leaderboard.length === 0
              ? 'Chưa có dữ liệu Clean Score. Lịch trình daily aggregation chạy lúc 00:00 và hourly cluster aggregation chạy mỗi giờ — chờ lần kế tiếp.'
              : 'Không có khu vực nào khớp bộ lọc hiện tại.'}
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
                <th>Cấp</th>
                <th onClick={() => handleSort('avgCO2')} style={{ cursor: 'pointer' }}>
                  CO₂{sortIcon('avgCO2')}
                </th>
                <th onClick={() => handleSort('avgNoise')} style={{ cursor: 'pointer' }}>
                  Tiếng Ồn{sortIcon('avgNoise')}
                </th>
                <th onClick={() => handleSort('avgTemperature')} style={{ cursor: 'pointer' }}>
                  Nhiệt Độ{sortIcon('avgTemperature')}
                </th>
                <th onClick={() => handleSort('avgPM25')} style={{ cursor: 'pointer' }}>
                  PM2.5{sortIcon('avgPM25')}
                </th>
                <th onClick={() => handleSort('avgHumidity')} style={{ cursor: 'pointer' }}>
                  Độ Ẩm{sortIcon('avgHumidity')}
                </th>
                <th onClick={() => handleSort('aqi')} style={{ cursor: 'pointer' }}>
                  AQI{sortIcon('aqi')}
                </th>
                <th onClick={() => handleSort('cleanScore')} style={{ cursor: 'pointer' }}>
                  Clean Score{sortIcon('cleanScore')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedEntries.map((entry) => {
                const aqi = aqiInfo(entry.aqi);
                const meta = locationMeta.get(entry.locationId);
                const typeLabel = meta?.type === 'City' ? 'Thành phố'
                                : meta?.type === 'District' ? 'Quận'
                                : meta?.type === 'Ward' ? 'Phường' : '—';
                return (
                  <tr key={entry.locationId}>
                    <td>
                      <span style={{ fontWeight: 600 }}>{entry.rank}</span>
                      {entry.rank <= 3 && (
                        <span style={{ marginLeft: 4 }}>{medalIcon(entry.rank)}</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'left', fontWeight: entry.rank <= 3 ? 600 : 400 }}>
                      {renderLocationName(entry)}
                    </td>
                    <td>
                      <span className={`leaderboard-type-badge type-${meta?.type ?? 'unknown'}`}>
                        {typeLabel}
                      </span>
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
