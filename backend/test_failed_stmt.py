"""Test the failed statement."""
import oracledb

# Connect
conn = oracledb.connect(
    user="system",
    password="OraclePass123",
    dsn="localhost:1521/XEPDB1"
)

cursor = conn.cursor()

# Read the failed statement
with open('app/db/sql/oracle_schema_v2_failed_stmt_10.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

print(f"Statement length: {len(sql)} chars")
print(f"Statement repr: {repr(sql[:100])}")

try:
    cursor.execute(sql)
    conn.commit()
    print("✓ Statement executed successfully!")
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Error type: {type(e)}")

cursor.close()
conn.close()
