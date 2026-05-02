"""
Oracle client module for Smart City IoT Dashboard.

This module provides connection pooling and operations for relational data including
location hierarchy, sensor registry, alerts, and telemetry summaries.

Validates: Requirements 1.1, 2.1, 6.3, 16.4
"""

import os
import sys
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
import oracledb

from app.models import Location, SensorRegistry, Alert

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Oracle configuration
ORACLE_USER = os.getenv("ORACLE_USER", "SMARTCITY")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "SmartCity2026!")
ORACLE_DSN = os.getenv("ORACLE_DSN", "oracle-xe:1521/XEPDB1")

# Retry configuration
MAX_RETRIES = 5

# Global flag to track if schema has been initialized
_schema_initialized = False
INITIAL_BACKOFF = 1  # seconds

# Schema and seed SQL file paths
SCHEMA_SQL_PATH = os.path.join(os.path.dirname(__file__), "sql", "oracle_schema.sql")
SEED_SQL_PATH = os.path.join(os.path.dirname(__file__), "sql", "oracle_seed.sql")


class OracleClient:
    """
    Oracle client with connection pooling and automatic schema initialization.
    
    Features:
    - Connection pooling for efficient resource usage
    - Automatic schema initialization on startup
    - Exponential backoff retry for transient failures
    - Support for location hierarchy, sensor registry, and alerts
    """
    
    def __init__(self):
        """Initialize Oracle client with connection pooling."""
        global _schema_initialized
        self._pool: Optional[oracledb.ConnectionPool] = None
        self._connect()
        # Schema initialization is now handled by startup.sh
        # which uses the v2 PL/SQL-aware parser
        _schema_initialized = True
    
    def _connect(self):
        """
        Establish connection pool to Oracle with exponential backoff retry.
        
        Implements retry logic for transient connection failures.
        Creates connection pool for efficient resource management.
        """
        retries = 0
        backoff = INITIAL_BACKOFF
        
        while retries < MAX_RETRIES:
            try:
                logger.info(f"Attempting to connect to Oracle (attempt {retries + 1}/{MAX_RETRIES})...")
                
                # Create connection pool
                self._pool = oracledb.create_pool(
                    user=ORACLE_USER,
                    password=ORACLE_PASSWORD,
                    dsn=ORACLE_DSN,
                    min=2,
                    max=10,
                    increment=1
                )
                
                # Test connection
                connection = self._pool.acquire()
                cursor = connection.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.close()
                self._pool.release(connection)
                
                logger.info("Successfully connected to Oracle")
                return
                
            except oracledb.DatabaseError as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    logger.error(f"Failed to connect to Oracle after {MAX_RETRIES} attempts: {e}")
                    raise
                
                logger.warning(f"Oracle connection failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)  # Exponential backoff, max 60 seconds

    
    def _initialize_schema(self):
        """
        Initialize Oracle database schema by executing SQL scripts.
        
        Runs schema creation script and seed data script on startup.
        Handles cases where tables already exist gracefully.
        
        Validates: Requirement 16.4
        """
        try:
            logger.info("Initializing Oracle database schema...")
            
            # Execute schema creation script
            if os.path.exists(SCHEMA_SQL_PATH):
                self._execute_sql_file(SCHEMA_SQL_PATH)
                logger.info("Schema initialization completed")
            else:
                logger.warning(f"Schema SQL file not found: {SCHEMA_SQL_PATH}")
            
            # Execute seed data script
            if os.path.exists(SEED_SQL_PATH):
                self._execute_sql_file(SEED_SQL_PATH)
                logger.info("Seed data initialization completed")
            else:
                logger.warning(f"Seed SQL file not found: {SEED_SQL_PATH}")
                
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            # Don't raise - allow system to continue if schema already exists
    
    def _execute_sql_file(self, file_path: str):
        """
        Execute SQL statements from a file.
        
        Args:
            file_path: Path to SQL file
        """
        connection = None
        try:
            connection = self._pool.acquire()
            cursor = connection.cursor()
            
            # Read SQL file
            with open(file_path, 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = sql_content.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                    except oracledb.DatabaseError as e:
                        error_obj, = e.args
                        # Ignore "name is already used" errors (ORA-00955)
                        if error_obj.code == 955:
                            logger.debug(f"Object already exists, skipping: {statement[:50]}...")
                        else:
                            logger.warning(f"SQL execution warning: {e}")
            
            connection.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to execute SQL file {file_path}: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                self._pool.release(connection)
    
    def _execute_with_retry(self, operation_name: str, operation_func) -> Any:
        """
        Execute database operation with exponential backoff retry.
        
        Args:
            operation_name: Name of operation for logging
            operation_func: Function to execute (should return result)
        
        Returns:
            Result from operation_func
        """
        retries = 0
        backoff = INITIAL_BACKOFF
        
        while retries < MAX_RETRIES:
            connection = None
            try:
                logger.info(f"{operation_name}: Acquiring connection from pool...")
                start_time = time.time()
                connection = self._pool.acquire()
                acquire_time = time.time() - start_time
                logger.info(f"{operation_name}: Connection acquired in {acquire_time:.2f}s")
                
                result = operation_func(connection)
                total_time = time.time() - start_time
                logger.info(f"{operation_name}: Operation completed in {total_time:.2f}s")
                return result
                
            except oracledb.DatabaseError as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    logger.error(f"{operation_name} failed after {MAX_RETRIES} attempts: {e}")
                    raise
                
                logger.warning(f"{operation_name} failed: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                
            finally:
                if connection:
                    self._pool.release(connection)
        
        raise Exception(f"{operation_name} failed after {MAX_RETRIES} retries")

    
    def insert_location(self, location: Location) -> bool:
        """
        Insert location record into LOCATIONS table.
        
        Args:
            location: Location object containing hierarchy information
        
        Returns:
            bool: True if insertion successful, False otherwise
        
        Validates: Requirement 1.1
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type)
                    VALUES (:location_id, :name, :parent_id, :type)
                    """,
                    {
                        'location_id': location.locationId,
                        'name': location.name,
                        'parent_id': location.parentId,
                        'type': location.type
                    }
                )
                connection.commit()
                logger.debug(f"Inserted location {location.locationId}")
                return True
            except oracledb.DatabaseError as e:
                connection.rollback()
                logger.error(f"Failed to insert location {location.locationId}: {e}")
                return False
            finally:
                cursor.close()
        
        try:
            return self._execute_with_retry("insert_location", operation)
        except Exception:
            return False
    
    def get_location_hierarchy(self, location_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve location hierarchy using recursive query.
        
        Args:
            location_id: Optional location ID to filter hierarchy (returns subtree)
        
        Returns:
            List of location dictionaries with hierarchy information
        
        Validates: Requirement 1.3
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                if location_id:
                    # Get subtree for specific location
                    cursor.execute(
                        """
                        WITH hierarchy (LocationID, Name, ParentID, Type, Path, Level) AS (
                            SELECT LocationID, Name, ParentID, Type,
                                   LocationID as Path, 0 as Level
                            FROM LOCATIONS
                            WHERE LocationID = :location_id
                            UNION ALL
                            SELECT l.LocationID, l.Name, l.ParentID, l.Type,
                                   h.Path || ' > ' || l.LocationID as Path,
                                   h.Level + 1 as Level
                            FROM LOCATIONS l
                            INNER JOIN hierarchy h ON l.ParentID = h.LocationID
                        )
                        SELECT * FROM hierarchy ORDER BY Level, LocationID
                        """,
                        {'location_id': location_id}
                    )
                else:
                    # Get complete hierarchy
                    cursor.execute(
                        """
                        SELECT LocationID, Name, ParentID, Type, Path, HierarchyLevel
                        FROM LOCATION_HIERARCHY
                        ORDER BY HierarchyLevel, LocationID
                        """
                    )
                
                columns = [col[0].lower() for col in cursor.description]
                results = []
                for row in cursor:
                    row_dict = dict(zip(columns, row))
                    # Map hierarchylevel to level for consistency
                    if 'hierarchylevel' in row_dict:
                        row_dict['level'] = row_dict['hierarchylevel']
                    results.append(row_dict)
                
                logger.debug(f"Retrieved {len(results)} locations from hierarchy")
                return results
                
            finally:
                cursor.close()
        
        try:
            return self._execute_with_retry("get_location_hierarchy", operation)
        except Exception as e:
            logger.error(f"Failed to retrieve location hierarchy: {e}")
            return []

    
    def insert_sensor(self, sensor: SensorRegistry) -> bool:
        """
        Insert sensor record into SENSOR_REGISTRY table.
        
        Args:
            sensor: Sensor object containing registration information
        
        Returns:
            bool: True if insertion successful, False otherwise
        
        Validates: Requirement 2.1
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType, RegisteredAt)
                    VALUES (:sensor_id, :location_id, :sensor_type, :registered_at)
                    """,
                    {
                        'sensor_id': sensor.sensorId,
                        'location_id': sensor.locationId,
                        'sensor_type': sensor.sensorType,
                        'registered_at': sensor.registeredAt
                    }
                )
                connection.commit()
                logger.debug(f"Inserted sensor {sensor.sensorId}")
                return True
            except oracledb.DatabaseError as e:
                connection.rollback()
                logger.error(f"Failed to insert sensor {sensor.sensorId}: {e}")
                return False
            finally:
                cursor.close()
        
        try:
            return self._execute_with_retry("insert_sensor", operation)
        except Exception:
            return False
    
    def get_sensors(self, location_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve sensor records with optional location filter.
        
        Args:
            location_id: Optional location ID to filter sensors
        
        Returns:
            List of sensor dictionaries with location information
        
        Validates: Requirement 2.1
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                if location_id:
                    cursor.execute(
                        """
                        SELECT s.SensorID, s.LocationID, s.SensorType, s.RegisteredAt,
                               l.Name as LocationName, l.Type as LocationType
                        FROM SENSOR_REGISTRY s
                        INNER JOIN LOCATIONS l ON s.LocationID = l.LocationID
                        WHERE s.LocationID = :location_id
                        ORDER BY s.RegisteredAt DESC
                        """,
                        {'location_id': location_id}
                    )
                else:
                    cursor.execute(
                        """
                        SELECT s.SensorID, s.LocationID, s.SensorType, s.RegisteredAt,
                               l.Name as LocationName, l.Type as LocationType
                        FROM SENSOR_REGISTRY s
                        INNER JOIN LOCATIONS l ON s.LocationID = l.LocationID
                        ORDER BY s.RegisteredAt DESC
                        """
                    )
                
                columns = [col[0].lower() for col in cursor.description]
                results = []
                for row in cursor:
                    results.append(dict(zip(columns, row)))
                
                logger.debug(f"Retrieved {len(results)} sensors")
                return results
                
            finally:
                cursor.close()
        
        try:
            return self._execute_with_retry("get_sensors", operation)
        except Exception as e:
            logger.error(f"Failed to retrieve sensors: {e}")
            return []

    
    def insert_alert(self, alert: Alert) -> bool:
        """
        Insert alert record into ALERTS table.
        
        Args:
            alert: Alert object containing threshold violation information
        
        Returns:
            bool: True if insertion successful, False otherwise
        
        Validates: Requirement 6.3
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO ALERTS (AlertID, SensorID, MetricType, Value, AlertLevel, CreatedAt)
                    VALUES (:alert_id, :sensor_id, :metric_type, :value, :alert_level, :created_at)
                    """,
                    {
                        'alert_id': alert.alertId,
                        'sensor_id': alert.sensorId,
                        'metric_type': alert.metricType,
                        'value': alert.value,
                        'alert_level': alert.level,
                        'created_at': alert.createdAt
                    }
                )
                connection.commit()
                logger.debug(f"Inserted alert {alert.alertId}")
                return True
            except oracledb.DatabaseError as e:
                connection.rollback()
                logger.error(f"Failed to insert alert {alert.alertId}: {e}")
                return False
            finally:
                cursor.close()
        
        try:
            return self._execute_with_retry("insert_alert", operation)
        except Exception:
            return False
    
    def get_alerts(
        self,
        level: Optional[str] = None,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve alert records with optional filters.
        
        Args:
            level: Optional alert level filter (LOW, MEDIUM, HIGH)
            location_id: Optional location ID filter
            limit: Maximum number of alerts to return (default: 100)
        
        Returns:
            List of alert dictionaries sorted by creation time descending
        
        Validates: Requirement 6.3
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                # Build query with optional filters
                query = """
                    SELECT a.AlertID, a.SensorID, a.MetricType, a.Value, a.AlertLevel, a.CreatedAt,
                           s.LocationID, l.Name as LocationName
                    FROM ALERTS a
                    INNER JOIN SENSOR_REGISTRY s ON a.SensorID = s.SensorID
                    INNER JOIN LOCATIONS l ON s.LocationID = l.LocationID
                    WHERE 1=1
                """
                params = {}
                
                if level:
                    query += " AND a.AlertLevel = :p_level"
                    params['p_level'] = level
                
                if location_id:
                    query += " AND s.LocationID = :p_location_id"
                    params['p_location_id'] = location_id
                
                query += " ORDER BY a.CreatedAt DESC FETCH FIRST :p_limit ROWS ONLY"
                params['p_limit'] = limit
                
                cursor.execute(query, params)
                
                columns = [col[0].lower() for col in cursor.description]
                results = []
                for row in cursor:
                    results.append(dict(zip(columns, row)))
                
                logger.debug(f"Retrieved {len(results)} alerts")
                return results
                
            finally:
                cursor.close()
        
        try:
            return self._execute_with_retry("get_alerts", operation)
        except Exception as e:
            logger.error(f"Failed to retrieve alerts: {e}")
            return []

    
    def insert_or_update_telemetry_summary(
        self,
        summary_id: str,
        location_id: str,
        summary_date: date,
        avg_co2: float,
        avg_noise: float,
        avg_temperature: float,
        clean_score: float
    ) -> bool:
        """
        Insert or update daily telemetry summary in TELEMETRY_SUMMARY table.
        
        Uses MERGE statement to insert new record or update existing one based on
        unique constraint (LocationID, Date). This ensures only one summary per
        location per day.
        
        Args:
            summary_id: Unique identifier for the summary
            location_id: Location identifier
            summary_date: Date for the summary
            avg_co2: Average CO2 level in ppm
            avg_noise: Average noise level in dB
            avg_temperature: Average temperature in °C
            clean_score: Calculated Clean Score (0-100)
        
        Returns:
            bool: True if operation successful, False otherwise
        
        Validates: Requirement 8.3
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                # Use MERGE to insert or update based on unique constraint
                cursor.execute(
                    """
                    MERGE INTO TELEMETRY_SUMMARY ts
                    USING (
                        SELECT :location_id as LocationID, :summary_date as SummaryDate FROM DUAL
                    ) src
                    ON (ts.LocationID = src.LocationID AND ts.SummaryDate = src.SummaryDate)
                    WHEN MATCHED THEN
                        UPDATE SET
                            AvgCO2 = :avg_co2,
                            AvgNoise = :avg_noise,
                            AvgTemperature = :avg_temperature,
                            CleanScore = :clean_score
                    WHEN NOT MATCHED THEN
                        INSERT (SummaryID, LocationID, SummaryDate, AvgCO2, AvgNoise, AvgTemperature, CleanScore)
                        VALUES (:summary_id, :location_id, :summary_date, :avg_co2, :avg_noise, :avg_temperature, :clean_score)
                    """,
                    {
                        'summary_id': summary_id,
                        'location_id': location_id,
                        'summary_date': summary_date,
                        'avg_co2': avg_co2,
                        'avg_noise': avg_noise,
                        'avg_temperature': avg_temperature,
                        'clean_score': clean_score
                    }
                )
                connection.commit()
                logger.debug(f"Inserted/updated telemetry summary for location {location_id} on {summary_date}")
                return True
            except oracledb.DatabaseError as e:
                connection.rollback()
                logger.error(f"Failed to insert/update telemetry summary: {e}")
                return False
            finally:
                cursor.close()
        
        try:
            return self._execute_with_retry("insert_or_update_telemetry_summary", operation)
        except Exception:
            return False
    
    def get_leaderboard(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve leaderboard of locations ranked by Clean Score.
        
        Queries the most recent telemetry summaries for each location and
        orders them by Clean Score descending (highest score = cleanest location).
        
        Args:
            limit: Maximum number of entries to return (default: 100)
        
        Returns:
            List of leaderboard dictionaries with location info and Clean Score
        
        Validates: Requirement 8.4
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                # Get most recent summary for each location, ordered by Clean Score
                cursor.execute(
                    """
                    WITH latest_summaries AS (
                        SELECT 
                            ts.LocationID,
                            ts.AvgCO2,
                            ts.AvgNoise,
                            ts.AvgTemperature,
                            ts.CleanScore,
                            ts.SummaryDate,
                            ROW_NUMBER() OVER (PARTITION BY ts.LocationID ORDER BY ts.SummaryDate DESC) as rn
                        FROM TELEMETRY_SUMMARY ts
                    )
                    SELECT 
                        ls.LocationID,
                        l.Name as LocationName,
                        ls.AvgCO2,
                        ls.AvgNoise,
                        ls.AvgTemperature,
                        ls.CleanScore,
                        ROW_NUMBER() OVER (ORDER BY ls.CleanScore DESC) as Rank
                    FROM latest_summaries ls
                    INNER JOIN LOCATIONS l ON ls.LocationID = l.LocationID
                    WHERE ls.rn = 1
                    ORDER BY ls.CleanScore DESC
                    FETCH FIRST :limit ROWS ONLY
                    """,
                    {'limit': limit}
                )
                
                columns = [col[0].lower() for col in cursor.description]
                results = []
                for row in cursor:
                    results.append(dict(zip(columns, row)))
                
                logger.debug(f"Retrieved {len(results)} leaderboard entries")
                return results
                
            finally:
                cursor.close()
        
        try:
            return self._execute_with_retry("get_leaderboard", operation)
        except Exception as e:
            logger.error(f"Failed to retrieve leaderboard: {e}")
            return []


    
    def close(self):
        """Close Oracle connection pool and release resources."""
        if self._pool:
            self._pool.close()
            logger.info("Oracle connection pool closed")


# Singleton instance
_oracle_client: Optional[OracleClient] = None


def get_oracle_client() -> OracleClient:
    """
    Get singleton Oracle client instance.
    
    Returns:
        OracleClient: Shared client instance with connection pooling
    """
    global _oracle_client
    if _oracle_client is None:
        _oracle_client = OracleClient()
    return _oracle_client
