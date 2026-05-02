CREATE TABLE ALERTS (
    AlertID          VARCHAR2(50)   PRIMARY KEY,
    SensorID         VARCHAR2(50),
    ClusterID        VARCHAR2(50),
    LocationID       VARCHAR2(50)   NOT NULL,
    AlertType        VARCHAR2(30)   NOT NULL,
    MetricType       VARCHAR2(20)   NOT NULL,
    Value            NUMBER(10,2)   NOT NULL,
    Threshold        NUMBER(10,2),
    PredictedValue   NUMBER(10,2),
    ConfidenceScore  NUMBER(5,4),
    Severity         VARCHAR2(10),
    Status           VARCHAR2(20)   DEFAULT 'OPEN',
    CreatedAt        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    AcknowledgedAt   TIMESTAMP,
    ResolvedAt       TIMESTAMP,
    Message          CLOB,
    CONSTRAINT fk_alert_sensor   FOREIGN KEY (SensorID)   REFERENCES SENSOR_REGISTRY(SensorID),
    CONSTRAINT fk_alert_cluster  FOREIGN KEY (ClusterID)  REFERENCES SENSOR_CLUSTERS(ClusterID),
    CONSTRAINT fk_alert_location FOREIGN KEY (LocationID) REFERENCES LOCATIONS(LocationID),
    CONSTRAINT chk_alert_target CHECK (
        SensorID IS NOT NULL OR ClusterID IS NOT NULL
    )
);