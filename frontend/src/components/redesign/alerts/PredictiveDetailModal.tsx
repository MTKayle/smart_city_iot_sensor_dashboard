import React, { useEffect, useMemo, useState } from 'react';
import {
  X,
  Activity,
  Clock,
  TrendingUp,
  ShieldAlert,
  Lightbulb,
  Loader2,
} from 'lucide-react';
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { fetchTelemetry } from '../../../services/api';
import type { Alert, Telemetry } from '../../../types';
import { formatLocationName } from '../../../utils/location';
import { useAppContext } from '../../../context/AppContext';

const HISTORY_HOURS = 6;     // pull last 6 hours so the chart has obvious slope
const HISTORY_LIMIT = 200;
const FORECAST_POINTS = 24;  // future points to plot — covers ~6h ahead at 15-min step
const FORECAST_STEP_MIN = 15;

interface Props {
  alert: Alert;
  onClose: () => void;
}

interface ChartPoint {
  t: number;
  /** ISO label for x-axis */
  label: string;
  /** Observed reading (null in the future) */
  actual?: number;
  /** Linear-regression value (defined for past + future) */
  fit?: number;
}

const METRIC_LABELS: Record<string, { label: string; unit: string }> = {
  CO2:         { label: 'CO₂',          unit: 'ppm'   },
  Noise:       { label: 'Tiếng ồn',     unit: 'dB'    },
  Temperature: { label: 'Nhiệt độ',     unit: '°C'    },
  PM25:        { label: 'PM2.5',        unit: 'µg/m³' },
  'PM2.5':     { label: 'PM2.5',        unit: 'µg/m³' },
  Humidity:    { label: 'Độ ẩm',        unit: '%'     },
};

function pickValue(metric: string, t: Telemetry): number | null {
  const key = metric.toLowerCase().replace('.', '');
  const map: Record<string, number | null | undefined> = {
    co2:         t.co2 ?? t.data?.co2 ?? null,
    noise:       t.noise ?? t.data?.noise ?? null,
    temperature: t.temperature ?? t.data?.temperature ?? null,
    pm25:        t.pm25 ?? t.data?.pm25 ?? null,
    humidity:    t.humidity ?? t.data?.humidity ?? null,
  };
  const v = map[key];
  if (v === undefined || v === null || isNaN(v as number)) return null;
  return v as number;
}

/** Simple linear regression on (x, y). Returns slope, intercept, R². */
function linearRegression(xs: number[], ys: number[]): { slope: number; intercept: number; r2: number } {
  const n = xs.length;
  if (n < 2) return { slope: 0, intercept: ys[0] ?? 0, r2: 0 };
  const meanX = xs.reduce((a, b) => a + b, 0) / n;
  const meanY = ys.reduce((a, b) => a + b, 0) / n;
  let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < n; i++) {
    const dx = xs[i] - meanX;
    const dy = ys[i] - meanY;
    sxy += dx * dy;
    sxx += dx * dx;
    syy += dy * dy;
  }
  const slope = sxx === 0 ? 0 : sxy / sxx;
  const intercept = meanY - slope * meanX;
  // R² = 1 - SSres/SStot where SSres = Σ(y - ŷ)²
  let ssRes = 0;
  for (let i = 0; i < n; i++) {
    const yhat = slope * xs[i] + intercept;
    ssRes += (ys[i] - yhat) ** 2;
  }
  const r2 = syy === 0 ? 1 : Math.max(0, 1 - ssRes / syy);
  return { slope, intercept, r2 };
}

const PredictiveDetailModal: React.FC<Props> = ({ alert, onClose }) => {
  const { locations } = useAppContext();
  const [points, setPoints] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<{ slope: number; intercept: number; r2: number; firstT: number } | null>(null);

  const metricInfo = METRIC_LABELS[alert.metricType] ?? { label: alert.metricType, unit: '' };
  const threshold = alert.threshold ?? 0;
  const sensorId = alert.sensorId ?? '';

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!sensorId) {
        setPoints([]);
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const endTime = new Date();
        const startTime = new Date(endTime.getTime() - HISTORY_HOURS * 3600 * 1000);
        const docs = await fetchTelemetry(sensorId, {
          startTime: startTime.toISOString(),
          endTime: endTime.toISOString(),
          limit: HISTORY_LIMIT,
        });
        if (cancelled) return;

        // Build (t, value) pairs sorted by time.
        const pairs: Array<{ t: number; v: number }> = [];
        for (const d of docs) {
          const ts = new Date(d.timestamp).getTime();
          const v = pickValue(alert.metricType, d);
          if (v !== null) pairs.push({ t: ts, v });
        }
        pairs.sort((a, b) => a.t - b.t);

        if (pairs.length < 2) {
          setPoints([]);
          setStats(null);
          setLoading(false);
          return;
        }

        const firstT = pairs[0].t;
        const lastT = pairs[pairs.length - 1].t;
        const xs = pairs.map((p) => (p.t - firstT) / 1000); // seconds since first reading
        const ys = pairs.map((p) => p.v);
        const reg = linearRegression(xs, ys);

        // Build chart points: history (with fit) + future projection.
        const out: ChartPoint[] = pairs.map((p) => {
          const x = (p.t - firstT) / 1000;
          return {
            t: p.t,
            label: new Date(p.t).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
            actual: p.v,
            fit: reg.slope * x + reg.intercept,
          };
        });
        for (let i = 1; i <= FORECAST_POINTS; i++) {
          const t = lastT + i * FORECAST_STEP_MIN * 60 * 1000;
          const x = (t - firstT) / 1000;
          out.push({
            t,
            label: new Date(t).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
            fit: reg.slope * x + reg.intercept,
          });
        }
        setPoints(out);
        setStats({ ...reg, firstT });
      } catch (e) {
        console.error('Predictive detail load failed:', e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [sensorId, alert.metricType]);

  // ─── Compute key stats ────────────────────────────────────────────
  const insights = useMemo(() => {
    if (!stats || points.length === 0) return null;
    const observed = points.filter((p) => p.actual !== undefined);
    const lastObs = observed[observed.length - 1];
    if (!lastObs) return null;

    const currentValue = lastObs.actual!;
    const minObs = Math.min(...observed.map((p) => p.actual!));
    const maxObs = Math.max(...observed.map((p) => p.actual!));

    // Rate of change per hour (slope is per second).
    const ratePerHour = stats.slope * 3600;

    // ETA — when does the regression line cross the threshold?
    let etaMs: number | null = null;
    let etaDirection: 'up' | 'down' | 'flat' = 'flat';
    if (Math.abs(stats.slope) > 1e-9) {
      const targetX = (threshold - stats.intercept) / stats.slope; // seconds since firstT
      const targetMs = stats.firstT + targetX * 1000;
      etaDirection = stats.slope > 0 ? 'up' : 'down';
      // Only show ETA if it's in the future and the trend is moving toward threshold.
      const movingToward =
        (stats.slope > 0 && currentValue < threshold) ||
        (stats.slope < 0 && currentValue > threshold);
      if (movingToward && targetMs > Date.now()) etaMs = targetMs;
    }

    // Predicted values at +1h, +3h, +6h.
    const forecasts = [1, 3, 6].map((h) => {
      const tFuture = lastObs.t + h * 3600 * 1000;
      const x = (tFuture - stats.firstT) / 1000;
      return { hour: h, value: stats.slope * x + stats.intercept };
    });

    return {
      currentValue,
      minObs,
      maxObs,
      ratePerHour,
      etaMs,
      etaDirection,
      forecasts,
      r2: stats.r2,
    };
  }, [stats, points, threshold]);

  // ─── Threshold severity bands ────────────────────────────────────
  const severityBand = useMemo(() => {
    if (!insights) return null;
    if (insights.etaMs === null) return null;
    const minutesAway = (insights.etaMs - Date.now()) / 60000;
    if (minutesAway < 30)  return { label: 'NGUY HIỂM CẬN KỀ', tone: 'critical' };
    if (minutesAway < 90)  return { label: 'CẢNH BÁO CAO',     tone: 'high'     };
    if (minutesAway < 240) return { label: 'CẢNH BÁO TRUNG BÌNH', tone: 'medium' };
    return { label: 'THEO DÕI', tone: 'low' };
  }, [insights]);

  const formatETA = (ms: number): string => {
    const minutes = Math.max(0, Math.round((ms - Date.now()) / 60000));
    const hh = Math.floor(minutes / 60);
    const mm = minutes % 60;
    const dt = new Date(ms);
    const time = dt.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    if (hh === 0) return `~${mm} phút nữa (lúc ${time})`;
    return `~${hh} giờ ${mm} phút nữa (lúc ${time})`;
  };

  const formatRate = (perHour: number): string => {
    const sign = perHour >= 0 ? '+' : '';
    return `${sign}${perHour.toFixed(2)} ${metricInfo.unit}/giờ`;
  };

  return (
    <div className="predictive-modal-backdrop" onClick={onClose}>
      <div className="predictive-modal" onClick={(e) => e.stopPropagation()}>
        <div className="predictive-modal-header">
          <div>
            <h2 className="predictive-modal-title">
              <ShieldAlert className="w-5 h-5 text-orange-400" />
              Chi Tiết Dự Đoán — {metricInfo.label}
            </h2>
            <p className="predictive-modal-subtitle">
              {formatLocationName(alert.locationId, locations)} · cảm biến {sensorId}
            </p>
          </div>
          <button className="predictive-modal-close" onClick={onClose} aria-label="Đóng">
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading && (
          <div className="predictive-loading">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span>Đang phân tích dữ liệu xu hướng…</span>
          </div>
        )}

        {!loading && !insights && (
          <div className="predictive-loading">
            <span>Không đủ dữ liệu lịch sử để phân tích xu hướng.</span>
          </div>
        )}

        {!loading && insights && (
          <>
            {/* Top severity banner */}
            {severityBand && (
              <div className={`predictive-severity-banner ${severityBand.tone}`}>
                <ShieldAlert className="w-5 h-5" />
                <span className="predictive-severity-label">{severityBand.label}</span>
                <span className="predictive-severity-eta">
                  Sẽ vượt ngưỡng {threshold.toFixed(1)} {metricInfo.unit} {formatETA(insights.etaMs!)}
                </span>
              </div>
            )}

            {/* Summary stat row */}
            <div className="predictive-stat-row">
              <div className="predictive-stat">
                <span className="predictive-stat-label">
                  <Activity className="w-3 h-3" /> Giá trị hiện tại
                </span>
                <span className="predictive-stat-value">
                  {insights.currentValue.toFixed(1)} <span className="predictive-stat-unit">{metricInfo.unit}</span>
                </span>
              </div>
              <div className="predictive-stat">
                <span className="predictive-stat-label">
                  <TrendingUp className="w-3 h-3" /> Tốc độ thay đổi
                </span>
                <span className={`predictive-stat-value ${insights.ratePerHour > 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {formatRate(insights.ratePerHour)}
                </span>
              </div>
              <div className="predictive-stat">
                <span className="predictive-stat-label">Ngưỡng nguy hiểm</span>
                <span className="predictive-stat-value text-yellow-400">
                  {threshold.toFixed(1)} <span className="predictive-stat-unit">{metricInfo.unit}</span>
                </span>
              </div>
              <div className="predictive-stat">
                <span className="predictive-stat-label">Độ tin cậy mô hình (R²)</span>
                <span className={`predictive-stat-value ${insights.r2 > 0.7 ? 'text-green-400' : insights.r2 > 0.4 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {(insights.r2 * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Chart: history + forecast + threshold */}
            <div className="predictive-chart-card">
              <div className="card-header">
                <h3 className="card-title">Xu Hướng &amp; Dự Đoán</h3>
                <p className="card-subtitle">
                  {HISTORY_HOURS} giờ vừa qua · dự đoán {FORECAST_POINTS * FORECAST_STEP_MIN / 60} giờ tiếp theo (đường nét đứt)
                </p>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={points} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="label" stroke="#9CA3AF" fontSize={11} minTickGap={28} />
                  <YAxis stroke="#9CA3AF" fontSize={11} unit={` ${metricInfo.unit}`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 8 }}
                    formatter={(value, name) => {
                      const n = typeof value === 'number' ? value : Number(value);
                      return [`${isNaN(n) ? '—' : n.toFixed(1)} ${metricInfo.unit}`, String(name)];
                    }}
                  />
                  <Legend />
                  <ReferenceLine
                    y={threshold}
                    stroke="#F59E0B"
                    strokeDasharray="6 4"
                    label={{ value: `Ngưỡng ${threshold} ${metricInfo.unit}`, fill: '#F59E0B', fontSize: 11, position: 'right' }}
                  />
                  {/* Soft danger zone above threshold */}
                  <Area
                    type="monotone"
                    dataKey={() => threshold * 2}
                    fill="rgba(239,68,68,0.06)"
                    stroke="none"
                    isAnimationActive={false}
                    name="Vùng nguy hiểm"
                    legendType="none"
                  />
                  <Line type="monotone" dataKey="actual" name="Thực tế (đã đo)"
                        stroke="#3B82F6" strokeWidth={2.5} dot={false} connectNulls={false} />
                  <Line type="monotone" dataKey="fit" name="Dự đoán (hồi quy tuyến tính)"
                        stroke="#EF4444" strokeWidth={2} strokeDasharray="6 4" dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Forecast table */}
            <div className="predictive-forecast-grid">
              {insights.forecasts.map((f) => {
                const exceeds = f.value > threshold;
                return (
                  <div key={f.hour} className={`predictive-forecast-card ${exceeds ? 'danger' : ''}`}>
                    <div className="predictive-forecast-when">
                      <Clock className="w-3 h-3" /> Sau {f.hour} giờ
                    </div>
                    <div className={`predictive-forecast-value ${exceeds ? 'text-red-400' : 'text-green-400'}`}>
                      {f.value.toFixed(1)}
                      <span className="predictive-forecast-unit"> {metricInfo.unit}</span>
                    </div>
                    <div className="predictive-forecast-state">
                      {exceeds
                        ? `Vượt ngưỡng ${threshold} ${metricInfo.unit}`
                        : `An toàn — dưới ngưỡng ${threshold} ${metricInfo.unit}`}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Why we predicted this */}
            <div className="predictive-explain">
              <h3 className="predictive-explain-title">
                <Lightbulb className="w-4 h-4 text-yellow-400" /> Cơ sở của dự đoán
              </h3>
              <ul className="predictive-explain-list">
                <li>
                  Phân tích <strong>{points.filter((p) => p.actual !== undefined).length}</strong> điểm đo thực tế
                  trong <strong>{HISTORY_HOURS} giờ qua</strong>.
                </li>
                <li>
                  Áp dụng <strong>hồi quy tuyến tính (linear regression)</strong> trên chuỗi thời gian.
                  Mô hình giải thích được <strong>{(insights.r2 * 100).toFixed(0)}%</strong> biến thiên
                  ({insights.r2 >= 0.7 ? 'tin cậy cao' : insights.r2 >= 0.4 ? 'tin cậy vừa' : 'tin cậy thấp'}).
                </li>
                <li>
                  Tốc độ thay đổi: <strong>{formatRate(insights.ratePerHour)}</strong>.
                  {insights.ratePerHour > 0
                    ? ` Giá trị đang tăng — cần theo dõi sát.`
                    : ` Giá trị đang giảm — tình trạng đang cải thiện.`}
                </li>
                <li>
                  Khoảng giá trị quan sát: <strong>{insights.minObs.toFixed(1)}</strong> – <strong>{insights.maxObs.toFixed(1)}</strong> {metricInfo.unit}.
                </li>
                {insights.etaMs !== null && (
                  <li className="text-orange-400">
                    Theo trend hiện tại, giá trị sẽ chạm ngưỡng <strong>{threshold} {metricInfo.unit}</strong>{' '}
                    {formatETA(insights.etaMs)}.
                  </li>
                )}
              </ul>
            </div>

            {/* Recommendations */}
            <div className="predictive-explain">
              <h3 className="predictive-explain-title">
                <ShieldAlert className="w-4 h-4 text-red-400" /> Khuyến nghị hành động
              </h3>
              <ul className="predictive-explain-list">
                {alert.metricType === 'CO2' && (
                  <>
                    <li>Mở cửa, tăng thông khí khu vực bị ảnh hưởng.</li>
                    <li>Kiểm tra hệ thống HVAC / quạt thông gió.</li>
                    <li>Hạn chế tập trung đông người tại điểm đo.</li>
                  </>
                )}
                {alert.metricType === 'Noise' && (
                  <>
                    <li>Yêu cầu giảm âm lượng từ nguồn phát (loa, công trình).</li>
                    <li>Thông báo cho cơ quan môi trường nếu vượt 85 dB liên tục.</li>
                  </>
                )}
                {(alert.metricType === 'PM25' || alert.metricType === 'PM2.5') && (
                  <>
                    <li>Cảnh báo cộng đồng nhạy cảm (trẻ em, người cao tuổi) hạn chế ra ngoài.</li>
                    <li>Đeo khẩu trang N95 nếu cần ra đường.</li>
                    <li>Đóng cửa sổ, sử dụng máy lọc không khí trong nhà.</li>
                  </>
                )}
                {alert.metricType === 'Humidity' && (
                  <>
                    <li>Bật máy hút ẩm hoặc điều hòa nếu độ ẩm tăng cao.</li>
                    <li>Kiểm tra thoát nước, ngăn nấm mốc tại các khu vực kín.</li>
                  </>
                )}
                {alert.metricType === 'Temperature' && (
                  <>
                    <li>Bật điều hòa / quạt làm mát nếu nhiệt độ tiếp tục tăng.</li>
                    <li>Cảnh báo nguy cơ sốc nhiệt khi vượt 36 °C.</li>
                  </>
                )}
                <li>Theo dõi sát điểm đo này trong {insights.etaMs !== null ? Math.round((insights.etaMs - Date.now()) / 60000) : '—'} phút tới.</li>
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default PredictiveDetailModal;
