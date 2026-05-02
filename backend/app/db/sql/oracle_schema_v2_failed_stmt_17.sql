CREATE TABLE SENSOR_REGISTRY (
    SensorID         VARCHAR2(50)  PRIMARY KEY,
    LocationID       VARCHAR2(50)  NOT NULL,
    ClusterID        VARCHAR2(50),
    Latitude         NUMBER(10,8)  NOT NULL,
    Longitude        NUMBER(11,8)  NOT NULL,
    Altitude         NUMBER(7,2),
    SensorModel      VARCHAR2(100),
    FirmwareVersion  VARCHAR2(50),
    Status           VARCHAR2(20)  DEFAULT 'Active' NOT NULL
                         CHECK (Status IN ('Active','Offline','Maintenance','Decommissioned')),
    InstallDate      DATE          NOT NULL,
    LastMaintenance  DATE,
    NextMaintenance  DATE,
    RegisteredAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sensors_location FOREIGN KEY (LocationID)
        REFERENCES LOCATIONS(LocationID),
    CONSTRAINT fk_sensors_cluster FOREIGN KEY (ClusterID)
        REFERENCES SENSOR_CLUSTERS(ClusterID),
    CONSTRAINT chk_lat CHECK (Latitude  BETWEEN -90  AND 90),
    CONSTRAINT chk_lng CHECK (Longitude BETWEEN -180 AND 180)
);