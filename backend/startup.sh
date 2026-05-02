#!/bin/bash
# Backend startup script for Smart City IoT Dashboard
# Validates: Requirement 16.4
#
# Responsibilities:
#   1. Wait for MongoDB to be ready
#   2. Wait for Oracle to be ready
#   3. Run Oracle schema v2 initialization (PL/SQL aware)
#   4. Seed MongoDB indexes + 7-day telemetry data
#   5. Start FastAPI server with uvicorn

set -e

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MONGODB_URI="${MONGODB_URI:-mongodb://admin:admin123@mongodb:27017/smart_city?authSource=admin}"
ORACLE_ADMIN_USER="${ORACLE_ADMIN_USER:-system}"
ORACLE_ADMIN_PASSWORD="${ORACLE_ADMIN_PASSWORD:-OraclePass123}"
ORACLE_USER="${ORACLE_USER:-SMARTCITY}"
ORACLE_PASSWORD="${ORACLE_PASSWORD:-SmartCity2026!}"
ORACLE_DSN="${ORACLE_DSN:-oracle-xe:1521/XEPDB1}"

MONGO_MAX_RETRIES=30
MONGO_RETRY_INTERVAL=5

ORACLE_MAX_RETRIES=30
ORACLE_RETRY_INTERVAL=10

SCHEMA_SQL="/app/app/db/sql/oracle_schema_v2.sql"
SEED_SQL="/app/app/db/sql/oracle_seed_v2.sql"

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
user     = os.getenv("ORACLE_ADMIN_USER",     "system")
password = os.getenv("ORACLE_ADMIN_PASSWORD", "OraclePass123")
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
# 3. Initialize Oracle schema v2 (PL/SQL-aware parser)
# ---------------------------------------------------------------------------
initialize_oracle_schema() {
    log "Initializing Oracle database schema v2..."

    python3 - <<'PYEOF'
import os, sys, logging
import oracledb

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("schema_init")

admin_user     = os.getenv("ORACLE_ADMIN_USER",     "system")
admin_password = os.getenv("ORACLE_ADMIN_PASSWORD", "OraclePass123")
user     = os.getenv("ORACLE_USER",     "SMARTCITY")
password = os.getenv("ORACLE_PASSWORD", "SmartCity2026!")
dsn      = os.getenv("ORACLE_DSN",      "oracle-xe:1521/XEPDB1")

SCHEMA_SQL = "/app/app/db/sql/oracle_schema_v2.sql"
SEED_SQL   = "/app/app/db/sql/oracle_seed_v2.sql"

def parse_sql_file(filepath):
    """Parse SQL file with PL/SQL blocks (/ delimiters)."""
    if not os.path.exists(filepath):
        logger.warning(f"SQL file not found: {filepath}")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    statements = []
    current_block = []
    in_plsql = False
    for line in lines:
        stripped = line.strip()
        if not in_plsql and (stripped == '' or stripped.startswith('--')):
            continue
        if not in_plsql and stripped.upper().startswith(
            ('BEGIN', 'DECLARE', 'CREATE OR REPLACE TRIGGER',
             'CREATE OR REPLACE PROCEDURE', 'CREATE OR REPLACE FUNCTION')):
            in_plsql = True
        if stripped == '/':
            if current_block:
                stmt = '\n'.join(current_block).strip()
                if stmt:
                    statements.append(('PLSQL', stmt))
                current_block = []
            in_plsql = False
            continue
        if not in_plsql and stripped.endswith(';'):
            current_block.append(line.rstrip('\r'))
            stmt = '\n'.join(current_block).strip()
            if stmt.endswith(';'):
                stmt = stmt[:-1].strip()
            if stmt and not stmt.startswith('--'):
                statements.append(('SQL', stmt))
            current_block = []
            continue
        current_block.append(line.rstrip('\r'))
    if current_block:
        stmt = '\n'.join(current_block).strip()
        if stmt and not stmt.startswith('--'):
            if stmt.endswith(';'):
                stmt = stmt[:-1].strip()
            statements.append(('SQL', stmt))
    return statements


def execute_statements(cursor, statements, description):
    ok = err = 0
    for i, (stype, stmt) in enumerate(statements, 1):
        try:
            cursor.execute(stmt)
            ok += 1
        except oracledb.DatabaseError as e:
            msg = str(e).lower()
            # expected errors: drop non-existent, already exists, duplicate row
            if any(code in msg for code in ['ora-00942', 'ora-00955', 'ora-00001', 'ora-02261', 'ora-01430', 'ora-01408']):
                ok += 1
            else:
                err += 1
                logger.warning(f"{description} stmt#{i}: {e}")
    return ok, err


try:
    # 1. Ensure user/schema exists using admin credentials
    admin_conn = oracledb.connect(user=admin_user, password=admin_password, dsn=dsn)
    admin_cursor = admin_conn.cursor()
    admin_cursor.execute(f"SELECT COUNT(*) FROM all_users WHERE username = UPPER('{user}')")
    user_exists = admin_cursor.fetchone()[0]
    if not user_exists:
        logger.info(f"Creating Oracle user/schema: {user}")
        admin_cursor.execute(f"CREATE USER {user} IDENTIFIED BY \"{password}\"")
        admin_cursor.execute(f"GRANT CONNECT, RESOURCE, CREATE VIEW, CREATE TRIGGER, CREATE PROCEDURE TO {user}")
        admin_cursor.execute(f"ALTER USER {user} QUOTA UNLIMITED ON USERS")
    else:
        # Check if password needs update or just proceed. We assume the user is properly setup if exists.
        pass
    admin_cursor.close()
    admin_conn.close()

    # 2. Connect as application user
    conn = oracledb.connect(user=user, password=password, dsn=dsn)

    # Check if schema already exists
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM user_tables
        WHERE table_name IN ('LOCATIONS','SENSOR_REGISTRY','ALERTS')
    """)
    existing = cursor.fetchone()[0]

    if existing >= 3:
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM SENSOR_REGISTRY")
        sensor_count = cursor.fetchone()[0]
        if sensor_count >= 33:
            logger.info(f"Oracle schema already initialized ({sensor_count} sensors). Skipping.")
            cursor.close()
            conn.close()
            sys.exit(0)

    cursor.close()

    # Execute schema
    stmts = parse_sql_file(SCHEMA_SQL)
    logger.info(f"Executing schema ({len(stmts)} statements)...")
    cursor = conn.cursor()
    ok, err = execute_statements(cursor, stmts, "schema")
    conn.commit()
    cursor.close()
    logger.info(f"Schema: {ok} ok, {err} errors")

    # Execute seed
    stmts = parse_sql_file(SEED_SQL)
    logger.info(f"Executing seed ({len(stmts)} statements)...")
    cursor = conn.cursor()
    ok, err = execute_statements(cursor, stmts, "seed")
    conn.commit()
    cursor.close()
    logger.info(f"Seed: {ok} ok, {err} errors")

    # Verify
    cursor = conn.cursor()
    for tbl in ['LOCATIONS','SENSOR_CLUSTERS','SENSOR_REGISTRY','SENSOR_CAPABILITIES']:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cursor.fetchone()[0]
        logger.info(f"  {tbl}: {cnt} rows")
    cursor.close()
    conn.close()

    logger.info("Oracle schema v2 initialization complete.")
    sys.exit(0)

except Exception as e:
    logger.error(f"Oracle schema initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

    if [ $? -ne 0 ]; then
        log "ERROR: Oracle schema initialization failed. Exiting."
        exit 1
    fi

    log "Oracle schema initialization complete."
}

# ---------------------------------------------------------------------------
# 4. Seed MongoDB (indexes + 7-day telemetry)
# ---------------------------------------------------------------------------
seed_mongodb() {
    log "Seeding MongoDB (indexes + telemetry data)..."

    python3 -m app.db.seed_telemetry

    if [ $? -ne 0 ]; then
        log "WARNING: MongoDB seeding had errors (non-fatal, continuing)."
    else
        log "MongoDB seeding complete."
    fi
}

# ---------------------------------------------------------------------------
# 5. Start FastAPI server
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
seed_mongodb
start_server
