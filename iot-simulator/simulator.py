#!/usr/bin/env python3
"""
IoT Sensor Simulator — Smart City Dashboard.

Generates realistic environmental telemetry and publishes to MQTT.
Emits a steady stream of varied alert-eligible events so the backend's
threshold / predictive / anomaly detection can be exercised end-to-end.

Realism principles:

1. Per-sensor state (no global RNG snapshots).
   Each sensor has its own current values; subsequent readings are
   autocorrelated, never jump from 30 dB to 99 dB between ticks.

2. Smoothing via exponentially-weighted moving average (EWMA):
       value_new = α · value_old + (1 - α) · target + small_noise
   With α = 0.85, every 5-second tick drifts ~15 % toward the target —
   producing realistic slow change between adjacent readings.

3. Spatial profile per ward — see WARD_PROFILES. Profiles match
   `backend/app/db/seed_telemetry.py` so historical seed data agrees
   with the live stream.

4. Diurnal patterns: rush-hour spikes (08:00 / 18:00), night dip
   (02:00–04:00), temperature sine wave peaking ~14:00, humidity
   inverse to temperature.

5. Weekend effect: Sat/Sun traffic impact reduced 40 %.

6. **Hotspot sensors** — a small fixed subset (busy markets, airport,
   port) carries higher baselines and higher anomaly probability so the
   alert dashboard always has interesting state. Demo-friendly.

7. **Configurable danger level** via `SIMULATOR_DANGER_LEVEL`:
       normal   — original behavior (research / quiet runs)
       elevated — DEFAULT: more frequent anomalies, ~30 alerts/hour
       extreme  — stress-test: ~150 alerts/hour, hits CRITICAL often

8. **Typed anomaly events** (instead of one generic spike):
       TRAFFIC_JAM          CO2 + PM2.5 + Noise rise together
       INDUSTRIAL_FIRE      PM2.5 dominates (→ HIGH / CRITICAL PM2.5)
       EQUIPMENT_MALFUNCTION Noise dominates (→ HIGH Noise)
       STORM_INCOMING       Humidity rise + Temp drop (→ Humidity alert)
       HEAT_WAVE            Temperature surge + Humidity drop
       CO2_TREND            Slow linear CO2 ramp (→ Predictive alert)
   Each event has a distinct duration, multiplier profile, and target
   severity tier so the lecturer can correlate "I see a CRITICAL PM2.5
   alert" with "INDUSTRIAL_FIRE on sensor X" in the simulator log.

9. Boundary clamping: every metric stays inside physically-plausible
   range (CO2 250–3000 ppm, Noise 30–125 dB, PM2.5 5–300 µg/m³, …).
"""

import os
import sys
import json
import math
import time
import random
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


# ============================================================================
# Per-ward pollution / noise profile (must match seed_telemetry.py)
# ============================================================================

# Each profile gives the *baseline* values around which the live signal
# oscillates. `traffic_factor` scales the rush-hour amplitude so e.g. Bến
# Thành (chợ trung tâm) reacts more strongly than a quiet residential street.

WARD_PROFILES: Dict[str, Dict[str, float]] = {
    # ── District 1 — downtown ────────────────────────────────────────
    'ward_q1_ben_nghe':         {'co2': 480, 'noise': 62, 'pm25': 45, 'temp': 29, 'hum': 72, 'traffic': 1.20},
    'ward_q1_ben_thanh':        {'co2': 520, 'noise': 68, 'pm25': 52, 'temp': 30, 'hum': 70, 'traffic': 1.30},
    'ward_q1_nguyen_thai_binh': {'co2': 460, 'noise': 58, 'pm25': 40, 'temp': 29, 'hum': 73, 'traffic': 1.10},
    # ── District 3 — midtown ─────────────────────────────────────────
    'ward_q3_01': {'co2': 420, 'noise': 55, 'pm25': 35, 'temp': 28, 'hum': 75, 'traffic': 1.00},
    'ward_q3_02': {'co2': 410, 'noise': 52, 'pm25': 33, 'temp': 28, 'hum': 76, 'traffic': 0.95},
    'ward_q3_03': {'co2': 430, 'noise': 54, 'pm25': 36, 'temp': 28, 'hum': 74, 'traffic': 1.05},
    # ── District 5 — Cholon residential ─────────────────────────────
    'ward_q5_01': {'co2': 390, 'noise': 48, 'pm25': 30, 'temp': 27, 'hum': 78, 'traffic': 0.85},
    'ward_q5_02': {'co2': 380, 'noise': 46, 'pm25': 28, 'temp': 27, 'hum': 79, 'traffic': 0.80},
    'ward_q5_03': {'co2': 400, 'noise': 50, 'pm25': 32, 'temp': 27, 'hum': 77, 'traffic': 0.90},
    # ── District 4 — riverside, port-adjacent ────────────────────────
    'ward_q4_vinh_khanh': {'co2': 440, 'noise': 56, 'pm25': 38, 'temp': 28, 'hum': 76, 'traffic': 1.05},
    'ward_q4_vinh_hoi':   {'co2': 450, 'noise': 58, 'pm25': 40, 'temp': 28, 'hum': 76, 'traffic': 1.10},
    'ward_q4_khanh_hoi':  {'co2': 470, 'noise': 60, 'pm25': 42, 'temp': 29, 'hum': 75, 'traffic': 1.15},
    # ── District 7 — Phú Mỹ Hưng, modern, cleaner ───────────────────
    'ward_q7_tan_phong':  {'co2': 360, 'noise': 44, 'pm25': 26, 'temp': 27, 'hum': 80, 'traffic': 0.70},
    'ward_q7_tan_phu':    {'co2': 370, 'noise': 46, 'pm25': 28, 'temp': 27, 'hum': 80, 'traffic': 0.75},
    'ward_q7_tan_quy':    {'co2': 380, 'noise': 48, 'pm25': 30, 'temp': 27, 'hum': 79, 'traffic': 0.80},
    # ── District 10 — residential mix ───────────────────────────────
    'ward_q10_01': {'co2': 410, 'noise': 53, 'pm25': 34, 'temp': 28, 'hum': 76, 'traffic': 0.95},
    'ward_q10_02': {'co2': 405, 'noise': 51, 'pm25': 33, 'temp': 28, 'hum': 76, 'traffic': 0.92},
    'ward_q10_03': {'co2': 415, 'noise': 54, 'pm25': 35, 'temp': 28, 'hum': 75, 'traffic': 0.98},
    # ── Bình Thạnh — busy mixed-use ─────────────────────────────────
    'ward_bt_01': {'co2': 470, 'noise': 60, 'pm25': 42, 'temp': 29, 'hum': 73, 'traffic': 1.15},
    'ward_bt_25': {'co2': 490, 'noise': 64, 'pm25': 46, 'temp': 29, 'hum': 72, 'traffic': 1.22},
    'ward_bt_26': {'co2': 460, 'noise': 58, 'pm25': 40, 'temp': 29, 'hum': 73, 'traffic': 1.12},
    # ── Tân Bình — airport adjacent, very dense ─────────────────────
    'ward_tb_01': {'co2': 510, 'noise': 70, 'pm25': 50, 'temp': 30, 'hum': 71, 'traffic': 1.28},
    'ward_tb_04': {'co2': 500, 'noise': 68, 'pm25': 48, 'temp': 30, 'hum': 71, 'traffic': 1.25},
    'ward_tb_15': {'co2': 495, 'noise': 66, 'pm25': 47, 'temp': 30, 'hum': 72, 'traffic': 1.20},
    # ── Phú Nhuận — leafy residential ───────────────────────────────
    'ward_pn_07': {'co2': 395, 'noise': 49, 'pm25': 31, 'temp': 28, 'hum': 78, 'traffic': 0.85},
    'ward_pn_09': {'co2': 400, 'noise': 50, 'pm25': 32, 'temp': 28, 'hum': 77, 'traffic': 0.88},
    'ward_pn_15': {'co2': 405, 'noise': 51, 'pm25': 33, 'temp': 28, 'hum': 77, 'traffic': 0.90},
    # ── Gò Vấp — suburban ───────────────────────────────────────────
    'ward_gv_01': {'co2': 385, 'noise': 47, 'pm25': 28, 'temp': 27, 'hum': 79, 'traffic': 0.80},
    'ward_gv_05': {'co2': 380, 'noise': 46, 'pm25': 27, 'temp': 27, 'hum': 80, 'traffic': 0.75},
    'ward_gv_10': {'co2': 390, 'noise': 48, 'pm25': 30, 'temp': 27, 'hum': 79, 'traffic': 0.82},
}

# Sensible default if a sensor maps to an unknown ward.
DEFAULT_PROFILE = WARD_PROFILES['ward_q3_01']

# Smoothing factor — higher value ⇒ slower drift between ticks.
EWMA_ALPHA = 0.85

# A small set of fixed "hotspot" sensors that always have higher baselines
# and a much higher anomaly probability. Keeps the alerts dashboard alive
# during demos. Chosen one per high-traffic ward (market / airport / port).
HOTSPOT_SENSORS = frozenset({
    'sen_q1_ben_thanh_01',   # Bến Thành market — peak crowd
    'sen_tb_01_01',          # Tân Bình — airport adjacent
    'sen_bt_25_01',          # Bình Thạnh — busy mixed-use
    'sen_q4_khanh_hoi_01',   # Q4 — port-adjacent
    'sen_q1_ben_nghe_01',    # Q1 downtown
})

# ============================================================================
# Danger level — tunes anomaly frequency + baseline shift via env var
# ============================================================================
#
# `SIMULATOR_DANGER_LEVEL` ∈ {normal, elevated, extreme}
#
#   normal   — research / quiet runs. Anomalies are rare (~2/hour).
#   elevated — DEFAULT for demos. ~30 alerts/hour spread across all sensors,
#              hotspots account for ~40% of them.
#   extreme  — stress test. ~150 alerts/hour, multiple CRITICAL events.

DANGER_LEVEL = os.getenv("SIMULATOR_DANGER_LEVEL", "elevated").lower()
if DANGER_LEVEL not in {"normal", "elevated", "extreme"}:
    logger.warning(f"Unknown SIMULATOR_DANGER_LEVEL={DANGER_LEVEL!r}, defaulting to 'elevated'")
    DANGER_LEVEL = "elevated"

# Per-tick anomaly probability for a normal sensor.
# Hotspot sensors multiply this by HOTSPOT_BOOST.
DANGER_CONFIG: Dict[str, Dict[str, float]] = {
    'normal':   {'normal_prob': 1 / 10000, 'hotspot_boost': 3.0,  'baseline_shift': 1.00},
    'elevated': {'normal_prob': 1 / 1500,  'hotspot_boost': 5.0,  'baseline_shift': 1.08},
    'extreme':  {'normal_prob': 1 / 400,   'hotspot_boost': 5.0,  'baseline_shift': 1.18},
}
_cfg = DANGER_CONFIG[DANGER_LEVEL]
ANOMALY_PROBABILITY = _cfg['normal_prob']
HOTSPOT_ANOMALY_BOOST = _cfg['hotspot_boost']
BASELINE_SHIFT = _cfg['baseline_shift']

logger.info(
    f"Danger level={DANGER_LEVEL} · anomaly_prob=1/{int(1 / ANOMALY_PROBABILITY)} "
    f"(hotspots ×{HOTSPOT_ANOMALY_BOOST:.1f}) · baseline_shift=×{BASELINE_SHIFT:.2f}"
)


# ============================================================================
# Anomaly event catalog
# ============================================================================
#
# Each event type carries multipliers / offsets applied on top of the
# normal target. Multiple events on the same sensor never overlap — a new
# event only starts when the previous one has fully decayed.
#
#   target_severity is informational only — it tells you what alert tier
#   the event is *designed* to trigger, so you can correlate the simulator
#   log with the alerts dashboard during a demo.

@dataclass(frozen=True)
class AnomalyEventSpec:
    name: str
    weight: float            # selection weight when picking a new event
    duration_range: Tuple[int, int]
    target_severity: str     # 'MEDIUM' | 'HIGH' | 'CRITICAL'
    # Per-metric ranges. (low, high) — sampled uniformly when event starts.
    co2_mult: Tuple[float, float] = (1.0, 1.0)
    noise_mult: Tuple[float, float] = (1.0, 1.0)
    pm25_mult: Tuple[float, float] = (1.0, 1.0)
    temp_offset: Tuple[float, float] = (0.0, 0.0)
    hum_offset: Tuple[float, float] = (0.0, 0.0)
    # Slow linear ramps (added per tick) — used to trigger predictive alerts.
    co2_slope: Tuple[float, float] = (0.0, 0.0)
    description: str = ""


ANOMALY_EVENTS: List[AnomalyEventSpec] = [
    AnomalyEventSpec(
        name="TRAFFIC_JAM", weight=0.45,
        duration_range=(4, 9), target_severity="HIGH",
        co2_mult=(1.7, 2.4), noise_mult=(1.2, 1.5), pm25_mult=(1.6, 2.2),
        description="Kẹt xe: CO2 + PM2.5 + Noise tăng đồng thời",
    ),
    AnomalyEventSpec(
        name="INDUSTRIAL_FIRE", weight=0.20,
        duration_range=(8, 18), target_severity="CRITICAL",
        pm25_mult=(2.8, 4.5), noise_mult=(1.1, 1.4), co2_mult=(1.3, 1.7),
        description="Cháy / khói công nghiệp: PM2.5 vọt rất cao",
    ),
    AnomalyEventSpec(
        name="EQUIPMENT_MALFUNCTION", weight=0.15,
        duration_range=(5, 12), target_severity="HIGH",
        noise_mult=(1.6, 2.2),
        description="Máy khoan / máy nén lỗi: tiếng ồn vượt ngưỡng OSHA",
    ),
    AnomalyEventSpec(
        name="STORM_INCOMING", weight=0.10,
        duration_range=(15, 25), target_severity="MEDIUM",
        hum_offset=(8.0, 18.0), temp_offset=(-3.5, -1.5),
        description="Áp thấp / mưa lớn: độ ẩm tăng vọt, nhiệt độ giảm",
    ),
    AnomalyEventSpec(
        name="HEAT_WAVE", weight=0.05,
        duration_range=(20, 35), target_severity="MEDIUM",
        temp_offset=(4.0, 7.5), hum_offset=(-15.0, -8.0),
        description="Sóng nhiệt: nhiệt độ tăng kéo dài, độ ẩm giảm",
    ),
    AnomalyEventSpec(
        name="CO2_TREND", weight=0.05,
        duration_range=(22, 30), target_severity="HIGH (Predictive)",
        co2_slope=(20.0, 35.0),
        description="Rò rỉ chậm: CO2 tăng tuyến tính → kích hoạt Predictive alert",
    ),
]
_TOTAL_WEIGHT = sum(e.weight for e in ANOMALY_EVENTS)


def _pick_event() -> AnomalyEventSpec:
    """Weighted random pick from ANOMALY_EVENTS."""
    r = random.random() * _TOTAL_WEIGHT
    cum = 0.0
    for ev in ANOMALY_EVENTS:
        cum += ev.weight
        if r <= cum:
            return ev
    return ANOMALY_EVENTS[-1]


# ============================================================================
# Per-sensor mutable state
# ============================================================================

@dataclass
class ActiveAnomaly:
    """A single in-flight anomaly event — sampled multipliers + countdown."""
    spec: AnomalyEventSpec
    ticks_left: int
    co2_mult: float
    noise_mult: float
    pm25_mult: float
    temp_offset: float
    hum_offset: float
    co2_slope: float


@dataclass
class SensorState:
    sensor_id: str
    location_id: str
    profile: Dict[str, float]
    is_hotspot: bool = False

    # Current metric values.
    co2: float = 0.0
    noise: float = 0.0
    temperature: float = 0.0
    pm25: float = 0.0
    humidity: float = 0.0

    # Device health (slowly drifting).
    battery: float = field(default_factory=lambda: random.uniform(80, 100))
    signal_dbm: float = field(default_factory=lambda: random.uniform(-55, -45))

    # Anomaly state.
    active_anomaly: Optional[ActiveAnomaly] = None

    def __post_init__(self):
        # Initialise current values to the (possibly shifted) profile baseline
        # so the first publish already looks plausible (not zero or extreme).
        p = self.profile
        # Hotspots get an extra +5% on top of the global baseline shift.
        hot_shift = 1.05 if self.is_hotspot else 1.0
        self.co2 = p['co2'] * BASELINE_SHIFT * hot_shift
        self.noise = p['noise'] * BASELINE_SHIFT * hot_shift
        self.temperature = p['temp']  # don't shift physical climate
        self.pm25 = p['pm25'] * BASELINE_SHIFT * hot_shift
        self.humidity = p['hum']

    def trigger_probability(self) -> float:
        """Per-tick anomaly trigger probability for this sensor."""
        return ANOMALY_PROBABILITY * (HOTSPOT_ANOMALY_BOOST if self.is_hotspot else 1.0)


# ============================================================================
# Realism math
# ============================================================================

def compute_targets(profile: Dict[str, float], ts: datetime, is_hotspot: bool) -> Dict[str, float]:
    """
    Produce the "target" value for each metric at this timestamp.
    The live state will EWMA-drift toward these targets.
    """
    hour = ts.hour + ts.minute / 60.0 + ts.second / 3600.0

    # Rush hour: Gaussian peaks at 08:00 and 18:00 (sigma √3 hours).
    rush = max(
        math.exp(-((hour - 8.0) ** 2) / 6.0),
        math.exp(-((hour - 18.0) ** 2) / 6.0),
    )
    # Night dip — quiet between 02:00 and 04:00.
    night = math.exp(-((hour - 3.0) ** 2) / 12.0)

    weekend_mult = 0.6 if ts.weekday() >= 5 else 1.0
    traffic = profile['traffic']

    # Sine wave: peak at 14:00, trough at 02:00.
    sun = math.sin(math.pi * (hour - 6.0) / 12.0)

    # Hotspots get a +5% baseline bump on top of the global shift.
    hot_shift = 1.05 if is_hotspot else 1.0
    base_co2   = profile['co2']   * BASELINE_SHIFT * hot_shift
    base_noise = profile['noise'] * BASELINE_SHIFT * hot_shift
    base_pm25  = profile['pm25']  * BASELINE_SHIFT * hot_shift

    return {
        'co2':   base_co2   + rush * 380 * weekend_mult * traffic - night * 80,
        'noise': base_noise + rush * 24  * weekend_mult * traffic - night * 18,
        'pm25':  base_pm25  + rush * 50  * weekend_mult * traffic - night * 10,
        'temp':  profile['temp']  + 4 * sun,
        'hum':   profile['hum']   - 12 * sun,
    }


def maybe_start_anomaly(state: SensorState) -> None:
    """If no event is active and the dice roll, start a new typed event."""
    if state.active_anomaly is not None:
        return
    if random.random() >= state.trigger_probability():
        return

    spec = _pick_event()
    duration = random.randint(*spec.duration_range)

    def _u(rng: Tuple[float, float]) -> float:
        return random.uniform(*rng)

    state.active_anomaly = ActiveAnomaly(
        spec=spec,
        ticks_left=duration,
        co2_mult=_u(spec.co2_mult),
        noise_mult=_u(spec.noise_mult),
        pm25_mult=_u(spec.pm25_mult),
        temp_offset=_u(spec.temp_offset),
        hum_offset=_u(spec.hum_offset),
        co2_slope=_u(spec.co2_slope),
    )

    tag = "🔥" if "FIRE" in spec.name else "⚡"
    hot_marker = " [HOTSPOT]" if state.is_hotspot else ""
    logger.info(
        f"{tag} {spec.name}{hot_marker} on {state.sensor_id} "
        f"({state.location_id}) for {duration} ticks "
        f"→ expect {spec.target_severity} alert · {spec.description}"
    )


def apply_anomaly(targets: Dict[str, float], anomaly: ActiveAnomaly,
                  current_co2: float) -> Dict[str, float]:
    """Apply the active anomaly's multipliers/offsets to `targets`."""
    targets['co2']   = targets['co2']   * anomaly.co2_mult
    targets['noise'] = targets['noise'] * anomaly.noise_mult
    targets['pm25']  = targets['pm25']  * anomaly.pm25_mult
    targets['temp']  = targets['temp']  + anomaly.temp_offset
    targets['hum']   = targets['hum']   + anomaly.hum_offset
    # Slow linear ramp on top of the current state — for predictive alerts.
    if anomaly.co2_slope > 0:
        targets['co2'] = max(targets['co2'], current_co2 + anomaly.co2_slope)
    return targets


def step_state(state: SensorState, ts: datetime) -> None:
    """
    Advance a sensor's state by one tick. Called every PUBLISH_INTERVAL
    seconds. Mutates `state` in place.
    """
    # 1. Maybe start a new typed anomaly event.
    maybe_start_anomaly(state)

    # 2. Compute time-of-day targets.
    targets = compute_targets(state.profile, ts, state.is_hotspot)

    # 3. Apply active anomaly (if any) and tick its countdown.
    if state.active_anomaly is not None:
        targets = apply_anomaly(targets, state.active_anomaly, state.co2)
        state.active_anomaly.ticks_left -= 1
        if state.active_anomaly.ticks_left <= 0:
            logger.info(
                f"✓ {state.active_anomaly.spec.name} cleared on {state.sensor_id}"
            )
            state.active_anomaly = None

    # 4. EWMA smoothing + small Gaussian sensor noise.
    α = EWMA_ALPHA
    state.co2         = α * state.co2         + (1 - α) * targets['co2']   + random.gauss(0, 5.0)
    state.noise       = α * state.noise       + (1 - α) * targets['noise'] + random.gauss(0, 1.0)
    state.temperature = α * state.temperature + (1 - α) * targets['temp']  + random.gauss(0, 0.2)
    state.pm25        = α * state.pm25        + (1 - α) * targets['pm25']  + random.gauss(0, 1.0)
    state.humidity    = α * state.humidity    + (1 - α) * targets['hum']   + random.gauss(0, 0.5)

    # 5. Boundary clamping (physical plausibility).
    # Bounds widened so anomalies can drive metrics into the CRITICAL band
    # without being capped at the threshold.
    state.co2 = max(250.0, min(3000.0, state.co2))
    state.noise = max(30.0, min(125.0, state.noise))
    state.temperature = max(15.0, min(42.0, state.temperature))
    state.pm25 = max(5.0, min(300.0, state.pm25))
    state.humidity = max(20.0, min(99.0, state.humidity))

    # 6. Device health.
    # Battery slowly discharges (~1% / 50 min at 5s tick); recharges
    # randomly when low — mimics field devices being swapped out.
    state.battery = max(0.0, state.battery - random.uniform(0.0, 0.005))
    if state.battery < 30 and random.random() < 0.05:
        state.battery = random.uniform(85.0, 100.0)
        logger.info(f"🔋 Battery swap on {state.sensor_id}")
    # Signal strength jitter ±1.5 dBm.
    state.signal_dbm = max(-90.0, min(-30.0, state.signal_dbm + random.gauss(0, 1.5)))


# ============================================================================
# Simulator
# ============================================================================

class SensorSimulator:
    """Simulates IoT sensors publishing telemetry data via MQTT."""

    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        sensor_ids: List[str],
        publish_interval: int = 5,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.sensor_ids = sensor_ids
        self.publish_interval = publish_interval
        self.client = mqtt.Client()
        self.connected = False
        self.retry_delay = 1
        self.max_retry_delay = 60

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        # Build per-sensor state (location lookup + initial values).
        self.sensor_locations = self._initialize_sensor_locations()
        self.states: Dict[str, SensorState] = {}
        for sid in self.sensor_ids:
            location_id = self.sensor_locations.get(sid, 'ward_q3_01')
            profile = WARD_PROFILES.get(location_id, DEFAULT_PROFILE)
            self.states[sid] = SensorState(
                sensor_id=sid,
                location_id=location_id,
                profile=profile,
                is_hotspot=(sid in HOTSPOT_SENSORS),
            )

        n_hot = sum(1 for s in self.states.values() if s.is_hotspot)
        logger.info(
            f"Initialised {len(self.states)} sensors ({n_hot} hotspots): "
            f"{sorted(s.sensor_id for s in self.states.values() if s.is_hotspot)}"
        )

    # ── Sensor → location resolution ──────────────────────────────────────
    def _initialize_sensor_locations(self) -> Dict[str, str]:
        # Most sensor IDs follow `sen_{ward_suffix}_{nn}` and the ward_id is
        # `ward_{ward_suffix}` — derived by stripping the trailing _NN.
        # The map below covers the legacy IDs (Q1/Q3/Q5) that don't match
        # this suffix convention.
        legacy_prefix_map = {
            'sen_q1_ben_nghe':  'ward_q1_ben_nghe',
            'sen_q1_ben_thanh': 'ward_q1_ben_thanh',
            'sen_q1_ntb':       'ward_q1_nguyen_thai_binh',
            'sen_q3_w1':        'ward_q3_01',
            'sen_q3_w2':        'ward_q3_02',
            'sen_q3_w3':        'ward_q3_03',
            'sen_q5_w1':        'ward_q5_01',
            'sen_q5_w2':        'ward_q5_02',
            'sen_q5_w3':        'ward_q5_03',
        }

        result: Dict[str, str] = {}
        for sensor_id in self.sensor_ids:
            parts = sensor_id.split('_')
            if len(parts) < 4 or parts[0] != 'sen':
                result[sensor_id] = 'ward_q3_01'
                continue

            # First try the legacy prefix lookup.
            matched = False
            for end_idx in range(len(parts) - 1, 1, -1):
                prefix = "_".join(parts[:end_idx])
                if prefix in legacy_prefix_map:
                    result[sensor_id] = legacy_prefix_map[prefix]
                    matched = True
                    break
            if matched:
                continue

            # Otherwise: drop trailing _NN and prefix with `ward_`.
            ward_id = "ward_" + "_".join(parts[1:-1])
            if ward_id in WARD_PROFILES:
                result[sensor_id] = ward_id
            else:
                result[sensor_id] = 'ward_q3_01'
        return result

    # ── MQTT callbacks ────────────────────────────────────────────────────
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.retry_delay = 1
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        else:
            self.connected = False
            logger.error(f"Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection (code {rc})")

    def _on_publish(self, client, userdata, mid):
        logger.debug(f"Message {mid} published")

    def connect(self):
        while not self.connected:
            try:
                logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
                self.client.connect(self.broker_host, self.broker_port, keepalive=60)
                self.client.loop_start()

                timeout = 10
                elapsed = 0.0
                while not self.connected and elapsed < timeout:
                    time.sleep(0.5)
                    elapsed += 0.5

                if not self.connected:
                    raise ConnectionError("Connection timeout")
            except Exception as e:
                logger.error(f"Connection failed: {e}. Retrying in {self.retry_delay}s …")
                time.sleep(self.retry_delay)
                self.retry_delay = min(self.retry_delay * 2, self.max_retry_delay)

    # ── Telemetry generation ─────────────────────────────────────────────
    def generate_telemetry(self, sensor_id: str) -> Dict:
        state = self.states[sensor_id]
        ts = datetime.now(timezone.utc)
        step_state(state, ts)

        return {
            "sensorId": sensor_id,
            "locationId": state.location_id,
            "data": {
                "co2":         round(state.co2, 2),
                "noise":       round(state.noise, 2),
                "temperature": round(state.temperature, 2),
                "pm25":        round(state.pm25, 2),
                "humidity":    round(state.humidity, 2),
            },
            "location": {
                "type": "Point",
                "coordinates": [0.0, 0.0],  # backend enriches from registry
            },
            "quality": {
                "batteryLevel":   round(state.battery, 2),
                "signalStrength": round(state.signal_dbm, 2),
            },
            "timestamp": ts.isoformat().replace('+00:00', 'Z'),
        }

    def publish_telemetry(self, sensor_id: str):
        if not self.connected:
            logger.warning("Not connected to MQTT broker — skipping publish")
            return

        telemetry = self.generate_telemetry(sensor_id)
        topic = f"sensors/{sensor_id}/telemetry"
        payload = json.dumps(telemetry)

        try:
            result = self.client.publish(topic, payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                d = telemetry['data']
                state = self.states[sensor_id]
                anomaly_tag = ""
                if state.active_anomaly is not None:
                    anomaly_tag = f" 🚨{state.active_anomaly.spec.name}"
                logger.info(
                    f"{sensor_id} ({telemetry['locationId']}): "
                    f"CO2={d['co2']:.0f} | PM2.5={d['pm25']:.1f} | "
                    f"Noise={d['noise']:.1f} | T={d['temperature']:.1f}°C | "
                    f"H={d['humidity']:.0f}%{anomaly_tag}"
                )
            else:
                logger.error(f"Publish failed rc={result.rc} on {topic}")
        except Exception as e:
            logger.error(f"Publish error: {e}")

    def run(self):
        logger.info(
            f"Starting simulator: {len(self.sensor_ids)} sensors, "
            f"interval={self.publish_interval}s, α={EWMA_ALPHA}, danger={DANGER_LEVEL}"
        )
        try:
            while True:
                for sensor_id in self.sensor_ids:
                    self.publish_telemetry(sensor_id)
                time.sleep(self.publish_interval)
        except KeyboardInterrupt:
            logger.info("Simulator stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.disconnect()

    def disconnect(self):
        logger.info("Disconnecting from MQTT broker …")
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False


# ============================================================================
# Entry point
# ============================================================================

def main():
    broker_host = os.getenv("MQTT_BROKER_HOST", "mosquitto")
    broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))

    # 96 sensors total — 33 legacy (Q1/Q3/Q5) + 63 new (Q4/Q7/Q10/BT/TB/PN/GV).
    default_sensors = (
        # Q1 — 15 sensors
        "sen_q1_ben_nghe_01,sen_q1_ben_nghe_02,sen_q1_ben_nghe_03,sen_q1_ben_nghe_04,sen_q1_ben_nghe_05,"
        "sen_q1_ben_thanh_01,sen_q1_ben_thanh_02,sen_q1_ben_thanh_03,sen_q1_ben_thanh_04,sen_q1_ben_thanh_05,"
        "sen_q1_ntb_01,sen_q1_ntb_02,sen_q1_ntb_03,sen_q1_ntb_04,sen_q1_ntb_05,"
        # Q3 — 9 sensors
        "sen_q3_w1_01,sen_q3_w1_02,sen_q3_w1_03,sen_q3_w2_01,sen_q3_w2_02,sen_q3_w2_03,"
        "sen_q3_w3_01,sen_q3_w3_02,sen_q3_w3_03,"
        # Q5 — 9 sensors
        "sen_q5_w1_01,sen_q5_w1_02,sen_q5_w1_03,sen_q5_w2_01,sen_q5_w2_02,sen_q5_w2_03,"
        "sen_q5_w3_01,sen_q5_w3_02,sen_q5_w3_03,"
        # Q4 — 9 sensors
        "sen_q4_vinh_khanh_01,sen_q4_vinh_khanh_02,sen_q4_vinh_khanh_03,"
        "sen_q4_vinh_hoi_01,sen_q4_vinh_hoi_02,sen_q4_vinh_hoi_03,"
        "sen_q4_khanh_hoi_01,sen_q4_khanh_hoi_02,sen_q4_khanh_hoi_03,"
        # Q7 — 9 sensors
        "sen_q7_tan_phong_01,sen_q7_tan_phong_02,sen_q7_tan_phong_03,"
        "sen_q7_tan_phu_01,sen_q7_tan_phu_02,sen_q7_tan_phu_03,"
        "sen_q7_tan_quy_01,sen_q7_tan_quy_02,sen_q7_tan_quy_03,"
        # Q10 — 9 sensors
        "sen_q10_01_01,sen_q10_01_02,sen_q10_01_03,"
        "sen_q10_02_01,sen_q10_02_02,sen_q10_02_03,"
        "sen_q10_03_01,sen_q10_03_02,sen_q10_03_03,"
        # Bình Thạnh — 9 sensors
        "sen_bt_01_01,sen_bt_01_02,sen_bt_01_03,"
        "sen_bt_25_01,sen_bt_25_02,sen_bt_25_03,"
        "sen_bt_26_01,sen_bt_26_02,sen_bt_26_03,"
        # Tân Bình — 9 sensors
        "sen_tb_01_01,sen_tb_01_02,sen_tb_01_03,"
        "sen_tb_04_01,sen_tb_04_02,sen_tb_04_03,"
        "sen_tb_15_01,sen_tb_15_02,sen_tb_15_03,"
        # Phú Nhuận — 9 sensors
        "sen_pn_07_01,sen_pn_07_02,sen_pn_07_03,"
        "sen_pn_09_01,sen_pn_09_02,sen_pn_09_03,"
        "sen_pn_15_01,sen_pn_15_02,sen_pn_15_03,"
        # Gò Vấp — 9 sensors
        "sen_gv_01_01,sen_gv_01_02,sen_gv_01_03,"
        "sen_gv_05_01,sen_gv_05_02,sen_gv_05_03,"
        "sen_gv_10_01,sen_gv_10_02,sen_gv_10_03"
    )
    sensor_list = os.getenv("SENSOR_LIST", default_sensors)
    publish_interval = int(os.getenv("PUBLISH_INTERVAL", "5"))

    sensor_ids = [s.strip() for s in sensor_list.split(",") if s.strip()]
    if not sensor_ids:
        logger.error("No sensors configured. Set SENSOR_LIST environment variable.")
        sys.exit(1)

    sim = SensorSimulator(
        broker_host=broker_host,
        broker_port=broker_port,
        sensor_ids=sensor_ids,
        publish_interval=publish_interval,
    )
    sim.connect()
    sim.run()


if __name__ == "__main__":
    main()
