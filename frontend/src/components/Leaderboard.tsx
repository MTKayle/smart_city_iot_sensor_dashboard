/**
 * Leaderboard Component — Location environmental quality ranking
 *
 * Displays a table showing locations ranked by Clean Score.
 * Extended with PM2.5, Humidity, and AQI columns.
 * Highlights top 3 locations and auto-refreshes every 60 seconds.
 *
 * Requirements: FR9.3
 */

import { useEffect, useState, useMemo } from 'react';
import { fetchLeaderboard } from '../services/api';
import type { LeaderboardEntry } from '../types';

export interface LeaderboardProps {
  onLocationClick?: (locationId: string) => void;
  refreshInterval?: number; // ms, default 60000
}

// ── Sort field type ──
type SortField = 'rank' | 'avgCO2' | 'avgNoise' | 'avgTemperature' | 'avgPM25' | 'avgHumidity' | 'aqi' | 'cleanScore';
type SortDirection = 'asc' | 'desc';

/**
 * Get medal emoji for top 3 ranks
 */
const getMedalIcon = (rank: number): string => {
  switch (rank) {
    case 1: return '🥇';
    case 2: return '🥈';
    case 3: return '🥉';
    default: return '';
  }
};

/**
 * Get background style for top 3 ranks
 */
const getRowStyle = (rank: number): React.CSSProperties => {
  const base: React.CSSProperties = {
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    backgroundColor: 'transparent',
    color: '#e0f2fe',
  };

  switch (rank) {
    case 1: return { ...base, backgroundColor: 'rgba(250, 204, 21, 0.12)', borderLeft: '3px solid #facc15' };
    case 2: return { ...base, backgroundColor: 'rgba(209, 213, 219, 0.10)', borderLeft: '3px solid #d1d5db' };
    case 3: return { ...base, backgroundColor: 'rgba(251, 146, 60, 0.10)', borderLeft: '3px solid #fb923c' };
    default: return { ...base, borderLeft: '3px solid transparent' };
  }
};

/**
 * Get color based on clean score value
 */
const getScoreColor = (score: number): string => {
  if (score >= 80) return '#00ff9d';
  if (score >= 60) return '#facc15';
  if (score >= 40) return '#fb923c';
  return '#ff003c';
};

/**
 * Get AQI badge color and label
 */
const getAqiInfo = (aqi: number | null | undefined): { color: string; label: string } => {
  if (aqi === null || aqi === undefined) return { color: '#64748b', label: '—' };
  if (aqi <= 50) return { color: '#22c55e', label: 'Good' };
  if (aqi <= 100) return { color: '#eab308', label: 'Moderate' };
  if (aqi <= 150) return { color: '#ea580c', label: 'USG' };
  if (aqi <= 200) return { color: '#dc2626', label: 'Unhealthy' };
  if (aqi <= 300) return { color: '#7e22ce', label: 'Very Bad' };
  return { color: '#831843', label: 'Hazardous' };
};

export const Leaderboard: React.FC<LeaderboardProps> = ({
  onLocationClick,
  refreshInterval = 60000,
}) => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortDir, setSortDir] = useState<SortDirection>('asc');

  const loadLeaderboard = async () => {
    try {
      setError(null);
      const data = await fetchLeaderboard();
      setLeaderboard(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load leaderboard');
      console.error('Error fetching leaderboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadLeaderboard(); }, []);

  useEffect(() => {
    const id = setInterval(loadLeaderboard, refreshInterval);
    return () => clearInterval(id);
  }, [refreshInterval]);

  // ── Sorting ──
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir(field === 'rank' ? 'asc' : 'desc');
    }
  };

  const sortedLeaderboard = useMemo(() => {
    const sorted = [...leaderboard].sort((a, b) => {
      let aVal: number, bVal: number;

      switch (sortField) {
        case 'rank': aVal = a.rank; bVal = b.rank; break;
        case 'avgCO2': aVal = a.avgCO2; bVal = b.avgCO2; break;
        case 'avgNoise': aVal = a.avgNoise; bVal = b.avgNoise; break;
        case 'avgTemperature': aVal = a.avgTemperature; bVal = b.avgTemperature; break;
        case 'avgPM25': aVal = a.avgPM25 ?? -1; bVal = b.avgPM25 ?? -1; break;
        case 'avgHumidity': aVal = a.avgHumidity ?? -1; bVal = b.avgHumidity ?? -1; break;
        case 'aqi': aVal = a.aqi ?? -1; bVal = b.aqi ?? -1; break;
        case 'cleanScore': aVal = a.cleanScore; bVal = b.cleanScore; break;
        default: aVal = a.rank; bVal = b.rank;
      }

      return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
    });

    return sorted;
  }, [leaderboard, sortField, sortDir]);

  const handleRowClick = (locationId: string) => {
    if (onLocationClick) onLocationClick(locationId);
  };

  // ── Sort indicator ──
  const sortIcon = (field: SortField) => {
    if (sortField !== field) return '';
    return sortDir === 'asc' ? ' ▲' : ' ▼';
  };

  // ── Render states ──
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px', color: '#64748b' }}>
        Loading leaderboard...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '400px', color: '#ef4444' }}>
        <p>Error: {error}</p>
        <button
          onClick={loadLeaderboard}
          style={{
            marginTop: '16px', padding: '8px 16px',
            backgroundColor: 'transparent', color: '#00f3ff',
            border: '1px solid #00f3ff', borderRadius: '6px',
            cursor: 'pointer', fontSize: '13px', fontWeight: '600',
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (leaderboard.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px', color: '#64748b' }}>
        No leaderboard data available
      </div>
    );
  }

  return (
    <div style={{ width: '100%', padding: '12px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h2 style={{
          margin: 0, fontSize: '16px', fontWeight: '700', color: '#e0f2fe',
          textTransform: 'uppercase', letterSpacing: '1px',
          textShadow: '0 0 10px rgba(0, 243, 255, 0.5)',
        }}>
          🏆 Leaderboard
        </h2>
        {lastUpdated && (
          <span style={{ fontSize: '11px', color: '#00f3ff', opacity: 0.7 }}>
            {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Table */}
      <div style={{ overflow: 'auto', maxHeight: '100%' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead>
            <tr style={{ backgroundColor: 'rgba(0, 243, 255, 0.04)', borderBottom: '2px solid rgba(0, 243, 255, 0.3)' }}>
              {[
                { field: 'rank' as SortField, label: '#' },
                { field: 'rank' as SortField, label: 'Location' },
                { field: 'avgCO2' as SortField, label: 'CO₂' },
                { field: 'avgNoise' as SortField, label: 'Noise' },
                { field: 'avgTemperature' as SortField, label: 'Temp' },
                { field: 'avgPM25' as SortField, label: 'PM2.5' },
                { field: 'avgHumidity' as SortField, label: 'Humid' },
                { field: 'aqi' as SortField, label: 'AQI' },
                { field: 'cleanScore' as SortField, label: 'Score' },
              ].map((col, i) => (
                <th
                  key={`${col.field}-${i}`}
                  onClick={() => i !== 1 ? handleSort(col.field) : undefined}
                  style={{
                    ...thStyle,
                    cursor: i !== 1 ? 'pointer' : 'default',
                    userSelect: 'none',
                  }}
                >
                  {col.label}{i !== 1 ? sortIcon(col.field) : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedLeaderboard.map((entry) => {
              const aqiInfo = getAqiInfo(entry.aqi);
              return (
                <tr
                  key={entry.locationId}
                  style={getRowStyle(entry.rank)}
                  onClick={() => handleRowClick(entry.locationId)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(0, 243, 255, 0.08)';
                    e.currentTarget.style.boxShadow = 'inset 0 0 10px rgba(0, 243, 255, 0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor =
                      (getRowStyle(entry.rank).backgroundColor as string) || 'transparent';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  {/* Rank */}
                  <td style={tdStyle}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'center' }}>
                      <span style={{ fontWeight: '600' }}>{entry.rank}</span>
                      {entry.rank <= 3 && <span style={{ fontSize: '14px' }}>{getMedalIcon(entry.rank)}</span>}
                    </div>
                  </td>
                  {/* Name */}
                  <td style={{ ...tdStyle, fontWeight: entry.rank <= 3 ? '600' : '400', textAlign: 'left' }}>
                    {entry.locationName}
                  </td>
                  {/* CO2 */}
                  <td style={tdStyle}>{entry.avgCO2.toFixed(0)}</td>
                  {/* Noise */}
                  <td style={tdStyle}>{entry.avgNoise.toFixed(0)}</td>
                  {/* Temperature */}
                  <td style={tdStyle}>{entry.avgTemperature.toFixed(1)}</td>
                  {/* PM2.5 */}
                  <td style={tdStyle}>
                    {entry.avgPM25 !== null && entry.avgPM25 !== undefined
                      ? entry.avgPM25.toFixed(1) : '—'}
                  </td>
                  {/* Humidity */}
                  <td style={tdStyle}>
                    {entry.avgHumidity !== null && entry.avgHumidity !== undefined
                      ? `${entry.avgHumidity.toFixed(0)}%` : '—'}
                  </td>
                  {/* AQI */}
                  <td style={tdStyle}>
                    {entry.aqi !== null && entry.aqi !== undefined ? (
                      <span style={{
                        display: 'inline-block', padding: '2px 6px',
                        borderRadius: '4px', fontSize: '11px', fontWeight: '700',
                        backgroundColor: `${aqiInfo.color}20`,
                        color: aqiInfo.color,
                        border: `1px solid ${aqiInfo.color}40`,
                      }}>
                        {entry.aqi}
                      </span>
                    ) : '—'}
                  </td>
                  {/* Score */}
                  <td style={{ ...tdStyle, fontWeight: '700' }}>
                    <span style={{ color: getScoreColor(entry.cleanScore) }}>
                      {entry.cleanScore.toFixed(1)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div style={{
        marginTop: '12px', display: 'flex', gap: '12px',
        justifyContent: 'center', fontSize: '12px', color: '#94a3b8',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span>🥇</span><span>1st</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span>🥈</span><span>2nd</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span>🥉</span><span>3rd</span>
        </div>
      </div>

      <div style={{
        marginTop: '6px', textAlign: 'center', color: '#00f3ff',
        fontSize: '10px', letterSpacing: '1px', opacity: 0.6,
      }}>
        CLICK LOCATION TO ZOOM ON MAP · CLICK HEADERS TO SORT
      </div>
    </div>
  );
};

// ── Shared cell styles ──
const thStyle: React.CSSProperties = {
  padding: '8px 6px', textAlign: 'center', fontSize: '11px',
  fontWeight: '700', color: '#00f3ff', textTransform: 'uppercase',
  letterSpacing: '0.5px', whiteSpace: 'nowrap',
};

const tdStyle: React.CSSProperties = {
  padding: '8px 6px', textAlign: 'center', fontSize: '12px',
  color: '#e0f2fe', borderBottom: '1px solid rgba(0, 243, 255, 0.12)',
  whiteSpace: 'nowrap',
};

export default Leaderboard;
