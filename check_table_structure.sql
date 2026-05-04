SET PAGESIZE 100;
SET LINESIZE 200;

-- Check if SENSOR_REGISTRY is a table or view
SELECT object_name, object_type 
FROM user_objects 
WHERE object_name = 'SENSOR_REGISTRY';

-- Check columns of SENSOR_REGISTRY
SELECT column_name, data_type 
FROM user_tab_columns 
WHERE table_name = 'SENSOR_REGISTRY'
ORDER BY column_id;

EXIT;
