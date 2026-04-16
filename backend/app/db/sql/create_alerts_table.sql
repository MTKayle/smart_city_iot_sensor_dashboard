-- Create ALERTS table with AlertLevel instead of Level
-- This fixes ORA-01747 error caused by using reserved word "Level"

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
