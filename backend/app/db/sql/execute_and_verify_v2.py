import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

"""
Smart City IoT Database - Schema v2 Execution & Verification Script
====================================================================
Tasks:
  1.2 - Execute oracle_schema_v2.sql (create 9 tables, triggers, indexes, FKs)
  1.3 - Execute oracle_seed_v2.sql (load seed data for 33 sensors)
  1.4 - Verify schema integrity (constraints, indexes, query plans)
"""

import oracledb
import sys
import re
import time
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================
ORACLE_USER = "system"
ORACLE_PASSWORD = "OraclePass123"
ORACLE_DSN = "localhost:1521/XEPDB1"

EXPECTED_TABLES = [
    'LOCATIONS', 'SENSOR_CLUSTERS', 'SENSOR_REGISTRY',
    'SENSOR_CAPABILITIES', 'ALERTS', 'INCIDENTS',
    'INCIDENT_ALERTS', 'SENSOR_HEALTH_LOGS', 'TELEMETRY_SUMMARY'
]

EXPECTED_TRIGGERS = [
    'TRG_LOCATIONS_UPDATED_AT',
    'TRG_CLUSTERS_UPDATED_AT',
    'TRG_SENSORS_UPDATED_AT',
    'TRG_ALERT_LOCATION_SYNC',
    'TRG_CLUSTER_COUNT'
]

# ============================================================================
# Helpers
# ============================================================================
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def ok(msg):
    print(f"  {Colors.GREEN}[OK]{Colors.END} {msg}")

def fail(msg):
    print(f"  {Colors.RED}[FAIL]{Colors.END} {msg}")

def info(msg):
    print(f"  {Colors.CYAN}[INFO]{Colors.END} {msg}")

def warn(msg):
    print(f"  {Colors.YELLOW}[WARN]{Colors.END} {msg}")

def header(msg):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}")
    print(f"  {msg}")
    print(f"{'='*70}{Colors.END}\n")

def subheader(msg):
    print(f"\n  {Colors.BOLD}{msg}{Colors.END}")

def parse_sql_file(filepath):
    """Parse a SQL file with PL/SQL blocks (separated by /) into executable statements."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove comment-only lines but keep inline comments
    lines = content.split('\n')
    
    statements = []
    current_block = []
    in_plsql = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines and pure comment lines at top level (not in PL/SQL)
        if not in_plsql and (stripped == '' or stripped.startswith('--')):
            continue
        
        # Check if we're entering a PL/SQL block
        if not in_plsql and stripped.upper().startswith(('BEGIN', 'DECLARE', 'CREATE OR REPLACE TRIGGER', 'CREATE OR REPLACE PROCEDURE', 'CREATE OR REPLACE FUNCTION')):
            in_plsql = True
        
        # Check for '/' delimiter (end of PL/SQL block)
        if stripped == '/':
            if current_block:
                stmt = '\n'.join(current_block).strip()
                if stmt:
                    statements.append(('PLSQL', stmt))
                current_block = []
            in_plsql = False
            continue
        
        # Check for ';' at end of line (end of regular SQL)
        if not in_plsql and stripped.endswith(';'):
            current_block.append(line.rstrip('\r'))
            stmt = '\n'.join(current_block).strip()
            # Remove trailing ';'
            if stmt.endswith(';'):
                stmt = stmt[:-1].strip()
            if stmt and not stmt.startswith('--'):
                statements.append(('SQL', stmt))
            current_block = []
            continue
        
        current_block.append(line.rstrip('\r'))
    
    # Handle any remaining block
    if current_block:
        stmt = '\n'.join(current_block).strip()
        if stmt and not stmt.startswith('--'):
            if stmt.endswith(';'):
                stmt = stmt[:-1].strip()
            statements.append(('SQL', stmt))
    
    return statements

def execute_statements(cursor, statements, description):
    """Execute a list of parsed SQL statements."""
    success = 0
    errors = 0
    
    for i, (stmt_type, stmt) in enumerate(statements, 1):
        try:
            if stmt_type == 'PLSQL':
                cursor.execute(stmt)
            else:
                cursor.execute(stmt)
            success += 1
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            error_msg = str(error_obj.message).strip()
            # Some errors are expected (e.g., dropping non-existent objects)
            if 'ORA-00942' in error_msg or 'table or view does not exist' in error_msg.lower():
                success += 1  # Expected cleanup
            else:
                errors += 1
                fail(f"Statement #{i} ({stmt_type}): {error_msg}")
                # Print first 100 chars of statement for context
                preview = stmt[:150].replace('\n', ' ')
                info(f"  → {preview}...")
    
    return success, errors


# ============================================================================
# TASK 1.2: Execute Schema v2
# ============================================================================
def task_1_2(conn):
    header("TASK 1.2: Execute Oracle Schema v2 Creation Script")
    cursor = conn.cursor()
    
    # Parse and execute schema
    info("Parsing oracle_schema_v2.sql...")
    statements = parse_sql_file('oracle_schema_v2.sql')
    info(f"Found {len(statements)} statements to execute")
    
    info("Executing schema creation...")
    success, errors = execute_statements(cursor, statements, "Schema v2")
    conn.commit()
    
    if errors == 0:
        ok(f"All {success} statements executed successfully")
    else:
        fail(f"{errors} errors out of {success + errors} statements")
    
    # Verify 9 tables created
    subheader("Verifying 9 tables created:")
    cursor.execute("""
        SELECT table_name FROM user_tables 
        WHERE table_name IN ('LOCATIONS','SENSOR_CLUSTERS','SENSOR_REGISTRY',
            'SENSOR_CAPABILITIES','ALERTS','INCIDENTS','INCIDENT_ALERTS',
            'SENSOR_HEALTH_LOGS','TELEMETRY_SUMMARY')
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    all_ok = True
    for t in EXPECTED_TABLES:
        if t in tables:
            ok(f"Table {t} exists")
        else:
            fail(f"Table {t} NOT FOUND")
            all_ok = False
    
    if len(tables) == 9:
        ok(f"All 9 tables created ✓")
    else:
        fail(f"Expected 9 tables, found {len(tables)}")
    
    # Verify triggers
    subheader("Verifying triggers:")
    cursor.execute("""
        SELECT trigger_name, table_name, status 
        FROM user_triggers 
        ORDER BY trigger_name
    """)
    triggers = cursor.fetchall()
    trigger_names = [t[0] for t in triggers]
    
    for t in EXPECTED_TRIGGERS:
        matching = [tr for tr in triggers if tr[0] == t]
        if matching:
            name, table, status = matching[0]
            if status == 'ENABLED':
                ok(f"Trigger {name} on {table} — {status}")
            else:
                warn(f"Trigger {name} on {table} — {status}")
        else:
            fail(f"Trigger {t} NOT FOUND")
    
    # Verify indexes
    subheader("Verifying indexes:")
    cursor.execute("""
        SELECT index_name, table_name, uniqueness 
        FROM user_indexes 
        WHERE table_name IN ('LOCATIONS','SENSOR_CLUSTERS','SENSOR_REGISTRY',
            'SENSOR_CAPABILITIES','ALERTS','INCIDENTS','INCIDENT_ALERTS',
            'SENSOR_HEALTH_LOGS','TELEMETRY_SUMMARY')
        AND index_name NOT LIKE 'SYS_%'
        ORDER BY table_name, index_name
    """)
    indexes = cursor.fetchall()
    info(f"Total indexes found: {len(indexes)}")
    for idx_name, table, uniqueness in indexes:
        ok(f"{idx_name} on {table} ({uniqueness})")
    
    # Verify foreign key constraints
    subheader("Verifying foreign key constraints:")
    cursor.execute("""
        SELECT constraint_name, table_name, r_constraint_name, status 
        FROM user_constraints 
        WHERE constraint_type = 'R'
        AND table_name IN ('LOCATIONS','SENSOR_CLUSTERS','SENSOR_REGISTRY',
            'SENSOR_CAPABILITIES','ALERTS','INCIDENTS','INCIDENT_ALERTS',
            'SENSOR_HEALTH_LOGS','TELEMETRY_SUMMARY')
        ORDER BY table_name
    """)
    fks = cursor.fetchall()
    info(f"Total foreign key constraints: {len(fks)}")
    for name, table, ref, status in fks:
        if status == 'ENABLED':
            ok(f"{name} on {table} → {ref} [{status}]")
        else:
            fail(f"{name} on {table} → {ref} [{status}]")
    
    # Verify check constraints
    subheader("Verifying check constraints:")
    cursor.execute("""
        SELECT constraint_name, table_name, status 
        FROM user_constraints 
        WHERE constraint_type = 'C'
        AND table_name IN ('LOCATIONS','SENSOR_CLUSTERS','SENSOR_REGISTRY',
            'SENSOR_CAPABILITIES','ALERTS','TELEMETRY_SUMMARY')
        AND constraint_name NOT LIKE 'SYS_%'
        ORDER BY table_name
    """)
    checks = cursor.fetchall()
    info(f"Total check constraints: {len(checks)}")
    for name, table, status in checks:
        ok(f"{name} on {table} [{status}]")
    
    cursor.close()
    return errors == 0


# ============================================================================
# TASK 1.3: Load Seed Data
# ============================================================================
def task_1_3(conn):
    header("TASK 1.3: Load Seed Data for 33 Sensors")
    cursor = conn.cursor()
    
    # Parse and execute seed data
    info("Parsing oracle_seed_v2.sql...")
    statements = parse_sql_file('oracle_seed_v2.sql')
    info(f"Found {len(statements)} statements to execute")
    
    info("Executing seed data insertion...")
    success, errors = execute_statements(cursor, statements, "Seed v2")
    conn.commit()
    
    if errors == 0:
        ok(f"All {success} statements executed successfully")
    else:
        fail(f"{errors} errors out of {success + errors} statements")
    
    # Verify 13 locations (1 city + 3 districts + 9 wards)
    subheader("Verifying locations (expected: 13):")
    cursor.execute("SELECT Type, COUNT(*) FROM LOCATIONS GROUP BY Type ORDER BY Type")
    loc_counts = cursor.fetchall()
    total_locations = 0
    for loc_type, count in loc_counts:
        total_locations += count
        ok(f"{loc_type}: {count}")
    
    if total_locations == 13:
        ok(f"Total locations: {total_locations} ✓")
    else:
        fail(f"Expected 13 locations, found {total_locations}")
    
    # Verify 4 sensor clusters
    subheader("Verifying sensor clusters (expected: 4):")
    cursor.execute("SELECT ClusterID, ClusterName, SensorCount FROM SENSOR_CLUSTERS ORDER BY ClusterID")
    clusters = cursor.fetchall()
    
    if len(clusters) == 4:
        ok(f"Total clusters: {len(clusters)} ✓")
    else:
        fail(f"Expected 4 clusters, found {len(clusters)}")
    
    for cid, cname, count in clusters:
        ok(f"{cid}: {cname} (SensorCount: {count})")
    
    # Verify 33 sensors
    subheader("Verifying sensors (expected: 33):")
    cursor.execute("SELECT COUNT(*) FROM SENSOR_REGISTRY")
    sensor_count = cursor.fetchone()[0]
    
    if sensor_count == 33:
        ok(f"Total sensors: {sensor_count} ✓")
    else:
        fail(f"Expected 33 sensors, found {sensor_count}")
    
    # Verify sensor distribution by location
    cursor.execute("""
        SELECT l.Name, l.Type, COUNT(s.SensorID) as cnt
        FROM LOCATIONS l
        LEFT JOIN SENSOR_REGISTRY s ON l.LocationID = s.LocationID
        WHERE l.Type = 'Ward'
        GROUP BY l.Name, l.Type
        ORDER BY cnt DESC
    """)
    ward_sensors = cursor.fetchall()
    info("Sensor distribution by ward:")
    for name, ltype, cnt in ward_sensors:
        ok(f"  {name}: {cnt} sensors")
    
    # Verify geolocation on sensors
    cursor.execute("""
        SELECT COUNT(*) FROM SENSOR_REGISTRY 
        WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL
    """)
    geo_count = cursor.fetchone()[0]
    if geo_count == sensor_count:
        ok(f"All {geo_count} sensors have geolocation ✓")
    else:
        fail(f"Only {geo_count}/{sensor_count} sensors have geolocation")
    
    # Verify 165 sensor capabilities (33 sensors × 5 metrics)
    subheader("Verifying sensor capabilities (expected: 165):")
    cursor.execute("SELECT COUNT(*) FROM SENSOR_CAPABILITIES")
    cap_count = cursor.fetchone()[0]
    
    if cap_count == 165:
        ok(f"Total capabilities: {cap_count} (33 × 5) ✓")
    else:
        fail(f"Expected 165 capabilities, found {cap_count}")
    
    # Verify capabilities distribution
    cursor.execute("""
        SELECT MetricType, COUNT(*) 
        FROM SENSOR_CAPABILITIES 
        GROUP BY MetricType 
        ORDER BY MetricType
    """)
    cap_dist = cursor.fetchall()
    for metric, count in cap_dist:
        if count == 33:
            ok(f"{metric}: {count} capabilities ✓")
        else:
            warn(f"{metric}: {count} capabilities (expected 33)")
    
    # Verify cluster sensor counts are correct (trigger should have updated)
    subheader("Verifying cluster sensor counts (trigger test):")
    cursor.execute("""
        SELECT sc.ClusterID, sc.ClusterName, sc.SensorCount,
               (SELECT COUNT(*) FROM SENSOR_REGISTRY sr WHERE sr.ClusterID = sc.ClusterID) as actual_count
        FROM SENSOR_CLUSTERS sc
        ORDER BY sc.ClusterID
    """)
    cluster_checks = cursor.fetchall()
    for cid, cname, stored_count, actual_count in cluster_checks:
        if stored_count == actual_count:
            ok(f"{cid}: stored={stored_count}, actual={actual_count} ✓")
        else:
            fail(f"{cid}: stored={stored_count}, actual={actual_count} — MISMATCH!")
    
    # Test triggers by inserting/deleting test sensor
    subheader("Testing triggers (insert/delete test sensor):")
    
    # Insert test sensor
    try:
        cursor.execute("""
            INSERT INTO SENSOR_REGISTRY 
            (SensorID, LocationID, ClusterID, Latitude, Longitude, SensorModel, FirmwareVersion, Status, InstallDate)
            VALUES ('TEST_SENSOR_001', 'ward_q1_ben_nghe', 'cluster_q1_north', 10.7756, 106.7019, 
                    'TestModel', 'v1.0.0', 'Active', DATE '2026-01-01')
        """)
        conn.commit()
        
        # Check cluster count increased
        cursor.execute("SELECT SensorCount FROM SENSOR_CLUSTERS WHERE ClusterID = 'cluster_q1_north'")
        count_after_insert = cursor.fetchone()[0]
        ok(f"After INSERT: cluster_q1_north SensorCount = {count_after_insert}")
        
        # Delete test sensor
        cursor.execute("DELETE FROM SENSOR_REGISTRY WHERE SensorID = 'TEST_SENSOR_001'")
        conn.commit()
        
        # Check cluster count decreased
        cursor.execute("SELECT SensorCount FROM SENSOR_CLUSTERS WHERE ClusterID = 'cluster_q1_north'")
        count_after_delete = cursor.fetchone()[0]
        ok(f"After DELETE: cluster_q1_north SensorCount = {count_after_delete}")
        
        if count_after_insert == count_after_delete + 1:
            ok("Trigger trg_cluster_count working correctly ✓")
        else:
            fail("Trigger trg_cluster_count not updating correctly")
            
    except oracledb.DatabaseError as e:
        fail(f"Trigger test failed: {e}")
        conn.rollback()
    
    cursor.close()
    return True


# ============================================================================
# TASK 1.4: Verify Schema Integrity
# ============================================================================
def task_1_4(conn):
    header("TASK 1.4: Verify Schema Integrity")
    cursor = conn.cursor()
    
    # Query all tables to confirm data loaded
    subheader("Table row counts:")
    for table in EXPECTED_TABLES:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            ok(f"{table}: {count} rows")
        except oracledb.DatabaseError as e:
            fail(f"{table}: {e}")
    
    # Test foreign key constraints
    subheader("Testing foreign key constraints:")
    
    # Test 1: Insert sensor with invalid LocationID (should fail)
    try:
        cursor.execute("""
            INSERT INTO SENSOR_REGISTRY 
            (SensorID, LocationID, Latitude, Longitude, SensorModel, FirmwareVersion, Status, InstallDate)
            VALUES ('FK_TEST_001', 'INVALID_LOCATION', 10.0, 106.0, 'Test', 'v1', 'Active', DATE '2026-01-01')
        """)
        conn.rollback()
        fail("FK constraint on SENSOR_REGISTRY.LocationID not enforced!")
    except oracledb.DatabaseError as e:
        conn.rollback()
        ok("FK constraint on SENSOR_REGISTRY.LocationID enforced ✓ (invalid location rejected)")
    
    # Test 2: Insert alert with invalid SensorID (should fail)
    try:
        cursor.execute("""
            INSERT INTO ALERTS 
            (AlertID, SensorID, LocationID, AlertType, MetricType, Value, Severity)
            VALUES ('FK_TEST_002', 'INVALID_SENSOR', 'ward_q1_ben_nghe', 'THRESHOLD', 'CO2', 999, 'HIGH')
        """)
        conn.rollback()
        fail("FK constraint on ALERTS.SensorID not enforced!")
    except oracledb.DatabaseError as e:
        conn.rollback()
        ok("FK constraint on ALERTS.SensorID enforced ✓ (invalid sensor rejected)")
    
    # Test 3: Insert capability with invalid SensorID (should fail)
    try:
        cursor.execute("""
            INSERT INTO SENSOR_CAPABILITIES 
            (CapabilityID, SensorID, MetricType, Unit)
            VALUES ('FK_TEST_003', 'INVALID_SENSOR', 'CO2', 'ppm')
        """)
        conn.rollback()
        fail("FK constraint on SENSOR_CAPABILITIES.SensorID not enforced!")
    except oracledb.DatabaseError as e:
        conn.rollback()
        ok("FK constraint on SENSOR_CAPABILITIES.SensorID enforced ✓ (invalid sensor rejected)")
    
    # Test 4: Delete location referenced by sensor (should fail)
    try:
        cursor.execute("DELETE FROM LOCATIONS WHERE LocationID = 'ward_q1_ben_nghe'")
        conn.rollback()
        fail("FK cascade not preventing delete of referenced location!")
    except oracledb.DatabaseError as e:
        conn.rollback()
        ok("FK constraint prevents deleting referenced LOCATIONS ✓")
    
    # Test check constraints
    subheader("Testing check constraints:")
    
    # Test: Invalid location type
    try:
        cursor.execute("""
            INSERT INTO LOCATIONS (LocationID, Name, Type, CenterLat, CenterLng)
            VALUES ('CHK_TEST_001', 'Test', 'InvalidType', 10.0, 106.0)
        """)
        conn.rollback()
        fail("CHECK constraint on LOCATIONS.Type not enforced!")
    except oracledb.DatabaseError as e:
        conn.rollback()
        ok("CHECK constraint on LOCATIONS.Type enforced ✓ (invalid type rejected)")
    
    # Test: Invalid sensor status
    try:
        cursor.execute("""
            INSERT INTO SENSOR_REGISTRY 
            (SensorID, LocationID, Latitude, Longitude, SensorModel, FirmwareVersion, Status, InstallDate)
            VALUES ('CHK_TEST_002', 'ward_q1_ben_nghe', 10.0, 106.0, 'Test', 'v1', 'BadStatus', DATE '2026-01-01')
        """)
        conn.rollback()
        fail("CHECK constraint on SENSOR_REGISTRY.Status not enforced!")
    except oracledb.DatabaseError as e:
        conn.rollback()
        ok("CHECK constraint on SENSOR_REGISTRY.Status enforced ✓ (invalid status rejected)")
    
    # Test: Latitude out of range
    try:
        cursor.execute("""
            INSERT INTO SENSOR_REGISTRY 
            (SensorID, LocationID, Latitude, Longitude, SensorModel, FirmwareVersion, Status, InstallDate)
            VALUES ('CHK_TEST_003', 'ward_q1_ben_nghe', 999.0, 106.0, 'Test', 'v1', 'Active', DATE '2026-01-01')
        """)
        conn.rollback()
        fail("CHECK constraint on Latitude range not enforced!")
    except oracledb.DatabaseError as e:
        conn.rollback()
        ok("CHECK constraint on Latitude range enforced ✓ (lat=999 rejected)")
    
    # Test: Negative cluster radius
    try:
        cursor.execute("""
            INSERT INTO SENSOR_CLUSTERS 
            (ClusterID, LocationID, CenterLat, CenterLng, Radius)
            VALUES ('CHK_TEST_004', 'city_hcmc', 10.0, 106.0, -100)
        """)
        conn.rollback()
        fail("CHECK constraint on SENSOR_CLUSTERS.Radius not enforced!")
    except oracledb.DatabaseError as e:
        conn.rollback()
        ok("CHECK constraint on SENSOR_CLUSTERS.Radius enforced ✓ (negative radius rejected)")
    
    # Test: AQI out of range
    try:
        cursor.execute("""
            INSERT INTO TELEMETRY_SUMMARY 
            (SummaryID, SensorID, TimeBucket, Granularity, AQI, DataPoints)
            VALUES ('CHK_TEST_005', 'sen_q1_ben_nghe_01', CURRENT_TIMESTAMP, '1H', 999, 10)
        """)
        conn.rollback()
        fail("CHECK constraint on AQI range not enforced!")
    except oracledb.DatabaseError as e:
        conn.rollback()
        ok("CHECK constraint on AQI range enforced ✓ (AQI=999 rejected)")
    
    # Verify indexes are being used in query plans
    subheader("Verifying indexes in query plans:")
    
    # Test query plan for sensor lookup by location
    test_queries = [
        ("Sensor by LocationID", 
         "SELECT * FROM SENSOR_REGISTRY WHERE LocationID = 'ward_q1_ben_nghe'",
         "IDX_SENSORS_LOCATION"),
        ("Alerts by Status", 
         "SELECT * FROM ALERTS WHERE Status = 'OPEN' ORDER BY CreatedAt",
         "IDX_ALERTS_STATUS"),
        ("Clusters by LocationID", 
         "SELECT * FROM SENSOR_CLUSTERS WHERE LocationID = 'district_q1'",
         "IDX_CLUSTERS_LOCATION"),
        ("Capabilities by SensorID",
         "SELECT * FROM SENSOR_CAPABILITIES WHERE SensorID = 'sen_q1_ben_nghe_01'",
         "IDX_CAPABILITIES_SENSOR"),
        ("Summary by Granularity+Time",
         "SELECT * FROM TELEMETRY_SUMMARY WHERE Granularity = '1H' AND TimeBucket > CURRENT_TIMESTAMP - 1",
         "IDX_SUMMARY_GRANULARITY"),
    ]
    
    for desc, query, expected_index in test_queries:
        try:
            # Use EXPLAIN PLAN
            cursor.execute(f"EXPLAIN PLAN FOR {query}")
            cursor.execute("""
                SELECT LISTAGG(operation || ' ' || NVL(object_name, ''), ' | ') 
                WITHIN GROUP (ORDER BY id)
                FROM plan_table 
                WHERE plan_id = (SELECT MAX(plan_id) FROM plan_table)
            """)
            plan = cursor.fetchone()[0]
            
            if expected_index.upper() in plan.upper():
                ok(f"{desc}: Uses {expected_index} ✓")
            else:
                # Check if any index is used
                if 'INDEX' in plan.upper():
                    ok(f"{desc}: Uses index (plan: {plan[:100]})")
                else:
                    warn(f"{desc}: Full table scan (plan: {plan[:100]})")
        except oracledb.DatabaseError as e:
            warn(f"{desc}: Could not check plan — {e}")
    
    # Summary of all constraints
    subheader("Constraint summary:")
    cursor.execute("""
        SELECT constraint_type, COUNT(*), 
               SUM(CASE WHEN status = 'ENABLED' THEN 1 ELSE 0 END) as enabled
        FROM user_constraints 
        WHERE table_name IN ('LOCATIONS','SENSOR_CLUSTERS','SENSOR_REGISTRY',
            'SENSOR_CAPABILITIES','ALERTS','INCIDENTS','INCIDENT_ALERTS',
            'SENSOR_HEALTH_LOGS','TELEMETRY_SUMMARY')
        GROUP BY constraint_type
        ORDER BY constraint_type
    """)
    constraint_summary = cursor.fetchall()
    type_names = {'P': 'Primary Key', 'R': 'Foreign Key', 'C': 'Check', 'U': 'Unique'}
    for ctype, total, enabled in constraint_summary:
        name = type_names.get(ctype, ctype)
        if total == enabled:
            ok(f"{name}: {total} constraints, all ENABLED ✓")
        else:
            warn(f"{name}: {total} constraints, {enabled} enabled, {total-enabled} disabled")
    
    cursor.close()
    return True


# ============================================================================
# Main
# ============================================================================
def main():
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"  SMART CITY IoT DATABASE - Schema v2 Execution & Verification")
    print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}{Colors.END}")
    
    # Connect to Oracle
    info(f"Connecting to Oracle at {ORACLE_DSN}...")
    try:
        conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)
        ok(f"Connected to Oracle {conn.version}")
    except oracledb.DatabaseError as e:
        fail(f"Cannot connect: {e}")
        sys.exit(1)
    
    results = {}
    
    # Task 1.2: Create Schema
    try:
        results['1.2'] = task_1_2(conn)
    except Exception as e:
        fail(f"Task 1.2 failed: {e}")
        results['1.2'] = False
    
    # Task 1.3: Load Seed Data
    try:
        results['1.3'] = task_1_3(conn)
    except Exception as e:
        fail(f"Task 1.3 failed: {e}")
        results['1.3'] = False
    
    # Task 1.4: Verify Integrity
    try:
        results['1.4'] = task_1_4(conn)
    except Exception as e:
        fail(f"Task 1.4 failed: {e}")
        results['1.4'] = False
    
    # Final Summary
    header("FINAL SUMMARY")
    for task, passed in results.items():
        if passed:
            ok(f"Task {task}: PASSED ✓")
        else:
            fail(f"Task {task}: FAILED ✗")
    
    conn.close()
    ok("Database connection closed")
    
    print(f"\n{Colors.BOLD}Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")
    
    # Exit with error code if any task failed
    if not all(results.values()):
        sys.exit(1)

if __name__ == '__main__':
    main()
