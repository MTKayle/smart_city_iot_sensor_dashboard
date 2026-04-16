-- Create LOCATION_HIERARCHY view using CONNECT BY (Oracle hierarchical query)
CREATE OR REPLACE VIEW LOCATION_HIERARCHY AS
SELECT 
    LocationID,
    Name,
    ParentID,
    Type,
    SYS_CONNECT_BY_PATH(LocationID, ' > ') as Path,
    LEVEL - 1 as HierarchyLevel
FROM LOCATIONS
START WITH ParentID IS NULL
CONNECT BY PRIOR LocationID = ParentID
ORDER SIBLINGS BY LocationID;

