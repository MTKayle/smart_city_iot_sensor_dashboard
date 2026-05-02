#!/usr/bin/env python3
"""
Execute Oracle Schema v2 Creation Script
Reads and executes the oracle_schema_v2.sql file
"""
import cx_Oracle
import os
import sys

def execute_schema():
    """Execute the Oracle schema v2 creation script"""
    
    # Database connection parameters
    username = os.getenv('ORACLE_USER', 'system')
    password = os.getenv('ORACLE_PASSWORD', 'OraclePass123')
    dsn = os.getenv('ORACLE_DSN', 'localhost:1521/XEPDB1')
    
    print(f"Connecting to Oracle: {username}@{dsn}")
    
    try:
        # Connect to Oracle
        connection = cx_Oracle.connect(
            user=username,
            password=password,
            dsn=dsn
        )
        
        print("✓ Connected to Oracle successfully")
        
        cursor = connection.cursor()
        
        # Read the SQL file
        sql_file = 'backend/app/db/sql/oracle_schema_v2.sql'
        print(f"\nReading SQL file: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by PL/SQL blocks and regular statements
        statements = []
        current_statement = []
        in_plsql_block = False
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('--'):
                continue
            
            # Check for PL/SQL block start
            if stripped.upper().startswith('BEGIN') or stripped.upper().startswith('CREATE OR REPLACE TRIGGER'):
                in_plsql_block = True
            
            current_statement.append(line)
            
            # Check for statement end
            if in_plsql_block:
                if stripped == '/' or stripped.endswith('/'):
                    statements.append('\n'.join(current_statement))
                    current_statement = []
                    in_plsql_block = False
            else:
                if stripped.endswith(';'):
                    statements.append('\n'.join(current_statement))
                    current_statement = []
        
        # Execute each statement
        print(f"\nExecuting {len(statements)} SQL statements...\n")
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            statement = statement.strip()
            if not statement:
                continue
            
            # Remove trailing / or ;
            statement = statement.rstrip('/').rstrip(';').strip()
            
            if not statement:
                continue
            
            try:
                # Show what we're executing (first 80 chars)
                preview = statement[:80].replace('\n', ' ')
                print(f"[{i}/{len(statements)}] {preview}...")
                
                cursor.execute(statement)
                success_count += 1
                print(f"    ✓ Success")
                
            except cx_Oracle.DatabaseError as e:
                error_obj, = e.args
                
                # Ignore "table does not exist" errors during DROP
                if 'ORA-00942' in str(error_obj.message) and 'DROP' in statement.upper():
                    print(f"    ⊘ Skipped (table doesn't exist)")
                    continue
                
                # Ignore "object does not exist" errors
                if 'ORA-04043' in str(error_obj.message):
                    print(f"    ⊘ Skipped (object doesn't exist)")
                    continue
                
                error_count += 1
                print(f"    ✗ Error: {error_obj.message}")
                
                # Don't stop on errors, continue with next statement
        
        # Commit all changes
        connection.commit()
        print(f"\n✓ Committed all changes")
        
        # Verify tables created
        print("\n" + "="*80)
        print("VERIFICATION: Checking created tables")
        print("="*80)
        
        cursor.execute("""
            SELECT table_name, num_rows 
            FROM user_tables 
            WHERE table_name IN (
                'LOCATIONS', 'SENSOR_CLUSTERS', 'SENSOR_REGISTRY', 
                'SENSOR_CAPABILITIES', 'ALERTS', 'INCIDENTS', 
                'INCIDENT_ALERTS', 'SENSOR_HEALTH_LOGS', 'TELEMETRY_SUMMARY'
            )
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n✓ Found {len(tables)} tables:")
            for table_name, num_rows in tables:
                rows_str = str(num_rows) if num_rows is not None else '0'
                print(f"  - {table_name}: {rows_str} rows")
        else:
            print("\n✗ No tables found!")
        
        # Check triggers
        print("\n" + "="*80)
        print("VERIFICATION: Checking triggers")
        print("="*80)
        
        cursor.execute("""
            SELECT trigger_name, table_name, status
            FROM user_triggers
            WHERE table_name IN (
                'LOCATIONS', 'SENSOR_CLUSTERS', 'SENSOR_REGISTRY', 'ALERTS'
            )
            ORDER BY trigger_name
        """)
        
        triggers = cursor.fetchall()
        
        if triggers:
            print(f"\n✓ Found {len(triggers)} triggers:")
            for trigger_name, table_name, status in triggers:
                status_icon = "✓" if status == "ENABLED" else "✗"
                print(f"  {status_icon} {trigger_name} on {table_name} ({status})")
        else:
            print("\n⚠ No triggers found")
        
        # Check indexes
        print("\n" + "="*80)
        print("VERIFICATION: Checking indexes")
        print("="*80)
        
        cursor.execute("""
            SELECT index_name, table_name, uniqueness
            FROM user_indexes
            WHERE table_name IN (
                'LOCATIONS', 'SENSOR_CLUSTERS', 'SENSOR_REGISTRY', 
                'SENSOR_CAPABILITIES', 'ALERTS', 'TELEMETRY_SUMMARY'
            )
            AND index_name NOT LIKE 'SYS_%'
            ORDER BY table_name, index_name
        """)
        
        indexes = cursor.fetchall()
        
        if indexes:
            print(f"\n✓ Found {len(indexes)} indexes:")
            current_table = None
            for index_name, table_name, uniqueness in indexes:
                if table_name != current_table:
                    print(f"\n  {table_name}:")
                    current_table = table_name
                unique_str = " (UNIQUE)" if uniqueness == "UNIQUE" else ""
                print(f"    - {index_name}{unique_str}")
        else:
            print("\n⚠ No indexes found")
        
        # Check foreign keys
        print("\n" + "="*80)
        print("VERIFICATION: Checking foreign key constraints")
        print("="*80)
        
        cursor.execute("""
            SELECT constraint_name, table_name, r_constraint_name, status
            FROM user_constraints
            WHERE constraint_type = 'R'
            AND table_name IN (
                'LOCATIONS', 'SENSOR_CLUSTERS', 'SENSOR_REGISTRY', 
                'SENSOR_CAPABILITIES', 'ALERTS', 'TELEMETRY_SUMMARY',
                'INCIDENT_ALERTS', 'SENSOR_HEALTH_LOGS'
            )
            ORDER BY table_name, constraint_name
        """)
        
        fks = cursor.fetchall()
        
        if fks:
            print(f"\n✓ Found {len(fks)} foreign key constraints:")
            current_table = None
            for fk_name, table_name, ref_constraint, status in fks:
                if table_name != current_table:
                    print(f"\n  {table_name}:")
                    current_table = table_name
                status_icon = "✓" if status == "ENABLED" else "✗"
                print(f"    {status_icon} {fk_name} ({status})")
        else:
            print("\n⚠ No foreign key constraints found")
        
        # Summary
        print("\n" + "="*80)
        print("EXECUTION SUMMARY")
        print("="*80)
        print(f"✓ Successful statements: {success_count}")
        print(f"✗ Failed statements: {error_count}")
        print(f"✓ Tables created: {len(tables)}")
        print(f"✓ Triggers created: {len(triggers)}")
        print(f"✓ Indexes created: {len(indexes)}")
        print(f"✓ Foreign keys created: {len(fks)}")
        
        if len(tables) == 9:
            print("\n✓✓✓ Schema v2 created successfully! ✓✓✓")
            return 0
        else:
            print(f"\n⚠ Warning: Expected 9 tables, found {len(tables)}")
            return 1
        
    except cx_Oracle.DatabaseError as e:
        error_obj, = e.args
        print(f"\n✗ Database error: {error_obj.message}")
        return 1
    
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        return 1
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == '__main__':
    sys.exit(execute_schema())
