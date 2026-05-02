CREATE TABLE LOCATIONS (
    LocationID  VARCHAR2(50)  PRIMARY KEY,
    Name        VARCHAR2(100) NOT NULL,
    ParentID    VARCHAR2(50),
    Type        VARCHAR2(20)  NOT NULL CHECK (Type IN ('City','District','Ward')),
    CenterLat   NUMBER(10,8),
    CenterLng   NUMBER(11,8),
    Geometry    CLOB,
    Area        NUMBER(12,2),
    Population  NUMBER,
    CreatedAt   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_locations_parent FOREIGN KEY (ParentID)
        REFERENCES LOCATIONS(LocationID),
    CONSTRAINT chk_locations_coords CHECK (
        (CenterLat IS NULL AND CenterLng IS NULL) OR
        (CenterLat IS NOT NULL AND CenterLng IS NOT NULL)
    )
);