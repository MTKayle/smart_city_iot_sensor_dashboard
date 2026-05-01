# 🏗️ SMART CITY IOT - PRODUCTION DATA FLOW DESIGN

**Architecture Redesign - No Kafka**  
**Date:** May 2, 2026  
**System:** Smart City Environmental Monitoring Dashboard

---

## 📋 EXECUTIVE SUMMARY

### Current Problem
```
IoT → MQTT → Backend (sync) → MongoDB + Oracle + WebSocket
                ↓
         BLOCKING, NO RETRY, NO FAULT TOLERANCE
```

### New Architecture
```
IoT → MQTT → Consumer → AsyncQueue → Worker Pool → Storage
                           ↓                ↓
                      (in-memory)    (MongoDB/Oracle)
                                            ↓
                                       WebSocket
```

**Key Improvements:**
- ✅ Non-blocking ingestion
- ✅ Async processing with workers
- ✅ Retry mechanism
- ✅ Batch insert optimization
- ✅ Fault tolerance
- ✅ Scalable (multiple workers)

---

## 1️⃣ KIẾN TRÚC TỔNG THỂ

### Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER                              │
│  ┌──────────────┐         ┌──────────────┐                         │
│  │ MQTT Consumer│────────>│ AsyncQueue   │                         │
│  │ (Paho MQTT)  │         │ (asyncio)    │                         │
│  └──────────────┘         └──────────────┘                         │
│       ↓                          ↓                                  │
│   Subscribe                  Enqueue                                │
│   QoS=1                      Non-blocking                           │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       PROCESSING LAYER                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │  Worker 1    │    │  Worker 2    │    │  Worker N    │         │
│  │  (asyncio)   │    │  (asyncio)   │    │  (asyncio)   │         │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘         │
│         │                   │                   │                  │
│         └───────────────────┴───────────────────┘                  │
│                             ↓                                       │
│                    ┌─────────────────┐                             │
│                    │  Alert Engine   │                             │
│                    │  (Threshold +   │                             │
│                    │   Predictive)   │                             │
│                    └─────────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                                │
│  ┌──────────────┐                    ┌──────────────┐             │
│  │   MongoDB    │                    │  Oracle SQL  │             │
│  │  (Telemetry) │                    │  (Metadata)  │             │
│  │              │                    │              │             │
│  │  • Batch     │                    │  • Alerts    │             │
│  │    insert    │                    │  • Summary   │             │
│  │  • TTL 30d   │                    │  • Sensors   │             │
│  └──────────────┘                    └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       DELIVERY LAYER                                │
│  ┌──────────────┐                    ┌──────────────┐             │
│  │  WebSocket   │                    │  REST API    │             │
│  │  (Realtime)  │                    │  (Query)     │             │
│  └──────────────┘                    └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **MQTT Consumer** | Subscribe to MQTT, validate, enqueue | Paho MQTT + asyncio |
| **AsyncQueue** | In-memory buffer, backpressure | asyncio.Queue |
| **Worker Pool** | Process messages, batch insert | asyncio tasks |
| **Alert Engine** | Detect thresholds, anomalies | Python logic |
| **MongoDB Client** | Batch insert telemetry | Motor (async) |
| **Oracle Client** | Insert alerts, summaries | cx_Oracle |
| **WebSocket Manager** | Broadcast updates | FastAPI WebSocket |

---

## 2️⃣ DATA INGESTION FLOW

### MQTT Configuration

#### QoS Level Selection

```python
# MQTT QoS Levels:
# QoS 0: At most once (fire and forget) - NO GUARANTEE
# QoS 1: At least once (acknowledged) - RECOMMENDED ✅
# QoS 2: Exactly once (4-way handshake) - OVERKILL

MQTT_QOS = 1  # At least once delivery
```

**Why QoS 1?**
- ✅ Guaranteed delivery (broker acknowledges)
- ✅ Acceptable for telemetry (duplicates handled)
- ✅ Lower overhead than QoS 2
- ❌ QoS 0: Too risky (data loss)
- ❌ QoS 2: Too slow (unnecessary for telemetry)

**Duplicate Handling:**
```python
# Deduplication strategy
seen_messages = {}  # {message_id: timestamp}

def is_duplicate(message_id: str) -> bool:
    """Check if message already processed in last 60 seconds."""
    if message_id in seen_messages:
        age = time.time() - seen_messages[message_id]
        if age < 60:  # 60 second window
            return True
    seen_messages[message_id] = time.time()
    return False
```

### Message Format

```json
{
  "messageId": "msg_1714567890_sen_q1_01",
  "sensorId": "sen_q1_01_combo",
  "locationId": "ward_q1_01",
  "timestamp": "2026-05-02T10:30:00.000Z",
  "data": {
    "co2": 450.5,
    "noise": 65.2,
    "temperature": 25.3,
    "pm25": 35.8,
    "humidity": 68.5
  },
  "metadata": {
    "firmwareVersion": "1.2.3",
    "batteryLevel": 87,
    "signalStrength": -45
  }
}
```

**Message ID Format:**
```
msg_{unix_timestamp}_{sensor_id}
```

### Fault Handling

#### 1. MQTT Disconnect

```python
class MQTTConsumer:
    def __init__(self):
        self.reconnect_delay = 1  # seconds
        self.max_reconnect_delay = 60
        self.reconnect_attempts = 0
    
    def on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection with exponential backoff."""
        if rc != 0:
            logger.warning(f"Unexpected disconnect: {rc}")
            self._reconnect_with_backoff()
    
    def _reconnect_with_backoff(self):
        """Exponential backoff: 1s, 2s, 4s, 8s, ..., 60s max."""
        self.reconnect_attempts += 1
        
        logger.info(f"Reconnect attempt #{self.reconnect_attempts} "
                   f"in {self.reconnect_delay}s")
        
        time.sleep(self.reconnect_delay)
        
        try:
            self.client.reconnect()
            self.reconnect_delay = 1  # Reset on success
            self.reconnect_attempts = 0
        except Exception as e:
            logger.error(f"Reconnect failed: {e}")
            # Exponential backoff
            self.reconnect_delay = min(
                self.reconnect_delay * 2, 
                self.max_reconnect_delay
            )
```

**What happens to messages during disconnect?**
- ✅ MQTT broker buffers messages (if QoS > 0)
- ✅ Consumer receives buffered messages on reconnect
- ✅ Clean session = False (persistent session)

```python
client = mqtt.Client(
    client_id="backend_consumer",
    clean_session=False  # Persistent session
)
```

#### 2. Backend Restart

**Problem:** In-memory queue lost on restart

**Solution:** Graceful shutdown

```python
import signal
import asyncio

class GracefulShutdown:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown_event.set()
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()

# Usage
shutdown = GracefulShutdown()

async def main():
    # Start consumer and workers
    consumer_task = asyncio.create_task(mqtt_consumer.run())
    worker_tasks = [asyncio.create_task(worker.run()) for _ in range(3)]
    
    # Wait for shutdown signal
    await shutdown.wait_for_shutdown()
    
    # Graceful shutdown
    logger.info("Draining queue...")
    await queue.join()  # Wait for all items processed
    
    logger.info("Stopping workers...")
    for task in worker_tasks:
        task.cancel()
    
    logger.info("Disconnecting MQTT...")
    mqtt_consumer.disconnect()
    
    logger.info("Shutdown complete")
```

**What happens:**
1. Signal received (Ctrl+C or Docker stop)
2. Stop accepting new messages
3. Process remaining queue items
4. Disconnect MQTT cleanly
5. Exit

**Data loss window:** ~5-10 seconds (messages in flight)

#### 3. Duplicate Messages

**Causes:**
- QoS 1 retry
- Network issues
- Backend restart

**Solution:** Idempotency

```python
# Option 1: Message ID tracking (in-memory)
recent_messages = TTLCache(maxsize=10000, ttl=60)

def is_duplicate(message_id: str) -> bool:
    if message_id in recent_messages:
        return True
    recent_messages[message_id] = True
    return False

# Option 2: MongoDB unique index (persistent)
# Create unique index on (sensorId, timestamp)
db.telemetry.create_index(
    [("sensorId", 1), ("timestamp", 1)],
    unique=True
)

# Insert with duplicate handling
try:
    await db.telemetry.insert_one(document)
except DuplicateKeyError:
    logger.debug(f"Duplicate message: {message_id}")
    # Silently ignore
```

**Recommendation:** Use MongoDB unique index (persistent, reliable)



---

## 3️⃣ PROCESSING LAYER (AsyncIO Queue)

### Architecture Choice

**Options Considered:**

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **asyncio.Queue** | Simple, no dependencies, fast | Lost on restart | ✅ **RECOMMENDED** |
| **Redis Queue** | Persistent, distributed | Extra dependency, complexity | Optional upgrade |
| **RabbitMQ** | Full-featured, persistent | Overkill for project | ❌ Too complex |
| **Celery** | Task queue, retry | Heavy, Redis/RabbitMQ needed | ❌ Overkill |

**Decision:** Start with `asyncio.Queue`, upgrade to Redis if needed

### AsyncIO Queue Implementation

```python
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class TelemetryQueue:
    """
    In-memory async queue for telemetry messages.
    
    Features:
    - Non-blocking enqueue
    - Backpressure handling
    - Metrics tracking
    """
    
    def __init__(self, maxsize: int = 10000):
        self.queue = asyncio.Queue(maxsize=maxsize)
        self.enqueued_count = 0
        self.dequeued_count = 0
        self.dropped_count = 0
    
    async def enqueue(self, message: Dict[str, Any], timeout: float = 1.0):
        """
        Enqueue message with timeout.
        
        Args:
            message: Telemetry message dict
            timeout: Max wait time if queue full
        
        Returns:
            bool: True if enqueued, False if dropped
        """
        try:
            await asyncio.wait_for(
                self.queue.put(message),
                timeout=timeout
            )
            self.enqueued_count += 1
            return True
        except asyncio.TimeoutError:
            # Queue full - drop message (backpressure)
            self.dropped_count += 1
            logger.warning(
                f"Queue full, dropped message. "
                f"Queue size: {self.queue.qsize()}"
            )
            return False
    
    async def dequeue(self) -> Dict[str, Any]:
        """
        Dequeue message (blocking).
        
        Returns:
            Message dict
        """
        message = await self.queue.get()
        self.dequeued_count += 1
        return message
    
    def task_done(self):
        """Mark task as done (for queue.join())."""
        self.queue.task_done()
    
    async def join(self):
        """Wait for all tasks to complete."""
        await self.queue.join()
    
    def qsize(self) -> int:
        """Current queue size."""
        return self.queue.qsize()
    
    def get_metrics(self) -> Dict[str, int]:
        """Get queue metrics."""
        return {
            "queue_size": self.qsize(),
            "enqueued_total": self.enqueued_count,
            "dequeued_total": self.dequeued_count,
            "dropped_total": self.dropped_count,
            "pending": self.enqueued_count - self.dequeued_count
        }
```

### Worker Pool

```python
import asyncio
from typing import List
import logging

logger = logging.getLogger(__name__)

class TelemetryWorker:
    """
    Async worker that processes telemetry messages.
    
    Features:
    - Batch processing
    - Retry mechanism
    - Error handling
    """
    
    def __init__(
        self,
        worker_id: int,
        queue: TelemetryQueue,
        batch_size: int = 100,
        batch_timeout: float = 1.0
    ):
        self.worker_id = worker_id
        self.queue = queue
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.processed_count = 0
        self.error_count = 0
        self.running = False
    
    async def run(self):
        """Main worker loop."""
        self.running = True
        logger.info(f"Worker {self.worker_id} started")
        
        batch = []
        last_flush = asyncio.get_event_loop().time()
        
        while self.running:
            try:
                # Dequeue with timeout for batch flushing
                try:
                    message = await asyncio.wait_for(
                        self.queue.dequeue(),
                        timeout=0.1  # 100ms
                    )
                    batch.append(message)
                except asyncio.TimeoutError:
                    # No message available, check if should flush
                    pass
                
                current_time = asyncio.get_event_loop().time()
                time_since_flush = current_time - last_flush
                
                # Flush batch if:
                # 1. Batch size reached
                # 2. Timeout reached and batch not empty
                should_flush = (
                    len(batch) >= self.batch_size or
                    (time_since_flush >= self.batch_timeout and len(batch) > 0)
                )
                
                if should_flush:
                    await self._process_batch(batch)
                    
                    # Mark tasks as done
                    for _ in batch:
                        self.queue.task_done()
                    
                    batch = []
                    last_flush = current_time
                
            except asyncio.CancelledError:
                logger.info(f"Worker {self.worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}", exc_info=True)
                self.error_count += 1
        
        # Flush remaining batch on shutdown
        if batch:
            await self._process_batch(batch)
            for _ in batch:
                self.queue.task_done()
        
        logger.info(f"Worker {self.worker_id} stopped")
    
    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """
        Process batch of messages.
        
        Steps:
        1. Insert to MongoDB (batch)
        2. Check alerts
        3. Broadcast to WebSocket
        """
        if not batch:
            return
        
        logger.debug(f"Worker {self.worker_id} processing batch of {len(batch)}")
        
        try:
            # Step 1: Batch insert to MongoDB
            await self._insert_mongodb_batch(batch)
            
            # Step 2: Check alerts (for each message)
            for message in batch:
                await self._check_alerts(message)
            
            # Step 3: Broadcast to WebSocket (sample, not all)
            if len(batch) > 0:
                # Broadcast first message as sample
                await self._broadcast_websocket(batch[0])
            
            self.processed_count += len(batch)
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}", exc_info=True)
            # Retry logic here
            await self._retry_batch(batch)
    
    async def _insert_mongodb_batch(self, batch: List[Dict[str, Any]]):
        """Insert batch to MongoDB."""
        from app.db.mongodb_client import get_mongodb_client
        
        mongo = get_mongodb_client()
        
        # Convert to MongoDB documents
        documents = []
        for msg in batch:
            doc = {
                "sensorId": msg["sensorId"],
                "locationId": msg["locationId"],
                "timestamp": msg["timestamp"],
                "data": msg["data"],
                "metadata": msg.get("metadata", {}),
                "expireAt": msg["timestamp"] + timedelta(days=30)
            }
            documents.append(doc)
        
        # Batch insert (ordered=False for partial success)
        try:
            result = await mongo.telemetry.insert_many(
                documents,
                ordered=False  # Continue on duplicate key errors
            )
            logger.debug(f"Inserted {len(result.inserted_ids)} documents")
        except BulkWriteError as e:
            # Some inserts failed (likely duplicates)
            inserted = e.details.get('nInserted', 0)
            logger.warning(f"Partial insert: {inserted}/{len(documents)}")
    
    async def _check_alerts(self, message: Dict[str, Any]):
        """Check if message triggers alerts."""
        from app.services.alert_engine import get_alert_engine
        
        alert_engine = get_alert_engine()
        alerts = await alert_engine.check_message(message)
        
        if alerts:
            logger.info(f"Generated {len(alerts)} alerts for {message['sensorId']}")
    
    async def _broadcast_websocket(self, message: Dict[str, Any]):
        """Broadcast message to WebSocket clients."""
        from app.core.websocket_manager import get_websocket_manager
        
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast({
            "type": "telemetry",
            "data": message
        })
    
    async def _retry_batch(self, batch: List[Dict[str, Any]], max_retries: int = 3):
        """Retry failed batch with exponential backoff."""
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
                await self._insert_mongodb_batch(batch)
                logger.info(f"Retry {attempt + 1} succeeded")
                return
            except Exception as e:
                logger.error(f"Retry {attempt + 1} failed: {e}")
        
        # All retries failed - log to dead letter
        logger.critical(f"Batch permanently failed after {max_retries} retries")
        # TODO: Write to dead letter file/table
    
    def stop(self):
        """Stop worker gracefully."""
        self.running = False
    
    def get_metrics(self) -> Dict[str, int]:
        """Get worker metrics."""
        return {
            "worker_id": self.worker_id,
            "processed_total": self.processed_count,
            "error_total": self.error_count
        }
```

### Worker Pool Manager

```python
class WorkerPool:
    """Manages multiple workers."""
    
    def __init__(self, queue: TelemetryQueue, num_workers: int = 3):
        self.queue = queue
        self.num_workers = num_workers
        self.workers: List[TelemetryWorker] = []
        self.tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Start all workers."""
        for i in range(self.num_workers):
            worker = TelemetryWorker(
                worker_id=i,
                queue=self.queue,
                batch_size=100,
                batch_timeout=1.0
            )
            self.workers.append(worker)
            
            task = asyncio.create_task(worker.run())
            self.tasks.append(task)
        
        logger.info(f"Started {self.num_workers} workers")
    
    async def stop(self):
        """Stop all workers gracefully."""
        logger.info("Stopping workers...")
        
        # Stop workers
        for worker in self.workers:
            worker.stop()
        
        # Cancel tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for completion
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("All workers stopped")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from all workers."""
        return {
            "num_workers": self.num_workers,
            "workers": [w.get_metrics() for w in self.workers]
        }
```

### Message Flow

```
MQTT Message
     ↓
Consumer validates
     ↓
queue.enqueue(message)  ← Non-blocking, timeout 1s
     ↓
[AsyncQueue - maxsize 10000]
     ↓
Worker.dequeue()  ← Blocking
     ↓
Batch accumulation (100 msgs or 1s timeout)
     ↓
_process_batch()
     ├─> MongoDB batch insert (ordered=False)
     ├─> Alert checking (per message)
     └─> WebSocket broadcast (sample)
     ↓
queue.task_done()
```

**Scalability:**
- Start with 3 workers
- Monitor queue size
- If queue consistently > 5000, add more workers
- Max workers = CPU cores * 2



---

## 4️⃣ STORAGE STRATEGY

### MongoDB Strategy

#### Batch Insert Configuration

```python
class MongoDBBatchWriter:
    """Optimized batch writer for MongoDB."""
    
    BATCH_SIZE = 100  # Documents per batch
    BATCH_TIMEOUT = 1.0  # Seconds
    
    async def insert_batch(self, documents: List[Dict]) -> int:
        """
        Insert batch with optimization.
        
        Returns:
            Number of documents inserted
        """
        if not documents:
            return 0
        
        try:
            # ordered=False: Continue on duplicate key errors
            # bypass_document_validation: Skip schema validation (faster)
            result = await self.collection.insert_many(
                documents,
                ordered=False,
                bypass_document_validation=False  # Keep validation for safety
            )
            return len(result.inserted_ids)
        
        except BulkWriteError as e:
            # Partial success
            inserted = e.details.get('nInserted', 0)
            duplicates = len([err for err in e.details.get('writeErrors', [])
                            if err['code'] == 11000])
            
            logger.info(f"Batch insert: {inserted} inserted, {duplicates} duplicates")
            return inserted
```

**Why 100 documents per batch?**
- ✅ Good balance between throughput and latency
- ✅ ~15KB per batch (150 bytes/doc * 100)
- ✅ Network efficient
- ❌ Too small (10): Too many round trips
- ❌ Too large (1000): High latency, memory pressure

**Performance:**
- Single insert: ~5ms per document = 200 docs/sec
- Batch insert (100): ~50ms per batch = 2000 docs/sec
- **10x improvement**

#### TTL Index

```python
# Create TTL index on expireAt field
db.telemetry.create_index(
    "expireAt",
    expireAfterSeconds=0  # Delete when expireAt < now
)

# Document structure
{
    "sensorId": "sen_q1_01",
    "timestamp": ISODate("2026-05-02T10:30:00Z"),
    "data": {...},
    "expireAt": ISODate("2026-06-01T10:30:00Z")  # 30 days later
}
```

**TTL Cleanup:**
- MongoDB checks every 60 seconds
- Deletes expired documents automatically
- No manual cleanup needed

#### MongoDB Down - Fault Tolerance

**Problem:** MongoDB unavailable

**Solution 1: Retry with Exponential Backoff**

```python
async def insert_with_retry(
    documents: List[Dict],
    max_retries: int = 3
) -> bool:
    """Insert with retry logic."""
    
    for attempt in range(max_retries):
        try:
            await mongo.telemetry.insert_many(documents, ordered=False)
            return True
        
        except ConnectionFailure as e:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            logger.warning(f"MongoDB down, retry {attempt + 1} in {wait_time}s")
            await asyncio.sleep(wait_time)
        
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            break
    
    return False
```

**Solution 2: Dead Letter Queue (File-based)**

```python
import json
from pathlib import Path
from datetime import datetime

class DeadLetterQueue:
    """File-based dead letter queue for failed inserts."""
    
    def __init__(self, directory: str = "./dead_letter"):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True)
    
    async def write(self, documents: List[Dict], reason: str):
        """Write failed batch to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"failed_batch_{timestamp}.json"
        filepath = self.directory / filename
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "count": len(documents),
            "documents": documents
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.warning(f"Wrote {len(documents)} docs to dead letter: {filename}")
    
    async def replay(self):
        """Replay dead letter files (manual recovery)."""
        for filepath in self.directory.glob("failed_batch_*.json"):
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            try:
                await mongo.telemetry.insert_many(
                    data['documents'],
                    ordered=False
                )
                logger.info(f"Replayed {filepath.name}")
                filepath.unlink()  # Delete after success
            except Exception as e:
                logger.error(f"Replay failed for {filepath.name}: {e}")
```

**Strategy:**
1. Try insert 3 times with backoff
2. If all fail → write to dead letter file
3. Manual replay later when MongoDB recovers

**Data loss:** Minimal (only messages during extended outage)

---

### Oracle Strategy

#### When to Insert

**1. ALERTS - Real-time**

```python
async def insert_alert(alert: Alert):
    """Insert alert immediately (not batched)."""
    
    # Alerts are critical - insert immediately
    try:
        oracle.execute(
            """
            INSERT INTO ALERTS (
                AlertID, SensorID, LocationID, AlertType,
                MetricType, Value, Threshold, Severity, Status, CreatedAt
            ) VALUES (
                :alert_id, :sensor_id, :location_id, :alert_type,
                :metric_type, :value, :threshold, :severity, :status, CURRENT_TIMESTAMP
            )
            """,
            alert.dict()
        )
        oracle.commit()
        
        logger.info(f"Alert inserted: {alert.alertId}")
        
    except IntegrityError as e:
        # Duplicate alert - ignore
        logger.debug(f"Duplicate alert: {alert.alertId}")
    except Exception as e:
        logger.error(f"Alert insert failed: {e}")
        # Retry or dead letter
```

**Why real-time?**
- ✅ Alerts are critical
- ✅ Low volume (~10-100 per minute)
- ✅ Need immediate notification

**2. TELEMETRY_SUMMARY - Batch (Hourly/Daily)**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour='*', minute=0)  # Every hour
async def aggregate_hourly():
    """Aggregate telemetry to Oracle (hourly)."""
    
    # Query MongoDB for last hour
    hour_start = datetime.now().replace(minute=0, second=0, microsecond=0)
    hour_end = hour_start + timedelta(hours=1)
    
    pipeline = [
        {
            "$match": {
                "timestamp": {"$gte": hour_start, "$lt": hour_end}
            }
        },
        {
            "$group": {
                "_id": "$sensorId",
                "avgCO2": {"$avg": "$data.co2"},
                "maxCO2": {"$max": "$data.co2"},
                "minCO2": {"$min": "$data.co2"},
                "avgNoise": {"$avg": "$data.noise"},
                "dataPoints": {"$sum": 1}
            }
        }
    ]
    
    results = await mongo.telemetry.aggregate(pipeline).to_list(None)
    
    # Insert to Oracle
    for result in results:
        oracle.execute(
            """
            MERGE INTO TELEMETRY_SUMMARY ts
            USING (SELECT :sensor_id as SensorID FROM DUAL) src
            ON (ts.SensorID = src.SensorID 
                AND ts.TimeBucket = :time_bucket 
                AND ts.Granularity = 'HOUR')
            WHEN MATCHED THEN
                UPDATE SET
                    AvgCO2 = :avg_co2,
                    MaxCO2 = :max_co2,
                    MinCO2 = :min_co2,
                    AvgNoise = :avg_noise,
                    DataPoints = :data_points
            WHEN NOT MATCHED THEN
                INSERT (SummaryID, SensorID, TimeBucket, Granularity, 
                        AvgCO2, MaxCO2, MinCO2, AvgNoise, DataPoints)
                VALUES (SYS_GUID(), :sensor_id, :time_bucket, 'HOUR',
                        :avg_co2, :max_co2, :min_co2, :avg_noise, :data_points)
            """,
            {
                "sensor_id": result["_id"],
                "time_bucket": hour_start,
                "avg_co2": result["avgCO2"],
                "max_co2": result["maxCO2"],
                "min_co2": result["minCO2"],
                "avg_noise": result["avgNoise"],
                "data_points": result["dataPoints"]
            }
        )
    
    oracle.commit()
    logger.info(f"Aggregated {len(results)} sensors for hour {hour_start}")
```

**Why batch?**
- ✅ Aggregations are not time-critical
- ✅ Reduces Oracle load
- ✅ More efficient (MERGE operation)

**Schedule:**
- Hourly: Every hour at :00
- Daily: Every day at 3:00 AM

#### Oracle Down - Fault Tolerance

**Problem:** Oracle unavailable

**Solution: Retry + Skip**

```python
async def insert_alert_with_fallback(alert: Alert):
    """Insert alert with fallback."""
    
    try:
        # Try Oracle
        await insert_alert_oracle(alert)
    
    except DatabaseError as e:
        logger.error(f"Oracle down: {e}")
        
        # Fallback: Store in MongoDB (temporary)
        await mongo.alerts_fallback.insert_one({
            "alertId": alert.alertId,
            "data": alert.dict(),
            "createdAt": datetime.now(),
            "synced": False
        })
        
        logger.warning(f"Alert stored in MongoDB fallback: {alert.alertId}")

# Background job to sync fallback alerts
@scheduler.scheduled_job('interval', minutes=5)
async def sync_fallback_alerts():
    """Sync fallback alerts to Oracle."""
    
    alerts = await mongo.alerts_fallback.find({"synced": False}).to_list(100)
    
    for alert_doc in alerts:
        try:
            await insert_alert_oracle(Alert(**alert_doc["data"]))
            
            # Mark as synced
            await mongo.alerts_fallback.update_one(
                {"_id": alert_doc["_id"]},
                {"$set": {"synced": True}}
            )
        except Exception as e:
            logger.error(f"Sync failed for {alert_doc['alertId']}: {e}")
```

**Strategy:**
1. Try Oracle insert
2. If fail → store in MongoDB fallback collection
3. Background job retries every 5 minutes
4. Mark as synced when successful

**Data loss:** None (fallback to MongoDB)

---

## 5️⃣ ALERT PROCESSING

### Alert Engine

```python
from typing import List, Optional
from app.models.alert import Alert
from app.db.mongodb_client import get_mongodb_client
from app.db.oracle_client import get_oracle_client

class AlertEngine:
    """
    Alert detection engine.
    
    Supports:
    - Threshold alerts
    - Predictive alerts (moving average)
    - Anomaly detection (Z-score)
    """
    
    # Thresholds
    THRESHOLDS = {
        'CO2': {'LOW': 800, 'MEDIUM': 1000, 'HIGH': 1500, 'CRITICAL': 2000},
        'Noise': {'LOW': 70, 'MEDIUM': 85, 'HIGH': 95, 'CRITICAL': 105},
        'PM2.5': {'LOW': 35, 'MEDIUM': 55, 'HIGH': 150, 'CRITICAL': 250}
    }
    
    def __init__(self):
        self.mongo = get_mongodb_client()
        self.oracle = get_oracle_client()
    
    async def check_message(self, message: Dict[str, Any]) -> List[Alert]:
        """
        Check message for alerts.
        
        Returns:
            List of generated alerts
        """
        alerts = []
        
        # 1. Threshold alerts
        threshold_alerts = await self._check_thresholds(message)
        alerts.extend(threshold_alerts)
        
        # 2. Predictive alerts
        predictive_alert = await self._check_predictive(message)
        if predictive_alert:
            alerts.append(predictive_alert)
        
        # 3. Anomaly detection
        anomaly_alert = await self._check_anomaly(message)
        if anomaly_alert:
            alerts.append(anomaly_alert)
        
        # Insert alerts to Oracle
        for alert in alerts:
            await self._insert_alert(alert)
        
        # Broadcast to WebSocket
        if alerts:
            await self._broadcast_alerts(alerts)
        
        return alerts
    
    async def _check_thresholds(self, message: Dict) -> List[Alert]:
        """Check threshold violations."""
        alerts = []
        data = message["data"]
        
        for metric, value in data.items():
            if metric.upper() not in self.THRESHOLDS:
                continue
            
            thresholds = self.THRESHOLDS[metric.upper()]
            severity = None
            threshold_value = None
            
            if value >= thresholds['CRITICAL']:
                severity = 'CRITICAL'
                threshold_value = thresholds['CRITICAL']
            elif value >= thresholds['HIGH']:
                severity = 'HIGH'
                threshold_value = thresholds['HIGH']
            elif value >= thresholds['MEDIUM']:
                severity = 'MEDIUM'
                threshold_value = thresholds['MEDIUM']
            
            if severity:
                alert = Alert(
                    alertId=f"alert_{uuid.uuid4().hex[:12]}",
                    sensorId=message["sensorId"],
                    locationId=message["locationId"],
                    alertType='THRESHOLD',
                    metricType=metric.upper(),
                    value=value,
                    threshold=threshold_value,
                    severity=severity,
                    status='OPEN',
                    message=f"{metric.upper()} level {value} exceeds {severity} threshold {threshold_value}"
                )
                alerts.append(alert)
        
        return alerts
    
    async def _check_predictive(self, message: Dict) -> Optional[Alert]:
        """
        Predictive alert using moving average trend.
        
        Algorithm:
        1. Get last 10 readings
        2. Calculate linear regression
        3. Predict next value
        4. Alert if predicted > threshold
        """
        sensor_id = message["sensorId"]
        
        # Get last 10 readings
        readings = await self.mongo.telemetry.find(
            {"sensorId": sensor_id},
            sort=[("timestamp", -1)],
            limit=10
        ).to_list(10)
        
        if len(readings) < 10:
            return None
        
        # Extract CO2 values
        co2_values = [r["data"]["co2"] for r in readings]
        
        # Simple linear regression
        n = len(co2_values)
        x = list(range(n))
        y = co2_values
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return None
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Predict next value (x = n)
        predicted = slope * n + intercept
        
        # R² score (confidence)
        ss_res = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Alert if predicted > HIGH threshold and confidence > 0.7
        if predicted >= self.THRESHOLDS['CO2']['HIGH'] and r_squared > 0.7:
            return Alert(
                alertId=f"alert_{uuid.uuid4().hex[:12]}",
                sensorId=sensor_id,
                locationId=message["locationId"],
                alertType='PREDICTIVE',
                metricType='CO2',
                value=co2_values[0],  # Current value
                threshold=self.THRESHOLDS['CO2']['HIGH'],
                predictedValue=predicted,
                confidenceScore=r_squared,
                severity='HIGH',
                status='OPEN',
                message=f"Predicted CO2 will reach {predicted:.1f} (confidence: {r_squared:.1%})"
            )
        
        return None
    
    async def _check_anomaly(self, message: Dict) -> Optional[Alert]:
        """
        Anomaly detection using Z-score.
        
        Algorithm:
        1. Get last 100 readings
        2. Calculate mean and std dev
        3. Calculate Z-score for current value
        4. Alert if |Z| > 3
        """
        sensor_id = message["sensorId"]
        current_co2 = message["data"]["co2"]
        
        # Get last 100 readings
        readings = await self.mongo.telemetry.find(
            {"sensorId": sensor_id},
            sort=[("timestamp", -1)],
            limit=100
        ).to_list(100)
        
        if len(readings) < 30:
            return None
        
        values = [r["data"]["co2"] for r in readings]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return None
        
        z_score = (current_co2 - mean) / std_dev
        
        # Alert if |Z| > 3 (99.7% confidence)
        if abs(z_score) > 3:
            return Alert(
                alertId=f"alert_{uuid.uuid4().hex[:12]}",
                sensorId=sensor_id,
                locationId=message["locationId"],
                alertType='ANOMALY',
                metricType='CO2',
                value=current_co2,
                threshold=mean + 3 * std_dev,
                severity='MEDIUM',
                status='OPEN',
                message=f"Anomaly detected: CO2={current_co2:.1f} (Z-score={z_score:.2f}, mean={mean:.1f})"
            )
        
        return None
    
    async def _insert_alert(self, alert: Alert):
        """Insert alert to Oracle."""
        # Implementation from previous section
        pass
    
    async def _broadcast_alerts(self, alerts: List[Alert]):
        """Broadcast alerts to WebSocket."""
        from app.core.websocket_manager import get_websocket_manager
        
        ws_manager = get_websocket_manager()
        for alert in alerts:
            await ws_manager.broadcast({
                "type": "alert",
                "data": alert.dict()
            })
```

### Alert Flow

```
Message arrives
     ↓
AlertEngine.check_message()
     ↓
├─> _check_thresholds()
│   └─> CO2 > 1000? → THRESHOLD alert
│
├─> _check_predictive()
│   ├─> Get last 10 readings
│   ├─> Linear regression
│   ├─> Predict next value
│   └─> Predicted > threshold? → PREDICTIVE alert
│
└─> _check_anomaly()
    ├─> Get last 100 readings
    ├─> Calculate Z-score
    └─> |Z| > 3? → ANOMALY alert
     ↓
Insert alerts to Oracle
     ↓
Broadcast to WebSocket
```



---

## 6️⃣ FAULT TOLERANCE STRATEGY

### Failure Scenarios & Solutions

#### 1. MongoDB Down

**Symptoms:**
- Connection timeout
- Write errors
- Slow queries

**Detection:**
```python
async def check_mongodb_health() -> bool:
    """Check MongoDB health."""
    try:
        await mongo.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        return False
```

**Solution:**

```python
class MongoDBFaultTolerance:
    """Fault tolerance for MongoDB."""
    
    def __init__(self):
        self.dead_letter = DeadLetterQueue("./dead_letter/mongodb")
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60  # seconds
        )
    
    async def insert_with_fallback(self, documents: List[Dict]) -> bool:
        """Insert with circuit breaker and fallback."""
        
        # Check circuit breaker
        if self.circuit_breaker.is_open():
            logger.warning("Circuit breaker OPEN - using dead letter")
            await self.dead_letter.write(documents, "Circuit breaker open")
            return False
        
        try:
            # Try insert
            await mongo.telemetry.insert_many(documents, ordered=False)
            self.circuit_breaker.record_success()
            return True
        
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"MongoDB insert failed: {e}")
            
            # Fallback to dead letter
            await self.dead_letter.write(documents, str(e))
            return False

class CircuitBreaker:
    """Circuit breaker pattern."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self) -> bool:
        """Check if circuit is open."""
        if self.state == "OPEN":
            # Check if timeout elapsed
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker: OPEN -> HALF_OPEN")
                return False
            return True
        return False
    
    def record_success(self):
        """Record successful operation."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            logger.info("Circuit breaker: HALF_OPEN -> CLOSED")
    
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker: CLOSED -> OPEN (failures: {self.failure_count})")
```

**Recovery:**
1. Circuit breaker opens after 5 failures
2. Writes go to dead letter queue
3. After 60 seconds, circuit breaker tries again (HALF_OPEN)
4. If success → CLOSED, if fail → OPEN again
5. Manual replay of dead letter when MongoDB recovers

---

#### 2. Oracle Down

**Symptoms:**
- Connection refused
- Timeout errors
- Lock timeouts

**Solution:**

```python
class OracleFaultTolerance:
    """Fault tolerance for Oracle."""
    
    def __init__(self):
        self.fallback_collection = mongo.alerts_fallback
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            timeout=30
        )
    
    async def insert_alert_with_fallback(self, alert: Alert) -> bool:
        """Insert alert with MongoDB fallback."""
        
        if self.circuit_breaker.is_open():
            # Store in MongoDB
            await self.fallback_collection.insert_one({
                "alertId": alert.alertId,
                "data": alert.dict(),
                "createdAt": datetime.now(),
                "synced": False
            })
            return False
        
        try:
            # Try Oracle
            oracle.execute(INSERT_ALERT_SQL, alert.dict())
            oracle.commit()
            self.circuit_breaker.record_success()
            return True
        
        except DatabaseError as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Oracle insert failed: {e}")
            
            # Fallback to MongoDB
            await self.fallback_collection.insert_one({
                "alertId": alert.alertId,
                "data": alert.dict(),
                "createdAt": datetime.now(),
                "synced": False
            })
            return False
    
    async def sync_fallback_alerts(self):
        """Background job to sync fallback alerts."""
        alerts = await self.fallback_collection.find(
            {"synced": False}
        ).limit(100).to_list(100)
        
        for alert_doc in alerts:
            try:
                alert = Alert(**alert_doc["data"])
                oracle.execute(INSERT_ALERT_SQL, alert.dict())
                oracle.commit()
                
                # Mark as synced
                await self.fallback_collection.update_one(
                    {"_id": alert_doc["_id"]},
                    {"$set": {"synced": True, "syncedAt": datetime.now()}}
                )
                
                logger.info(f"Synced alert: {alert.alertId}")
            
            except Exception as e:
                logger.error(f"Sync failed: {e}")
```

**Strategy:**
- Alerts stored in MongoDB fallback collection
- Background job syncs every 5 minutes
- No data loss (MongoDB is backup)

---

#### 3. MQTT Disconnect

**Solution:** Already covered in Section 2

**Summary:**
- Exponential backoff reconnection
- Clean session = False (persistent)
- QoS 1 (broker buffers messages)
- Messages delivered on reconnect

---

#### 4. Worker Crash

**Symptoms:**
- Worker exception
- Process killed
- Out of memory

**Detection:**
```python
class WorkerHealthMonitor:
    """Monitor worker health."""
    
    def __init__(self, workers: List[TelemetryWorker]):
        self.workers = workers
    
    async def monitor(self):
        """Monitor worker health."""
        while True:
            await asyncio.sleep(10)  # Check every 10s
            
            for worker in self.workers:
                if not worker.running:
                    logger.error(f"Worker {worker.worker_id} is dead!")
                    # Restart worker
                    await self._restart_worker(worker)
    
    async def _restart_worker(self, worker: TelemetryWorker):
        """Restart crashed worker."""
        logger.info(f"Restarting worker {worker.worker_id}")
        
        # Create new worker
        new_worker = TelemetryWorker(
            worker_id=worker.worker_id,
            queue=worker.queue,
            batch_size=worker.batch_size,
            batch_timeout=worker.batch_timeout
        )
        
        # Start new worker
        task = asyncio.create_task(new_worker.run())
        
        # Replace in pool
        idx = self.workers.index(worker)
        self.workers[idx] = new_worker
```

**Solution:**
- Health monitor checks workers every 10s
- Auto-restart crashed workers
- Messages in queue not lost (queue persists)

---

#### 5. Queue Full (Backpressure)

**Symptoms:**
- Queue size > maxsize
- Enqueue timeout
- Dropped messages

**Detection:**
```python
async def monitor_queue_health():
    """Monitor queue health."""
    while True:
        await asyncio.sleep(5)
        
        metrics = queue.get_metrics()
        queue_size = metrics["queue_size"]
        dropped = metrics["dropped_total"]
        
        if queue_size > 8000:  # 80% full
            logger.warning(f"Queue nearly full: {queue_size}/10000")
        
        if dropped > 0:
            logger.error(f"Dropped messages: {dropped}")
```

**Solution:**

```python
# Option 1: Add more workers
if queue_size > 8000:
    logger.info("Adding emergency worker")
    emergency_worker = TelemetryWorker(
        worker_id=99,
        queue=queue,
        batch_size=200,  # Larger batch
        batch_timeout=0.5  # Faster flush
    )
    asyncio.create_task(emergency_worker.run())

# Option 2: Increase batch size temporarily
for worker in workers:
    worker.batch_size = 200  # Double batch size

# Option 3: Drop low-priority messages
async def enqueue_with_priority(message: Dict, priority: str = "normal"):
    """Enqueue with priority."""
    if priority == "low" and queue.qsize() > 8000:
        # Drop low-priority messages when queue full
        logger.debug("Dropped low-priority message")
        return False
    
    return await queue.enqueue(message)
```

---

### Kafka Replacement Strategy

**Why NOT Kafka:**
- ❌ Too complex for university project
- ❌ Requires ZooKeeper (extra dependency)
- ❌ Overkill for single-node deployment

**What Replaces Kafka:**

| Kafka Feature | Replacement | Implementation |
|---------------|-------------|----------------|
| **Message Queue** | asyncio.Queue | In-memory, fast |
| **Persistence** | Dead Letter Queue | File-based fallback |
| **Retry** | Worker retry logic | Exponential backoff |
| **Fault Tolerance** | Circuit Breaker | Automatic failover |
| **Scalability** | Multiple workers | asyncio tasks |
| **Monitoring** | Metrics + Logging | Prometheus-ready |

**Optional Upgrade Path:**
If project grows, can add Redis:

```python
# Redis Queue (optional)
import aioredis

class RedisQueue:
    """Redis-based persistent queue."""
    
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis = aioredis.from_url(redis_url)
        self.queue_key = "telemetry:queue"
    
    async def enqueue(self, message: Dict):
        """Push to Redis list."""
        await self.redis.rpush(
            self.queue_key,
            json.dumps(message, default=str)
        )
    
    async def dequeue(self) -> Dict:
        """Pop from Redis list (blocking)."""
        _, message_json = await self.redis.blpop(self.queue_key)
        return json.loads(message_json)
```

**Benefits of Redis upgrade:**
- ✅ Persistent queue (survives restart)
- ✅ Distributed (multiple backend instances)
- ✅ Still simpler than Kafka

---

## 7️⃣ FINAL FLOW DIAGRAM

### Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE DATA FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

IoT Sensors (27 sensors, every 5 seconds)
     │
     │ Publish (QoS 1)
     ▼
┌─────────────────────┐
│   MQTT Broker       │
│   (Mosquitto)       │
│                     │
│  • QoS 1            │
│  • Persistent       │
│  • Buffer messages  │
└──────────┬──────────┘
           │
           │ Subscribe
           ▼
┌─────────────────────┐
│  MQTT Consumer      │
│  (Paho MQTT)        │
│                     │
│  • Validate         │
│  • Deduplicate      │
│  • Enqueue          │
└──────────┬──────────┘
           │
           │ Non-blocking enqueue (timeout 1s)
           ▼
┌─────────────────────┐
│   AsyncQueue        │
│   (asyncio.Queue)   │
│                     │
│  • Maxsize: 10000   │
│  • In-memory        │
│  • Backpressure     │
└──────────┬──────────┘
           │
           │ Dequeue (blocking)
           ▼
┌─────────────────────────────────────────────────────────┐
│                    Worker Pool (3 workers)              │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │ Worker 1 │    │ Worker 2 │    │ Worker 3 │         │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘         │
│       │               │               │                │
│       └───────────────┴───────────────┘                │
│                       │                                │
│              Batch (100 msgs or 1s)                    │
│                       │                                │
│       ┌───────────────┴───────────────┐                │
│       │                               │                │
│       ▼                               ▼                │
│  ┌─────────┐                    ┌─────────┐           │
│  │ MongoDB │                    │  Alert  │           │
│  │ Batch   │                    │ Engine  │           │
│  │ Insert  │                    └────┬────┘           │
│  └─────────┘                         │                │
│       │                              │                │
│       │ Success                      │ Alerts         │
│       ▼                              ▼                │
│  ┌─────────┐                    ┌─────────┐           │
│  │ MongoDB │                    │ Oracle  │           │
│  │ (TTL)   │                    │ (Alerts)│           │
│  └─────────┘                    └────┬────┘           │
│                                      │                │
│                                      │ Success        │
│                                      ▼                │
│                                 ┌─────────┐           │
│                                 │WebSocket│           │
│                                 │Broadcast│           │
│                                 └─────────┘           │
└─────────────────────────────────────────────────────────┘
           │
           │ Realtime updates
           ▼
┌─────────────────────┐
│   Frontend          │
│   (React)           │
│                     │
│  • Dashboard        │
│  • Charts           │
│  • Alerts           │
└─────────────────────┘

FAULT TOLERANCE:
─────────────────
• MQTT disconnect → Exponential backoff reconnect
• MongoDB down → Dead letter queue (file)
• Oracle down → MongoDB fallback collection
• Worker crash → Auto-restart
• Queue full → Add emergency worker
```

### Simplified Flow

```
Sensor → MQTT → Consumer → Queue → Worker → Storage → WebSocket → Frontend
         (QoS1)  (validate) (async) (batch)  (Mongo)   (realtime)
                                              (Oracle)
```

### Performance Metrics

```
┌─────────────────────────────────────────────────────────────┐
│                    PERFORMANCE TARGETS                      │
└─────────────────────────────────────────────────────────────┘

Ingestion:
• MQTT → Consumer: < 5ms
• Consumer → Queue: < 1ms (non-blocking)
• Queue → Worker: < 1ms

Processing:
• Worker batch: 100 messages
• Batch time: ~1 second
• MongoDB insert: ~50ms per batch
• Alert check: ~10ms per message

Throughput:
• Single worker: ~100 msg/sec
• 3 workers: ~300 msg/sec
• 27 sensors @ 5s interval = 5.4 msg/sec
• Headroom: 55x capacity

Latency:
• End-to-end (sensor → dashboard): < 2 seconds
• MQTT → MongoDB: < 1 second
• Alert → WebSocket: < 500ms

Storage:
• MongoDB: 2.6M docs/month (27 sensors)
• Batch insert: 2000 docs/sec
• TTL cleanup: Automatic (30 days)
```



---

## 8️⃣ CODE ARCHITECTURE

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   │
│   ├── main.py                    # FastAPI app + startup
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration
│   │   ├── queue_manager.py       # AsyncQueue + WorkerPool
│   │   └── websocket_manager.py   # WebSocket broadcast
│   │
│   ├── messaging/
│   │   ├── __init__.py
│   │   └── mqtt_consumer.py       # MQTT consumer
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── telemetry_worker.py    # Worker implementation
│   │   └── worker_pool.py         # Worker pool manager
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── alert_engine.py        # Alert detection
│   │   ├── telemetry_service.py   # Telemetry processing
│   │   └── analytics_service.py   # Analytics aggregation
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── mongodb_client.py      # MongoDB operations
│   │   ├── oracle_client.py       # Oracle operations
│   │   └── dead_letter_queue.py   # Fallback storage
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── telemetry.py           # Telemetry model
│   │   └── alert.py               # Alert model
│   │
│   └── api/
│       ├── __init__.py
│       ├── routes.py              # REST API endpoints
│       └── websocket.py           # WebSocket endpoints
│
├── requirements.txt
└── Dockerfile
```

### File Responsibilities

#### 1. `app/main.py` - Application Entry Point

```python
"""
FastAPI application with async worker startup.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import logging

from app.core.queue_manager import get_queue_manager
from app.messaging.mqtt_consumer import get_mqtt_consumer
from app.api import routes, websocket

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Startup:
    - Initialize queue and workers
    - Start MQTT consumer
    
    Shutdown:
    - Stop MQTT consumer
    - Drain queue
    - Stop workers
    """
    # Startup
    logger.info("Starting application...")
    
    # Initialize queue manager
    queue_manager = get_queue_manager()
    await queue_manager.start()
    
    # Start MQTT consumer
    mqtt_consumer = get_mqtt_consumer()
    mqtt_consumer.start_async()
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Stop MQTT consumer
    mqtt_consumer.stop()
    
    # Stop queue manager (drains queue)
    await queue_manager.stop()
    
    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Smart City IoT Dashboard",
    version="2.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(routes.router, prefix="/api")
app.include_router(websocket.router, prefix="/ws")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    queue_manager = get_queue_manager()
    metrics = queue_manager.get_metrics()
    
    return {
        "status": "healthy",
        "queue": metrics
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
```

---

#### 2. `app/core/queue_manager.py` - Queue & Worker Pool

```python
"""
Queue manager with worker pool.
"""

import asyncio
from typing import Dict, Any, Optional
import logging

from app.workers.telemetry_worker import TelemetryWorker

logger = logging.getLogger(__name__)

class QueueManager:
    """
    Manages async queue and worker pool.
    
    Singleton pattern.
    """
    
    def __init__(
        self,
        queue_maxsize: int = 10000,
        num_workers: int = 3,
        batch_size: int = 100,
        batch_timeout: float = 1.0
    ):
        self.queue = asyncio.Queue(maxsize=queue_maxsize)
        self.num_workers = num_workers
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
        self.workers = []
        self.worker_tasks = []
        
        # Metrics
        self.enqueued_count = 0
        self.dropped_count = 0
    
    async def start(self):
        """Start worker pool."""
        logger.info(f"Starting {self.num_workers} workers...")
        
        for i in range(self.num_workers):
            worker = TelemetryWorker(
                worker_id=i,
                queue=self.queue,
                batch_size=self.batch_size,
                batch_timeout=self.batch_timeout
            )
            self.workers.append(worker)
            
            task = asyncio.create_task(worker.run())
            self.worker_tasks.append(task)
        
        logger.info(f"Started {self.num_workers} workers")
    
    async def stop(self):
        """Stop worker pool gracefully."""
        logger.info("Stopping workers...")
        
        # Wait for queue to drain
        logger.info(f"Draining queue ({self.queue.qsize()} items)...")
        await self.queue.join()
        
        # Stop workers
        for worker in self.workers:
            worker.stop()
        
        # Cancel tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for completion
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        logger.info("All workers stopped")
    
    async def enqueue(self, message: Dict[str, Any], timeout: float = 1.0) -> bool:
        """
        Enqueue message.
        
        Returns:
            True if enqueued, False if dropped
        """
        try:
            await asyncio.wait_for(
                self.queue.put(message),
                timeout=timeout
            )
            self.enqueued_count += 1
            return True
        except asyncio.TimeoutError:
            self.dropped_count += 1
            logger.warning(f"Queue full, dropped message. Size: {self.queue.qsize()}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get queue and worker metrics."""
        return {
            "queue_size": self.queue.qsize(),
            "queue_maxsize": self.queue._maxsize,
            "enqueued_total": self.enqueued_count,
            "dropped_total": self.dropped_count,
            "num_workers": self.num_workers,
            "workers": [w.get_metrics() for w in self.workers]
        }

# Singleton
_queue_manager: Optional[QueueManager] = None

def get_queue_manager() -> QueueManager:
    """Get singleton queue manager."""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = QueueManager()
    return _queue_manager
```

---

#### 3. `app/messaging/mqtt_consumer.py` - MQTT Consumer

```python
"""
MQTT consumer with queue integration.
"""

import json
import logging
from typing import Optional, Callable
import paho.mqtt.client as mqtt

from app.core.queue_manager import get_queue_manager
from app.models.telemetry import Telemetry

logger = logging.getLogger(__name__)

class MQTTConsumer:
    """
    MQTT consumer that enqueues messages.
    
    Features:
    - QoS 1 (at least once)
    - Persistent session
    - Auto-reconnect
    - Message validation
    """
    
    def __init__(
        self,
        broker_host: str = "mosquitto",
        broker_port: int = 1883,
        topic_pattern: str = "sensors/+/telemetry"
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic_pattern = topic_pattern
        
        self.client = mqtt.Client(
            client_id="backend_consumer",
            clean_session=False  # Persistent session
        )
        
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        self.queue_manager = get_queue_manager()
        
        # Reconnection
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle connection."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker")
            self.reconnect_delay = 1
            
            # Subscribe
            client.subscribe(self.topic_pattern, qos=1)
            logger.info(f"Subscribed to {self.topic_pattern}")
        else:
            logger.error(f"Connection failed: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Handle disconnection."""
        if rc != 0:
            logger.warning(f"Unexpected disconnect: {rc}")
            self._reconnect_with_backoff()
    
    def _reconnect_with_backoff(self):
        """Reconnect with exponential backoff."""
        import time
        
        logger.info(f"Reconnecting in {self.reconnect_delay}s...")
        time.sleep(self.reconnect_delay)
        
        try:
            self.client.reconnect()
            self.reconnect_delay = 1
        except Exception as e:
            logger.error(f"Reconnect failed: {e}")
            self.reconnect_delay = min(
                self.reconnect_delay * 2,
                self.max_reconnect_delay
            )
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming message."""
        try:
            # Parse JSON
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Validate with Pydantic
            telemetry = Telemetry(**payload)
            
            # Enqueue (async-safe)
            import asyncio
            loop = asyncio.get_event_loop()
            loop.create_task(
                self.queue_manager.enqueue(telemetry.dict())
            )
            
            logger.debug(f"Enqueued message from {telemetry.sensorId}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Message processing error: {e}")
    
    def start_async(self):
        """Start consumer (non-blocking)."""
        logger.info(f"Connecting to {self.broker_host}:{self.broker_port}")
        self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        self.client.loop_start()
    
    def stop(self):
        """Stop consumer."""
        logger.info("Stopping MQTT consumer...")
        self.client.loop_stop()
        self.client.disconnect()

# Singleton
_mqtt_consumer: Optional[MQTTConsumer] = None

def get_mqtt_consumer() -> MQTTConsumer:
    """Get singleton MQTT consumer."""
    global _mqtt_consumer
    if _mqtt_consumer is None:
        _mqtt_consumer = MQTTConsumer()
    return _mqtt_consumer
```

---

#### 4. `app/workers/telemetry_worker.py` - Worker Implementation

```python
"""
Telemetry worker with batch processing.
"""

import asyncio
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta

from app.db.mongodb_client import get_mongodb_client
from app.services.alert_engine import get_alert_engine
from app.core.websocket_manager import get_websocket_manager

logger = logging.getLogger(__name__)

class TelemetryWorker:
    """
    Async worker for processing telemetry messages.
    
    Features:
    - Batch processing
    - MongoDB batch insert
    - Alert checking
    - WebSocket broadcast
    - Retry mechanism
    """
    
    def __init__(
        self,
        worker_id: int,
        queue: asyncio.Queue,
        batch_size: int = 100,
        batch_timeout: float = 1.0
    ):
        self.worker_id = worker_id
        self.queue = queue
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
        self.running = False
        self.processed_count = 0
        self.error_count = 0
        
        # Dependencies
        self.mongo = get_mongodb_client()
        self.alert_engine = get_alert_engine()
        self.ws_manager = get_websocket_manager()
    
    async def run(self):
        """Main worker loop."""
        self.running = True
        logger.info(f"Worker {self.worker_id} started")
        
        batch = []
        last_flush = asyncio.get_event_loop().time()
        
        while self.running:
            try:
                # Dequeue with timeout
                try:
                    message = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=0.1
                    )
                    batch.append(message)
                except asyncio.TimeoutError:
                    pass
                
                # Check if should flush
                current_time = asyncio.get_event_loop().time()
                should_flush = (
                    len(batch) >= self.batch_size or
                    (current_time - last_flush >= self.batch_timeout and batch)
                )
                
                if should_flush:
                    await self._process_batch(batch)
                    
                    for _ in batch:
                        self.queue.task_done()
                    
                    batch = []
                    last_flush = current_time
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}", exc_info=True)
                self.error_count += 1
        
        # Flush remaining
        if batch:
            await self._process_batch(batch)
            for _ in batch:
                self.queue.task_done()
        
        logger.info(f"Worker {self.worker_id} stopped")
    
    async def _process_batch(self, batch: List[Dict]):
        """Process batch of messages."""
        if not batch:
            return
        
        logger.debug(f"Worker {self.worker_id} processing {len(batch)} messages")
        
        try:
            # 1. MongoDB batch insert
            await self._insert_mongodb(batch)
            
            # 2. Check alerts
            for message in batch:
                await self.alert_engine.check_message(message)
            
            # 3. Broadcast sample
            if batch:
                await self.ws_manager.broadcast({
                    "type": "telemetry",
                    "data": batch[0]
                })
            
            self.processed_count += len(batch)
        
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            await self._retry_batch(batch)
    
    async def _insert_mongodb(self, batch: List[Dict]):
        """Insert batch to MongoDB."""
        documents = []
        for msg in batch:
            doc = {
                "sensorId": msg["sensorId"],
                "locationId": msg["locationId"],
                "timestamp": msg["timestamp"],
                "data": msg["data"],
                "metadata": msg.get("metadata", {}),
                "expireAt": datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00')) + timedelta(days=30)
            }
            documents.append(doc)
        
        try:
            result = await self.mongo.telemetry.insert_many(
                documents,
                ordered=False
            )
            logger.debug(f"Inserted {len(result.inserted_ids)} documents")
        except Exception as e:
            logger.error(f"MongoDB insert failed: {e}")
            raise
    
    async def _retry_batch(self, batch: List[Dict], max_retries: int = 3):
        """Retry failed batch."""
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(2 ** attempt)
                await self._insert_mongodb(batch)
                logger.info(f"Retry {attempt + 1} succeeded")
                return
            except Exception as e:
                logger.error(f"Retry {attempt + 1} failed: {e}")
        
        logger.critical(f"Batch permanently failed")
        # TODO: Write to dead letter
    
    def stop(self):
        """Stop worker."""
        self.running = False
    
    def get_metrics(self) -> Dict:
        """Get worker metrics."""
        return {
            "worker_id": self.worker_id,
            "processed": self.processed_count,
            "errors": self.error_count
        }
```

---

#### 5. `app/services/alert_engine.py` - Alert Detection

```python
"""
Alert detection engine.
"""

import logging
from typing import List, Optional, Dict, Any
import uuid

from app.models.alert import Alert
from app.db.mongodb_client import get_mongodb_client
from app.db.oracle_client import get_oracle_client

logger = logging.getLogger(__name__)

class AlertEngine:
    """
    Alert detection engine.
    
    Supports:
    - Threshold alerts
    - Predictive alerts
    - Anomaly detection
    """
    
    THRESHOLDS = {
        'CO2': {'HIGH': 1000, 'CRITICAL': 1500},
        'Noise': {'HIGH': 85, 'CRITICAL': 95},
        'PM2.5': {'HIGH': 55, 'CRITICAL': 150}
    }
    
    def __init__(self):
        self.mongo = get_mongodb_client()
        self.oracle = get_oracle_client()
    
    async def check_message(self, message: Dict[str, Any]) -> List[Alert]:
        """Check message for alerts."""
        alerts = []
        
        # Threshold check
        threshold_alerts = self._check_thresholds(message)
        alerts.extend(threshold_alerts)
        
        # Insert to Oracle
        for alert in alerts:
            await self._insert_alert(alert)
        
        return alerts
    
    def _check_thresholds(self, message: Dict) -> List[Alert]:
        """Check threshold violations."""
        alerts = []
        data = message["data"]
        
        for metric, value in data.items():
            metric_upper = metric.upper()
            if metric_upper not in self.THRESHOLDS:
                continue
            
            thresholds = self.THRESHOLDS[metric_upper]
            
            if value >= thresholds['CRITICAL']:
                severity = 'CRITICAL'
                threshold = thresholds['CRITICAL']
            elif value >= thresholds['HIGH']:
                severity = 'HIGH'
                threshold = thresholds['HIGH']
            else:
                continue
            
            alert = Alert(
                alertId=f"alert_{uuid.uuid4().hex[:12]}",
                sensorId=message["sensorId"],
                locationId=message["locationId"],
                alertType='THRESHOLD',
                metricType=metric_upper,
                value=value,
                threshold=threshold,
                severity=severity,
                status='OPEN'
            )
            alerts.append(alert)
        
        return alerts
    
    async def _insert_alert(self, alert: Alert):
        """Insert alert to Oracle."""
        try:
            self.oracle.insert_alert(alert)
            logger.info(f"Alert created: {alert.alertId}")
        except Exception as e:
            logger.error(f"Alert insert failed: {e}")

# Singleton
_alert_engine: Optional[AlertEngine] = None

def get_alert_engine() -> AlertEngine:
    """Get singleton alert engine."""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine()
    return _alert_engine
```

---

#### 6. `app/db/dead_letter_queue.py` - Fallback Storage

```python
"""
Dead letter queue for failed operations.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class DeadLetterQueue:
    """File-based dead letter queue."""
    
    def __init__(self, directory: str = "./dead_letter"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
    
    async def write(self, documents: List[Dict], reason: str):
        """Write failed batch to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"failed_{timestamp}.json"
        filepath = self.directory / filename
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "count": len(documents),
            "documents": documents
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.warning(f"Dead letter: {filename} ({len(documents)} docs)")
```

---

### Docker Compose Integration

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MQTT_BROKER_HOST=mosquitto
      - MONGODB_URL=mongodb://mongodb:27017
      - ORACLE_DSN=oracle:1521/XE
      - NUM_WORKERS=3
      - BATCH_SIZE=100
    depends_on:
      - mosquitto
      - mongodb
      - oracle
    volumes:
      - ./dead_letter:/app/dead_letter
```

---

## 🎯 CONCLUSION

This production-ready data flow design provides:

✅ **Non-blocking ingestion** - MQTT → AsyncQueue  
✅ **Scalable processing** - Worker pool (3+ workers)  
✅ **Batch optimization** - 100 docs/batch, 10x faster  
✅ **Fault tolerance** - Circuit breaker, dead letter, retry  
✅ **No Kafka needed** - AsyncIO queue + optional Redis  
✅ **Docker-ready** - Single compose file  
✅ **Production patterns** - Graceful shutdown, health checks, metrics  

**Suitable for:**
- ✅ University project (demonstrates advanced concepts)
- ✅ Production deployment (with Redis upgrade path)
- ✅ Portfolio demonstration
- ✅ Real-world IoT systems

**Next Steps:**
1. Implement code structure
2. Add monitoring (Prometheus metrics)
3. Add health checks
4. Test fault scenarios
5. Optional: Upgrade to Redis queue

