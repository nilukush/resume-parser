# Platform Update: Render + Fly.io + Supabase Deployment Strategy

**Date:** 2026-02-21
**Reason:** Railway limits free projects; switching to multi-platform free tier approach

---

## Platform Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Multi-Platform Deployment                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Render     │    │   Fly.io     │    │   Vercel     │      │
│  │              │    │              │    │              │      │
│  │ FastAPI      │    │ Celery       │    │ React        │      │
│  │ Backend      │◄──►│ Worker       │◄──►│ Frontend     │      │
│  │              │    │              │    │              │      │
│  │ + PostgreSQL │    │ (Docker)     │    │ (Static)     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                      │               │
│         │         ┌──────────────┐            │               │
│         └────────►│  Supabase    │────────────┘               │
│                  │  PostgreSQL  │                            │
│                  │  (Optional)   │                            │
│                  └──────────────┘                            │
│                                                                  │
│                  ┌──────────────┐                              │
│                  │ Redis Cloud  │                              │
│                  │   (Redis)    │                              │
│                  └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Platform Comparison: Why This Stack?

### 1. **Render** - FastAPI Backend ⭐ Primary Choice

**Free Tier:**

- 750 hours/month web service runtime (enough for 24/7 operation)
- 1GB PostgreSQL database included
- Automatic SSL certificates
- Auto-deploys from GitHub

**Pros:**

- ✅ Native Python/FastAPI support
- ✅ Best documentation for Python deployment
- ✅ Built-in PostgreSQL with backups
- ✅ Simple environment variable management
- ✅ Easy scaling to paid tiers ($7/month for permanent service)

**Cons:**

- ⚠️ Services spin down after 15 min inactivity (cold start ~15-30s)
- ⚠️ 512MB RAM limit on free tier

**For ResuMate:**

- Acceptable cold start for MVP (users wait 30s for parsing anyway)
- PostgreSQL included (no separate DB setup needed)
- Can upgrade to "Always On" for $7/month if needed

---

### 2. **Fly.io** - Celery Worker ⭐ Best for Background Jobs

**Free Tier:**

- 3 shared CPU VMs (256MB RAM each)
- No sleep mode (runs 24/7)
- Global edge deployment (35+ regions)

**Pros:**

- ✅ **Stays running** - no sleep mode (critical for Celery!)
- ✅ Full Docker support
- ✅ TCP/WebSocket support
- ✅ Can deploy close to users (low latency)

**Cons:**

- ⚠️ More complex configuration (requires `flyctl` CLI)
- ⚠️ Smaller RAM (256MB vs Render's 512MB)

**For ResuMate:**

- Perfect for Celery worker (needs to stay running)
- Can sleep Render backend when idle, keep Celery worker active
- Dockerfile already compatible with Fly.io

---

### 3. **Supabase** - PostgreSQL Database ⭐ Alternative to Render's DB

**Free Tier:**

- 500MB PostgreSQL database
- 1GB bandwidth/month
- 50MB file storage

**Pros:**

- ✅ Excellent management dashboard
- ✅ Real-time subscriptions (future feature potential)
- ✅ Built-in authentication (future user accounts)
- ✅ RESTful API auto-generated (optional use)
- ✅ Row-level security (future multi-tenant)

**Cons:**

- ⚠️ Smaller free tier than Render (500MB vs 1GB)
- ⚠️ Additional service to manage

**For ResuMate:**

- Use **Render's PostgreSQL** initially (simpler)
- Migrate to Supabase if needing advanced features (auth, real-time)

**Decision:** Start with Render's built-in PostgreSQL, evaluate Supabase later.

---

### 4. **Redis Cloud** - Celery Broker ⭐ Best Redis Option

**Free Tier:**

- 30K commands/month
- 25MB storage
- 30 connections

**Alternative:** **Upstash**

- 10K commands/day free tier
- Serverless Redis (no cold starts)
- Better for sporadic usage

**For ResuMate:**

- Use **Redis Cloud** (more commands/month)
- Or use **Render's Redis** add-on (simpler, $0.20/month)

**Recommendation:** Start with Render's built-in Redis add-on.

---

### 5. **Vercel** - Frontend (Unchanged) ✅

**Free Tier:**

- Unlimited projects
- 100GB bandwidth/month
- Automatic deployments
- Edge CDN

**Perfect for:** React/Next.js frontend deployment

---

## Updated Task 37: Production Deployment Steps

### Step 1: Deploy FastAPI Backend to Render

**Prerequisites:**

- Render account: https://render.com (free signup)
- GitHub repository connected
- Backend code tested locally

**Implementation:**

1. **Prepare backend for Render:**

Create `backend/render.yaml`:

```yaml
services:
  - type: web
    name: resumate-backend
    env: python
    region: oregon
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: resumate-db
          property: connectionString
      - key: OPENAI_API_KEY
        sync: false
      - key: SECRET_KEY
        generate: true
      - key: ENVIRONMENT
        value: production
      - key: ALLOWED_ORIGINS
        value: https://resumate-frontend.vercel.app

databases:
  - name: resumate-db
    databaseName: resumate
    user: resumate_user
```

2. **Deploy via Render Dashboard:**
   
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Select root directory: `backend`
   - Render detects Python, creates config
   - Add environment variables
   - Click "Deploy"

3. **Verify deployment:**
   
   ```bash
   # Check health endpoint
   curl https://resumate-backend.onrender.com/health
   
   # Expected response:
   # {"status":"healthy","version":"1.0.0","database":"connected"}
   ```

**Acceptance Criteria:**

- ✅ Backend deployed at `https://resumate-backend.onrender.com`
- ✅ Health check returns 200
- ✅ Database connected
- ✅ Auto-deploys from GitHub main branch

---

### Step 2: Deploy Celery Worker to Fly.io

**Prerequisites:**

- Fly.io account: https://fly.io (free signup)
- `flyctl` CLI installed
- Dockerfile for Celery worker

**Implementation:**

1. **Create `backend/Dockerfile.celery`:**
   
   ```dockerfile
   FROM python:3.11-slim
   ```

WORKDIR /app

# Install dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install system dependencies for OCR

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy application

COPY . .

# Command to run Celery worker

CMD ["celery", "-A", "app.core.celery_app", "worker", "--loglevel=info"]

```
2. **Initialize Fly.io app:**
```bash
cd backend
fly launch --name resumate-celery --dockerfile Dockerfile.celery

# Follow prompts:
# - Choose region:就近 (e.g., Singapore for Dubai users)
# - Do not deploy yet (we'll configure first)
```

3. **Create `backend/fly.toml`:**
   
   ```toml
   app = "resumate-celery"
   primary_region = "sin"
   ```

[env]
  REDIS_URL = "redis://default:password@your-redis-cloud-host:port"
  DATABASE_URL = "postgresql+asyncpg://user:pass@resumate-db.onrender.com:5432/resumate"
  OPENAI_API_KEY = "sk-..."
  SECRET_KEY = "..."
  ENVIRONMENT = "production"

[build]
  dockerfile = "Dockerfile.celery"

[vm]
  cpu = "shared"
  memory_mb = 256

[[mounts]]
  source = "celery_data"
  destination = "/data"

```
4. **Deploy Celery worker:**
```bash
fly deploy
```

5. **Scale to 1 instance (free tier):**
   
   ```bash
   fly scale count 1
   ```

**Acceptance Criteria:**

- ✅ Celery worker deployed to Fly.io
- ✅ Logs show worker connected to Redis
- ✅ Worker ready to process tasks
- ✅ Auto-restart on failure

---

### Step 3: Configure Redis for Celery

**Options:**

**Option A: Render Redis Add-On** (Simpler)

- Price: $0.20/month (basically free)
- Setup: Render dashboard → Redis → Create
- Get `REDIS_URL` from dashboard
- Add to Celery worker env vars

**Option B: Redis Cloud Free Tier** (More free)

- Price: Free (30K commands/month)
- Signup: https://redis.com/try-free/
- Create database, get connection URL
- Add to Fly.io env vars

**Option C: Upstash** (Serverless)

- Price: Free (10K commands/day)
- Best for sporadic usage
- Signup: https://upstash.com/

**Recommendation:** Use **Render Redis Add-On** for simplicity ($0.20/month is negligible).

---

### Step 4: Configure CI/CD Pipeline

**GitHub Actions Workflow:**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Test Backend
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/ -v

      - name: Test Frontend
        run: |
          cd frontend
          npm install
          npm test -- --run
          npm run type-check

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    # Auto-deploys via Render's GitHub integration
    # No action needed - Render watches main branch

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    # Auto-deploys via Vercel's GitHub integration
    # No action needed - Vercel watches main branch

  deploy-celery:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Fly.io
        uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        working-directory: ./backend
```

**Benefits:**

- Tests run before deployment
- Render + Vercel auto-deploy on test success
- Fly.io deploys via GitHub Actions
- Rollback if any stage fails

---

### Step 5: Environment Variables Summary

**Render (Backend):**

```bash
DATABASE_URL=postgresql+asyncpg://... (auto-filled by Render)
REDIS_URL=redis://... (from Render Redis add-on)
OPENAI_API_KEY=sk-...
SECRET_KEY=... (auto-generated by Render)
ENVIRONMENT=production
ALLOWED_ORIGINS=https://resumate-frontend.vercel.app
USE_CELERY=true
TESSERACT_PATH=/usr/bin/tesseract
ENABLE_OCR_FALLBACK=true
SENTRY_DSN=https://...
```

**Fly.io (Celery Worker):**

```bash
REDIS_URL=redis://... (same as Render)
DATABASE_URL=postgresql+asyncpg://... (Render's DB external URL)
OPENAI_API_KEY=sk-...
SECRET_KEY=...
ENVIRONMENT=production
USE_CELERY=true
```

**Vercel (Frontend):**

```bash
VITE_API_BASE_URL=https://resumate-backend.onrender.com/v1
VITE_WS_BASE_URL=wss://resumate-backend.onrender.com/ws
```

---

### Step 6: Domain Configuration (Optional)

**Custom Domains:**

**Render Backend:**

- Render dashboard → resumate-backend → Settings → Custom Domains
- Add `api.yourdomain.com`
- Update DNS (CNAME record)
- SSL auto-provisioned by Render

**Vercel Frontend:**

- Vercel dashboard → Settings → Domains
- Add `yourdomain.com`
- Update DNS (A record)
- SSL auto-provisioned by Vercel

**Cost:**

- Domain registration ~$10-15/year (Namecheap, Cloudflare, etc.)
- SSL certificates free (Let's Encrypt)

---

## Cost Summary (All Free Tiers)

| Service           | Platform             | Free Tier          | Monthly Cost   |
| ----------------- | -------------------- | ------------------ | -------------- |
| **Backend API**   | Render               | 750 hours          | $0             |
| **PostgreSQL**    | Render               | 1GB                | $0             |
| **Celery Worker** | Fly.io               | 3 VMs × 256MB      | $0             |
| **Redis**         | Render Add-on        | 25MB               | $0.20          |
| **Frontend**      | Vercel               | Unlimited projects | $0             |
| **Sentry**        | Sentry Developer     | 5K errors/month    | $0             |
| **Domain**        | Cloudflare/Namecheap | -                  | $10-15/year    |
| **TOTAL**         |                      |                    | **~$1-2/year** |

**Future Scaling Costs (if needed):**

- Render "Always On": $7/month (eliminates cold starts)
- Render PostgreSQL: $7/month (10GB storage)
- Fly.io larger VM: $5-15/month
- Total production-ready: ~$20-30/month

---

## Updated URL Format

**Development (Local):**

```bash
Backend:  http://localhost:8000
Frontend: http://localhost:3000
WebSocket: ws://localhost:8000/ws
```

**Production:**

```bash
Backend:  https://resumate-backend.onrender.com
Frontend: https://resumate-frontend.vercel.app
WebSocket: wss://resumate-backend.onrender.com/ws
```

**Custom Domain (Optional):**

```bash
Backend:  https://api.resumate.app
Frontend: https://resumate.app
WebSocket: wss://api.resumate.app/ws
```

---

## Migration from Railway to Render

**If you have existing Railway deployment:**

1. **Export data from Railway:**
   
   ```bash
   # Dump PostgreSQL database
   pg_dump $RAILWAY_DATABASE_URL > railway_backup.sql
   ```

2. **Import to Render:**
   
   ```bash
   # Connect to Render PostgreSQL
   psql $RENDER_DATABASE_URL < railway_backup.sql
   ```

3. **Update environment variables:**
   
   - Change `RAILWAY_*` URLs to `RENDER_*` equivalents
   - Update `ALLOWED_ORIGINS` to new domains

4. **DNS cutover:**
   
   - Update DNS records to point to Render
   - Wait for propagation (up to 48 hours)

---

## Advantages of Multi-Platform Approach

### ✅ **Benefits:**

1. **No Platform Lock-in** - Each service can be moved independently
2. **Maximize Free Tiers** - Use best free tier from each platform
3. **Best-in-Class Services** - Each platform excels at its specific task
4. **Cost Effective** - Only pay for what you need
5. **Easy Scaling** - Scale individual services as needed

### ⚠️ **Challenges:**

1. **Multiple Dashboards** - Manage services across 3 platforms
2. **Latency** - Cross-region communication (Render US ↔ Fly.io Singapore)
3. **Monitoring** - Need centralized logging (Sentry helps)
4. **DNS Management** - Need custom domain for unified experience

### 🔧 **Mitigation:**

1. **Use Custom Domain** - Single domain for all services
2. **Centralized Logging** - Sentry for errors, structured JSON logs
3. **Health Checks** - Monitor each service independently
4. **Documentation** - Keep clear record of service locations

---

## Quick Start Checklist

**Setup Accounts (All Free):**

- [ ] Render: https://render.com/register
- [ ] Fly.io: https://fly.io/app/signup
- [ ] Vercel: https://vercel.com/signup
- [ ] Sentry: https://sentry.io/signup/
- [ ] GitHub: https://github.com (connect repos)

**Deploy Backend (Render):**

- [ ] Push code to GitHub
- [ ] Create Render web service
- [ ] Connect PostgreSQL database
- [ ] Add environment variables
- [ ] Verify `/health` endpoint

**Deploy Celery Worker (Fly.io):**

- [ ] Install `flyctl` CLI
- [ ] Create `Dockerfile.celery`
- [ ] Run `fly launch`
- [ ] Configure `fly.toml`
- [ ] Run `fly deploy`

**Deploy Frontend (Vercel):**

- [ ] Connect GitHub repo to Vercel
- [ ] Add environment variables
- [ ] Auto-deploy on push

**Test Integration:**

- [ ] Upload resume via frontend
- [ ] Verify parsing completes
- [ ] Check Celery logs on Fly.io
- [ ] Check backend logs on Render
- [ ] Verify data saved in PostgreSQL

---

**Status:** ✅ Ready for implementation
**Updated:** 2026-02-21
**Next:** Update main plan document with platform changes
