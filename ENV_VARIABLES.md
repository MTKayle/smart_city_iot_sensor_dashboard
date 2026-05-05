# Environment Variables Reference

This document describes all environment variables used in the Smart City IoT Sensor Dashboard.

## MQTT Broker Configuration

### MQTT_BROKER_HOST
- **Description**: Hostname or IP address of the MQTT broker
- **Default**: `mosquitto` (Docker service name)
- **Used by**: Backend, IoT Simulator
- **Example**: `mosquitto`, `192.168.1.100`, `mqtt.example.com`

### MQTT_BROKER_PORT
- **Description**: Port number for MQTT broker
- **Default**: `1883`
- **Used by**: Backend, IoT Simulator
- **Example**: `1883`

## MongoDB Configuration

### MONGO_USERNAME
- **Description**: MongoDB admin username
- **Default**: `admin`
- **Used by**: MongoDB container
- **Security**: Change in production

### MONGO_PASSWORD
- **Description**: MongoDB admin password
- **Default**: `admin123`
- **Used by**: MongoDB container
- **Security**: Use strong password in production

### MONGO_DATABASE
- **Description**: MongoDB database name
- **Default**: `smart_city`
- **Used by**: MongoDB container, Backend

### MONGODB_URI
- **Description**: Complete MongoDB connection string
- **Format**: `mongodb://username:password@host:port/database?authSource=admin`
- **Default**: `mongodb://admin:admin123@mongodb:27017/smart_city?authSource=admin`
- **Used by**: Backend
- **Note**: Must match MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE

## Oracle Database Configuration

### ORACLE_PASSWORD
- **Description**: Oracle system user password
- **Default**: `OraclePass123`
- **Used by**: Oracle container, Backend
- **Security**: Use strong password in production
- **Requirements**: Must contain uppercase, lowercase, and numbers

### ORACLE_DATABASE
- **Description**: Oracle pluggable database name
- **Default**: `XEPDB1`
- **Used by**: Oracle container, Backend
- **Note**: XEPDB1 is the default PDB for Oracle XE

### ORACLE_USER
- **Description**: Oracle database username
- **Default**: `system`
- **Used by**: Backend
- **Note**: Use dedicated user in production, not system

### ORACLE_DSN
- **Description**: Oracle Data Source Name (connection string)
- **Format**: `host:port/service_name`
- **Default**: `oracle-xe:1521/XEPDB1`
- **Used by**: Backend

## Backend API Configuration

### API_BASE_URL
- **Description**: Internal base URL for backend API
- **Default**: `http://backend:8000`
- **Used by**: Internal service communication
- **Note**: Uses Docker service name for internal networking

## Frontend Configuration (Vite)

> Vite reads `import.meta.env.VITE_*` at BUILD time only. Pass them via
> `docker-compose.yml` `args:` so they bake into the bundle. Setting them only
> as runtime `environment:` is a no-op for the production build.

### VITE_API_URL
- **Description**: External base URL for backend API (from browser)
- **Default**: `http://localhost:8000`
- **Used by**: Frontend (browser)
- **Production**: Change to public domain (e.g., `https://api.example.com`)

### VITE_WS_URL
- **Description**: WebSocket endpoint URL (from browser)
- **Default**: `ws://localhost:8000/ws`
- **Used by**: Frontend (browser)
- **Production**: Change to secure WebSocket (e.g., `wss://api.example.com/ws`)

### Legacy: REACT_APP_API_URL / REACT_APP_WS_URL
These were used by Create React App. The project has migrated to Vite — use
`VITE_API_URL` / `VITE_WS_URL` instead. The legacy names are now ignored.

## IoT Simulator Configuration

### SENSOR_LIST
- **Description**: Comma-separated list of sensor IDs to simulate
- **Default**: `sensor_001,sensor_002,sensor_003,sensor_004,sensor_005`
- **Used by**: IoT Simulator
- **Format**: Comma-separated, no spaces
- **Example**: `sensor_001,sensor_002,sensor_003`

### PUBLISH_INTERVAL
- **Description**: Interval in seconds between telemetry publications
- **Default**: `5`
- **Used by**: IoT Simulator
- **Range**: 1-60 seconds recommended
- **Note**: Lower values increase data volume and system load

## Environment File Setup

### Development (.env)
```bash
# Copy example file
cp .env.example .env

# Edit as needed
nano .env  # or use your preferred editor
```

### Production Considerations

1. **Never commit `.env` to version control**
   - Already in `.gitignore`
   - Contains sensitive credentials

2. **Use strong passwords**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, special characters
   - Different passwords for each service

3. **Use secrets management**
   - Docker secrets
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault

4. **Use HTTPS/TLS**
   - Change `http://` to `https://`
   - Change `ws://` to `wss://`
   - Configure SSL certificates

5. **Restrict CORS**
   - Configure specific allowed origins in backend
   - Don't use wildcard (*) in production

## Validation

### Check current environment
```bash
# View all environment variables (be careful with sensitive data)
docker-compose config

# Check specific service environment
docker-compose exec backend env | grep MONGO
```

### Test connections
```bash
# Test MongoDB connection
docker-compose exec mongodb mongosh -u admin -p admin123 --authenticationDatabase admin

# Test Oracle connection
docker-compose exec oracle-xe sqlplus system/OraclePass123@XEPDB1

# Test MQTT broker
docker-compose exec mosquitto mosquitto_sub -t 'sensors/#' -v
```

## Troubleshooting

### Connection refused errors
- Verify service names match Docker Compose service definitions
- Check services are running: `docker-compose ps`
- Check network connectivity: `docker-compose exec backend ping mongodb`

### Authentication errors
- Verify credentials match in all places they're used
- Check for typos in passwords
- Ensure special characters are properly escaped

### Port conflicts
- Check if ports are already in use: `netstat -tuln | grep <port>`
- Change host port mapping in docker-compose.yml
- Update REACT_APP_API_URL and REACT_APP_WS_URL accordingly

## Default Credentials Summary

| Service | Username | Password | Port |
|---------|----------|----------|------|
| MongoDB | admin | admin123 | 27017 |
| Oracle XE | system | OraclePass123 | 1521 |
| MQTT | (anonymous) | (none) | 1883 |

**⚠️ WARNING: Change all default credentials before deploying to production!**
