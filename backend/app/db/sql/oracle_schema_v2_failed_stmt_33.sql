CREATE TABLE INCIDENT_ALERTS (
    IncidentAlertID  VARCHAR2(50)  PRIMARY KEY,
    IncidentID       VARCHAR2(50),
    AlertID          VARCHAR2(50),
    AddedAt          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    AddedBy          VARCHAR2(100),
    CONSTRAINT fk_incident FOREIGN KEY (IncidentID) REFERENCES INCIDENTS(IncidentID),
    CONSTRAINT fk_alert    FOREIGN KEY (AlertID)    REFERENCES ALERTS(AlertID),
    CONSTRAINT uk_incident_alert UNIQUE (IncidentID, AlertID)
);