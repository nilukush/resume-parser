# Deployment Troubleshooting Guide

**Date:** 2026-02-23
**Status:** 🔧 CONFIGURATION REQUIRED
**Severity:** Blocking deployment

---

## Current Status

### ✅ Completed Steps

1. **Frontend vercel.json** - Fixed environment variable syntax (strings instead of objects)
2. **Frontend .env.production** - Updated to correct HTTPS/WSS URLs
3. **Backend Configuration** - All configuration files fixed

### ❌ Blocking Issue: Vercel Project Root Directory

**Problem:** The Vercel project `resumate-backend` has incorrect root directory configured in the dashboard.

**Symptoms:**
- All requests return 404 NOT_FOUND
- Serverless functions not being executed
- Error: `The provided path "~/gh/resume-parser/backend/backend" does not exist`

**Root Cause:** The Vercel dashboard has Root Directory set to `backend/backend` instead of `.` or `backend`.

---

## Solution Options

### Option 1: Fix via Vercel Dashboard (RECOMMENDED)

1. Go to: https://vercel.com/nilukushs-projects/resumate-backend/settings
2. Scroll to **"Root Directory"** section
3. Change from `backend/backend` to `.`
4. Click **Save**
5. Redeploy from `/Users/nileshkumar/gh/resume-parser/backend`:
   ```bash
   cd /Users/nileshkumar/gh/resume-parser/backend
   vercel --prod --scope nilukushs-projects --yes
   ```

### Option 2: Create New Project (CLEAN SLATE)

1. Unlink current project:
   ```bash
   cd /Users/nileshkumar/gh/resume-parser/backend
   rm -rf .vercel
   ```

2. Create new project:
   ```bash
   vercel link --scope nilukushs-projects
   # When prompted for project name, use: resumate-backend-v2
   # When prompted for root directory, use: . (current directory)
   ```

3. Deploy:
   ```bash
   vercel --prod --scope nilukushs-projects --yes
   ```

4. Update frontend .env.production with new backend URL

---

## After Fix: Verification Steps

Once the root directory is fixed and deployment succeeds, verify:

```bash
# 1. Test health endpoint
curl https://YOUR_BACKEND_URL.vercel.app/health

# Should return:
# {
#   "status": "healthy",
#   "database": "connected",
#   "version": "1.0.0",
#   "environment": "production",
#   "timestamp": "2026-02-23T..."
# }
```

---

## Deployment URLs Reference

### Current Deployment URLs

**Backend:**
- Latest: https://resumate-backend-4yl17dd45-nilukushs-projects.vercel.app
- Aliased: https://resume-parser-woad.vercel.app
- Expected: https://resumate-backend.vercel.app (after fixing)

**Frontend:**
- Not yet deployed (configuration fixed, ready to deploy)

---

## Files Modified

### Frontend Configuration

**`frontend/vercel.json`** - Fixed environment variable syntax:
```json
{
  "env": {
    "VITE_API_BASE_URL": "https://resumate-backend.vercel.app/v1",
    "VITE_WS_BASE_URL": "wss://resumate-backend.vercel.app/ws"
  }
}
```

**`frontend/.env.production`** - Updated URLs:
```bash
VITE_API_BASE_URL=https://resumate-backend.vercel.app/v1
VITE_WS_BASE_URL=wss://resumate-backend.vercel.app/ws
```

### Backend Configuration

**`backend/vercel.json`** - Minimal configuration (no rewrites needed):
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "pip install --break-system-packages -r requirements.txt",
  "installCommand": "pip install --break-system-packages -r requirements.txt",
  "framework": null
}
```

---

## Next Steps (After Fixing Root Directory)

1. ✅ Fix backend root directory in Vercel dashboard
2. ✅ Redeploy backend
3. ✅ Test health endpoint returns 200 OK
4. ⏳ Deploy frontend
5. ⏳ Test complete user flow

---

## Technical Details

### Why Root Directory Matters

Vercel uses the root directory to determine:
- Where to find the `api/` folder for serverless functions
- Where to find `vercel.json` for build configuration
- What files to include in the deployment bundle

**Incorrect:** `backend/backend` (looks for `backend/backend/api/`)
**Correct:** `.` or `backend` (looks for `backend/api/`)

### Serverless Function Detection

Vercel automatically detects serverless functions in:
- `api/*.py` (Python)
- `api/*.js` (Node.js)
- `api/*.go` (Go)

The deployment must include the `api/` directory at the root level.

---

## Support Resources

- [Vercel Project Settings Documentation](https://vercel.com/docs/projects/project-settings)
- [Vercel Python Runtime Documentation](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Deployment Protection](https://vercel.com/docs/deployments/troubleshooting#deployment-protection)

---

**Created by:** Claude (Sonnet 4.5)
**Date:** 2026-02-23 13:30 GST
**Related Bug Fixes:** #17b (PEP 668 Compliance)
