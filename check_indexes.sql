SET PAGESIZE 100;
SET LINESIZE 200;

-- Check indexes on SENSOR_REGISTRY
SELECT index_name, table_name, column_name, column_position
FROM user_ind_columns
WHERE table_name = 'SENSOR_REGISTRY'
ORDER BY index_name, column_position;

-- Check indexes on LOCATIONS
SELECT index_name, table_name, column_name, column_position
FROM user_ind_columns
WHERE table_name = 'LOCATIONS'
ORDER BY index_name, column_position;

-- Check if LOCATION_HIERARCHY view exists
SELECT view_name FROM user_views WHERE view_name = 'LOCATION_HIERARCHY';

EXIT;
