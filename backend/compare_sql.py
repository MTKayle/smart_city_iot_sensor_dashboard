"""Compare working vs failing SQL."""

# Working SQL (from test_create_table.py)
working_sql = """
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
)
"""

# Failing SQL (from file)
with open('test_simple_create_lf.sql', 'r') as f:
    failing_sql = f.read()

print(f"Working SQL length: {len(working_sql)}")
print(f"Failing SQL length: {len(failing_sql)}")
print(f"Working SQL ends with: {repr(working_sql[-20:])}")
print(f"Failing SQL ends with: {repr(failing_sql[-20:])}")

# Find first difference
for i, (c1, c2) in enumerate(zip(working_sql, failing_sql)):
    if c1 != c2:
        print(f"First difference at position {i}:")
        print(f"  Working: {repr(working_sql[max(0,i-10):i+10])}")
        print(f"  Failing: {repr(failing_sql[max(0,i-10):i+10])}")
        break
else:
    if len(working_sql) != len(failing_sql):
        print(f"Lengths differ: working={len(working_sql)}, failing={len(failing_sql)}")
        print(f"Working ends: {repr(working_sql[-50:])}")
        print(f"Failing ends: {repr(failing_sql[-50:])}")
    else:
        print("SQL strings are identical!")

# Test both
import oracledb
conn = oracledb.connect(user='system', password='OraclePass123', dsn='localhost:1521/XEPDB1')
cursor = conn.cursor()

print("\nTesting working SQL...")
try:
    cursor.execute(working_sql)
    conn.commit()
    print("✓ Working SQL succeeded!")
    # Drop it for next test
    cursor.execute("DROP TABLE LOCATIONS CASCADE CONSTRAINTS")
    conn.commit()
except Exception as e:
    print(f"✗ Working SQL failed: {e}")

print("\nTesting failing SQL...")
try:
    cursor.execute(failing_sql)
    conn.commit()
    print("✓ Failing SQL succeeded!")
except Exception as e:
    print(f"✗ Failing SQL failed: {e}")

cursor.close()
conn.close()
