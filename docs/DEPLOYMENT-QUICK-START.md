# Quick Start: Deploy to Vercel

**⏱️ Estimated Time:** 15 minutes
**💰 Cost:** $0/month (free tier)

---

## Prerequisites

- ✅ GitHub account with `nilukush/resume-parser` access
- ✅ Vercel account (free tier)
- ✅ Supabase account (free tier)

---

## Step 1: Create Vercel Project (2 min)

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Import `nilukush/resume-parser`
4. Configure:
   - **Framework Preset:** Other
   - **Root Directory:** backend
   - **Build Command:** [LEAVE EMPTY]
   - **Install Command:** [LEAVE EMPTY]
   - **Output Directory:** . (dot)
5. Click **"Deploy"** (will fail - env vars needed)

---

## Step 2: Add Environment Variables (5 min)

Go to **Settings** → **Environment Variables** and add:

```
DATABASE_URL = postgresql+asyncpg://postgres:ENCODED_PASSWORD@piqltpksqaldndikmaob.supabase.co:5432/postgres
DATABASE_URL_SYNC = postgresql://postgres:ENCODED_PASSWORD@piqltpksqaldndikmaob.supabase.co:5432/postgres
USE_DATABASE = true
SECRET_KEY = 6796cb1a326759a2fb772f26a7fd3f41b380588bac425d9ad21172997d896fce
ENVIRONMENT = production
USE_CELERY = false
ALLOWED_ORIGINS = https://resumate-frontend.vercel.app
```

**Important:** Replace `ENCODED_PASSWORD` with your URL-encoded Supabase password.

---

## Step 3: Redeploy (1 min)

1. Go to **Deployments** tab
2. Click **"..."** on latest deployment
3. Click **"Redeploy"**
4. Wait for build to complete (~3 min)

---

## Step 4: Run Migrations (5 min)

```bash
# Install Vercel CLI
npm i -g vercel@latest

# Login
vercel login

# Link project
cd backend
vercel link

# Pull env vars
vercel env pull .env.local

# Run migrations
alembic upgrade head
```

---

## Step 5: Verify (2 min)

```bash
# Test health endpoint
curl https://resumate-backend.vercel.app/health
```

**Expected:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "environment": "production"
}
```

---

## ✅ Success!

Your backend is now deployed!

**Next Steps:**
- Deploy frontend (similar process)
- Test full application
- Monitor in Vercel dashboard

---

**Need Help?** See [VERCEL-DEPLOYMENT-GUIDE.md](./VERCEL-DEPLOYMENT-GUIDE.md) for detailed instructions.
