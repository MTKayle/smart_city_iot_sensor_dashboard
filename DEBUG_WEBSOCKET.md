# Debug WebSocket Connection Issue

## Current Status
- Backend API is working (http://localhost:8000/api/health returns 200 OK)
- Frontend is loading but WebSocket keeps failing and retrying
- Network tab shows WebSocket requests stuck in "Pending" status

## Root Cause Analysis

The issue is that the frontend JavaScript bundle was built WITHOUT the correct WebSocket URL environment variable. Even though we added `VITE_WS_URL=ws://localhost:8000/ws` to the `.env` file, Vite needs this variable during BUILD TIME, not runtime.

## Step-by-Step Fix

### Step 1: Test WebSocket Directly

Open `test-websocket.html` in your browser (double-click the file or drag it into browser).

**Expected result:**
- Should show "✓ Connected to ws://localhost:8000/ws" in green
- Should receive real-time messages from backend

**If this works:** WebSocket server is fine, problem is in frontend build
**If this fails:** WebSocket server has issues (check backend logs)

### Step 2: Hard Refresh Browser

Even though we rebuilt the Docker image, your browser is still loading the OLD cached JavaScript files.

**Press: Ctrl + Shift + R** (or Ctrl + F5)

This forces the browser to reload ALL files from the server, bypassing cache.

### Step 3: Verify New Build is Loaded

After hard refresh, check the browser console (F12 → Console):

1. Look for the JavaScript filename in the Network tab
2. It should be a DIFFERENT hash than `index-DzTxaeaj.js`
3. If it's still `index-DzTxaeaj.js`, the new build wasn't loaded

### Step 4: Check What URL Frontend is Using

In browser console (F12 → Console), run:

```javascript
console.log(import.meta.env.VITE_WS_URL);
```

**Expected:** `ws://localhost:8000/ws`
**If undefined:** Environment variable wasn't baked into the build

## Alternative Solution: Bypass Docker Build

If the Docker build continues to have issues with environment variables, we can serve the frontend directly with Vite dev server:

### Option A: Run Frontend Locally (Recommended for Development)

```bash
cd frontend
npm install
npm run dev
```

This will start Vite dev server on http://localhost:5173 and will read `.env` file correctly.

### Option B: Fix Docker Build Args

Update `docker-compose.yml` to pass build args:

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
    args:
      VITE_API_URL: http://localhost:8000
      VITE_WS_URL: ws://localhost:8000/ws
```

Then rebuild: `docker-compose build --no-cache frontend`

## Troubleshooting Commands

### Check if backend WebSocket is accessible:
```bash
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" http://localhost:8000/ws
```

Expected: HTTP 101 Switching Protocols

### Check backend logs for WebSocket connections:
```bash
docker logs backend-consumer --tail 50 | grep -i websocket
```

### Check frontend container files:
```bash
docker exec frontend-dashboard ls -la /usr/share/nginx/html/assets/
```

Should show JavaScript files with hash names.

## Next Steps

1. Try `test-websocket.html` first to verify WebSocket server works
2. Hard refresh browser (Ctrl + Shift + R)
3. If still not working, try running frontend locally with `npm run dev`
4. Report back which step worked or failed
