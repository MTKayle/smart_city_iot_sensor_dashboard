-- Execute oracle_schema_v2.sql and verify results
-- This script is designed to be run with sqlplus

SET SERVEROUTPUT ON
SET ECHO ON
SET FEEDBACK ON

-- Execute the schema v2 script
@@oracle_schema_v2.sql

-- Verification queries
PROMPT
PROMPT ================================================================================
PROMPT VERIFICATION RESULTS
PROMPT ================================================================================
PROMPT

PROMPT Tables Created:
SELECT table_name, num_rows 
FROM user_tables 
WHERE table_name IN (
    'LOCATIONS', 'SENSOR_CLUSTERS', 'SENSOR_REGISTRY', 
    'SENSOR_CAPABILITIES', 'ALERTS', 'INCIDENTS', 
    'INCIDENT_ALERTS', 'SENSOR_HEALTH_LOGS', 'TELEMETRY_SUMMARY'
)
ORDER BY table_name;

PROMPT
PROMPT Triggers Created:
SELECT trigger_name, status, trigger_type
FROM user_triggers
WHERE trigger_name IN (
    'TRG_LOCATIONS_UPDATED_AT',
    'TRG_CLUSTERS_UPDATED_AT',
    'TRG_SENSORS_UPDATED_AT',
    'TRG_ALERT_LOCATION_SYNC',
    'TRG_CLUSTER_COUNT'
)
ORDER BY trigger_name;

PROMPT
PROMPT Indexes Created:
SELECT index_name, table_name, status
FROM user_indexes
WHERE index_name LIKE 'IDX_%'
ORDER BY table_name, index_name;

PROMPT
PROMPT Foreign Key Constraints:
SELECT constraint_name, table_name, status
FROM user_constraints
WHERE constraint_type = 'R'
AND constraint_name LIKE 'FK_%'
ORDER BY table_name, constraint_name;

PROMPT
PROMPT ================================================================================
PROMPT VERIFICATION COMPLETE
PROMPT ================================================================================

EXIT;
