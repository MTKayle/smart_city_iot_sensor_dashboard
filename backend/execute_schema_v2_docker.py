"""
Script to execute Oracle schema v2 creation and verify all database objects.
This version is designed to run inside a Docker container with Oracle access.
"""

import os
import sys
import logging
import oracledb
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Oracle configuration
ORACLE_USER = os.getenv("ORACLE_USER", "system")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "OraclePass123")
ORACLE_DSN = os.getenv("ORACLE_DSN", "oracle-xe:1521/XEPDB1")

# Schema file path
SCHEMA_V2_PATH = "/tmp/oracle_schema_v2.sql"


def parse_sql_file(file_path):
    """
    Parse SQL file into executable statements, handling PL/SQL blocks.
    
    Returns:
        List of SQL statements ready for execution
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    statements = []
    current_statement = []
    in_plsql_block = False
    in_comment_block = False
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            i += 1
            continue
        
        # Handle comment blocks
        if stripped.startswith('/*'):
            in_comment_block = True
        if '*/' in stripped:
            in_comment_block = False
            i += 1
            continue
        if in_comment_block or stripped.startswith('--'):
            i += 1
            continue
        
        # Check for PL/SQL block start
        if re.match(r'^(BEGIN|DECLARE|CREATE\s+(OR\s+REPLACE\s+)?TRIGGER)', stripped, re.IGNORECASE):
            in_plsql_block = True
        
        current_statement.append(line)
        
        # Check for statement terminator
        if stripped == '/' and in_plsql_block:
            # PL/SQL block terminator - exclude the '/'
            stmt = '\n'.join(current_statement[:-1]).strip()
            if stmt:
                statements.append(stmt)
            current_statement = []
            in_plsql_block = False
        elif stripped.endswith(';') and not in_plsql_block:
            # Regular SQL statement
            stmt = '\n'.join(current_statement).strip()
            if stmt and not stmt.startswith('--'):
                statements.append(stmt)
            current_statement = []
        
        i += 1
    
    # Add any remaining statement
    if current_statement:
        stmt = '\n'.join(current_statement).strip()
        if stmt and not stmt.startswith('--'):
            statements.append(stmt)
    
    return statements


def execute_statements(connection, statements):
    """Execute list of SQL statements."""
    cursor = connection.cursor()
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements):
        if not statement or statement.startswith('--'):
            continue
        
        try:
            logger.debug(f"Executing statement {i+1}/{len(statements)}: {statement[:80]}...")
            cursor.execute(statement)
            connection.commit()
            success_count += 1
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            # Ignore expected errors
            if error_obj.code in (955, 942, 4043, 1418):  # Object exists, doesn't exist, trigger doesn't exist, cannot drop
                logger.debug(f"Ignoring expected error {error_obj.code}: {error_obj.message[:100]}")
            else:
                logger.warning(f"Error executing statement: {error_obj.message[:200]}")
                error_count += 1
    
    cursor.close()
    logger.info(f"Executed {success_count} statements successfully, {error_count} errors")
    return success_count, error_count


def verify_tables(connection):
    """Verify all 9 tables are created."""
    logger.info("Verifying tables...")
    
    expected_tables = [
        'LOCATIONS', 'SENSOR_CLUSTERS', 'SENSOR_REGISTRY', 'SENSOR_CAPABILITIES',
        'ALERTS', 'INCIDENTS', 'INCIDENT_ALERTS', 'SENSOR_HEALTH_LOGS', 'TELEMETRY_SUMMARY'
    ]
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM user_tables 
        WHERE table_name IN ({})
    """.format(','.join([f"'{t}'" for t in expected_tables])))
    
    existing_tables = {row[0] for row in cursor.fetchall()}
    cursor.close()
    
    results = {}
    for table in expected_tables:
        exists = table in existing_tables
        results[table] = exists
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {table}")
    
    return results


def verify_triggers(connection):
    """Verify all triggers are created and enabled."""
    logger.info("Verifying triggers...")
    
    expected_triggers = [
        'TRG_LOCATIONS_UPDATED_AT', 'TRG_CLUSTERS_UPDATED_AT', 'TRG_SENSORS_UPDATED_AT',
        'TRG_ALERT_LOCATION_SYNC', 'TRG_CLUSTER_COUNT'
    ]
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT trigger_name, status
        FROM user_triggers
        WHERE trigger_name IN ({})
    """.format(','.join([f"'{t}'" for t in expected_triggers])))
    
    existing_triggers = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    
    results = {}
    for trigger in expected_triggers:
        exists = trigger in existing_triggers
        status_str = existing_triggers.get(trigger, 'N/A')
        results[trigger] = exists and status_str == 'ENABLED'
        status = "✓" if results[trigger] else "✗"
        logger.info(f"  {status} {trigger} ({status_str})")
    
    return results


def verify_indexes(connection):
    """Verify all indexes are created."""
    logger.info("Verifying indexes...")
    
    expected_indexes = [
        'IDX_LOCATIONS_PARENT', 'IDX_LOCATIONS_TYPE', 'IDX_CLUSTERS_LOCATION',
        'IDX_SENSORS_LOCATION', 'IDX_SENSORS_CLUSTER', 'IDX_SENSORS_STATUS',
        'IDX_CAPABILITIES_SENSOR', 'IDX_ALERTS_SENSOR', 'IDX_ALERTS_CLUSTER',
        'IDX_ALERTS_LOCATION', 'IDX_ALERTS_STATUS', 'IDX_ALERTS_TYPE',
        'IDX_INCIDENTS_STATUS', 'IDX_IA_INCIDENT', 'IDX_IA_ALERT',
        'IDX_HEALTH_SENSOR_TIME', 'IDX_SUMMARY_SENSOR', 'IDX_SUMMARY_CLUSTER',
        'IDX_SUMMARY_LOCATION', 'IDX_SUMMARY_TIME', 'IDX_SUMMARY_GRANULARITY'
    ]
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT index_name, status
        FROM user_indexes
        WHERE index_name IN ({})
    """.format(','.join([f"'{i}'" for i in expected_indexes])))
    
    existing_indexes = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    
    results = {}
    for index in expected_indexes:
        exists = index in existing_indexes
        status_str = existing_indexes.get(index, 'N/A')
        results[index] = exists and status_str == 'VALID'
        status = "✓" if results[index] else "✗"
        logger.info(f"  {status} {index} ({status_str})")
    
    return results


def verify_foreign_keys(connection):
    """Verify all foreign key constraints are active."""
    logger.info("Verifying foreign key constraints...")
    
    expected_fks = [
        'FK_LOCATIONS_PARENT', 'FK_CLUSTERS_LOCATION', 'FK_SENSORS_LOCATION',
        'FK_SENSORS_CLUSTER', 'FK_CAPABILITIES_SENSOR', 'FK_ALERT_SENSOR',
        'FK_ALERT_CLUSTER', 'FK_ALERT_LOCATION', 'FK_INCIDENT', 'FK_ALERT',
        'FK_HEALTH_SENSOR', 'FK_SUMMARY_SENSOR', 'FK_SUMMARY_CLUSTER', 'FK_SUMMARY_LOCATION'
    ]
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT constraint_name, status
        FROM user_constraints
        WHERE constraint_type = 'R'
        AND constraint_name IN ({})
    """.format(','.join([f"'{fk}'" for fk in expected_fks])))
    
    existing_fks = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    
    results = {}
    for fk in expected_fks:
        exists = fk in existing_fks
        status_str = existing_fks.get(fk, 'N/A')
        results[fk] = exists and status_str == 'ENABLED'
        status = "✓" if results[fk] else "✗"
        logger.info(f"  {status} {fk} ({status_str})")
    
    return results


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("Oracle Schema v2 Creation and Verification")
    logger.info("=" * 80)
    
    # Connect to Oracle
    try:
        logger.info(f"Connecting to Oracle: {ORACLE_DSN}")
        connection = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN
        )
        logger.info("Successfully connected to Oracle")
    except oracledb.DatabaseError as e:
        logger.error(f"Failed to connect to Oracle: {e}")
        sys.exit(1)
    
    try:
        # Parse and execute schema v2 script
        logger.info("\n" + "=" * 80)
        logger.info("Step 1: Parsing and executing oracle_schema_v2.sql")
        logger.info("=" * 80)
        
        statements = parse_sql_file(SCHEMA_V2_PATH)
        logger.info(f"Parsed {len(statements)} SQL statements")
        
        success_count, error_count = execute_statements(connection, statements)
        
        # Verify tables
        logger.info("\n" + "=" * 80)
        logger.info("Step 2: Verifying Tables (9 expected)")
        logger.info("=" * 80)
        table_results = verify_tables(connection)
        tables_ok = all(table_results.values())
        
        # Verify triggers
        logger.info("\n" + "=" * 80)
        logger.info("Step 3: Verifying Triggers (5 expected)")
        logger.info("=" * 80)
        trigger_results = verify_triggers(connection)
        triggers_ok = all(trigger_results.values())
        
        # Verify indexes
        logger.info("\n" + "=" * 80)
        logger.info("Step 4: Verifying Indexes (21 expected)")
        logger.info("=" * 80)
        index_results = verify_indexes(connection)
        indexes_ok = all(index_results.values())
        
        # Verify foreign keys
        logger.info("\n" + "=" * 80)
        logger.info("Step 5: Verifying Foreign Key Constraints (14 expected)")
        logger.info("=" * 80)
        fk_results = verify_foreign_keys(connection)
        fks_ok = all(fk_results.values())
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Tables:              {sum(table_results.values())}/9 {'✓' if tables_ok else '✗'}")
        logger.info(f"Triggers:            {sum(trigger_results.values())}/5 {'✓' if triggers_ok else '✗'}")
        logger.info(f"Indexes:             {sum(index_results.values())}/21 {'✓' if indexes_ok else '✗'}")
        logger.info(f"Foreign Keys:        {sum(fk_results.values())}/14 {'✓' if fks_ok else '✗'}")
        
        all_ok = tables_ok and triggers_ok and indexes_ok and fks_ok
        
        if all_ok:
            logger.info("\n✓ ALL VERIFICATIONS PASSED - Schema v2 successfully created!")
            sys.exit(0)
        else:
            logger.error("\n✗ SOME VERIFICATIONS FAILED - Please review the output above")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        connection.close()
        logger.info("\nOracle connection closed")


if __name__ == "__main__":
    main()
