CREATE TABLE TELEMETRY_SUMMARY (
    SummaryID    VARCHAR2(50)  PRIMARY KEY,
    SensorID     VARCHAR2(50),
    ClusterID    VARCHAR2(50),
    LocationID   VARCHAR2(50),
    TimeBucket   TIMESTAMP     NOT NULL,
    Granularity  VARCHAR2(10)  NOT NULL,
    AvgCO2         NUMBER(10,2),
    MaxCO2         NUMBER(10,2),
    MinCO2         NUMBER(10,2),
    StdDevCO2      NUMBER(10,2),
    AvgNoise       NUMBER(10,2),
    MaxNoise       NUMBER(10,2),
    MinNoise       NUMBER(10,2),
    StdDevNoise    NUMBER(10,2),
    AvgTemperature NUMBER(10,2),
    MaxTemperature NUMBER(10,2),
    MinTemperature NUMBER(10,2),
    StdDevTemperature NUMBER(10,2),
    AvgPM25        NUMBER(10,2),
    MaxPM25        NUMBER(10,2),
    AvgHumidity    NUMBER(5,2),
    CleanScore     NUMBER(5,2),
    AQI            NUMBER,
    DataPoints     NUMBER        NOT NULL,
    DataCompleteness NUMBER(5,2),
    CreatedAt      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_summary_sensor   FOREIGN KEY (SensorID)   REFERENCES SENSOR_REGISTRY(SensorID),
    CONSTRAINT fk_summary_cluster  FOREIGN KEY (ClusterID)  REFERENCES SENSOR_CLUSTERS(ClusterID),
    CONSTRAINT fk_summary_location FOREIGN KEY (LocationID) REFERENCES LOCATIONS(LocationID),
    CONSTRAINT chk_summary_target CHECK (
        (SensorID IS NOT NULL AND ClusterID IS NULL     AND LocationID IS NULL) OR
        (SensorID IS NULL     AND ClusterID IS NOT NULL AND LocationID IS NULL) OR
        (SensorID IS NULL     AND ClusterID IS NULL     AND LocationID IS NOT NULL)
    ),
    CONSTRAINT chk_aqi CHECK (AQI IS NULL OR AQI BETWEEN 0 AND 500)
);