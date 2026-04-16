#!/bin/bash
# Backend startup script for Smart City IoT Dashboard
# Validates: Requirement 16.4
#
# Responsibilities:
#   1. Wait for MongoDB to be ready
#   2. Wait for Oracle to be ready
#   3. Run Oracle schema initialization scripts
#   4. Start FastAPI server with uvicorn (MQTT consumer starts inside the app lifespan)

set -e

# ---------------------------------------------------------------------------
# Configuration (can be overridden via environment variables)
# ---------------------------------------------------------------------------
MONGODB_URI="${MONGODB_URI:-mongodb://admin:admin123@mongodb:27017/smart_city?authSource=admin}"
ORACLE_USER="${ORACLE_USER:-system}"
ORACLE_PASSWORD="${ORACLE_PASSWORD:-OraclePass123}"
ORACLE_DSN="${ORACLE_DSN:-oracle-xe:1521/XEPDB1}"

MONGO_MAX_RETRIES=30
MONGO_RETRY_INTERVAL=5

ORACLE_MAX_RETRIES=30
ORACLE_RETRY_INTERVAL=10

SCHEMA_SQL="/app/app/db/sql/oracle_schema.sql"
SEED_SQL="/app/app/db/sql/oracle_seed.sql"

# ---------------------------------------------------------------------------
# Helper: log with timestamp
# ---------------------------------------------------------------------------
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# ---------------------------------------------------------------------------
# 1. Wait for MongoDB
# ---------------------------------------------------------------------------
wait_for_mongodb() {
    log "Waiting for MongoDB to be ready..."
    local attempt=1

    until python3 - <<'EOF'
import os, sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
uri = os.getenv("MONGODB_URI", "mongodb://admin:admin123@mongodb:27017/smart_city?authSource=admin")
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    client.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
EOF
    do
        if [ "$attempt" -ge "$MONGO_MAX_RETRIES" ]; then
            log "ERROR: MongoDB did not become ready after $MONGO_MAX_RETRIES attempts. Exiting."
            exit 1
        fi
        log "MongoDB not ready (attempt $attempt/$MONGO_MAX_RETRIES). Retrying in ${MONGO_RETRY_INTERVAL}s..."
        attempt=$((attempt + 1))
        sleep "$MONGO_RETRY_INTERVAL"
    done

    log "MongoDB is ready."
}

# ---------------------------------------------------------------------------
# 2. Wait for Oracle
# ---------------------------------------------------------------------------
wait_for_oracle() {
    log "Waiting for Oracle to be ready..."
    local attempt=1

    until python3 - <<'EOF'
import os, sys
import oracledb
user     = os.getenv("ORACLE_USER",     "system")
password = os.getenv("ORACLE_PASSWORD", "OraclePass123")
dsn      = os.getenv("ORACLE_DSN",      "oracle-xe:1521/XEPDB1")
try:
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    conn.cursor().execute("SELECT 1 FROM DUAL")
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
EOF
    do
        if [ "$attempt" -ge "$ORACLE_MAX_RETRIES" ]; then
            log "ERROR: Oracle did not become ready after $ORACLE_MAX_RETRIES attempts. Exiting."
            exit 1
        fi
        log "Oracle not ready (attempt $attempt/$ORACLE_MAX_RETRIES). Retrying in ${ORACLE_RETRY_INTERVAL}s..."
        attempt=$((attempt + 1))
        sleep "$ORACLE_RETRY_INTERVAL"
    done

    log "Oracle is ready."
}

# ---------------------------------------------------------------------------
# 3. Initialize Oracle schema
# ---------------------------------------------------------------------------
initialize_oracle_schema() {
    log "Initializing Oracle database schema..."

    python3 - <<'EOF'
import os, sys, logging
import oracledb

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("schema_init")

user     = os.getenv("ORACLE_USER",     "system")
password = os.getenv("ORACLE_PASSWORD", "OraclePass123")
dsn      = os.getenv("ORACLE_DSN",      "oracle-xe:1521/XEPDB1")

SCHEMA_SQL = "/app/app/db/sql/oracle_schema.sql"
SEED_SQL   = "/app/app/db/sql/oracle_seed.sql"

def execute_sql_file(conn, path):
    if not os.path.exists(path):
        logger.warning(f"SQL file not found, skipping: {path}")
        return
    with open(path, "r") as f:
        content = f.read()
    cursor = conn.cursor()
    for stmt in content.split(";"):
        stmt = stmt.strip()
        if not stmt or stmt.startswith("--"):
            continue
        try:
            cursor.execute(stmt)
        except oracledb.DatabaseError as e:
            code = e.args[0].code if e.args else 0
            if code == 955:   # ORA-00955: name already used
                logger.debug(f"Object already exists, skipping: {stmt[:60]}...")
            elif code == 1:   # ORA-00001: unique constraint violated (seed data)
                logger.debug(f"Duplicate row, skipping: {stmt[:60]}...")
            else:
                logger.warning(f"SQL warning ({code}): {e} — stmt: {stmt[:80]}")
    conn.commit()
    cursor.close()
    logger.info(f"Executed: {path}")

try:
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    execute_sql_file(conn, SCHEMA_SQL)
    execute_sql_file(conn, SEED_SQL)
    conn.close()
    logger.info("Oracle schema initialization complete.")
    sys.exit(0)
except Exception as e:
    logger.error(f"Schema initialization failed: {e}")
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        log "ERROR: Oracle schema initialization failed. Exiting."
        exit 1
    fi

    log "Oracle schema initialization complete."
}

# ---------------------------------------------------------------------------
# 4. Start FastAPI server
#    The MQTT consumer is started inside app lifespan (app/main.py).
# ---------------------------------------------------------------------------
start_server() {
    log "Starting FastAPI server with uvicorn on port 8000..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
wait_for_mongodb
wait_for_oracle
initialize_oracle_schema
start_server
