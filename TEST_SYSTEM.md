# System Test - Quick Verification

## ✅ All Services Are Running

Run this command to verify:
```bash
docker-compose ps
```

All containers should show "Up" or "Healthy" status.

## 🧪 Test Backend API

### Test 1: Health Check
Open in browser or run in terminal:
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{"status":"healthy","service":"smart-city-iot-backend"}
```

### Test 2: Get Sensors
```bash
curl http://localhost:8000/api/sensors
```

Should return JSON array with 27 sensors.

### Test 3: Get Alerts
```bash
curl http://localhost:8000/api/alerts
```

Should return JSON array with recent alerts.

### Test 4: API Documentation
Open in browser:
```
http://localhost:8000/docs
```

You should see the interactive Swagger API documentation.

## 🌐 Test Frontend

### Step 1: Clear Browser Cache
**IMPORTANT**: The frontend was just rebuilt, so you need to clear your browser cache.

**Option A: Hard Refresh (Recommended)**
- Windows/Linux: Press `Ctrl + Shift + R` or `Ctrl + F5`
- Mac: Press `Cmd + Shift + R`

**Option B: Clear Cache Manually**
1. Open browser settings
2. Clear browsing data
3. Select "Cached images and files"
4. Clear data

### Step 2: Open Frontend
Navigate to:
```
http://localhost:3000
```

### Step 3: Check Browser Console
1. Press F12 to open Developer Tools
2. Go to "Console" tab
3. Look for any errors (should be none)
4. Look for "WebSocket connected" message (indicates real-time connection is working)

### Step 4: Check Network Tab
1. In Developer Tools, go to "Network" tab
2. Refresh the page (F5)
3. Look for requests to:
   - `http://localhost:8000/api/locations`
   - `http://localhost:8000/api/sensors`
   - `http://localhost:8000/api/alerts`
   - `http://localhost:8000/api/leaderboard`
4. All should show status 200 (OK)

## 📊 Expected Frontend Display

After clearing cache and refreshing, you should see:

1. **MapView** (top section)
   - Interactive map with sensor markers
   - Markers colored by sensor type (CO2, Noise, Temperature)
   - Click markers to see sensor details

2. **ChartView** (middle section)
   - Real-time line charts for selected sensor
   - Three metrics: CO2, Noise, Temperature
   - Charts update automatically as new data arrives

3. **Leaderboard** (right panel)
   - List of locations ranked by Clean Score
   - Highest score = cleanest location
   - Shows average metrics for each location

4. **AlertsPanel** (bottom section)
   - Recent threshold violations
   - Color-coded by severity (LOW/MEDIUM/HIGH)
   - Updates in real-time via WebSocket

## 🔧 If Frontend Still Shows Error

### Quick Fix Commands:
```bash
# 1. Rebuild frontend without cache
docker-compose build --no-cache frontend

# 2. Restart frontend
docker-compose up -d frontend

# 3. Wait 5 seconds for container to start
Start-Sleep -Seconds 5

# 4. Open browser and do HARD REFRESH (Ctrl+Shift+R)
```

### Check if API is accessible from browser:
1. Open http://localhost:8000/api/health in browser
2. If you see JSON response, backend is working
3. If you see "This site can't be reached", backend is not accessible

### Check Docker logs:
```bash
# Backend logs
docker-compose logs backend --tail 30

# Frontend logs  
docker-compose logs frontend --tail 30
```

## ✨ Real-Time Features Test

Once frontend is loaded:

1. **Watch for new alerts**
   - Alerts should appear automatically in the AlertsPanel
   - No page refresh needed

2. **Select a sensor**
   - Click on a sensor marker in the MapView
   - ChartView should update to show that sensor's data

3. **Monitor telemetry**
   - Charts should update every 5 seconds with new data
   - IoT Simulator is publishing data continuously

## 📝 Manual Testing Checklist

- [ ] Backend API responds at http://localhost:8000/api/health
- [ ] API documentation accessible at http://localhost:8000/docs
- [ ] Frontend loads at http://localhost:3000 (after hard refresh)
- [ ] MapView displays sensor markers
- [ ] ChartView shows telemetry charts
- [ ] Leaderboard shows location rankings
- [ ] AlertsPanel shows recent alerts
- [ ] WebSocket connection established (check console)
- [ ] Real-time updates working (alerts appear automatically)
- [ ] No errors in browser console

## 🎯 Success Criteria

✅ All checkboxes above are checked
✅ No errors in browser console
✅ Real-time data is flowing
✅ All components are interactive

If all tests pass, the system is working correctly! 🎉

Refer to `MANUAL_TESTING_GUIDE.md` for detailed testing procedures.
