CREATE TABLE SENSOR_HEALTH_LOGS (
    LogID            VARCHAR2(50)  PRIMARY KEY,
    SensorID         VARCHAR2(50)  NOT NULL,
    Timestamp        TIMESTAMP     NOT NULL,
    Status           VARCHAR2(20),
    BatteryLevel     NUMBER(5,2),
    SignalStrength   NUMBER(6,2),
    DataCompleteness NUMBER(5,2),
    LastReadingAt    TIMESTAMP,
    ErrorCode        VARCHAR2(50),
    ErrorMessage     VARCHAR2(500),
    Metadata         CLOB,
    CONSTRAINT fk_health_sensor FOREIGN KEY (SensorID)
        REFERENCES SENSOR_REGISTRY(SensorID)
);