-- Fix ALERTS table by renaming Level column to AlertLevel
-- This fixes ORA-01747 error caused by using reserved word "Level"

-- Drop the old table (cascade constraints to remove foreign keys)
DROP TABLE ALERTS CASCADE CONSTRAINTS;

-- Recreate ALERTS table with AlertLevel instead of Level
CREATE TABLE ALERTS (
    AlertID VARCHAR2(50) PRIMARY KEY,
    SensorID VARCHAR2(50) NOT NULL,
    MetricType VARCHAR2(20) NOT NULL,
    Value NUMBER NOT NULL,
    AlertLevel VARCHAR2(10) NOT NULL CHECK (AlertLevel IN ('LOW', 'MEDIUM', 'HIGH')),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alerts_sensor FOREIGN KEY (SensorID) REFERENCES SENSOR_REGISTRY(SensorID)
);

-- Recreate indexes
CREATE INDEX idx_alerts_sensor ON ALERTS(SensorID);
CREATE INDEX idx_alerts_created ON ALERTS(CreatedAt);
