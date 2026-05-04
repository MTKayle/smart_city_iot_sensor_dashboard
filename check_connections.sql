SET PAGESIZE 50;
SET LINESIZE 200;

-- Check active sessions
SELECT username, machine, program, status, COUNT(*) as session_count
FROM v$session
WHERE username = 'SMARTCITY'
GROUP BY username, machine, program, status
ORDER BY session_count DESC;

-- Check total sessions
SELECT COUNT(*) as total_sessions
FROM v$session
WHERE username = 'SMARTCITY';

EXIT;
