CREATE TABLE SENSOR_CAPABILITIES (
    CapabilityID      VARCHAR2(50)  PRIMARY KEY,
    SensorID          VARCHAR2(50)  NOT NULL,
    MetricType        VARCHAR2(20)  NOT NULL,
    Unit              VARCHAR2(20)  NOT NULL,
    MinRange          NUMBER(10,2),
    MaxRange          NUMBER(10,2),
    Accuracy          NUMBER(5,2),
    CalibrationDate   DATE,
    NextCalibration   DATE,
    IsActive          NUMBER(1)     DEFAULT 1 CHECK (IsActive IN (0,1)),
    CONSTRAINT fk_capabilities_sensor FOREIGN KEY (SensorID)
        REFERENCES SENSOR_REGISTRY(SensorID),
    CONSTRAINT uk_cap_sensor_metric UNIQUE (SensorID, MetricType)
);