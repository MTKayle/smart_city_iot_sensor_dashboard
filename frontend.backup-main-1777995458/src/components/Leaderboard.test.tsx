/**
 * Leaderboard Component Tests
 * 
 * Tests for the Leaderboard component rendering and functionality.
 * 
 * Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Leaderboard } from './Leaderboard';
import * as api from '../services/api';
import type { LeaderboardEntry } from '../types';

// Mock the API module
vi.mock('../services/api');

describe('Leaderboard Component', () => {
  const mockLeaderboardData: LeaderboardEntry[] = [
    {
      locationId: 'loc-1',
      locationName: 'Ward 1',
      avgCO2: 420.5,
      avgNoise: 55.2,
      avgTemperature: 26.3,
      cleanScore: 85.5,
      rank: 1,
    },
    {
      locationId: 'loc-2',
      locationName: 'Ward 2',
      avgCO2: 480.0,
      avgNoise: 60.0,
      avgTemperature: 25.0,
      cleanScore: 78.0,
      rank: 2,
    },
    {
      locationId: 'loc-3',
      locationName: 'Ward 3',
      avgCO2: 520.0,
      avgNoise: 65.0,
      avgTemperature: 27.0,
      cleanScore: 72.5,
      rank: 3,
    },
    {
      locationId: 'loc-4',
      locationName: 'Ward 4',
      avgCO2: 600.0,
      avgNoise: 70.0,
      avgTemperature: 28.0,
      cleanScore: 65.0,
      rank: 4,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should render leaderboard table with data', async () => {
    vi.mocked(api.fetchLeaderboard).mockResolvedValue(mockLeaderboardData);

    render(<Leaderboard />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Environmental Quality Leaderboard')).toBeDefined();
    });

    // Check table headers
    expect(screen.getByText('Rank')).toBeDefined();
    expect(screen.getByText('Location Name')).toBeDefined();
    expect(screen.getByText('Avg CO2 (ppm)')).toBeDefined();
    expect(screen.getByText('Avg Noise (dB)')).toBeDefined();
    expect(screen.getByText('Clean Score')).toBeDefined();

    // Check data rows
    expect(screen.getByText('Ward 1')).toBeDefined();
    expect(screen.getByText('Ward 2')).toBeDefined();
    expect(screen.getByText('Ward 3')).toBeDefined();
    expect(screen.getByText('Ward 4')).toBeDefined();
  });

  it('should display loading state initially', () => {
    vi.mocked(api.fetchLeaderboard).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<Leaderboard />);

    expect(screen.getByText('Loading leaderboard...')).toBeDefined();
  });

  it('should display error state on fetch failure', async () => {
    const errorMessage = 'Failed to fetch leaderboard';
    vi.mocked(api.fetchLeaderboard).mockRejectedValue(new Error(errorMessage));

    render(<Leaderboard />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeDefined();
      expect(screen.getByText(/Failed to fetch leaderboard/)).toBeDefined();
    });

    // Check retry button exists
    expect(screen.getByText('Retry')).toBeDefined();
  });

  it('should display empty state when no data', async () => {
    vi.mocked(api.fetchLeaderboard).mockResolvedValue([]);

    render(<Leaderboard />);

    await waitFor(() => {
      expect(screen.getByText('No leaderboard data available')).toBeDefined();
    });
  });

  it('should highlight top 3 locations with medals', async () => {
    vi.mocked(api.fetchLeaderboard).mockResolvedValue(mockLeaderboardData);

    const { container } = render(<Leaderboard />);

    await waitFor(() => {
      expect(screen.getByText('Ward 1')).toBeDefined();
    });

    // Check for medal emojis (🥇, 🥈, 🥉)
    const medals = container.querySelectorAll('span[style*="font-size: 20px"]');
    expect(medals.length).toBe(3); // Top 3 should have medals
  });

  it('should call onLocationClick when row is clicked', async () => {
    vi.mocked(api.fetchLeaderboard).mockResolvedValue(mockLeaderboardData);
    const onLocationClick = vi.fn();

    render(<Leaderboard onLocationClick={onLocationClick} />);

    await waitFor(() => {
      expect(screen.getByText('Ward 1')).toBeDefined();
    });

    // Click on first row
    const ward1Row = screen.getByText('Ward 1').closest('tr');
    expect(ward1Row).toBeDefined();
    
    if (ward1Row) {
      await userEvent.click(ward1Row);
      expect(onLocationClick).toHaveBeenCalledWith('loc-1');
    }
  });

  it('should auto-refresh data every 60 seconds', async () => {
    vi.useFakeTimers();
    vi.mocked(api.fetchLeaderboard).mockResolvedValue(mockLeaderboardData);

    render(<Leaderboard />);

    // Initial load
    await vi.waitFor(() => {
      expect(api.fetchLeaderboard).toHaveBeenCalledTimes(1);
    }, { timeout: 1000 });

    // Advance time by 60 seconds
    await vi.advanceTimersByTimeAsync(60000);

    expect(api.fetchLeaderboard).toHaveBeenCalledTimes(2);

    vi.useRealTimers();
  });

  it('should use custom refresh interval', async () => {
    vi.useFakeTimers();
    vi.mocked(api.fetchLeaderboard).mockResolvedValue(mockLeaderboardData);

    render(<Leaderboard refreshInterval={30000} />);

    // Initial load
    await vi.waitFor(() => {
      expect(api.fetchLeaderboard).toHaveBeenCalledTimes(1);
    }, { timeout: 1000 });

    // Advance time by 30 seconds
    await vi.advanceTimersByTimeAsync(30000);

    expect(api.fetchLeaderboard).toHaveBeenCalledTimes(2);

    vi.useRealTimers();
  });

  it('should display last updated timestamp', async () => {
    vi.mocked(api.fetchLeaderboard).mockResolvedValue(mockLeaderboardData);

    render(<Leaderboard />);

    await waitFor(() => {
      const element = screen.queryByText(/Last updated:/);
      expect(element).not.toBeNull();
    }, { timeout: 1000 });
  });

  it('should display correct column values', async () => {
    vi.mocked(api.fetchLeaderboard).mockResolvedValue(mockLeaderboardData);

    render(<Leaderboard />);

    await waitFor(() => {
      expect(screen.queryByText('Ward 1')).not.toBeNull();
    }, { timeout: 1000 });

    // Check first entry values
    expect(screen.queryByText('420.5')).not.toBeNull(); // avgCO2
    expect(screen.queryByText('55.2')).not.toBeNull(); // avgNoise
    expect(screen.queryByText('85.5')).not.toBeNull(); // cleanScore
  });

  it('should display legend for medal indicators', async () => {
    vi.mocked(api.fetchLeaderboard).mockResolvedValue(mockLeaderboardData);

    render(<Leaderboard />);

    await waitFor(() => {
      expect(screen.queryByText('Ward 1')).not.toBeNull();
    }, { timeout: 1000 });

    // Check legend
    expect(screen.queryByText('1st Place')).not.toBeNull();
    expect(screen.queryByText('2nd Place')).not.toBeNull();
    expect(screen.queryByText('3rd Place')).not.toBeNull();
  });

  it('should display info text about clicking and auto-refresh', async () => {
    vi.mocked(api.fetchLeaderboard).mockResolvedValue(mockLeaderboardData);

    render(<Leaderboard />);

    await waitFor(() => {
      expect(screen.queryByText('Ward 1')).not.toBeNull();
    }, { timeout: 1000 });

    expect(screen.queryByText(/Click on a location to zoom the map/)).not.toBeNull();
    expect(screen.queryByText(/Auto-refreshes every 60 seconds/)).not.toBeNull();
  });

  it('should retry loading on retry button click', async () => {
    vi.mocked(api.fetchLeaderboard)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce(mockLeaderboardData);

    render(<Leaderboard />);

    // Wait for error state
    await waitFor(() => {
      expect(screen.queryByText(/Error:/)).not.toBeNull();
    }, { timeout: 1000 });

    // Click retry button
    const retryButton = screen.getByText('Retry');
    await userEvent.click(retryButton);

    // Should load data successfully
    await waitFor(() => {
      expect(screen.queryByText('Ward 1')).not.toBeNull();
    }, { timeout: 1000 });
  });

  it('should clean up interval on unmount', async () => {
    vi.useFakeTimers();
    vi.mocked(api.fetchLeaderboard).mockResolvedValue(mockLeaderboardData);

    const { unmount } = render(<Leaderboard />);

    await vi.waitFor(() => {
      expect(api.fetchLeaderboard).toHaveBeenCalledTimes(1);
    }, { timeout: 1000 });

    // Unmount component
    unmount();

    // Advance time - should not trigger more fetches
    await vi.advanceTimersByTimeAsync(60000);

    // Should still be only 1 call
    expect(api.fetchLeaderboard).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });
});
