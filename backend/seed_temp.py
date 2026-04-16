import sys
import os

# Add /app to python path since we are running inside container
sys.path.append("/app")

from app.db.oracle_client import get_oracle_client

client = get_oracle_client()
print("Connected to Oracle.")

cursor = client.connection.cursor()
cursor.execute("INSERT INTO TELEMETRY_SUMMARY (LocationID, SummaryDate, AvgCO2, AvgNoise, AvgTemperature, CleanScore) VALUES ('ward_001', TRUNC(SYSDATE), 400.5, 45.2, 26.5, 95.5)")
cursor.execute("INSERT INTO TELEMETRY_SUMMARY (LocationID, SummaryDate, AvgCO2, AvgNoise, AvgTemperature, CleanScore) VALUES ('ward_002', TRUNC(SYSDATE), 850.5, 65.2, 28.5, 75.0)")
cursor.execute("INSERT INTO TELEMETRY_SUMMARY (LocationID, SummaryDate, AvgCO2, AvgNoise, AvgTemperature, CleanScore) VALUES ('ward_003', TRUNC(SYSDATE), 1200.0, 75.5, 30.0, 55.0)")
cursor.execute("INSERT INTO TELEMETRY_SUMMARY (LocationID, SummaryDate, AvgCO2, AvgNoise, AvgTemperature, CleanScore) VALUES ('ward_004', TRUNC(SYSDATE), 2000.0, 95.0, 35.0, 20.0)")
client.connection.commit()
print("Inserted mock telemetry summaries for leaderboard.")
cursor.close()
