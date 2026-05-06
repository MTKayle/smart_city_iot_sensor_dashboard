#!/usr/bin/env python3
"""
IoT Sensor Simulator — Smart City Dashboard.

Generates realistic environmental telemetry and publishes to MQTT.

Realism principles:

1. Per-sensor state (no global RNG snapshots).
   Each sensor has its own current values; subsequent readings are
   autocorrelated, never jump from 30 dB to 99 dB between ticks.

2. Smoothing via exponentially-weighted moving average (EWMA):
       value_new = α · value_old + (1 - α) · target + small_noise
   With α = 0.85, every 5-second tick drifts ~15 % toward the target —
   producing realistic slow change between adjacent readings.

3. Spatial profile per ward:
       - District 1 (downtown markets) is the most polluted / loudest
       - District 5 (Cholon residential) is the cleanest
   Profiles match `backend/app/db/seed_telemetry.py` so historical seed
   data and live data agree.

4. Diurnal patterns:
       - Rush-hour spikes for CO2 / Noise / PM2.5 at 08:00 and 18:00
       - Night-time dip 02:00-04:00
       - Temperature follows a sine wave peaking ~14:00
       - Humidity inverse to temperature (warm air → drier)

5. Weekend effect: Sat/Sun traffic impact reduced 40 % vs weekdays.

6. Rare anomalies (~1 in 10 000 ticks per sensor):
       - Pollution spike 1.5–2.5× lasting 2–6 ticks (mô phỏng cháy, kẹt xe)
       - Then smoothly returns to baseline via the EWMA.

7. Inter-metric correlation:
       - Traffic factor multiplies CO2 + PM2.5 + Noise together
       - Sun curve drives Temperature & inversely Humidity

8. Boundary clamping: every metric stays inside physically-plausible range.
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
from typing import Dict, List

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

# Anomaly rate (per sensor per tick). 33 sensors × 720 ticks/hour
# ≈ ~2.4 anomalies/hour at this rate — rare enough to be plausible.
ANOMALY_PROBABILITY = 1 / 10000


# ============================================================================
# Per-sensor mutable state
# ============================================================================

@dataclass
class SensorState:
    sensor_id: str
    location_id: str
    profile: Dict[str, float]

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
    anomaly_ticks_left: int = 0
    anomaly_factor: float = 1.0

    def __post_init__(self):
        # Initialise current values to the profile baseline so the first
        # publish already looks plausible (not zero or extreme).
        p = self.profile
        self.co2 = p['co2']
        self.noise = p['noise']
        self.temperature = p['temp']
        self.pm25 = p['pm25']
        self.humidity = p['hum']


# ============================================================================
# Realism math
# ============================================================================

def compute_targets(profile: Dict[str, float], ts: datetime) -> Dict[str, float]:
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

    return {
        'co2':   profile['co2']   + rush * 350 * weekend_mult * traffic - night * 80,
        'noise': profile['noise'] + rush * 22  * weekend_mult * traffic - night * 18,
        'pm25':  profile['pm25']  + rush * 45  * weekend_mult * traffic - night * 10,
        'temp':  profile['temp']  + 4 * sun,
        'hum':   profile['hum']   - 12 * sun,
    }


def step_state(state: SensorState, ts: datetime) -> None:
    """
    Advance a sensor's state by one tick. Called every PUBLISH_INTERVAL seconds.
    Mutates `state` in place.
    """
    # ── Anomaly trigger ──
    if state.anomaly_ticks_left == 0 and random.random() < ANOMALY_PROBABILITY:
        state.anomaly_ticks_left = random.randint(2, 6)
        state.anomaly_factor = random.uniform(1.5, 2.5)
        logger.info(
            f"⚡ Anomaly on {state.sensor_id}: ×{state.anomaly_factor:.2f} "
            f"for {state.anomaly_ticks_left} ticks"
        )

    targets = compute_targets(state.profile, ts)

    # Apply anomaly to traffic-correlated pollutants only.
    if state.anomaly_ticks_left > 0:
        targets['co2']   *= state.anomaly_factor
        targets['noise'] *= state.anomaly_factor
        targets['pm25']  *= state.anomaly_factor
        state.anomaly_ticks_left -= 1

    # ── EWMA smoothing + small Gaussian sensor noise ──
    α = EWMA_ALPHA
    state.co2         = α * state.co2         + (1 - α) * targets['co2']   + random.gauss(0, 5.0)
    state.noise       = α * state.noise       + (1 - α) * targets['noise'] + random.gauss(0, 1.0)
    state.temperature = α * state.temperature + (1 - α) * targets['temp']  + random.gauss(0, 0.2)
    state.pm25        = α * state.pm25        + (1 - α) * targets['pm25']  + random.gauss(0, 1.0)
    state.humidity    = α * state.humidity    + (1 - α) * targets['hum']   + random.gauss(0, 0.5)

    # ── Boundary clamping (physical plausibility) ──
    state.co2 = max(300.0, min(2500.0, state.co2))
    state.noise = max(30.0, min(110.0, state.noise))
    state.temperature = max(15.0, min(40.0, state.temperature))
    state.pm25 = max(5.0, min(250.0, state.pm25))
    state.humidity = max(30.0, min(98.0, state.humidity))

    # ── Device health ──
    # Battery slowly discharges (about 1% / 50 min at 5s tick); recharges
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
                logger.info(
                    f"{sensor_id} ({telemetry['locationId']}): "
                    f"CO2={d['co2']:.0f} | PM2.5={d['pm25']:.1f} | "
                    f"Noise={d['noise']:.1f} | T={d['temperature']:.1f}°C | "
                    f"H={d['humidity']:.0f}%"
                )
            else:
                logger.error(f"Publish failed rc={result.rc} on {topic}")
        except Exception as e:
            logger.error(f"Publish error: {e}")

    def run(self):
        logger.info(f"Starting simulator: {len(self.sensor_ids)} sensors, "
                    f"interval={self.publish_interval}s, α={EWMA_ALPHA}")
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
