SET PAGESIZE 50;
SET LINESIZE 200;

-- Check all views
SELECT view_name FROM user_views ORDER BY view_name;

-- Check LOCATION_HIERARCHY view definition
SELECT text FROM user_views WHERE view_name = 'LOCATION_HIERARCHY';

EXIT;
