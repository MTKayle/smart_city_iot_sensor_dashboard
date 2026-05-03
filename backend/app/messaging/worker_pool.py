"""
Telemetry Worker Pool for Smart City IoT Dashboard.

Uses **Redis Streams** as the durable message queue instead of in-memory
``asyncio.Queue``.  This gives us:

┌──────────────────────────────────────────────────────────────────────┐
│  asyncio.Queue (old)              │  Redis Stream (new)             │
├───────────────────────────────────┼─────────────────────────────────┤
│  In-memory only                   │  Persisted (AOF / RDB)          │
│  Lost on crash / restart          │  Survives crash / restart       │
│  Single-process only              │  Multi-process / multi-node     │
│  No consumer groups               │  Consumer groups + XACK         │
│  No observability                 │  XINFO / XLEN / XPENDING       │
│  Queue full → drop                │  MAXLEN trim + oldest eviction  │
└───────────────────────────────────┴─────────────────────────────────┘

Architecture
────────────
    MQTT Consumer (paho-mqtt thread)
         │ validate + XADD
         ▼
    Redis Stream  «telemetry:stream»  (MAXLEN ~10 000)
         │ XREADGROUP (consumer group «workers»)
         ▼
    Worker Pool (N async workers, default 3)
         │ collect batch (100 msgs OR 1 s)
         │ enrich via Oracle (thread-pool)
         ▼
    ┌────┴─────────────┐
    │  parallel fan-out │  ← asyncio.gather()
    ├──────────────────┤
    │ MongoDB Batch     │  ← enriched docs
    │ Alert Engine      │  ← threshold / predictive / anomaly → Oracle → WS
    │ WebSocket Bcast   │  ← enriched telemetry (no MongoDB round-trip)
    └──────────────────┘
         │ XACK (message acknowledged)
         ▼
       Done

Validates: FR4.1–FR4.5, FR5.1–FR5.4, NFR1.2, NFR1.3, NFR3.3
"""

import asyncio
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple

import redis

from app.models import Telemetry, TelemetryData, GeoLocation, DataQuality
from app.db.mongodb_client import get_mongodb_client
from app.db.oracle_client import get_oracle_client
from app.services.alert_service import get_alert_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
REDIS_URL             = os.getenv("REDIS_URL", "redis://redis:6379/0")
STREAM_KEY            = "telemetry:stream"
CONSUMER_GROUP        = "workers"
DEFAULT_WORKERS       = 3
DEFAULT_BATCH_SIZE    = 100
DEFAULT_BATCH_TIMEOUT = 1000      # milliseconds (for XREADGROUP BLOCK)
STREAM_MAXLEN         = 10_000    # Redis auto-trims oldest entries
TELEMETRY_TTL_DAYS    = 30

# Thread-pool shared by all workers for blocking I/O
_io_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="worker-io")


# ─────────────────────────────────────────────────────────────────────────────
# Enrichment helper (sync — runs inside executor)
# ─────────────────────────────────────────────────────────────────────────────

def _enrich_telemetry(
    raw: Telemetry,
    oracle_client=None,
) -> Telemetry:
    """
    Enrich raw telemetry with geolocation from Oracle SENSOR_REGISTRY.

    Mirrors ``telemetry_service.enrich_telemetry_with_geolocation`` but is
    self-contained so workers don't depend on the TelemetryService singleton.
    """
    if oracle_client is None:
        oracle_client = get_oracle_client()

    try:
        geo_info = oracle_client.get_sensor_geolocation(raw.sensorId)
    except Exception as exc:
        logger.error(f"[enrich] Oracle lookup failed for '{raw.sensorId}': {exc}")
        geo_info = None

    if geo_info is None:
        return raw  # pass through un-enriched

    lat = geo_info["latitude"]
    lng = geo_info["longitude"]
    cluster_id = geo_info.get("clusterId") or raw.clusterId
    location_id = geo_info.get("locationId") or raw.locationId

    geo_location = GeoLocation(type="Point", coordinates=[lng, lat])
    received_at = raw.receivedAt or datetime.now(timezone.utc)
    expire_at = received_at + timedelta(days=TELEMETRY_TTL_DAYS)

    return Telemetry(
        sensorId=raw.sensorId,
        locationId=location_id,
        clusterId=cluster_id,
        data=raw.data,
        location=geo_location,
        quality=raw.quality,
        timestamp=raw.timestamp,
        receivedAt=received_at,
        expireAt=expire_at,
    )


def _validate_telemetry(t: Telemetry) -> bool:
    """Quick pre-storage validation."""
    if not t.sensorId or not t.locationId:
        return False
    if not t.location or len(t.location.coordinates) != 2:
        return False
    d = t.data
    if not any(v is not None for v in [d.co2, d.noise, d.temperature, d.pm25, d.humidity]):
        return False
    if t.expireAt is None:
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# TelemetryPipeline — Redis Streams Edition
# ─────────────────────────────────────────────────────────────────────────────

class TelemetryPipeline:
    """
    Durable async pipeline backed by **Redis Streams**.

    Producer side (MQTT thread):
        ``enqueue(telemetry)`` → ``XADD telemetry:stream MAXLEN ~10000 * payload …``

    Consumer side (async workers):
        ``XREADGROUP GROUP workers consumer-{i} COUNT {batch_size} BLOCK {timeout}``
        → enrich → fan-out (Mongo + Alerts + WS) → ``XACK``

    Durability guarantees:
    • Messages survive process crash (Redis AOF / RDB)
    • Unacknowledged messages are re-delivered via ``XREADGROUP … 0`` on restart
    • ``MAXLEN ~10000`` caps memory; oldest messages trimmed when limit exceeded
    """

    def __init__(
        self,
        websocket_manager=None,
        num_workers: int = DEFAULT_WORKERS,
        batch_size: int = DEFAULT_BATCH_SIZE,
        batch_timeout_ms: int = DEFAULT_BATCH_TIMEOUT,
        redis_url: str = REDIS_URL,
    ):
        self.websocket_manager = websocket_manager
        self.num_workers = num_workers
        self.batch_size = batch_size
        self.batch_timeout_ms = batch_timeout_ms

        # Redis connection (sync client — thread-safe for producer)
        self._redis: redis.Redis = redis.from_url(
            redis_url, decode_responses=True
        )
        self._stream = STREAM_KEY
        self._group = CONSUMER_GROUP

        self._workers: List[asyncio.Task] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False

        # Lazy service init
        self._mongodb_client = None
        self._oracle_client = None
        self._alert_service = None

        # Metrics
        self.metrics = {
            "enqueued": 0,
            "dropped": 0,
            "processed": 0,
            "batches": 0,
            "mongo_inserts": 0,
            "alerts_created": 0,
            "ws_broadcasts": 0,
            "acked": 0,
            "redelivered": 0,
        }

        # Ensure consumer group exists
        self._ensure_consumer_group()

        logger.info(
            f"TelemetryPipeline (Redis Streams) created — "
            f"workers={num_workers}, batch={batch_size}/{batch_timeout_ms}ms, "
            f"stream={self._stream}, group={self._group}"
        )

    # ── lazy service accessors ───────────────────────────────────────────

    @property
    def mongodb_client(self):
        if self._mongodb_client is None:
            self._mongodb_client = get_mongodb_client()
        return self._mongodb_client

    @property
    def oracle_client(self):
        if self._oracle_client is None:
            self._oracle_client = get_oracle_client()
        return self._oracle_client

    @property
    def alert_service(self):
        if self._alert_service is None:
            self._alert_service = get_alert_service(self.websocket_manager)
        return self._alert_service

    # ── Redis Stream setup ───────────────────────────────────────────────

    def _ensure_consumer_group(self):
        """Create consumer group if it does not already exist."""
        try:
            self._redis.xgroup_create(
                self._stream, self._group, id="0", mkstream=True
            )
            logger.info(
                f"Created consumer group '{self._group}' on stream '{self._stream}'"
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group '{self._group}' already exists")
            else:
                raise

    # ── lifecycle ────────────────────────────────────────────────────────

    async def start(self):
        """Spawn worker tasks on the running event loop."""
        self._loop = asyncio.get_running_loop()
        self._running = True

        # First, re-deliver any pending (unacknowledged) messages
        await self._recover_pending()

        for i in range(self.num_workers):
            consumer_name = f"consumer-{i}"
            task = asyncio.create_task(
                self._worker(i, consumer_name), name=f"worker-{i}"
            )
            self._workers.append(task)
        logger.info(f"TelemetryPipeline started — {self.num_workers} workers")

    async def stop(self):
        """Cancel workers and let pending messages be re-delivered on restart."""
        self._running = False
        for t in self._workers:
            t.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("TelemetryPipeline stopped")

    # ── enqueue (thread-safe, sync) ──────────────────────────────────────

    def enqueue(self, telemetry: Telemetry):
        """
        Called from the MQTT consumer thread.

        Serializes the Telemetry to JSON and pushes to Redis Stream via XADD.
        Thread-safe — ``redis-py`` handles connection locking internally.

        MAXLEN ~10000 auto-trims oldest entries if the stream grows too large,
        providing natural backpressure without message loss in normal operation.
        """
        try:
            payload = telemetry.model_dump(mode="json")
            self._redis.xadd(
                self._stream,
                {"payload": json.dumps(payload)},
                maxlen=STREAM_MAXLEN,
                approximate=True,
            )
            self.metrics["enqueued"] += 1
        except redis.RedisError as exc:
            self.metrics["dropped"] += 1
            logger.error(f"[enqueue] Redis XADD failed: {exc}")
        except Exception as exc:
            self.metrics["dropped"] += 1
            logger.error(f"[enqueue] serialization failed: {exc}")

    # ── pending recovery ─────────────────────────────────────────────────

    async def _recover_pending(self):
        """
        On startup, re-process messages that were delivered but never ACKed
        (e.g. due to a crash).  Uses ``XREADGROUP … 0`` to get pending entries.
        """
        loop = asyncio.get_running_loop()
        try:
            entries = await loop.run_in_executor(
                _io_executor,
                lambda: self._redis.xreadgroup(
                    self._group,
                    "recovery",
                    {self._stream: "0"},  # "0" = all pending entries
                    count=self.batch_size * 3,
                ),
            )
            if entries:
                for stream_name, messages in entries:
                    if messages:
                        batch, msg_ids = self._deserialize_messages(messages)
                        if batch:
                            self.metrics["redelivered"] += len(batch)
                            logger.info(
                                f"[recovery] re-processing {len(batch)} pending messages"
                            )
                            await self._process_and_ack(batch, msg_ids, -1)
        except Exception as exc:
            logger.error(f"[recovery] failed: {exc}")

    # ── worker ───────────────────────────────────────────────────────────

    async def _worker(self, worker_id: int, consumer_name: str):
        """
        Long-running async task that:
        1. XREADGROUP — blocks up to *batch_timeout_ms* for new messages
        2. Deserializes JSON payloads → Telemetry objects
        3. Enriches via Oracle (thread-pool)
        4. Fan-out: MongoDB + Alerts + WebSocket (parallel)
        5. XACK — acknowledges processed messages
        """
        logger.info(f"[worker-{worker_id}] started (consumer={consumer_name})")
        loop = asyncio.get_running_loop()

        while self._running:
            try:
                # ── Step 1: XREADGROUP (blocking read from Redis) ────────
                entries = await loop.run_in_executor(
                    _io_executor,
                    lambda: self._redis.xreadgroup(
                        self._group,
                        consumer_name,
                        {self._stream: ">"},  # ">" = only new messages
                        count=self.batch_size,
                        block=self.batch_timeout_ms,
                    ),
                )

                if not entries:
                    continue  # timeout — no new messages

                # ── Step 2: Deserialize ──────────────────────────────────
                for stream_name, messages in entries:
                    if not messages:
                        continue

                    batch, msg_ids = self._deserialize_messages(messages)
                    if not batch:
                        # ACK messages we couldn't parse
                        await self._ack(msg_ids)
                        continue

                    self.metrics["batches"] += 1
                    await self._process_and_ack(batch, msg_ids, worker_id)

            except asyncio.CancelledError:
                logger.info(f"[worker-{worker_id}] cancelled")
                break
            except redis.RedisError as exc:
                logger.error(f"[worker-{worker_id}] Redis error: {exc}")
                await asyncio.sleep(1)  # back off
            except Exception as exc:
                logger.error(
                    f"[worker-{worker_id}] unhandled error: {exc}",
                    exc_info=True,
                )
                await asyncio.sleep(0.5)

    # ── process + ack ────────────────────────────────────────────────────

    async def _process_and_ack(
        self,
        batch: List[Telemetry],
        msg_ids: List[str],
        worker_id: int,
    ):
        """Enrich → validate → parallel fan-out → XACK."""
        t0 = time.monotonic()

        # ── Enrich (blocking Oracle I/O → executor) ──────────────────
        enriched = await self._enrich_batch(batch)

        # ── Validate ─────────────────────────────────────────────────
        valid = [t for t in enriched if _validate_telemetry(t)]
        if not valid:
            await self._ack(msg_ids)
            return

        # ── Parallel fan-out ─────────────────────────────────────────
        await asyncio.gather(
            self._branch_mongo(valid, worker_id),
            self._branch_alerts(valid, worker_id),
            self._branch_broadcast(valid, worker_id),
        )

        # ── ACK — all messages successfully processed ────────────────
        await self._ack(msg_ids)

        elapsed = (time.monotonic() - t0) * 1000
        self.metrics["processed"] += len(valid)
        logger.info(
            f"[worker-{worker_id}] batch={len(valid)} "
            f"elapsed={elapsed:.0f}ms "
            f"stream_len={self._redis.xlen(self._stream)}"
        )

    # ── deserialization ──────────────────────────────────────────────────

    def _deserialize_messages(
        self, messages: List[Tuple[str, dict]]
    ) -> Tuple[List[Telemetry], List[str]]:
        """Deserialize Redis stream messages → (Telemetry list, message ID list)."""
        batch: List[Telemetry] = []
        msg_ids: List[str] = []

        for msg_id, fields in messages:
            msg_ids.append(msg_id)
            try:
                payload = json.loads(fields.get("payload", "{}"))
                telemetry = Telemetry(**payload)
                batch.append(telemetry)
            except Exception as exc:
                logger.warning(f"[deserialize] skipped msg {msg_id}: {exc}")

        return batch, msg_ids

    # ── XACK ─────────────────────────────────────────────────────────────

    async def _ack(self, msg_ids: List[str]):
        """Acknowledge messages in Redis (removes from pending list)."""
        if not msg_ids:
            return
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                _io_executor,
                lambda: self._redis.xack(self._stream, self._group, *msg_ids),
            )
            self.metrics["acked"] += len(msg_ids)
        except Exception as exc:
            logger.error(f"[ack] failed for {len(msg_ids)} messages: {exc}")

    # ── enrichment ───────────────────────────────────────────────────────

    async def _enrich_batch(self, batch: List[Telemetry]) -> List[Telemetry]:
        """Enrich each telemetry in a thread-pool (Oracle is blocking)."""
        loop = asyncio.get_running_loop()
        oracle = self.oracle_client

        async def _enrich_one(t: Telemetry) -> Telemetry:
            return await loop.run_in_executor(
                _io_executor, _enrich_telemetry, t, oracle
            )

        results = await asyncio.gather(
            *[_enrich_one(t) for t in batch], return_exceptions=True
        )

        enriched = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"[enrich] failed: {r}")
            else:
                enriched.append(r)
        return enriched

    # ── Branch A: MongoDB batch insert ───────────────────────────────────

    async def _branch_mongo(self, batch: List[Telemetry], worker_id: int):
        """Insert enriched telemetry into MongoDB (blocking → executor)."""
        loop = asyncio.get_running_loop()
        mongo = self.mongodb_client
        try:
            result = await loop.run_in_executor(
                _io_executor,
                mongo.batch_insert_telemetry,
                batch,
            )
            self.metrics["mongo_inserts"] += result.inserted
            if result.errors > 0:
                logger.warning(
                    f"[worker-{worker_id}][mongo] "
                    f"inserted={result.inserted} dupes={result.duplicates} "
                    f"errors={result.errors}"
                )
        except Exception as exc:
            logger.error(f"[worker-{worker_id}][mongo] batch insert failed: {exc}")

    # ── Branch B: Alert engine ───────────────────────────────────────────

    async def _branch_alerts(self, batch: List[Telemetry], worker_id: int):
        """Run threshold / predictive / anomaly checks for each item."""
        loop = asyncio.get_running_loop()
        alert_svc = self.alert_service

        def _check_alerts_sync(t: Telemetry):
            """Run all alert checks synchronously (Oracle / MongoDB I/O)."""
            data = t.data
            metrics = {
                "CO2": data.co2,
                "Noise": data.noise,
                "PM25": data.pm25,
                "Humidity": data.humidity,
            }
            alerts_created = 0
            for metric_type, value in metrics.items():
                if value is None:
                    continue

                # Threshold
                try:
                    a = alert_svc.check_threshold_alerts(
                        sensor_id=t.sensorId,
                        location_id=t.locationId,
                        metric_type=metric_type,
                        value=value,
                        cluster_id=t.clusterId,
                        timestamp=t.timestamp,
                    )
                    if a:
                        alerts_created += 1
                except Exception as e:
                    logger.debug(f"[alerts] threshold {metric_type}: {e}")

                # Predictive
                try:
                    a = alert_svc.check_predictive_alerts(
                        sensor_id=t.sensorId,
                        location_id=t.locationId,
                        metric_type=metric_type,
                        cluster_id=t.clusterId,
                        timestamp=t.timestamp,
                    )
                    if a:
                        alerts_created += 1
                except Exception as e:
                    logger.debug(f"[alerts] predictive {metric_type}: {e}")

                # Anomaly
                try:
                    a = alert_svc.detect_anomalies(
                        sensor_id=t.sensorId,
                        location_id=t.locationId,
                        metric_type=metric_type,
                        current_value=value,
                        cluster_id=t.clusterId,
                        timestamp=t.timestamp,
                    )
                    if a:
                        alerts_created += 1
                except Exception as e:
                    logger.debug(f"[alerts] anomaly {metric_type}: {e}")

            return alerts_created

        try:
            futures = [
                loop.run_in_executor(_io_executor, _check_alerts_sync, t)
                for t in batch
            ]
            results = await asyncio.gather(*futures, return_exceptions=True)
            total = sum(r for r in results if isinstance(r, int))
            self.metrics["alerts_created"] += total
        except Exception as exc:
            logger.error(f"[worker-{worker_id}][alerts] error: {exc}")

    # ── Branch C: WebSocket broadcast ────────────────────────────────────

    async def _branch_broadcast(self, batch: List[Telemetry], worker_id: int):
        """
        Broadcast enriched telemetry to WebSocket clients immediately.
        Does NOT wait for MongoDB — data comes from in-memory enriched objects.
        """
        if not self.websocket_manager:
            return

        for t in batch:
            try:
                message = {
                    "type": "telemetry",
                    "data": t.model_dump(mode="json"),
                }
                self.websocket_manager.broadcast(message)
                self.metrics["ws_broadcasts"] += 1
            except Exception as exc:
                logger.error(
                    f"[worker-{worker_id}][ws] broadcast failed for "
                    f"sensor '{t.sensorId}': {exc}"
                )

    # ── public helpers ───────────────────────────────────────────────────

    def set_websocket_manager(self, ws_manager):
        """Attach/update WebSocket manager at runtime."""
        self.websocket_manager = ws_manager
        if self._alert_service:
            self._alert_service.set_websocket_manager(ws_manager)
        logger.info("WebSocket manager configured for TelemetryPipeline")

    def get_queue_size(self) -> int:
        """Current stream length."""
        try:
            return self._redis.xlen(self._stream)
        except Exception:
            return -1

    def get_metrics(self) -> Dict[str, Any]:
        """Return pipeline metrics snapshot."""
        pending = 0
        try:
            info = self._redis.xpending(self._stream, self._group)
            pending = info.get("pending", 0) if isinstance(info, dict) else 0
        except Exception:
            pass

        return {
            **self.metrics,
            "stream_length": self.get_queue_size(),
            "pending_messages": pending,
            "workers_active": sum(1 for t in self._workers if not t.done()),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_pipeline: Optional[TelemetryPipeline] = None


def get_telemetry_pipeline(
    websocket_manager=None,
    num_workers: int = DEFAULT_WORKERS,
) -> TelemetryPipeline:
    """Get or create the singleton TelemetryPipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = TelemetryPipeline(
            websocket_manager=websocket_manager,
            num_workers=num_workers,
        )
    elif websocket_manager and not _pipeline.websocket_manager:
        _pipeline.set_websocket_manager(websocket_manager)
    return _pipeline
