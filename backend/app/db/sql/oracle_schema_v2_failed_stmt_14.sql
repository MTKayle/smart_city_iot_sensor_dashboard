CREATE TABLE SENSOR_CLUSTERS (
    ClusterID    VARCHAR2(50)  PRIMARY KEY,
    LocationID   VARCHAR2(50)  NOT NULL,
    ClusterName  VARCHAR2(100),
    CenterLat    NUMBER(10,8)  NOT NULL,
    CenterLng    NUMBER(11,8)  NOT NULL,
    Radius       NUMBER(8,2)   NOT NULL,
    SensorCount  NUMBER        DEFAULT 0,
    Algorithm    VARCHAR2(50),
    CreatedAt    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_clusters_location FOREIGN KEY (LocationID)
        REFERENCES LOCATIONS(LocationID),
    CONSTRAINT chk_clusters_radius CHECK (Radius > 0)
);