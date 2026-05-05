/**
 * useTelemetryHistory — rolling buffer of telemetry samples for a single sensor.
 *
 * Seeds with the most recent N points from REST `/api/telemetry/{id}` so the
 * chart isn't empty on first open, then appends realtime samples as the
 * AppContext.telemetryMap updates from WebSocket.
 *
 * Each point is flat (pm25/co2/temperature/humidity/noise/aqi) so the chart
 * can switch metric without remapping the data array.
 */

import { useEffect, useRef, useState } from 'react';
import { useAppContext } from '../context/AppContext';
import { fetchTelemetry } from '../services/api';

export interface TelemetryHistoryPoint {
  timestamp: string;
  time: string; // formatted hh:mm:ss for X axis
  pm25: number | null;
  co2: number | null;
  temperature: number | null;
  humidity: number | null;
  noise: number | null;
  aqi: number | null;
}

const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

export function useTelemetryHistory(
  sensorId: string | null,
  maxPoints: number = 60,
): TelemetryHistoryPoint[] {
  const { telemetryMap } = useAppContext();
  const [history, setHistory] = useState<TelemetryHistoryPoint[]>([]);
  const lastTimestampRef = useRef<string | null>(null);
  const sensorIdRef = useRef<string | null>(null);

  // Reset + seed from REST whenever sensorId changes.
  useEffect(() => {
    let cancelled = false;
    setHistory([]);
    lastTimestampRef.current = null;
    sensorIdRef.current = sensorId;

    if (!sensorId) return;

    fetchTelemetry(sensorId, { limit: maxPoints })
      .then((rows) => {
        if (cancelled || sensorIdRef.current !== sensorId) return;
        const sorted = [...rows].sort(
          (a, b) =>
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
        );
        const points: TelemetryHistoryPoint[] = sorted.map((t) => ({
          timestamp: t.timestamp,
          time: fmtTime(t.timestamp),
          pm25: (t.pm25 ?? t.data?.pm25 ?? null) as number | null,
          co2: (t.co2 ?? t.data?.co2 ?? null) as number | null,
          temperature: (t.temperature ?? t.data?.temperature ?? null) as number | null,
          humidity: (t.humidity ?? t.data?.humidity ?? null) as number | null,
          noise: (t.noise ?? t.data?.noise ?? null) as number | null,
          aqi: (t.aqi ?? null) as number | null,
        }));
        const trimmed = points.slice(-maxPoints);
        setHistory(trimmed);
        if (trimmed.length > 0) {
          lastTimestampRef.current = trimmed[trimmed.length - 1].timestamp;
        }
      })
      .catch((err) => console.error('useTelemetryHistory seed failed:', err));

    return () => {
      cancelled = true;
    };
  }, [sensorId, maxPoints]);

  // Append a realtime sample whenever a new telemetry arrives for this sensor.
  useEffect(() => {
    if (!sensorId) return;
    const t = telemetryMap[sensorId];
    if (!t) return;
    if (t.timestamp === lastTimestampRef.current) return;
    lastTimestampRef.current = t.timestamp;

    setHistory((prev) => {
      const next: TelemetryHistoryPoint = {
        timestamp: t.timestamp,
        time: fmtTime(t.timestamp),
        pm25: (t.pm25 ?? t.data?.pm25 ?? null) as number | null,
        co2: (t.co2 ?? t.data?.co2 ?? null) as number | null,
        temperature: (t.temperature ?? t.data?.temperature ?? null) as number | null,
        humidity: (t.humidity ?? t.data?.humidity ?? null) as number | null,
        noise: (t.noise ?? t.data?.noise ?? null) as number | null,
        aqi: (t.aqi ?? null) as number | null,
      };
      return [...prev, next].slice(-maxPoints);
    });
  }, [sensorId, telemetryMap, maxPoints]);

  return history;
}

/**
 * useClusterHistory — rolling buffer of cluster-averaged samples.
 *
 * Recomputes the average across all member sensors whenever telemetryMap
 * changes, throttled to once per second to avoid noise.
 */
export function useClusterHistory(
  memberIds: string[],
  maxPoints: number = 60,
): TelemetryHistoryPoint[] {
  const { telemetryMap } = useAppContext();
  const [history, setHistory] = useState<TelemetryHistoryPoint[]>([]);
  const lastSampleAtRef = useRef<number>(0);

  // Stable join key so we can reset on member-set change.
  const memberKey = [...memberIds].sort().join(',');

  useEffect(() => {
    setHistory([]);
    lastSampleAtRef.current = 0;
  }, [memberKey]);

  useEffect(() => {
    if (memberIds.length === 0) return;

    const now = Date.now();
    // Throttle to one sample every 2 s — telemetryMap can update faster than the chart needs.
    if (now - lastSampleAtRef.current < 2000) return;

    const members = memberIds
      .map((id) => telemetryMap[id])
      .filter((t): t is NonNullable<typeof t> => t !== undefined);

    if (members.length === 0) return;

    const avg = (
      key: 'pm25' | 'co2' | 'temperature' | 'humidity' | 'noise',
    ): number | null => {
      const vals = members
        .map((m) => {
          const flat = (m as unknown as Record<string, unknown>)[key];
          if (typeof flat === 'number') return flat;
          const nested = m.data?.[key];
          return typeof nested === 'number' ? nested : null;
        })
        .filter((v): v is number => v !== null && !isNaN(v));
      return vals.length > 0 ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
    };

    const aqiAvg = (() => {
      const vals = members
        .map((m) => m.aqi)
        .filter((v): v is number => typeof v === 'number');
      return vals.length > 0 ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
    })();

    lastSampleAtRef.current = now;
    const ts = new Date().toISOString();

    setHistory((prev) =>
      [
        ...prev,
        {
          timestamp: ts,
          time: fmtTime(ts),
          pm25: avg('pm25'),
          co2: avg('co2'),
          temperature: avg('temperature'),
          humidity: avg('humidity'),
          noise: avg('noise'),
          aqi: aqiAvg,
        },
      ].slice(-maxPoints),
    );
  }, [telemetryMap, memberIds, memberKey, maxPoints]);

  return history;
}
