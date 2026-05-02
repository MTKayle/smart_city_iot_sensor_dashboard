#!/bin/bash
# Oracle Database Backup Script using Data Pump
# Date: $(date +%Y-%m-%d_%H-%M-%S)

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/oracle/admin/XE/dpdump"
BACKUP_FILE="smart_city_backup_${TIMESTAMP}.dmp"
LOG_FILE="smart_city_backup_${TIMESTAMP}.log"

echo "Starting Oracle database backup..."
echo "Backup file: ${BACKUP_FILE}"
echo "Log file: ${LOG_FILE}"

# Execute Data Pump export
expdp system/OraclePass123@XEPDB1 \
  DIRECTORY=DATA_PUMP_DIR \
  DUMPFILE=${BACKUP_FILE} \
  LOGFILE=${LOG_FILE} \
  SCHEMAS=SYSTEM \
  EXCLUDE=STATISTICS

echo "Backup completed. Files created:"
echo "  - ${BACKUP_DIR}/${BACKUP_FILE}"
echo "  - ${BACKUP_DIR}/${LOG_FILE}"
