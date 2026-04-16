-- Complete schema initialization for Smart City IoT Dashboard
-- This script creates all tables in the correct order

-- Drop existing tables if they exist (in reverse dependency order)
BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE TELEMETRY_SUMMARY CASCADE CONSTRAINTS';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE ALERTS CASCADE CONSTRAINTS';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE SENSOR_REGISTRY CASCADE CONSTRAINTS';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE LOCATIONS CASCADE CONSTRAINTS';
EXCEPTION
   WHEN OTHERS THEN NULL;
END;
/

-- Create LOCATIONS table
CREATE TABLE LOCATIONS (
    LocationID VARCHAR2(50) PRIMARY KEY,
    Name VARCHAR2(100) NOT NULL,
    ParentID VARCHAR2(50),
    Type VARCHAR2(20) NOT NULL CHECK (Type IN ('City', 'District', 'Ward')),
    CONSTRAINT fk_locations_parent FOREIGN KEY (ParentID) REFERENCES LOCATIONS(LocationID)
);

CREATE INDEX idx_locations_parent ON LOCATIONS(ParentID);

-- Create SENSOR_REGISTRY table
CREATE TABLE SENSOR_REGISTRY (
    SensorID VARCHAR2(50) PRIMARY KEY,
    LocationID VARCHAR2(50) NOT NULL,
    SensorType VARCHAR2(20) NOT NULL CHECK (SensorType IN ('CO2', 'Noise', 'Temperature')),
    RegisteredAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sensors_location FOREIGN KEY (LocationID) REFERENCES LOCATIONS(LocationID)
);

CREATE INDEX idx_sensors_location ON SENSOR_REGISTRY(LocationID);

-- Create ALERTS table with AlertLevel instead of Level
CREATE TABLE ALERTS (
    AlertID VARCHAR2(50) PRIMARY KEY,
    SensorID VARCHAR2(50) NOT NULL,
    MetricType VARCHAR2(20) NOT NULL,
    Value NUMBER NOT NULL,
    AlertLevel VARCHAR2(10) NOT NULL CHECK (AlertLevel IN ('LOW', 'MEDIUM', 'HIGH')),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alerts_sensor FOREIGN KEY (SensorID) REFERENCES SENSOR_REGISTRY(SensorID)
);

CREATE INDEX idx_alerts_sensor ON ALERTS(SensorID);
CREATE INDEX idx_alerts_created ON ALERTS(CreatedAt);

-- Create TELEMETRY_SUMMARY table
CREATE TABLE TELEMETRY_SUMMARY (
    SummaryID VARCHAR2(50) PRIMARY KEY,
    LocationID VARCHAR2(50) NOT NULL,
    SummaryDate DATE NOT NULL,
    AvgCO2 NUMBER,
    AvgNoise NUMBER,
    AvgTemperature NUMBER,
    CleanScore NUMBER,
    CONSTRAINT fk_summary_location FOREIGN KEY (LocationID) REFERENCES LOCATIONS(LocationID),
    CONSTRAINT uk_summary_location_date UNIQUE (LocationID, SummaryDate)
);

CREATE INDEX idx_summary_location_date ON TELEMETRY_SUMMARY(LocationID, SummaryDate);

-- Create LOCATION_HIERARCHY view
CREATE OR REPLACE VIEW LOCATION_HIERARCHY AS
WITH hierarchy (LocationID, Name, ParentID, Type, Path, Level) AS (
    SELECT 
        LocationID, 
        Name, 
        ParentID, 
        Type,
        LocationID as Path,
        0 as Level
    FROM LOCATIONS
    WHERE ParentID IS NULL
    
    UNION ALL
    
    SELECT 
        l.LocationID,
        l.Name,
        l.ParentID,
        l.Type,
        h.Path || ' > ' || l.LocationID as Path,
        h.Level + 1 as Level
    FROM LOCATIONS l
    INNER JOIN hierarchy h ON l.ParentID = h.LocationID
)
SELECT * FROM hierarchy;
