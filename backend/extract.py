import re
data = open('d:/DB Advance/smart-city/smart_city_iot_sensor_dashboard/backend/app/db/sql/oracle_seed_v2.sql', encoding='utf-8').read()
sensors = re.findall(r"INSERT INTO SENSOR_REGISTRY[^\)]+\)[\s]*VALUES\s*\('([^']+)'", data)
print(sensors)
print(len(sensors))
