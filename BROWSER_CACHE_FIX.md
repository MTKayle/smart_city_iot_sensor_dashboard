# Browser Cache Fix - Load New Frontend

## Problem
Your browser is loading the OLD cached JavaScript files from the previous frontend build. Even though we rebuilt the frontend Docker container with the 30-second timeout, your browser is still using the old 10-second timeout from cache.

## Solution: Hard Refresh Browser

You need to force your browser to reload all files from the server, bypassing the cache.

### Windows (Chrome/Edge/Firefox)
Press: **Ctrl + Shift + R**

Or:

Press: **Ctrl + F5**

### Alternative Method (If hard refresh doesn't work)
1. Open Developer Tools (F12)
2. Right-click the refresh button in the browser toolbar
3. Select "Empty Cache and Hard Reload"

## Verify It Worked

After hard refresh, check the browser console:
- You should see "WebSocket connected" ✓
- You should NOT see "Error loading initial data" ✗
- The map should load with sensor markers ✓

## What Changed
- Old frontend: 10 second API timeout → `/api/locations` request was canceled
- New frontend: 30 second API timeout → `/api/locations` request will complete successfully

The `/api/locations` endpoint takes ~15 seconds to respond (Oracle client initialization), so the 30-second timeout allows it to complete.
