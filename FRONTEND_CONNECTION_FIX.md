# Frontend Connection Issue - Troubleshooting Guide

## Problem
Frontend shows error: "No response from server. Please check your connection."

## Root Cause
The frontend was built without the correct `VITE_API_URL` environment variable, causing API calls to fail.

## Solution Applied
1. Created `frontend/.env` file with correct API URL
2. Rebuilt frontend Docker image with environment variables
3. Restarted frontend container

## Verification Steps

### 1. Check if Backend API is Accessible
Open your browser and navigate to:
- http://localhost:8000/api/health
- http://localhost:8000/api/sensors
- http://localhost:8000/docs (API documentation)

You should see JSON responses. If not, the backend is not running properly.

### 2. Check Frontend
Open http://localhost:3000 in your browser and:
1. Open Browser Developer Tools (F12)
2. Go to the "Network" tab
3. Refresh the page
4. Look for requests to `http://localhost:8000/api/*`

### 3. Check for CORS Errors
In the browser console (F12 → Console tab), look for errors like:
- "CORS policy: No 'Access-Control-Allow-Origin' header"
- "Failed to fetch"
- "Network error"

## Common Issues and Fixes

### Issue 1: Browser Cache
**Symptom**: Old version of frontend is still loaded
**Fix**: Hard refresh the browser
- Windows/Linux: Ctrl + Shift + R or Ctrl + F5
- Mac: Cmd + Shift + R

### Issue 2: Backend Not Running
**Symptom**: Cannot access http://localhost:8000/api/health
**Fix**: 
```bash
docker-compose ps
docker-compose logs backend
docker-compose restart backend
```

### Issue 3: Frontend Container Not Updated
**Symptom**: Frontend still shows old error after rebuild
**Fix**:
```bash
# Force rebuild and restart
docker-compose build --no-cache frontend
docker-compose up -d frontend

# Clear browser cache and hard refresh
```

### Issue 4: Port Conflicts
**Symptom**: Cannot access localhost:8000 or localhost:3000
**Fix**: Check if ports are already in use
```bash
# Windows PowerShell
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# If ports are in use, stop the conflicting process or change ports in docker-compose.yml
```

### Issue 5: Docker Network Issues
**Symptom**: Containers can't communicate
**Fix**:
```bash
# Restart all containers
docker-compose down
docker-compose up -d

# Check network
docker network ls
docker network inspect smart_city_iot_sensor_dashboard_smart-city-network
```

## Manual Test After Fix

1. Open http://localhost:3000
2. You should see:
   - MapView with sensor markers
   - ChartView with real-time metrics
   - Leaderboard with location rankings
   - AlertsPanel with recent alerts

3. Check WebSocket connection:
   - Open browser console (F12)
   - Look for "WebSocket connected" message
   - Alerts should appear in real-time as they're generated

## If Still Not Working

1. Check all services are running:
```bash
docker-compose ps
```

2. Check backend logs for errors:
```bash
docker-compose logs backend --tail 50
```

3. Check frontend logs:
```bash
docker-compose logs frontend --tail 50
```

4. Verify environment variables:
```bash
# Check backend environment
docker exec backend-consumer env | grep -E "MQTT|MONGO|ORACLE"

# Check if frontend was built with correct env
docker exec frontend-dashboard cat /usr/share/nginx/html/index.html | head -20
```

5. Test API directly from browser:
   - Open http://localhost:8000/docs
   - Try the `/api/health` endpoint
   - Try the `/api/sensors` endpoint

## Expected Behavior After Fix

- Frontend loads without errors
- MapView shows sensor locations on map
- ChartView displays real-time telemetry data
- Leaderboard shows locations ranked by Clean Score
- AlertsPanel shows recent threshold violations
- WebSocket connection established and receiving real-time updates
- No console errors in browser developer tools
