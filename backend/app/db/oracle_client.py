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

from app.models import Location, SensorRegistry, SensorCluster, SensorCapability, Alert

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
                # Increased max to 20 to handle concurrent API requests + MQTT worker pool
                # (3 workers * 8 thread-pool = 24 potential concurrent operations)
                self._pool = oracledb.create_pool(
                    user=ORACLE_USER,
                    password=ORACLE_PASSWORD,
                    dsn=ORACLE_DSN,
                    min=5,
                    max=20,
                    increment=2
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
                    INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate, RegisteredAt)
                    VALUES (:sensor_id, :location_id, :cluster_id, :latitude, :longitude, :altitude, :sensor_model, :firmware, :status, :install_date, :registered_at)
                    """,
                    {
                        'sensor_id': sensor.sensorId,
                        'location_id': sensor.locationId,
                        'cluster_id': sensor.clusterId,
                        'latitude': sensor.latitude,
                        'longitude': sensor.longitude,
                        'altitude': sensor.altitude,
                        'sensor_model': getattr(sensor, 'sensorModel', None),
                        'firmware': getattr(sensor, 'firmwareVersion', None),
                        'status': getattr(sensor, 'status', 'Active'),
                        'install_date': getattr(sensor, 'installDate', datetime.now().date()),
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
                        SELECT s.*,
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
                        SELECT s.*,
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
        
        Uses v2 schema columns (Severity instead of AlertLevel).
        
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
                    INSERT INTO ALERTS (AlertID, SensorID, LocationID, AlertType,
                                       MetricType, Value, Severity, Status, CreatedAt)
                    VALUES (:alert_id, :sensor_id, :location_id, :alert_type,
                            :metric_type, :value, :severity, :status, :created_at)
                    """,
                    {
                        'alert_id': alert.alertId,
                        'sensor_id': alert.sensorId,
                        'location_id': getattr(alert, 'locationId', 'unknown'),
                        'alert_type': getattr(alert, 'alertType', 'THRESHOLD'),
                        'metric_type': alert.metricType,
                        'value': alert.value,
                        'severity': getattr(alert, 'severity', None) or getattr(alert, 'level', 'LOW'),
                        'status': getattr(alert, 'status', 'OPEN'),
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
        
        Uses v2 schema columns (Severity instead of AlertLevel).
        
        Args:
            level: Optional severity filter (LOW, MEDIUM, HIGH, CRITICAL)
            location_id: Optional location ID filter
            limit: Maximum number of alerts to return (default: 100)
        
        Returns:
            List of alert dictionaries sorted by creation time descending
        
        Validates: Requirement 6.3
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                # Build query with v2 schema columns
                query = """
                    SELECT a.AlertID, a.SensorID, a.LocationID, a.AlertType,
                           a.MetricType, a.Value, a.Severity, a.Status,
                           a.Threshold, a.PredictedValue, a.ConfidenceScore,
                           a.CreatedAt,
                           l.Name as LocationName
                    FROM ALERTS a
                    LEFT JOIN LOCATIONS l ON a.LocationID = l.LocationID
                    WHERE 1=1
                """
                params = {}
                
                if level:
                    query += " AND a.Severity = :p_level"
                    params['p_level'] = level
                
                if location_id:
                    query += " AND a.LocationID = :p_location_id"
                    params['p_location_id'] = location_id
                
                query += " ORDER BY a.CreatedAt DESC FETCH FIRST :p_limit ROWS ONLY"
                params['p_limit'] = limit
                
                cursor.execute(query, params)
                
                columns = [col[0].lower() for col in cursor.description]
                results = []
                for row in cursor:
                    row_dict = dict(zip(columns, row))
                    # Backward compat: provide 'alertlevel' alias
                    row_dict['alertlevel'] = row_dict.get('severity')
                    results.append(row_dict)
                
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
        clean_score: float,
        avg_pm25: Optional[float] = None,
        avg_humidity: Optional[float] = None,
        aqi: Optional[int] = None,
        data_points: int = 0,
        granularity: str = 'DAILY',
    ) -> bool:
        """
        Insert or update daily telemetry summary in TELEMETRY_SUMMARY table (v2 schema).
        
        Uses MERGE statement keyed on (LocationID, TimeBucket, Granularity) so that
        repeated runs for the same date/granularity upsert rather than duplicate.
        
        Args:
            summary_id: Unique identifier for the summary
            location_id: Location identifier
            summary_date: Date for the summary (converted to TimeBucket timestamp)
            avg_co2: Average CO2 level in ppm
            avg_noise: Average noise level in dB
            avg_temperature: Average temperature in °C
            clean_score: Calculated Clean Score (0-100)
            avg_pm25: Average PM2.5 in µg/m³ (optional)
            avg_humidity: Average humidity in % (optional)
            aqi: Air Quality Index (optional)
            data_points: Number of data points aggregated (default 0)
            granularity: Aggregation granularity - 'HOURLY' or 'DAILY' (default 'DAILY')
        
        Returns:
            bool: True if operation successful, False otherwise
        
        Validates: Requirement 8.3, FR6.2, FR6.4
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                # Convert date to timestamp for TimeBucket
                time_bucket = datetime.combine(summary_date, datetime.min.time())

                cursor.execute(
                    """
                    MERGE INTO TELEMETRY_SUMMARY ts
                    USING (
                        SELECT :location_id  AS LocationID,
                               :time_bucket  AS TimeBucket,
                               :granularity  AS Granularity
                        FROM DUAL
                    ) src
                    ON (    ts.LocationID  = src.LocationID
                        AND ts.TimeBucket  = src.TimeBucket
                        AND ts.Granularity = src.Granularity
                        AND ts.SensorID    IS NULL
                        AND ts.ClusterID   IS NULL)
                    WHEN MATCHED THEN
                        UPDATE SET
                            AvgCO2         = :avg_co2,
                            AvgNoise       = :avg_noise,
                            AvgTemperature = :avg_temperature,
                            AvgPM25        = :avg_pm25,
                            AvgHumidity    = :avg_humidity,
                            CleanScore     = :clean_score,
                            AQI            = :aqi,
                            DataPoints     = :data_points
                    WHEN NOT MATCHED THEN
                        INSERT (SummaryID, LocationID, TimeBucket, Granularity,
                                AvgCO2, AvgNoise, AvgTemperature,
                                AvgPM25, AvgHumidity,
                                CleanScore, AQI, DataPoints)
                        VALUES (:summary_id, :location_id, :time_bucket, :granularity,
                                :avg_co2, :avg_noise, :avg_temperature,
                                :avg_pm25, :avg_humidity,
                                :clean_score, :aqi, :data_points)
                    """,
                    {
                        'summary_id': summary_id,
                        'location_id': location_id,
                        'time_bucket': time_bucket,
                        'granularity': granularity,
                        'avg_co2': avg_co2,
                        'avg_noise': avg_noise,
                        'avg_temperature': avg_temperature,
                        'avg_pm25': avg_pm25,
                        'avg_humidity': avg_humidity,
                        'clean_score': clean_score,
                        'aqi': aqi,
                        'data_points': data_points,
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
                            ts.AvgPM25,
                            ts.AvgHumidity,
                            ts.CleanScore,
                            ts.AQI,
                            ts.TimeBucket,
                            ROW_NUMBER() OVER (PARTITION BY ts.LocationID ORDER BY ts.TimeBucket DESC) as rn
                        FROM TELEMETRY_SUMMARY ts
                        WHERE ts.LocationID IS NOT NULL
                          AND ts.SensorID   IS NULL
                          AND ts.ClusterID  IS NULL
                    )
                    SELECT 
                        ls.LocationID,
                        l.Name as LocationName,
                        ls.AvgCO2,
                        ls.AvgNoise,
                        ls.AvgTemperature,
                        ls.AvgPM25,
                        ls.AvgHumidity,
                        ls.CleanScore,
                        ls.AQI,
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


    
    def get_sensor_geolocation(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Query geolocation and cluster metadata for a sensor from SENSOR_REGISTRY.
        Includes an in-memory cache to prevent connection pool starvation during high-throughput telemetry ingestion.

        Returns a dict with keys: latitude, longitude, clusterId, locationId.
        Returns None if sensor not found or query fails.

        Args:
            sensor_id: Unique sensor identifier

        Returns:
            dict with geolocation info, or None

        Validates: FR4.1, FR4.2
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT Latitude, Longitude, ClusterID, LocationID
                    FROM SENSOR_REGISTRY
                    WHERE SensorID = :sensor_id
                    """,
                    {'sensor_id': sensor_id}
                )
                row = cursor.fetchone()
                if row is None:
                    logger.warning(f"Sensor '{sensor_id}' not found in SENSOR_REGISTRY")
                    return None
                lat, lng, cluster_id, location_id = row
                return {
                    "latitude": float(lat),
                    "longitude": float(lng),
                    "clusterId": cluster_id,
                    "locationId": location_id,
                }
            finally:
                cursor.close()

        # Check cache first to avoid hammering the DB
        if not hasattr(self, '_geo_cache'):
            self._geo_cache = {}
        if sensor_id in self._geo_cache:
            return self._geo_cache[sensor_id]

        try:
            result = self._execute_with_retry("get_sensor_geolocation", operation)
            if result is not None:
                self._geo_cache[sensor_id] = result
            return result
        except Exception as e:
            logger.error(f"Failed to get geolocation for sensor '{sensor_id}': {e}")
            return None

    # =========================================================================
    # TASK 5.1 – Sensor Registry Methods
    # =========================================================================

    def get_sensor(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single sensor record by SensorID.

        Joins SENSOR_REGISTRY with LOCATIONS and SENSOR_CLUSTERS to return
        a fully-enriched sensor dict.

        Args:
            sensor_id: Unique sensor identifier

        Returns:
            dict with sensor details, or None if not found

        Validates: FR1.2, IR3.1
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT s.SensorID, s.LocationID, s.ClusterID,
                           s.Latitude, s.Longitude, s.Altitude,
                           s.SensorModel, s.FirmwareVersion, s.Status,
                           s.InstallDate, s.LastMaintenance, s.NextMaintenance,
                           s.RegisteredAt, s.UpdatedAt,
                           l.Name  AS LocationName,
                           l.Type  AS LocationType,
                           c.ClusterName
                    FROM   SENSOR_REGISTRY s
                    JOIN   LOCATIONS       l ON l.LocationID = s.LocationID
                    LEFT JOIN SENSOR_CLUSTERS c ON c.ClusterID = s.ClusterID
                    WHERE  s.SensorID = :sensor_id
                    """,
                    {'sensor_id': sensor_id}
                )
                row = cursor.fetchone()
                if row is None:
                    logger.debug(f"Sensor '{sensor_id}' not found")
                    return None
                cols = [d[0].lower() for d in cursor.description]
                return dict(zip(cols, row))
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("get_sensor", operation)
        except Exception as e:
            logger.error(f"Failed to get sensor '{sensor_id}': {e}")
            return None

    def get_sensors_by_location(self, location_id: str,
                                status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all sensors belonging to a given location (ward/district/city).

        Args:
            location_id: Location identifier
            status:      Optional status filter (Active, Offline, Maintenance, Decommissioned)

        Returns:
            List of sensor dicts ordered by RegisteredAt DESC

        Validates: FR1.2, FR1.3, IR3.2
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                query = """
                    SELECT s.SensorID, s.LocationID, s.ClusterID,
                           s.Latitude, s.Longitude, s.Altitude,
                           s.SensorModel, s.FirmwareVersion, s.Status,
                           s.InstallDate, s.LastMaintenance, s.NextMaintenance,
                           s.RegisteredAt, s.UpdatedAt,
                           l.Name  AS LocationName,
                           l.Type  AS LocationType,
                           c.ClusterName
                    FROM   SENSOR_REGISTRY s
                    JOIN   LOCATIONS       l ON l.LocationID = s.LocationID
                    LEFT JOIN SENSOR_CLUSTERS c ON c.ClusterID = s.ClusterID
                    WHERE  s.LocationID = :location_id
                """
                params: Dict[str, Any] = {'location_id': location_id}
                if status:
                    query += " AND s.Status = :status"
                    params['status'] = status
                query += " ORDER BY s.RegisteredAt DESC"
                cursor.execute(query, params)
                cols = [d[0].lower() for d in cursor.description]
                results = [dict(zip(cols, row)) for row in cursor]
                logger.debug(
                    f"Retrieved {len(results)} sensors for location '{location_id}'"
                )
                return results
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("get_sensors_by_location", operation)
        except Exception as e:
            logger.error(f"Failed to get sensors for location '{location_id}': {e}")
            return []

    def get_sensors_by_cluster(self, cluster_id: str,
                               status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all sensors belonging to a spatial cluster.

        Args:
            cluster_id: Cluster identifier
            status:     Optional status filter

        Returns:
            List of sensor dicts

        Validates: FR1.3, IR3.3
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                query = """
                    SELECT s.SensorID, s.LocationID, s.ClusterID,
                           s.Latitude, s.Longitude, s.Altitude,
                           s.SensorModel, s.FirmwareVersion, s.Status,
                           s.InstallDate, s.LastMaintenance, s.NextMaintenance,
                           s.RegisteredAt, s.UpdatedAt,
                           l.Name  AS LocationName,
                           l.Type  AS LocationType,
                           c.ClusterName
                    FROM   SENSOR_REGISTRY  s
                    JOIN   LOCATIONS        l ON l.LocationID = s.LocationID
                    JOIN   SENSOR_CLUSTERS  c ON c.ClusterID = s.ClusterID
                    WHERE  s.ClusterID = :cluster_id
                """
                params: Dict[str, Any] = {'cluster_id': cluster_id}
                if status:
                    query += " AND s.Status = :status"
                    params['status'] = status
                query += " ORDER BY s.RegisteredAt DESC"
                cursor.execute(query, params)
                cols = [d[0].lower() for d in cursor.description]
                results = [dict(zip(cols, row)) for row in cursor]
                logger.debug(
                    f"Retrieved {len(results)} sensors for cluster '{cluster_id}'"
                )
                return results
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("get_sensors_by_cluster", operation)
        except Exception as e:
            logger.error(f"Failed to get sensors for cluster '{cluster_id}': {e}")
            return []

    def get_sensor_capabilities(self, sensor_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all active capabilities for a sensor from SENSOR_CAPABILITIES.

        Args:
            sensor_id: Unique sensor identifier

        Returns:
            List of capability dicts (MetricType, Unit, range, accuracy, etc.)

        Validates: FR1.2, IR3.4
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT CapabilityID, SensorID, MetricType, Unit,
                           MinRange, MaxRange, Accuracy,
                           CalibrationDate, NextCalibration, IsActive
                    FROM   SENSOR_CAPABILITIES
                    WHERE  SensorID = :sensor_id
                    ORDER BY MetricType
                    """,
                    {'sensor_id': sensor_id}
                )
                cols = [d[0].lower() for d in cursor.description]
                results = [dict(zip(cols, row)) for row in cursor]
                logger.debug(
                    f"Retrieved {len(results)} capabilities for sensor '{sensor_id}'"
                )
                return results
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("get_sensor_capabilities", operation)
        except Exception as e:
            logger.error(
                f"Failed to get capabilities for sensor '{sensor_id}': {e}"
            )
            return []

    # =========================================================================
    # TASK 5.2 – Location Hierarchy Methods
    # =========================================================================

    def get_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single location record by LocationID.

        Includes CenterLat/CenterLng, Area, Population, and HierarchyLevel
        from the LOCATION_HIERARCHY view.

        Args:
            location_id: Location identifier

        Returns:
            dict with location details, or None if not found

        Validates: FR1.1, FR8.1
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT l.LocationID, l.Name, l.ParentID, l.Type,
                           l.CenterLat, l.CenterLng, l.Area, l.Population,
                           l.CreatedAt, l.UpdatedAt,
                           h.HierarchyLevel, h.Path
                    FROM   LOCATIONS        l
                    JOIN   LOCATION_HIERARCHY h ON h.LocationID = l.LocationID
                    WHERE  l.LocationID = :location_id
                    """,
                    {'location_id': location_id}
                )
                row = cursor.fetchone()
                if row is None:
                    logger.debug(f"Location '{location_id}' not found")
                    return None
                cols = [d[0].lower() for d in cursor.description]
                return dict(zip(cols, row))
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("get_location", operation)
        except Exception as e:
            logger.error(f"Failed to get location '{location_id}': {e}")
            return None

    def get_all_locations(self, location_type: Optional[str] = None,
                          parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all locations, optionally filtered by type or parent.

        Args:
            location_type: Optional filter – 'City', 'District', or 'Ward'
            parent_id:     Optional parent location filter

        Returns:
            List of location dicts ordered by HierarchyLevel then LocationID

        Validates: FR1.1, FR8.1
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                query = """
                    SELECT l.LocationID, l.Name, l.ParentID, l.Type,
                           l.CenterLat, l.CenterLng, l.Area, l.Population,
                           l.CreatedAt, l.UpdatedAt,
                           h.HierarchyLevel, h.Path
                    FROM   LOCATIONS        l
                    JOIN   LOCATION_HIERARCHY h ON h.LocationID = l.LocationID
                    WHERE  1 = 1
                """
                params: Dict[str, Any] = {}
                if location_type:
                    query += " AND l.Type = :loc_type"
                    params['loc_type'] = location_type
                if parent_id:
                    query += " AND l.ParentID = :parent_id"
                    params['parent_id'] = parent_id
                query += " ORDER BY h.HierarchyLevel, l.LocationID"
                cursor.execute(query, params)
                cols = [d[0].lower() for d in cursor.description]
                results = [dict(zip(cols, row)) for row in cursor]
                logger.debug(f"Retrieved {len(results)} locations")
                return results
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("get_all_locations", operation)
        except Exception as e:
            logger.error(f"Failed to get all locations: {e}")
            return []

    # get_location_hierarchy() already exists above (lines ~267-331).
    # The existing implementation supports both full-tree (no arg) and
    # subtree-rooted-at (location_id) queries via LOCATION_HIERARCHY view /
    # recursive CTE.  No changes required.

    # =========================================================================
    # TASK 5.3 – Cluster Methods
    # =========================================================================

    def get_cluster(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single cluster record by ClusterID.

        Args:
            cluster_id: Cluster identifier

        Returns:
            dict with cluster details, or None if not found

        Validates: FR1.4, FR8.2
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT c.ClusterID, c.LocationID, c.ClusterName,
                           c.CenterLat, c.CenterLng, c.Radius,
                           c.SensorCount, c.Algorithm,
                           c.CreatedAt, c.UpdatedAt,
                           l.Name AS LocationName, l.Type AS LocationType
                    FROM   SENSOR_CLUSTERS c
                    JOIN   LOCATIONS       l ON l.LocationID = c.LocationID
                    WHERE  c.ClusterID = :cluster_id
                    """,
                    {'cluster_id': cluster_id}
                )
                row = cursor.fetchone()
                if row is None:
                    logger.debug(f"Cluster '{cluster_id}' not found")
                    return None
                cols = [d[0].lower() for d in cursor.description]
                return dict(zip(cols, row))
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("get_cluster", operation)
        except Exception as e:
            logger.error(f"Failed to get cluster '{cluster_id}': {e}")
            return None

    def get_all_clusters(self, location_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all sensor clusters, optionally filtered by location.

        Args:
            location_id: Optional location filter

        Returns:
            List of cluster dicts ordered by LocationID, ClusterID

        Validates: FR1.4, FR8.2
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                query = """
                    SELECT c.ClusterID, c.LocationID, c.ClusterName,
                           c.CenterLat, c.CenterLng, c.Radius,
                           c.SensorCount, c.Algorithm,
                           c.CreatedAt, c.UpdatedAt,
                           l.Name AS LocationName, l.Type AS LocationType
                    FROM   SENSOR_CLUSTERS c
                    JOIN   LOCATIONS       l ON l.LocationID = c.LocationID
                    WHERE  1 = 1
                """
                params: Dict[str, Any] = {}
                if location_id:
                    query += " AND c.LocationID = :location_id"
                    params['location_id'] = location_id
                query += " ORDER BY c.LocationID, c.ClusterID"
                cursor.execute(query, params)
                cols = [d[0].lower() for d in cursor.description]
                results = [dict(zip(cols, row)) for row in cursor]
                logger.debug(f"Retrieved {len(results)} clusters")
                return results
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("get_all_clusters", operation)
        except Exception as e:
            logger.error(f"Failed to get all clusters: {e}")
            return []

    def update_cluster_sensor_count(self, cluster_id: str) -> bool:
        """
        Recompute and persist the SensorCount for a cluster by counting
        Active sensors currently assigned to it in SENSOR_REGISTRY.

        This is a manual reconciliation helper that complements the DB
        trigger (trg_cluster_count) which fires on INSERT/DELETE.

        Args:
            cluster_id: Cluster identifier to update

        Returns:
            bool: True if updated successfully, False otherwise

        Validates: FR1.4, FR8.2
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE SENSOR_CLUSTERS
                    SET    SensorCount = (
                               SELECT COUNT(*)
                               FROM   SENSOR_REGISTRY
                               WHERE  ClusterID = :cluster_id
                               AND    Status    = 'Active'
                           ),
                           UpdatedAt = CURRENT_TIMESTAMP
                    WHERE  ClusterID = :cluster_id
                    """,
                    {'cluster_id': cluster_id}
                )
                rows_updated = cursor.rowcount
                connection.commit()
                if rows_updated == 0:
                    logger.warning(
                        f"update_cluster_sensor_count: cluster '{cluster_id}' not found"
                    )
                    return False
                logger.debug(
                    f"Updated SensorCount for cluster '{cluster_id}'"
                )
                return True
            except oracledb.DatabaseError as e:
                connection.rollback()
                logger.error(
                    f"Failed to update sensor count for cluster "
                    f"'{cluster_id}': {e}"
                )
                return False
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("update_cluster_sensor_count", operation)
        except Exception:
            return False

    # =========================================================================
    # TASK 6 – Enhanced Alert Methods
    # =========================================================================

    def insert_alert_v2(self, alert) -> bool:
        """
        Insert alert record into ALERTS table using the v2 schema.

        Supports all v2 columns: AlertType, Severity, Threshold,
        PredictedValue, ConfidenceScore, Status, Message.

        Args:
            alert: Alert pydantic model (v2)

        Returns:
            bool: True if insertion successful

        Validates: FR5.1, FR5.2, FR5.3
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO ALERTS (
                        AlertID, SensorID, ClusterID, LocationID,
                        AlertType, MetricType,
                        Value, Threshold, PredictedValue, ConfidenceScore,
                        Severity, Status,
                        CreatedAt, Message
                    ) VALUES (
                        :alert_id, :sensor_id, :cluster_id, :location_id,
                        :alert_type, :metric_type,
                        :value, :threshold, :predicted_value, :confidence_score,
                        :severity, :status,
                        :created_at, :message
                    )
                    """,
                    {
                        'alert_id':         alert.alertId,
                        'sensor_id':        alert.sensorId,
                        'cluster_id':       alert.clusterId,
                        'location_id':      alert.locationId,
                        'alert_type':       alert.alertType.value if hasattr(alert.alertType, 'value') else str(alert.alertType),
                        'metric_type':      alert.metricType,
                        'value':            alert.value,
                        'threshold':        alert.threshold,
                        'predicted_value':  alert.predictedValue,
                        'confidence_score': alert.confidenceScore,
                        'severity':         alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity),
                        'status':           alert.status or 'OPEN',
                        'created_at':       alert.createdAt,
                        'message':          alert.message,
                    }
                )
                connection.commit()
                logger.debug(f"Inserted alert (v2) {alert.alertId}")
                return True
            except oracledb.DatabaseError as e:
                connection.rollback()
                logger.error(f"Failed to insert alert (v2) {alert.alertId}: {e}")
                return False
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("insert_alert_v2", operation)
        except Exception:
            return False

    def get_recent_alerts_for_sensor(
        self,
        sensor_id: str,
        metric_type: str,
        alert_type: str,
        window_minutes: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Query ALERTS for recent alerts matching sensor + metric + alert type
        within a time window.

        Used for deduplication — returns alerts created within the last
        *window_minutes* minutes.

        Args:
            sensor_id:      Sensor identifier
            metric_type:    Metric type (CO2, Noise, PM25, Humidity)
            alert_type:     Alert type (THRESHOLD, PREDICTIVE, ANOMALY)
            window_minutes: How far back to look (default 5)

        Returns:
            List of matching alert dicts, ordered by CreatedAt DESC

        Validates: FR5.4
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT AlertID, SensorID, MetricType, AlertType,
                           Value, Severity, Status, CreatedAt
                    FROM   ALERTS
                    WHERE  SensorID   = :sensor_id
                    AND    MetricType = :metric_type
                    AND    AlertType  = :alert_type
                    AND    CreatedAt >= CURRENT_TIMESTAMP - NUMTODSINTERVAL(:window_min, 'MINUTE')
                    ORDER BY CreatedAt DESC
                    """,
                    {
                        'sensor_id':   sensor_id,
                        'metric_type': metric_type,
                        'alert_type':  alert_type,
                        'window_min':  window_minutes,
                    }
                )
                cols = [d[0].lower() for d in cursor.description]
                return [dict(zip(cols, row)) for row in cursor]
            finally:
                cursor.close()

        try:
            return self._execute_with_retry(
                "get_recent_alerts_for_sensor", operation
            )
        except Exception as e:
            logger.error(f"Failed to query recent alerts: {e}")
            return []

    def update_alert_status(
        self,
        alert_id: str,
        new_status: str,
        acknowledged_at: Optional[datetime] = None,
        resolved_at: Optional[datetime] = None,
    ) -> bool:
        """
        Update the status of an alert (lifecycle transitions).

        Supports:
        - OPEN → ACKNOWLEDGED  (sets AcknowledgedAt)
        - OPEN/ACKNOWLEDGED → RESOLVED  (sets ResolvedAt)

        Args:
            alert_id:         Alert identifier
            new_status:       Target status (ACKNOWLEDGED, RESOLVED)
            acknowledged_at:  Timestamp for acknowledgment
            resolved_at:      Timestamp for resolution

        Returns:
            bool: True if update succeeded

        Validates: FR5.5
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                if new_status == "ACKNOWLEDGED":
                    cursor.execute(
                        """
                        UPDATE ALERTS
                        SET    Status         = :new_status,
                               AcknowledgedAt = :ack_at
                        WHERE  AlertID = :alert_id
                        AND    Status  = 'OPEN'
                        """,
                        {
                            'new_status': new_status,
                            'ack_at':     acknowledged_at or datetime.utcnow(),
                            'alert_id':   alert_id,
                        }
                    )
                elif new_status == "RESOLVED":
                    cursor.execute(
                        """
                        UPDATE ALERTS
                        SET    Status     = :new_status,
                               ResolvedAt = :resolved_at
                        WHERE  AlertID = :alert_id
                        AND    Status IN ('OPEN', 'ACKNOWLEDGED')
                        """,
                        {
                            'new_status':  new_status,
                            'resolved_at': resolved_at or datetime.utcnow(),
                            'alert_id':    alert_id,
                        }
                    )
                else:
                    logger.warning(f"Invalid alert status transition: {new_status}")
                    return False

                rows_updated = cursor.rowcount
                connection.commit()

                if rows_updated == 0:
                    logger.warning(
                        f"Alert {alert_id} not updated — already in target "
                        f"status or not found"
                    )
                    return False

                logger.info(f"Alert {alert_id} → {new_status}")
                return True

            except oracledb.DatabaseError as e:
                connection.rollback()
                logger.error(f"Failed to update alert {alert_id}: {e}")
                return False
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("update_alert_status", operation)
        except Exception:
            return False

    def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single alert record by AlertID.

        Args:
            alert_id: Alert identifier

        Returns:
            dict with alert details, or None if not found
        """
        def operation(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT AlertID, SensorID, ClusterID, LocationID,
                           AlertType, MetricType,
                           Value, Threshold, PredictedValue, ConfidenceScore,
                           Severity, Status,
                           CreatedAt, AcknowledgedAt, ResolvedAt,
                           Message
                    FROM   ALERTS
                    WHERE  AlertID = :alert_id
                    """,
                    {'alert_id': alert_id}
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                cols = [d[0].lower() for d in cursor.description]
                return dict(zip(cols, row))
            finally:
                cursor.close()

        try:
            return self._execute_with_retry("get_alert_by_id", operation)
        except Exception as e:
            logger.error(f"Failed to get alert {alert_id}: {e}")
            return None

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
