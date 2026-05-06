import React, { useEffect, useState, useMemo } from 'react';
import {
  TrendingUp, TrendingDown, Filter, RotateCcw,
  Download, GitCompareArrows, ArrowLeft, Loader2,
  Calendar,
} from 'lucide-react';
import {
  LineChart, Line,
  BarChart, Bar,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { useAppContext } from '../../context/AppContext';
import { fetchLocationHistory, type HistoryGranularity, type LocationHistoryPoint } from '../../services/api';
import { classifySensorStatus } from '../../utils/telemetry';
import RealtimeLiveChart from './analytics/RealtimeLiveChart';
import {
  buildAnalyticsExcel,
  downloadWorkbook,
  type ExcelChartCapture,
} from './analytics/excelExport';

const ALL = '__ALL__';

// ─── Time range definitions ──────────────────────────────────────────────
type TimeRange = 'today' | 'week' | 'month' | 'year';

interface TimeRangeSpec {
  label: string;
  hours: number;
  granularity: HistoryGranularity;
  tickFormat: 'time' | 'day' | 'date' | 'month';
  description: string;
}

const TIME_RANGE_SPECS: Record<TimeRange, TimeRangeSpec> = {
  today: { label: 'Hôm nay', hours: 24,        granularity: 'HOURLY', tickFormat: 'time',  description: 'Mỗi điểm = 1 giờ' },
  week:  { label: 'Tuần',    hours: 24 * 7,    granularity: 'HOURLY', tickFormat: 'day',   description: 'Mỗi điểm = 1 giờ' },
  month: { label: 'Tháng',   hours: 24 * 30,   granularity: 'DAILY',  tickFormat: 'date',  description: 'Mỗi điểm = 1 ngày (trung bình 24 giờ)' },
  year:  { label: 'Năm',     hours: 24 * 365,  granularity: 'WEEKLY', tickFormat: 'month', description: 'Mỗi điểm = 1 tuần (trung bình 7 ngày, T2–CN)' },
};

type MetricKey = 'pm25' | 'temperature' | 'humidity' | 'co2' | 'noise';

interface MetricSpec {
  key: MetricKey;
  label: string;
  unit: string;
  color: string;
  digits: number;
}

const METRICS: MetricSpec[] = [
  { key: 'pm25',        label: 'PM2.5',    unit: 'µg/m³', color: '#3B82F6', digits: 1 },
  { key: 'temperature', label: 'Nhiệt độ', unit: '°C',    color: '#F97316', digits: 1 },
  { key: 'humidity',    label: 'Độ ẩm',    unit: '%',     color: '#06B6D4', digits: 0 },
  { key: 'co2',         label: 'CO₂',      unit: 'ppm',   color: '#8B5CF6', digits: 0 },
  { key: 'noise',       label: 'Tiếng ồn', unit: 'dB',    color: '#10B981', digits: 1 },
];

interface TrendPoint { t: number; time: string; value: number }
interface TrendBundle { range: TimeRange; data: Record<MetricKey, TrendPoint[]> }

const HISTORY_FIELD: Record<MetricKey, keyof LocationHistoryPoint> = {
  pm25:        'avgPM25',
  temperature: 'avgTemperature',
  humidity:    'avgHumidity',
  co2:         'avgCO2',
  noise:       'avgNoise',
};

interface CompareRow {
  locationId: string;
  locationName: string;
  pm25: number;
  noise: number;
  temperature: number;
  humidity: number;
  co2: number;
  aqi: number;
  cleanScore: number;
}

function formatBucketLabel(d: Date, fmt: 'time' | 'day' | 'date' | 'month'): string {
  if (fmt === 'time') {
    return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  }
  if (fmt === 'day') {
    return d.toLocaleDateString('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit' });
  }
  if (fmt === 'date') {
    return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
  }
  // 'month' = WEEKLY bucket — label is "Mon DD/MM → Sun DD/MM" so the user
  // immediately sees this point covers an entire week, not a single day.
  const start = d;
  const end = new Date(d.getTime() + 6 * 24 * 3600 * 1000);
  const fmtDay = (x: Date) => x.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
  return `${fmtDay(start)}–${fmtDay(end)}`;
}

// ════════════════════════════════════════════════════════════════════════
const AnalyticsView: React.FC = () => {
  const { sensors, alerts, telemetryMap, leaderboard, locations } = useAppContext();

  // ─── Filter state ───
  const [districtId, setDistrictId] = useState<string>(ALL);
  const [wardId, setWardId] = useState<string>(ALL);
  const [timeRange, setTimeRange] = useState<TimeRange>('today');
  const [compareMode, setCompareMode] = useState(false);
  const [compareDistrictIds, setCompareDistrictIds] = useState<string[]>([]);
  const [comparePreset, setComparePreset] = useState<TimeRange | 'custom'>('week');
  const [compareCustomStart, setCompareCustomStart] = useState<string>('');
  const [compareCustomEnd, setCompareCustomEnd] = useState<string>('');
  const [isExporting, setIsExporting] = useState(false);

  const districts = useMemo(() => locations.filter((l) => l.type === 'District'), [locations]);
  const wardsOfSelectedDistrict = useMemo(() => {
    if (districtId === ALL) return [];
    return locations.filter((l) => l.type === 'Ward' && l.parentId === districtId);
  }, [locations, districtId]);

  useEffect(() => { setWardId(ALL); }, [districtId]);

  useEffect(() => {
    if (compareMode && compareDistrictIds.length === 0 && districts.length > 0) {
      setCompareDistrictIds(districts.map((d) => d.locationId));
    }
  }, [compareMode, districts, compareDistrictIds.length]);

  // Default custom range = last 7 days
  useEffect(() => {
    if (comparePreset === 'custom' && (!compareCustomStart || !compareCustomEnd)) {
      const now = new Date();
      const week = new Date(now.getTime() - 7 * 24 * 3600 * 1000);
      const fmt = (d: Date) => d.toISOString().slice(0, 10);
      if (!compareCustomStart) setCompareCustomStart(fmt(week));
      if (!compareCustomEnd) setCompareCustomEnd(fmt(now));
    }
  }, [comparePreset, compareCustomStart, compareCustomEnd]);

  // ─── Scope ──────────────────────────────────────────────
  const scopedWardIds = useMemo(() => {
    if (wardId !== ALL) return new Set([wardId]);
    if (districtId !== ALL) {
      return new Set(
        locations.filter((l) => l.type === 'Ward' && l.parentId === districtId)
          .map((l) => l.locationId),
      );
    }
    return null;
  }, [districtId, wardId, locations]);

  const filteredSensors = useMemo(() => {
    if (!scopedWardIds) return sensors;
    return sensors.filter((s) => scopedWardIds.has(s.locationId));
  }, [sensors, scopedWardIds]);

  const filteredAlerts = useMemo(() => {
    if (!scopedWardIds && districtId === ALL) return alerts;
    const sensorIds = new Set(filteredSensors.map((s) => s.sensorId));
    const locationIds = new Set<string>();
    if (wardId !== ALL) locationIds.add(wardId);
    if (districtId !== ALL) {
      locationIds.add(districtId);
      locations.filter((l) => l.type === 'Ward' && l.parentId === districtId)
        .forEach((l) => locationIds.add(l.locationId));
    }
    return alerts.filter(
      (a) =>
        (a.sensorId && sensorIds.has(a.sensorId)) ||
        (a.locationId && locationIds.has(a.locationId)),
    );
  }, [alerts, filteredSensors, locations, districtId, wardId, scopedWardIds]);

  // ─── Historical trend — pulled from Oracle TELEMETRY_SUMMARY via the
  //     /api/locations/{id}/history endpoint. Real aggregated data, not mock.
  const [trend, setTrend] = useState<TrendBundle | null>(null);
  const [trendLoading, setTrendLoading] = useState(false);

  // Resolve the scope to a single Oracle LocationID.
  const scopeLocationId = useMemo(() => {
    if (wardId !== ALL) return wardId;
    if (districtId !== ALL) return districtId;
    return 'city_hcmc';
  }, [districtId, wardId]);

  useEffect(() => {
    let cancelled = false;
    const loadTrends = async () => {
      setTrendLoading(true);
      try {
        const spec = TIME_RANGE_SPECS[timeRange];
        const endTime = new Date();
        const startTime = new Date(endTime.getTime() - spec.hours * 3600 * 1000);

        const rows = await fetchLocationHistory(scopeLocationId, {
          granularity: spec.granularity,
          startTime: startTime.toISOString(),
          endTime: endTime.toISOString(),
        });
        if (cancelled) return;

        const data: Record<MetricKey, TrendPoint[]> = {
          pm25: [], temperature: [], humidity: [], co2: [], noise: [],
        };
        for (const row of rows) {
          if (!row.timeBucket) continue;
          const ts = new Date(row.timeBucket).getTime();
          const label = formatBucketLabel(new Date(ts), spec.tickFormat);
          for (const m of METRICS) {
            const v = row[HISTORY_FIELD[m.key]] as number | null | undefined;
            if (v === null || v === undefined) continue;
            data[m.key].push({ t: ts, time: label, value: v });
          }
        }
        setTrend({ range: timeRange, data });
      } catch (e) {
        console.error('Trend load failed:', e);
        if (!cancelled) setTrend(null);
      } finally {
        if (!cancelled) setTrendLoading(false);
      }
    };
    loadTrends();
    return () => { cancelled = true; };
  }, [scopeLocationId, timeRange]);

  // ─── Realtime averages ─────────────────────────────────
  const averages = useMemo(() => {
    const liveTelemetry = filteredSensors
      .map((s) => telemetryMap[s.sensorId])
      .filter((t): t is NonNullable<typeof t> => t !== undefined);

    const avg = (vals: Array<number | undefined | null>): number => {
      const nums = vals
        .map((v) => (v === undefined || v === null ? null : Number(v)))
        .filter((v): v is number => v !== null && !isNaN(v));
      if (nums.length === 0) return 0;
      return nums.reduce((a, b) => a + b, 0) / nums.length;
    };

    return {
      pm25: avg(liveTelemetry.map((t) => t.pm25 ?? t.data?.pm25)),
      temp: avg(liveTelemetry.map((t) => t.temperature ?? t.data?.temperature)),
      humidity: avg(liveTelemetry.map((t) => t.humidity ?? t.data?.humidity)),
      noise: avg(liveTelemetry.map((t) => t.noise ?? t.data?.noise)),
      co2: avg(liveTelemetry.map((t) => t.co2 ?? t.data?.co2)),
      aqi: avg(liveTelemetry.map((t) => t.aqi)),
      liveCount: liveTelemetry.length,
    };
  }, [filteredSensors, telemetryMap]);

  const aqiCategory =
    averages.aqi > 150 ? 'Không lành mạnh'
    : averages.aqi > 100 ? 'Không lành mạnh cho nhóm nhạy cảm'
    : averages.aqi > 50 ? 'Trung bình'
    : 'Tốt';

  const statusDistribution = useMemo(() => {
    let normal = 0; let warning = 0; let critical = 0;
    filteredSensors.forEach((s) => {
      const t = telemetryMap[s.sensorId];
      if (!t) return;
      const pm25 = t.pm25 ?? t.data?.pm25 ?? null;
      const co2 = t.co2 ?? t.data?.co2 ?? null;
      const status = classifySensorStatus(pm25, co2);
      if (status === 'critical') critical += 1;
      else if (status === 'warning') warning += 1;
      else normal += 1;
    });
    return [
      { name: 'Bình thường', value: normal, color: '#10B981' },
      { name: 'Cảnh báo', value: warning, color: '#F59E0B' },
      { name: 'Nghiêm trọng', value: critical, color: '#EF4444' },
    ];
  }, [filteredSensors, telemetryMap]);

  const criticalAlerts    = filteredAlerts.filter((a) => a.severity === 'CRITICAL').length;
  const highAlerts        = filteredAlerts.filter((a) => a.severity === 'HIGH').length;
  const mediumAlerts      = filteredAlerts.filter((a) => a.severity === 'MEDIUM').length;
  const lowAlerts         = filteredAlerts.filter((a) => a.severity === 'LOW').length;
  const acknowledgedAlerts = filteredAlerts.filter((a) => a.status === 'ACKNOWLEDGED').length;
  const resolvedAlerts    = filteredAlerts.filter((a) => a.status === 'RESOLVED').length;

  // ─── Compare-mode history per district (Oracle TELEMETRY_SUMMARY) ───
  // Each selected district fetches its own history rows for the chosen range.
  // The trend chart, the comparison table and the bar chart are all derived
  // from the same dataset so changing the date range updates EVERYTHING.
  const [compareHistory, setCompareHistory] = useState<Record<string, LocationHistoryPoint[]>>({});
  const [compareTrendLoading, setCompareTrendLoading] = useState(false);

  // Resolve the active range for compare mode.
  const compareRange = useMemo(() => {
    if (comparePreset === 'custom' && compareCustomStart && compareCustomEnd) {
      const startTime = new Date(`${compareCustomStart}T00:00:00`);
      const endTime   = new Date(`${compareCustomEnd}T23:59:59`);
      const days = (endTime.getTime() - startTime.getTime()) / (24 * 3600 * 1000);
      const granularity: HistoryGranularity =
        days <= 2 ? 'HOURLY' : days <= 60 ? 'DAILY' : 'WEEKLY';
      const tickFormat: 'time' | 'day' | 'date' | 'month' =
        days <= 2 ? 'time' : days <= 14 ? 'day' : days <= 60 ? 'date' : 'month';
      return { startTime, endTime, granularity, tickFormat, label: `${compareCustomStart} → ${compareCustomEnd}` };
    }
    const presetSpec = TIME_RANGE_SPECS[comparePreset as TimeRange] ?? TIME_RANGE_SPECS.week;
    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - presetSpec.hours * 3600 * 1000);
    return {
      startTime, endTime,
      granularity: presetSpec.granularity,
      tickFormat: presetSpec.tickFormat,
      label: presetSpec.label,
    };
  }, [comparePreset, compareCustomStart, compareCustomEnd]);

  useEffect(() => {
    if (!compareMode) return;
    let cancelled = false;
    const loadCompareHistory = async () => {
      if (compareDistrictIds.length === 0) {
        setCompareHistory({});
        return;
      }
      setCompareTrendLoading(true);
      try {
        const result: Record<string, LocationHistoryPoint[]> = {};
        await Promise.all(
          compareDistrictIds.map(async (id) => {
            try {
              const rows = await fetchLocationHistory(id, {
                granularity: compareRange.granularity,
                startTime: compareRange.startTime.toISOString(),
                endTime: compareRange.endTime.toISOString(),
              });
              result[id] = rows;
            } catch {
              result[id] = [];
            }
          }),
        );
        if (!cancelled) setCompareHistory(result);
      } catch (e) {
        console.error('Compare history load failed:', e);
      } finally {
        if (!cancelled) setCompareTrendLoading(false);
      }
    };
    loadCompareHistory();
    return () => { cancelled = true; };
  }, [compareMode, compareDistrictIds, compareRange]);

  // ─── Period-averaged compare rows ───
  // Average each metric over all buckets within the selected date range.
  // When the user switches preset/custom dates, this re-derives → table +
  // bar chart automatically reflect the new period.
  const compareRows = useMemo<CompareRow[]>(() => {
    return compareDistrictIds
      .map((id) => {
        const node = locations.find((l) => l.locationId === id);
        if (!node) return null;
        const rows = compareHistory[id] ?? [];

        const avgOf = (field: keyof LocationHistoryPoint): number => {
          const nums = rows
            .map((r) => r[field] as number | null | undefined)
            .filter((v): v is number => typeof v === 'number' && !isNaN(v));
          if (nums.length === 0) return 0;
          return nums.reduce((a, b) => a + b, 0) / nums.length;
        };

        // Fall back to leaderboard snapshot if the history is empty.
        if (rows.length === 0) {
          const entry = leaderboard.find((l) => l.locationId === id);
          if (!entry) return null;
          return {
            locationId: id,
            locationName: node.name,
            pm25:        entry.avgPM25 ?? 0,
            noise:       entry.avgNoise ?? 0,
            temperature: entry.avgTemperature ?? 0,
            humidity:    entry.avgHumidity ?? 0,
            co2:         entry.avgCO2 ?? 0,
            aqi:         entry.aqi ?? 0,
            cleanScore:  entry.cleanScore ?? 0,
          };
        }

        return {
          locationId: id,
          locationName: node.name,
          pm25:        avgOf('avgPM25'),
          noise:       avgOf('avgNoise'),
          temperature: avgOf('avgTemperature'),
          humidity:    avgOf('avgHumidity'),
          co2:         avgOf('avgCO2'),
          aqi:         avgOf('aqi'),
          cleanScore:  avgOf('cleanScore'),
        };
      })
      .filter((r): r is CompareRow => r !== null);
  }, [compareDistrictIds, compareHistory, leaderboard, locations]);

  // Combine per-district history into the chart-friendly array
  // (one row per timestamp, one column per district).
  const compareTrendChartData = useMemo(() => {
    const allTimestamps = new Set<number>();
    const lookups: Record<string, Map<number, number>> = {};
    for (const id of compareDistrictIds) {
      const rows = compareHistory[id] ?? [];
      const map = new Map<number, number>();
      for (const r of rows) {
        if (!r.timeBucket || r.avgPM25 === null || r.avgPM25 === undefined) continue;
        const t = new Date(r.timeBucket).getTime();
        map.set(t, r.avgPM25);
        allTimestamps.add(t);
      }
      lookups[id] = map;
    }
    const sorted = Array.from(allTimestamps).sort((a, b) => a - b);
    return sorted.map((ts) => {
      const row: Record<string, string | number> = {
        label: formatBucketLabel(new Date(ts), compareRange.tickFormat),
      };
      for (const id of compareDistrictIds) {
        const node = locations.find((l) => l.locationId === id);
        const v = lookups[id].get(ts);
        if (v !== undefined) row[node?.name ?? id] = +v.toFixed(1);
      }
      return row;
    });
  }, [compareHistory, compareDistrictIds, compareRange, locations]);

  const scopeLabel = useMemo(() => {
    if (wardId !== ALL) {
      const w = locations.find((l) => l.locationId === wardId);
      const d = locations.find((l) => l.locationId === districtId);
      return `${d?.name ?? ''} › ${w?.name ?? ''}`;
    }
    if (districtId !== ALL) {
      const d = locations.find((l) => l.locationId === districtId);
      return d?.name ?? 'Quận đã chọn';
    }
    return 'Toàn thành phố';
  }, [districtId, wardId, locations]);

  const isFiltered = districtId !== ALL || wardId !== ALL;

  // ════════════════════════════════════════════════════════
  // EXCEL EXPORT
  // ════════════════════════════════════════════════════════
  const exportToExcel = async () => {
    setIsExporting(true);
    try {
      const stamp = new Date();
      const stampStr = stamp.toLocaleString('vi-VN');
      const dateStr = stamp.toISOString().slice(0, 10);

      if (compareMode) {
        // Compare export — summary table + chart.
        const cmpSummary = [
          { label: 'Loại báo cáo',     value: 'So sánh khu vực' },
          { label: 'Khoảng thời gian', value: comparePreset === 'custom'
              ? `${compareCustomStart} → ${compareCustomEnd}`
              : TIME_RANGE_SPECS[comparePreset as TimeRange]?.label ?? '—' },
          { label: 'Số quận so sánh',  value: compareRows.length },
          { label: 'Quận đã chọn',     value: compareRows.map((r) => r.locationName).join(', ') },
          { label: 'Ngày xuất',        value: stampStr },
        ];
        // Inline metric table as additional summary rows.
        const metricNames = [
          ['PM2.5 (µg/m³)',    'pm25',         1],
          ['Tiếng ồn (dB)',    'noise',        1],
          ['CO₂ (ppm)',        'co2',          0],
          ['Nhiệt độ (°C)',    'temperature',  1],
          ['Độ ẩm (%)',        'humidity',     0],
          ['AQI',              'aqi',          0],
          ['Clean Score',      'cleanScore',   0],
        ] as const;
        for (const [label, key, digits] of metricNames) {
          for (const r of compareRows) {
            cmpSummary.push({
              label: `${label} — ${r.locationName}`,
              value: +(r[key as keyof CompareRow] as number).toFixed(digits as number),
            });
          }
        }

        const charts: ExcelChartCapture[] = [];
        const trendEl = document.getElementById('compare-trend-chart');
        if (trendEl) charts.push({ sheetName: 'BĐ Xu Hướng', element: trendEl, title: 'Xu hướng PM2.5 — So sánh giữa các quận' });
        const tableEl = document.getElementById('compare-table-chart');
        if (tableEl) charts.push({ sheetName: 'BĐ So Sánh', element: tableEl, title: 'Biểu đồ so sánh hiện tại' });

        const wb = await buildAnalyticsExcel({
          title: 'Báo cáo So Sánh Khu Vực',
          subtitle: `Khoảng thời gian: ${comparePreset === 'custom'
            ? `${compareCustomStart} → ${compareCustomEnd}`
            : TIME_RANGE_SPECS[comparePreset as TimeRange]?.label ?? '—'} · Xuất ${stampStr}`,
          scopeLabel: 'So sánh',
          timeRangeLabel: comparePreset === 'custom' ? 'Tùy chỉnh' : (TIME_RANGE_SPECS[comparePreset as TimeRange]?.label ?? ''),
          summary: cmpSummary,
          trend: compareTrendChartData.map((row) => {
            const out: Record<string, string | number | undefined> = { time: String(row.label) };
            // Re-shape: store first district as pm25 for compatibility (other columns blank).
            const firstId = compareDistrictIds[0];
            const node = firstId ? locations.find((l) => l.locationId === firstId) : null;
            if (node) {
              out.pm25 = typeof row[node.name] === 'number' ? (row[node.name] as number) : undefined;
            }
            return out as { time: string; pm25?: number };
          }),
          charts,
        });
        await downloadWorkbook(wb, `phan-tich-so-sanh-${dateStr}.xlsx`);
      } else {
        // Standard analytics export — only data shown on this page.
        const summary = [
          { label: 'Phạm vi',                   value: scopeLabel },
          { label: 'Cảm biến trực tuyến',       value: `${averages.liveCount} / ${filteredSensors.length}` },
          { label: 'TB PM2.5 (µg/m³)',          value: +averages.pm25.toFixed(1) },
          { label: 'TB Nhiệt độ (°C)',          value: +averages.temp.toFixed(1) },
          { label: 'TB Độ ẩm (%)',              value: Math.round(averages.humidity) },
          { label: 'TB CO₂ (ppm)',              value: Math.round(averages.co2) },
          { label: 'TB Tiếng ồn (dB)',          value: +averages.noise.toFixed(1) },
          { label: 'AQI hiện tại',              value: Math.round(averages.aqi) },
          { label: 'Phân loại AQI',             value: aqiCategory },
          { label: 'Cảnh báo trong phạm vi',    value: filteredAlerts.length },
          { label: 'Khoảng thời gian xu hướng', value: TIME_RANGE_SPECS[timeRange].label },
          { label: 'Ngày xuất',                 value: stampStr },
        ];

        // Trend rows (combined across metrics, by timestamp).
        const allTs = new Set<number>();
        if (trend) {
          for (const m of METRICS) for (const p of trend.data[m.key]) allTs.add(p.t);
        }
        const sorted = Array.from(allTs).sort((a, b) => a - b);
        const lookup: Record<MetricKey, Map<number, number>> = {} as Record<MetricKey, Map<number, number>>;
        if (trend) {
          for (const m of METRICS) {
            lookup[m.key] = new Map(trend.data[m.key].map((p) => [p.t, p.value]));
          }
        }
        const trendRows = sorted.map((ts) => ({
          time: new Date(ts).toLocaleString('vi-VN'),
          pm25:        lookup.pm25?.get(ts),
          temperature: lookup.temperature?.get(ts),
          humidity:    lookup.humidity?.get(ts),
          co2:         lookup.co2?.get(ts),
          noise:       lookup.noise?.get(ts),
        }));

        // Capture every chart-card on the analytics page so the workbook
        // mirrors what's on screen.
        const charts: ExcelChartCapture[] = [];
        const live = document.getElementById('realtime-live-chart');
        if (live) charts.push({ sheetName: 'BĐ Trực Tiếp', element: live, title: 'Trực tiếp — 15 phút gần nhất' });
        for (const m of METRICS) {
          const el = document.getElementById(`trend-chart-${m.key}`);
          if (el) charts.push({ sheetName: `BĐ ${m.label}`, element: el, title: `${m.label} — ${TIME_RANGE_SPECS[timeRange].label}` });
        }

        const wb = await buildAnalyticsExcel({
          title: 'Báo cáo Phân Tích Môi Trường',
          subtitle: `${scopeLabel} · ${TIME_RANGE_SPECS[timeRange].label} · Xuất ${stampStr}`,
          scopeLabel,
          timeRangeLabel: TIME_RANGE_SPECS[timeRange].label,
          summary,
          trend: trendRows,
          charts,
        });

        const slug = scopeLabel.replace(/[^A-Za-zÀ-ỹ0-9]+/g, '-').toLowerCase();
        await downloadWorkbook(wb, `phan-tich-${slug}-${dateStr}.xlsx`);
      }
    } catch (err) {
      console.error('Excel export failed:', err);
    } finally {
      setIsExporting(false);
    }
  };

  const toggleCompareDistrict = (id: string) => {
    setCompareDistrictIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  // ════════════════════════════════════════════════════════
  // COMPARISON VIEW
  // ════════════════════════════════════════════════════════
  if (compareMode) {
    const compareChartData = compareRows.map((r) => ({
      name: r.locationName,
      'PM2.5 (µg/m³)': Number(r.pm25.toFixed(1)),
      'Tiếng ồn (dB)': Number(r.noise.toFixed(1)),
      'AQI': Math.round(r.aqi),
    }));

    const compareSeriesColors = ['#3B82F6', '#F97316', '#06B6D4', '#10B981', '#EF4444', '#8B5CF6'];
    const rangeLabel = compareRange.label;

    return (
      <div className="analytics-view">
        <div className="view-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button className="filter-reset-btn" onClick={() => setCompareMode(false)} style={{ padding: '8px 14px' }}>
              <ArrowLeft className="w-4 h-4" />
              <span>Quay Lại</span>
            </button>
            <div>
              <h1 className="view-title">So Sánh Khu Vực</h1>
              <p className="view-subtitle">So sánh chỉ số môi trường giữa các quận theo khoảng thời gian</p>
            </div>
          </div>
          <div className="analytics-toolbar">
            <button className="toolbar-btn primary" onClick={exportToExcel} disabled={isExporting || compareRows.length === 0}>
              {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              <span>{isExporting ? 'Đang xuất…' : 'Xuất Excel'}</span>
            </button>
          </div>
        </div>

        <div className="compare-export-root">
          <div className="compare-selector">
            <span className="compare-selector-label">Chọn quận để so sánh:</span>
            <div className="compare-chip-row">
              {districts.map((d) => {
                const checked = compareDistrictIds.includes(d.locationId);
                return (
                  <button
                    key={d.locationId}
                    className={`compare-chip ${checked ? 'active' : ''}`}
                    onClick={() => toggleCompareDistrict(d.locationId)}
                  >
                    <span className="compare-chip-check">{checked ? '✓' : ''}</span>
                    <span>{d.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="compare-selector">
            <span className="compare-selector-label">Khoảng thời gian:</span>
            <div className="compare-chip-row">
              {(['today', 'week', 'month', 'year'] as TimeRange[]).map((r) => (
                <button
                  key={r}
                  className={`compare-chip ${comparePreset === r ? 'active' : ''}`}
                  onClick={() => setComparePreset(r)}
                >
                  <Calendar className="w-4 h-4" /> {TIME_RANGE_SPECS[r].label}
                </button>
              ))}
              <button
                className={`compare-chip ${comparePreset === 'custom' ? 'active' : ''}`}
                onClick={() => setComparePreset('custom')}
              >
                <Calendar className="w-4 h-4" /> Tùy chỉnh
              </button>
              {comparePreset === 'custom' && (
                <div className="compare-date-inputs">
                  <input
                    type="date"
                    className="compare-date-input"
                    value={compareCustomStart}
                    max={compareCustomEnd || undefined}
                    onChange={(e) => setCompareCustomStart(e.target.value)}
                  />
                  <span className="compare-date-arrow">→</span>
                  <input
                    type="date"
                    className="compare-date-input"
                    value={compareCustomEnd}
                    min={compareCustomStart || undefined}
                    onChange={(e) => setCompareCustomEnd(e.target.value)}
                  />
                </div>
              )}
            </div>
          </div>

          {compareRows.length === 0 ? (
            <div className="compare-empty"><p>Vui lòng chọn ít nhất một quận để so sánh.</p></div>
          ) : (
            <>
              {/* Trend chart — multi-line, one per district */}
              <div id="compare-trend-chart" className="chart-card full-width" style={{ marginTop: 'var(--spacing-lg)' }}>
                <div className="card-header">
                  <h3 className="card-title">Xu Hướng PM2.5 Theo Khoảng Thời Gian</h3>
                  <p className="card-subtitle">
                    {rangeLabel} · {compareRows.length} quận
                    {compareTrendLoading ? ' · đang tải…' : ''}
                  </p>
                </div>
                <ResponsiveContainer width="100%" height={340}>
                  <LineChart data={compareTrendChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="label" stroke="#9CA3AF" fontSize={11} minTickGap={28} />
                    <YAxis stroke="#9CA3AF" fontSize={11} unit=" µg/m³" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 8 }} />
                    <Legend />
                    {compareRows.map((r, idx) => (
                      <Line
                        key={r.locationId}
                        type="monotone"
                        dataKey={r.locationName}
                        stroke={compareSeriesColors[idx % compareSeriesColors.length]}
                        strokeWidth={2.5}
                        dot={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Period-averaged comparison table */}
              <div className="chart-card full-width">
                <div className="card-header">
                  <h3 className="card-title">Bảng So Sánh — {rangeLabel}</h3>
                  <p className="card-subtitle">
                    Trung bình {compareRows.length} quận trong khoảng thời gian đã chọn
                    {compareTrendLoading ? ' · đang tải…' : ''}
                  </p>
                </div>
                <div className="compare-table-wrap">
                  <table className="compare-table">
                    <thead>
                      <tr>
                        <th>Chỉ số</th>
                        {compareRows.map((r) => (<th key={r.locationId}>{r.locationName}</th>))}
                      </tr>
                    </thead>
                    <tbody>
                      <CompareRowDisplay label="PM2.5 (µg/m³)" rows={compareRows} pick={(r) => r.pm25} digits={1} better="low"  warnAt={50}  critAt={100} />
                      <CompareRowDisplay label="Tiếng ồn (dB)" rows={compareRows} pick={(r) => r.noise} digits={1} better="low"  warnAt={70}  critAt={85} />
                      <CompareRowDisplay label="CO₂ (ppm)"    rows={compareRows} pick={(r) => r.co2}   digits={0} better="low"  warnAt={1000} critAt={1500} />
                      <CompareRowDisplay label="Nhiệt độ (°C)" rows={compareRows} pick={(r) => r.temperature} digits={1} better="band" lowEdge={22} highEdge={32} />
                      <CompareRowDisplay label="Độ ẩm (%)"    rows={compareRows} pick={(r) => r.humidity}    digits={0} better="band" lowEdge={45} highEdge={65} />
                      <CompareRowDisplay label="AQI"           rows={compareRows} pick={(r) => r.aqi}        digits={0} better="low"  warnAt={100} critAt={150} highlight />
                      <CompareRowDisplay label="Clean Score"   rows={compareRows} pick={(r) => r.cleanScore} digits={0} better="high" warnAt={60}  critAt={40} highlight />
                    </tbody>
                  </table>
                </div>
              </div>

              <div id="compare-table-chart" className="chart-card full-width">
                <div className="card-header">
                  <h3 className="card-title">Biểu Đồ Tóm Tắt — {rangeLabel}</h3>
                  <p className="card-subtitle">PM2.5, Tiếng ồn và AQI trung bình theo khoảng thời gian</p>
                </div>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={compareChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="name" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 8 }} />
                    <Legend />
                    <Bar dataKey="PM2.5 (µg/m³)" fill="#3B82F6" />
                    <Bar dataKey="Tiếng ồn (dB)" fill="#10B981" />
                    <Bar dataKey="AQI" fill="#F59E0B" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  // ════════════════════════════════════════════════════════
  // NORMAL ANALYTICS VIEW
  // ════════════════════════════════════════════════════════
  return (
    <div className="analytics-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Phân Tích</h1>
          <p className="view-subtitle">
            Đang hiển thị: <strong>{scopeLabel}</strong> — {averages.liveCount}/
            {filteredSensors.length} cảm biến đang trực tuyến
          </p>
        </div>
        <div className="analytics-toolbar">
          <button className="toolbar-btn" onClick={exportToExcel} disabled={isExporting}>
            {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            <span>{isExporting ? 'Đang xuất…' : 'Xuất Excel'}</span>
          </button>
          <button className="toolbar-btn primary" onClick={() => setCompareMode(true)}>
            <GitCompareArrows className="w-4 h-4" />
            <span>So Sánh</span>
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="analytics-filter-bar">
        <div className="filter-group">
          <Filter className="filter-icon" />
          <label className="filter-label">Quận</label>
          <select className="filter-select" value={districtId} onChange={(e) => setDistrictId(e.target.value)}>
            <option value={ALL}>Tất cả quận</option>
            {districts.map((d) => (
              <option key={d.locationId} value={d.locationId}>{d.name}</option>
            ))}
          </select>
        </div>
        <div className="filter-group">
          <label className="filter-label">Phường</label>
          <select className="filter-select" value={wardId} onChange={(e) => setWardId(e.target.value)} disabled={districtId === ALL}>
            <option value={ALL}>{districtId === ALL ? 'Chọn quận trước' : 'Tất cả phường'}</option>
            {wardsOfSelectedDistrict.map((w) => (
              <option key={w.locationId} value={w.locationId}>{w.name}</option>
            ))}
          </select>
        </div>
        {isFiltered && (
          <button className="filter-reset-btn" onClick={() => { setDistrictId(ALL); setWardId(ALL); }} title="Đặt lại bộ lọc">
            <RotateCcw className="w-4 h-4" />
            <span>Đặt lại</span>
          </button>
        )}
        <div className="filter-summary">
          <span className="filter-summary-label">Phạm vi:</span>
          <span className="filter-summary-value">{scopeLabel}</span>
        </div>
      </div>

      {/* ════ HIỆN TẠI ════ */}
      <div className="analytics-section-header">
        <div>
          <span className="analytics-section-title">Hiện Tại</span>
          <span className="analytics-section-subtitle">
            Trung bình các cảm biến trong phạm vi · cập nhật trực tiếp qua WebSocket
          </span>
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-box">
          <span className="stat-label">TB PM2.5</span>
          <div className="stat-value-row">
            <span className={`stat-number ${averages.pm25 > 50 ? 'text-red-400' : 'text-green-400'}`}>
              {averages.pm25.toFixed(1)} <span className="stat-unit">µg/m³</span>
            </span>
            <div className={`stat-change ${averages.pm25 > 50 ? 'negative' : 'positive'}`}>
              {averages.pm25 > 50 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span>Real-time</span>
            </div>
          </div>
        </div>
        <div className="stat-box">
          <span className="stat-label">TB Nhiệt Độ</span>
          <div className="stat-value-row">
            <span className="stat-number text-blue-400">{averages.temp.toFixed(1)} <span className="stat-unit">°C</span></span>
            <div className="stat-change positive"><TrendingDown className="w-4 h-4" /><span>Real-time</span></div>
          </div>
        </div>
        <div className="stat-box">
          <span className="stat-label">TB Độ Ẩm</span>
          <div className="stat-value-row">
            <span className="stat-number text-cyan-400">{averages.humidity.toFixed(0)} <span className="stat-unit">%</span></span>
            <div className="stat-change negative"><TrendingUp className="w-4 h-4" /><span>Real-time</span></div>
          </div>
        </div>
        <div className="stat-box">
          <span className="stat-label">TB Tiếng Ồn</span>
          <div className="stat-value-row">
            <span className="stat-number text-purple-400">{averages.noise.toFixed(0)} <span className="stat-unit">dB</span></span>
            <div className="stat-change negative"><TrendingUp className="w-4 h-4" /><span>Real-time</span></div>
          </div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <div className="card-header">
            <h3 className="card-title">Chỉ Số Chất Lượng Không Khí</h3>
            <p className="card-subtitle">AQI hiện tại — {scopeLabel}</p>
          </div>
          <div className="aqi-display">
            <div className={`aqi-value ${averages.aqi > 150 ? 'text-red-400' : averages.aqi > 100 ? 'text-orange-400' : 'text-green-400'}`}>
              {averages.aqi.toFixed(0)}
            </div>
            <div className={`aqi-label ${averages.aqi > 150 ? 'text-red-400' : averages.aqi > 100 ? 'text-orange-400' : 'text-green-400'}`}>
              {aqiCategory}
            </div>
            <div className="aqi-scale">
              <div className="aqi-scale-item"><div className="aqi-scale-bar bg-green-500"></div><span>Tốt</span></div>
              <div className="aqi-scale-item"><div className="aqi-scale-bar bg-yellow-500"></div><span>Trung bình</span></div>
              <div className="aqi-scale-item active"><div className="aqi-scale-bar bg-red-500"></div><span>Không lành mạnh</span></div>
            </div>
          </div>
        </div>

        <div className="chart-card">
          <div className="card-header">
            <h3 className="card-title">Trạng Thái Cảm Biến</h3>
            <p className="card-subtitle">Phân bố theo tình trạng (real-time)</p>
          </div>
          <div className="pie-chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={statusDistribution} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={5} dataKey="value">
                  {statusDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <div className="card-header">
            <h3 className="card-title">Hoạt Động Cảnh Báo</h3>
            <p className="card-subtitle">{filteredAlerts.length} cảnh báo trong phạm vi</p>
          </div>
          <div className="alert-stats">
            <div className="alert-stat-item"><span className="alert-stat-label">Tổng Cảnh Báo</span><span className="alert-stat-value">{filteredAlerts.length}</span></div>
            <div className="alert-stat-item"><span className="alert-stat-label">Nghiêm Trọng</span><span className="alert-stat-value text-red-400">{criticalAlerts}</span></div>
            <div className="alert-stat-item"><span className="alert-stat-label">Cao</span><span className="alert-stat-value text-orange-400">{highAlerts}</span></div>
            <div className="alert-stat-item"><span className="alert-stat-label">Trung Bình</span><span className="alert-stat-value text-yellow-400">{mediumAlerts}</span></div>
            <div className="alert-stat-item"><span className="alert-stat-label">Thấp</span><span className="alert-stat-value text-green-400">{lowAlerts}</span></div>
            <div className="alert-stat-item"><span className="alert-stat-label">Đã Xác Nhận / Giải Quyết</span><span className="alert-stat-value">{acknowledgedAlerts} / {resolvedAlerts}</span></div>
          </div>
        </div>
      </div>

      {/* Realtime live rolling chart */}
      <div className="charts-grid" style={{ paddingTop: 0 }}>
        <RealtimeLiveChart sensors={filteredSensors} />
      </div>

      {/* ════ XU HƯỚNG LỊCH SỬ ════ */}
      <div className="analytics-section-header trend-header">
        <div>
          <span className="analytics-section-title">Xu Hướng Lịch Sử</span>
          <span className="analytics-section-subtitle">
            {TIME_RANGE_SPECS[timeRange].description}
            {trendLoading && ' · đang tải…'}
          </span>
        </div>
        <div className="time-range-pills">
          {(['today', 'week', 'month', 'year'] as TimeRange[]).map((r) => (
            <button
              key={r}
              className={`time-range-pill ${timeRange === r ? 'active' : ''}`}
              onClick={() => setTimeRange(r)}
            >
              {TIME_RANGE_SPECS[r].label}
            </button>
          ))}
        </div>
      </div>

      <div className="trend-grid">
        {METRICS.map((m) => {
          const points = trend?.data[m.key] ?? [];
          const last = points.length > 0 ? points[points.length - 1].value : null;
          const min = points.length > 0 ? Math.min(...points.map((p) => p.value)) : null;
          const max = points.length > 0 ? Math.max(...points.map((p) => p.value)) : null;
          return (
            <div key={m.key} id={`trend-chart-${m.key}`} className="chart-card trend-card">
              <div className="card-header">
                <h3 className="card-title">{m.label}</h3>
                <p className="card-subtitle">
                  {last !== null
                    ? `${TIME_RANGE_SPECS[timeRange].label}: ${last.toFixed(m.digits)} ${m.unit} · min ${min!.toFixed(m.digits)} · max ${max!.toFixed(m.digits)}`
                    : 'Không có dữ liệu'}
                </p>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={points} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9CA3AF" fontSize={11} interval="preserveStartEnd" minTickGap={28} />
                  <YAxis stroke="#9CA3AF" fontSize={11} width={48} tickFormatter={(v) => v.toFixed(m.digits === 0 ? 0 : 1)} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 8 }}
                    formatter={(value) => {
                      const n = typeof value === 'number' ? value : Number(value);
                      return [`${isNaN(n) ? '—' : n.toFixed(m.digits)} ${m.unit}`, m.label];
                    }}
                  />
                  <Line type="monotone" dataKey="value" stroke={m.color} strokeWidth={2.5} dot={false} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ─── Helper component for compare table rows ───
interface CompareRowDisplayProps {
  label: string;
  rows: CompareRow[];
  pick: (r: CompareRow) => number;
  digits: number;
  better: 'low' | 'high' | 'band';
  warnAt?: number;
  critAt?: number;
  lowEdge?: number;
  highEdge?: number;
  highlight?: boolean;
}

const CompareRowDisplay: React.FC<CompareRowDisplayProps> = ({
  label, rows, pick, digits, better, warnAt, critAt, lowEdge, highEdge, highlight,
}) => {
  const values = rows.map(pick);
  const best = better === 'low' ? Math.min(...values)
             : better === 'high' ? Math.max(...values)
             : null;

  const colorOf = (v: number): string => {
    if (better === 'low' && warnAt && critAt) {
      if (v >= critAt) return 'text-red-400';
      if (v >= warnAt) return 'text-yellow-400';
      return 'text-green-400';
    }
    if (better === 'high' && warnAt && critAt) {
      if (v <= critAt) return 'text-red-400';
      if (v <= warnAt) return 'text-yellow-400';
      return 'text-green-400';
    }
    if (better === 'band' && lowEdge !== undefined && highEdge !== undefined) {
      if (v < lowEdge || v > highEdge) return 'text-yellow-400';
      return 'text-green-400';
    }
    return '';
  };

  return (
    <tr className={highlight ? 'highlight-row' : undefined}>
      <td className="compare-row-label">{label}</td>
      {rows.map((r) => {
        const v = pick(r);
        const isBest = best !== null && v === best;
        return (
          <td key={r.locationId} className={`compare-cell ${colorOf(v)} ${isBest ? 'best' : ''}`}>
            {v.toFixed(digits)}
            {isBest && <span className="best-badge" title="Tốt nhất">★</span>}
          </td>
        );
      })}
    </tr>
  );
};

export default AnalyticsView;
