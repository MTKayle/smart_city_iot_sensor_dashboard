import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useAppContext } from '../../../context/AppContext';
import type { Sensor, Telemetry } from '../../../types';

const WINDOW_MS = 15 * 60 * 1000; // rolling 15-minute window
const SAMPLE_LIMIT = 240;          // hard cap on stored points per metric

interface RealtimeLiveChartProps {
  /** The sensors that should feed the rolling buffer (already scoped). */
  sensors: Sensor[];
}

interface Sample {
  t: number;       // epoch ms
  pm25: number;
  temperature: number;
  humidity: number;
  co2: number;
  noise: number;
}

/**
 * Live rolling chart of the area average across the in-scope sensors.
 *
 * Subscribes to AppContext.telemetryMap; whenever a new reading arrives, the
 * scoped sensors are averaged and a new sample is pushed onto the buffer.
 * Old samples beyond `WINDOW_MS` are evicted on every update so the chart
 * stays bounded.
 */
const RealtimeLiveChart: React.FC<RealtimeLiveChartProps> = ({ sensors }) => {
  const { telemetryMap } = useAppContext();
  const [samples, setSamples] = useState<Sample[]>([]);
  const lastTimestampRef = useRef<string | null>(null);

  // Reset the buffer if the scope changes (different sensor set).
  const sensorIds = useMemo(() => sensors.map((s) => s.sensorId).sort().join(','), [sensors]);
  useEffect(() => {
    setSamples([]);
    lastTimestampRef.current = null;
  }, [sensorIds]);

  useEffect(() => {
    if (sensors.length === 0) return;

    const now = Date.now();
    const tels: Telemetry[] = sensors
      .map((s) => telemetryMap[s.sensorId])
      .filter((t): t is Telemetry => t !== undefined);
    if (tels.length === 0) return;

    // Use the freshest timestamp in the bundle as the de-duplication key.
    const newest = tels.reduce((acc, t) => (t.timestamp > acc ? t.timestamp : acc), '');
    if (newest === lastTimestampRef.current) return;
    lastTimestampRef.current = newest;

    const avg = (vals: Array<number | undefined | null>): number => {
      const nums = vals
        .map((v) => (v === undefined || v === null ? null : Number(v)))
        .filter((v): v is number => v !== null && !isNaN(v));
      if (nums.length === 0) return 0;
      return nums.reduce((a, b) => a + b, 0) / nums.length;
    };

    const sample: Sample = {
      t: now,
      pm25:        avg(tels.map((t) => t.pm25 ?? t.data?.pm25)),
      temperature: avg(tels.map((t) => t.temperature ?? t.data?.temperature)),
      humidity:    avg(tels.map((t) => t.humidity ?? t.data?.humidity)),
      co2:         avg(tels.map((t) => t.co2 ?? t.data?.co2)),
      noise:       avg(tels.map((t) => t.noise ?? t.data?.noise)),
    };

    setSamples((prev) => {
      const cutoff = now - WINDOW_MS;
      const next = [...prev, sample].filter((s) => s.t >= cutoff);
      return next.length > SAMPLE_LIMIT ? next.slice(-SAMPLE_LIMIT) : next;
    });
  }, [telemetryMap, sensors]);

  // Pretty-format a sample timestamp on the x-axis.
  const data = samples.map((s) => ({
    ...s,
    label: new Date(s.t).toLocaleTimeString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
  }));

  const last = samples[samples.length - 1];

  return (
    <div className="chart-card full-width realtime-live-chart" id="realtime-live-chart">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <span className="live-dot" /> Trực Tiếp — 15 phút gần nhất
          </h3>
          <p className="card-subtitle">
            {samples.length === 0
              ? 'Đang chờ dữ liệu mới…'
              : `${samples.length} điểm dữ liệu · cập nhật ${last ? new Date(last.t).toLocaleTimeString('vi-VN') : ''}`}
          </p>
        </div>
        {last && (
          <div className="realtime-pill-row">
            <span className="realtime-pill" style={{ borderColor: '#3B82F6', color: '#3B82F6' }}>
              PM2.5 {last.pm25.toFixed(1)}
            </span>
            <span className="realtime-pill" style={{ borderColor: '#F97316', color: '#F97316' }}>
              {last.temperature.toFixed(1)}°C
            </span>
            <span className="realtime-pill" style={{ borderColor: '#06B6D4', color: '#06B6D4' }}>
              {last.humidity.toFixed(0)}%
            </span>
            <span className="realtime-pill" style={{ borderColor: '#8B5CF6', color: '#8B5CF6' }}>
              CO₂ {last.co2.toFixed(0)}
            </span>
            <span className="realtime-pill" style={{ borderColor: '#10B981', color: '#10B981' }}>
              {last.noise.toFixed(0)} dB
            </span>
          </div>
        )}
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="label" stroke="#9CA3AF" fontSize={11} minTickGap={28} />
          {/* Left axis: PM2.5 + temp + humidity + noise (shared but small ranges) */}
          <YAxis yAxisId="left" stroke="#9CA3AF" fontSize={11} width={42} />
          {/* Right axis: CO2 (much larger scale) */}
          <YAxis yAxisId="right" orientation="right" stroke="#9CA3AF" fontSize={11} width={50} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 8 }}
            labelFormatter={(label) => `Lúc ${label}`}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line yAxisId="left" type="monotone" dataKey="pm25"        stroke="#3B82F6" strokeWidth={2} dot={false} name="PM2.5 (µg/m³)" />
          <Line yAxisId="left" type="monotone" dataKey="temperature" stroke="#F97316" strokeWidth={2} dot={false} name="Nhiệt độ (°C)" />
          <Line yAxisId="left" type="monotone" dataKey="humidity"    stroke="#06B6D4" strokeWidth={2} dot={false} name="Độ ẩm (%)" />
          <Line yAxisId="left" type="monotone" dataKey="noise"       stroke="#10B981" strokeWidth={2} dot={false} name="Tiếng ồn (dB)" />
          <Line yAxisId="right" type="monotone" dataKey="co2"        stroke="#8B5CF6" strokeWidth={2} dot={false} name="CO₂ (ppm)" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RealtimeLiveChart;
