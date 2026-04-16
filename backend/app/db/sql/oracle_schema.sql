-- Oracle Database Schema Initialization
-- Smart City IoT Sensor Dashboard
-- Requirements: 16.1, 16.2, 16.3, 1.1, 2.1, 6.3, 8.3

-- ============================================================================
-- TABLE: LOCATIONS
-- Stores geographic hierarchy (City > District > Ward)
-- ============================================================================
CREATE TABLE LOCATIONS (
    LocationID VARCHAR2(50) PRIMARY KEY,
    Name VARCHAR2(100) NOT NULL,
    ParentID VARCHAR2(50),
    Type VARCHAR2(20) NOT NULL CHECK (Type IN ('City', 'District', 'Ward')),
    CONSTRAINT fk_locations_parent FOREIGN KEY (ParentID) REFERENCES LOCATIONS(LocationID)
);

-- Index for efficient parent-child queries
CREATE INDEX idx_locations_parent ON LOCATIONS(ParentID);

-- ============================================================================
-- TABLE: SENSOR_REGISTRY
-- Stores registered IoT sensors with their locations
-- ============================================================================
CREATE TABLE SENSOR_REGISTRY (
    SensorID VARCHAR2(50) PRIMARY KEY,
    LocationID VARCHAR2(50) NOT NULL,
    SensorType VARCHAR2(20) NOT NULL CHECK (SensorType IN ('CO2', 'Noise', 'Temperature')),
    RegisteredAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sensors_location FOREIGN KEY (LocationID) REFERENCES LOCATIONS(LocationID)
);

-- Index for efficient location-based sensor queries
CREATE INDEX idx_sensors_location ON SENSOR_REGISTRY(LocationID);

-- ============================================================================
-- TABLE: ALERTS
-- Stores environmental alerts when thresholds are exceeded
-- ============================================================================
CREATE TABLE ALERTS (
    AlertID VARCHAR2(50) PRIMARY KEY,
    SensorID VARCHAR2(50) NOT NULL,
    MetricType VARCHAR2(20) NOT NULL,
    Value NUMBER NOT NULL,
    AlertLevel VARCHAR2(10) NOT NULL CHECK (AlertLevel IN ('LOW', 'MEDIUM', 'HIGH')),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alerts_sensor FOREIGN KEY (SensorID) REFERENCES SENSOR_REGISTRY(SensorID)
);

-- Indexes for efficient alert queries
CREATE INDEX idx_alerts_sensor ON ALERTS(SensorID);
CREATE INDEX idx_alerts_created ON ALERTS(CreatedAt);

-- ============================================================================
-- TABLE: TELEMETRY_SUMMARY
-- Stores daily aggregated telemetry data and Clean Score
-- ============================================================================
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

-- Index for efficient location and date-based queries
CREATE INDEX idx_summary_location_date ON TELEMETRY_SUMMARY(LocationID, SummaryDate);

-- ============================================================================
-- VIEW: LOCATION_HIERARCHY
-- Recursive CTE view for querying complete hierarchy paths
-- ============================================================================
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
