/**
 * Leaderboard Component - Location environmental quality ranking
 * 
 * Displays a table showing locations ranked by Clean Score.
 * Highlights top 3 locations and auto-refreshes every 60 seconds.
 * 
 * Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
 */

import { useEffect, useState } from 'react';
import { fetchLeaderboard } from '../services/api';
import type { LeaderboardEntry } from '../types';

/**
 * Leaderboard component props
 */
export interface LeaderboardProps {
  onLocationClick?: (locationId: string) => void;
  refreshInterval?: number; // milliseconds, default 60000 (60 seconds)
}

/**
 * Get medal emoji for top 3 ranks
 */
const getMedalIcon = (rank: number): string => {
  switch (rank) {
    case 1:
      return '🥇';
    case 2:
      return '🥈';
    case 3:
      return '🥉';
    default:
      return '';
  }
};

/**
 * Get background color for top 3 ranks
 */
const getRowStyle = (rank: number): React.CSSProperties => {
  const baseStyle: React.CSSProperties = {
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    backgroundColor: 'transparent',
    color: '#e0f2fe'
  };

  switch (rank) {
    case 1:
      return { ...baseStyle, backgroundColor: 'rgba(250, 204, 21, 0.15)', borderLeft: '3px solid #facc15' }; // gold
    case 2:
      return { ...baseStyle, backgroundColor: 'rgba(209, 213, 219, 0.15)', borderLeft: '3px solid #d1d5db' }; // silver
    case 3:
      return { ...baseStyle, backgroundColor: 'rgba(251, 146, 60, 0.15)', borderLeft: '3px solid #fb923c' }; // bronze
    default:
      return { ...baseStyle, borderLeft: '3px solid transparent' };
  }
};

/**
 * Leaderboard Component
 * 
 * Renders a table displaying locations ranked by Clean Score.
 * Top 3 locations are highlighted with visual indicators.
 * Auto-refreshes data every 60 seconds.
 */
export const Leaderboard: React.FC<LeaderboardProps> = ({
  onLocationClick,
  refreshInterval = 60000,
}) => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  /**
   * Fetch leaderboard data
   */
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

  /**
   * Fetch leaderboard data on mount
   */
  useEffect(() => {
    loadLeaderboard();
  }, []);

  /**
   * Set up auto-refresh interval
   */
  useEffect(() => {
    const intervalId = setInterval(() => {
      loadLeaderboard();
    }, refreshInterval);

    return () => clearInterval(intervalId);
  }, [refreshInterval]);

  /**
   * Handle row click
   */
  const handleRowClick = (locationId: string) => {
    if (onLocationClick) {
      onLocationClick(locationId);
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        color: '#6b7280',
      }}>
        Loading leaderboard...
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        color: '#ef4444',
      }}>
        <p>Error: {error}</p>
        <button
          onClick={loadLeaderboard}
          style={{
            marginTop: '16px',
            padding: '8px 16px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  /**
   * Render empty state
   */
  if (leaderboard.length === 0) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        color: '#6b7280',
      }}>
        No leaderboard data available
      </div>
    );
  }

  return (
    <div style={{ width: '100%', padding: '16px' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <h2 style={{ 
          margin: 0, 
          fontSize: '20px', 
          fontWeight: '700',
          color: '#e0f2fe',
          textTransform: 'uppercase',
          letterSpacing: '1px',
          textShadow: '0 0 10px rgba(0, 243, 255, 0.5)'
        }}>
          Leaderboard
        </h2>
        {lastUpdated && (
          <span style={{ 
            fontSize: '12px', 
            color: '#00f3ff',
          }}>
            Last updated: {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Table */}
      <div style={{ 
        backgroundColor: 'transparent',
        borderRadius: '0',
        overflow: 'hidden',
      }}>
        <table style={{ 
          width: '100%', 
          borderCollapse: 'collapse',
        }}>
          <thead>
            <tr style={{ 
              backgroundColor: 'rgba(0, 243, 255, 0.05)',
              borderBottom: '2px solid rgba(0, 243, 255, 0.5)',
            }}>
              <th style={headerCellStyle}>Rank</th>
              <th style={headerCellStyle}>Location</th>
              <th style={headerCellStyle}>CO2 (ppm)</th>
              <th style={headerCellStyle}>Noise (dB)</th>
              <th style={headerCellStyle}>Score</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((entry) => (
              <tr
                key={entry.locationId}
                style={getRowStyle(entry.rank)}
                onClick={() => handleRowClick(entry.locationId)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = darkenColor('');
                  e.currentTarget.style.boxShadow = 'inset 0 0 10px rgba(0, 243, 255, 0.2)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = (getRowStyle(entry.rank).backgroundColor as string) || 'transparent';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <td style={cellStyle}>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    justifyContent: 'center',
                  }}>
                    <span style={{ fontWeight: '600' }}>{entry.rank}</span>
                    {entry.rank <= 3 && (
                      <span style={{ fontSize: '20px' }}>
                        {getMedalIcon(entry.rank)}
                      </span>
                    )}
                  </div>
                </td>
                <td style={{ ...cellStyle, fontWeight: entry.rank <= 3 ? '600' : '400' }}>
                  {entry.locationName}
                </td>
                <td style={cellStyle}>{entry.avgCO2.toFixed(1)}</td>
                <td style={cellStyle}>{entry.avgNoise.toFixed(1)}</td>
                <td style={{ ...cellStyle, fontWeight: '600' }}>
                  <span style={{ 
                    color: getScoreColor(entry.cleanScore),
                  }}>
                    {entry.cleanScore.toFixed(1)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div style={{ 
        marginTop: '16px', 
        display: 'flex', 
        gap: '16px',
        justifyContent: 'center',
        fontSize: '14px',
        color: '#94a3b8',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span>🥇</span>
          <span>1st</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span>🥈</span>
          <span>2nd</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span>🥉</span>
          <span>3rd</span>
        </div>
      </div>

      {/* Info */}
      <div style={{ 
        marginTop: '8px', 
        textAlign: 'center', 
        color: '#00f3ff',
        fontSize: '11px',
        letterSpacing: '1px',
        opacity: 0.7
      }}>
        CLICK LOCATION TO ZOOM OVER MAP
      </div>
    </div>
  );
};

/**
 * Table header cell style
 */
const headerCellStyle: React.CSSProperties = {
  padding: '12px 16px',
  textAlign: 'center',
  fontSize: '13px',
  fontWeight: '700',
  color: '#00f3ff', // Neon Cyan
  textTransform: 'uppercase',
  letterSpacing: '1px',
};

/**
 * Table cell style
 */
const cellStyle: React.CSSProperties = {
  padding: '12px 16px',
  textAlign: 'center',
  fontSize: '14px',
  color: '#e0f2fe',
  borderBottom: '1px solid rgba(0, 243, 255, 0.2)',
};

/**
 * Get color based on clean score value
 */
const getScoreColor = (score: number): string => {
  if (score >= 80) return '#00ff9d'; // neon green
  if (score >= 60) return '#facc15'; // neon yellow
  if (score >= 40) return '#fb923c'; // neon orange
  return '#ff003c'; // neon red
};

/**
 * Darken a hex color by 10% for hover effect
 */
const darkenColor = (_color: string): string => {
  // Overridden: Instead of matching exact colors, we use standard hover states
  return 'rgba(0, 243, 255, 0.1)';
};

export default Leaderboard;
