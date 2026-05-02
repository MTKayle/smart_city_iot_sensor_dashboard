CREATE TABLE INCIDENTS (
    IncidentID   VARCHAR2(50)   PRIMARY KEY,
    Title        VARCHAR2(200),
    Description  CLOB,
    Priority     VARCHAR2(10),
    Status       VARCHAR2(20)   DEFAULT 'NEW',
    AssignedTo   VARCHAR2(100),
    AssignedTeam VARCHAR2(100),
    RootCause    VARCHAR2(200),
    Resolution   CLOB,
    CreatedAt    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ResolvedAt   TIMESTAMP
);