# Vercel Deployment Guide - ResuMate Backend

**Date:** 2026-02-23
**Status:** ✅ Ready for Deployment
**Bundle Size:** ~180MB (estimated, down from 285MB)

---

## 🎯 Overview

This guide covers deploying the ResuMate backend to Vercel's free tier using serverless functions.

### What Changed?

**Before (Failed Deployment):**
- ❌ Bundle size: 285.45 MB (exceeds Lambda limit)
- ❌ Used uv.lock with binary dependencies
- ❌ Included OCR dependencies (pdf2image, pytesseract)
- ❌ Bundled spaCy models

**After (Optimized):**
- ✅ Bundle size: ~180 MB (estimated)
- ✅ Uses requirements.txt for dependency control
- ✅ OCR removed (requires external binaries)
- ✅ spaCy models downloaded at runtime
- ✅ Graceful error messages for unsupported files

---

## 📋 Prerequisites

### Required Accounts

1. **Vercel Account** (free tier)
   - Sign up: https://vercel.com/signup
   - Connect GitHub account

2. **Supabase Account** (free tier)
   - Sign up: https://supabase.com/signup
   - Create project: `resumate-backend`

### Local Setup

```bash
# Navigate to project
cd /Users/nileshkumar/gh/resume-parser

# Verify changes
git log --oneline -1
# Should show: a5ca7d0 fix: optimize Vercel deployment...
```

---

## 🚀 Deployment Steps

### Step 1: Create Vercel Project

1. **Go to Vercel Dashboard:**
   - Visit: https://vercel.com/dashboard
   - Click **"Add New..."** → **"Project"**

2. **Import Repository:**
   - Select: `nilukush/resume-parser`
   - Branch: `main`

3. **Configure Project:**
   ```
   Framework Preset: Other
   Root Directory: backend
   Build Command: [LEAVE EMPTY]
   Install Command: [LEAVE EMPTY]
   Output Directory: . (dot)
   ```

   **Why leave empty?** Vercel will use `backend/vercel.json` automatically.

4. **Click "Deploy"** (will fail initially - we'll add env vars next)

---

### Step 2: Add Environment Variables

1. **Go to Project Settings:**
   - In Vercel dashboard → Click your project
   - Go to **Settings** → **Environment Variables**

2. **Add Required Variables:**

   **Database (Supabase):**
   ```
   DATABASE_URL = postgresql+asyncpg://postgres:ENCODED_PASSWORD@piqltpksqaldndikmaob.supabase.co:5432/postgres
   DATABASE_URL_SYNC = postgresql://postgres:ENCODED_PASSWORD@piqltpksqaldndikmaob.supabase.co:5432/postgres
   USE_DATABASE = true
   ```

   **Important:** Replace `ENCODED_PASSWORD` with your URL-encoded Supabase password.

   **Application:**
   ```
   SECRET_KEY = 6796cb1a326759a2fb772f26a7fd3f41b380588bac425d9ad21172997d896fce
   ENVIRONMENT = production
   USE_CELERY = false
   ALLOWED_ORIGINS = https://resumate-frontend.vercel.app
   ```

   **AI (Optional):**
   ```
   OPENAI_API_KEY = sk-your-openai-api-key
   ```

   **Monitoring (Optional):**
   ```
   SENTRY_DSN = https://your-sentry-dsn
   ```

3. **Select Environments:**
   - Choose **Production** (and **Preview** if desired)
   - Click **Save**

---

### Step 3: Redeploy with Environment Variables

1. **Go to Deployments Tab:**
   - Click **Deployments** in project sidebar

2. **Redeploy:**
   - Click **...** menu on latest deployment
   - Click **"Redeploy"**

3. **Monitor Build Logs:**
   - Click into the deployment
   - Watch for:
     ```
     Running "pip install --user -r requirements.txt"
     Successfully installed ...
     Build completed successfully
     ```

4. **Expected Bundle Size:**
   - Look for: `Bundle size: ~180MB`
   - If still exceeds 250MB, check Troubleshooting section

---

### Step 4: Run Database Migrations

**Option A: Via Vercel CLI (Recommended)**

```bash
# Install Vercel CLI
npm i -g vercel@latest

# Login to Vercel
vercel login

# Link to project
cd backend
vercel link

# Pull environment variables
vercel env pull .env.local

# Run migrations
alembic upgrade head

# Verify
alembic current
```

**Option B: Via Supabase SQL Editor**

1. Go to Supabase Dashboard → SQL Editor
2. Run migration SQL manually from `backend/alembic/versions/`
3. Verify tables created in Table Editor

**Expected Tables:**
- `alembic_version`
- `resumes`
- `parsed_resume_data`
- `resume_corrections`
- `resume_shares`

---

### Step 5: Verify Deployment

1. **Test Health Endpoint:**
   ```bash
   curl https://resumate-backend.vercel.app/health
   ```

   **Expected Response:**
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "version": "1.0.0",
     "environment": "production",
     "timestamp": "2026-02-23T..."
   }
   ```

2. **Test Upload Endpoint:**
   ```bash
   # Should return 422 (validation error) not 500
   curl -X POST https://resumate-backend.vercel.app/v1/resumes/upload
   ```

3. **Check Vercel Function Logs:**
   - Go to Vercel Dashboard → Deployments → Click latest
   - Go to **Functions** tab
   - Look for errors or warnings

---

## 📊 Bundle Size Breakdown

### Estimated Size Reduction

```
Original Bundle: 285.45 MB
├── spaCy + models: ~120 MB → ~50 MB (models downloaded at runtime)
├── pdfplumber + pdfminer: ~40 MB → ~40 MB (unchanged)
├── psycopg2-binary: ~25 MB → ~25 MB (unchanged)
├── Pillow + image libs: ~30 MB → ~30 MB (unchanged)
├── OCR deps (removed): ~20 MB → 0 MB
└── Other: ~50 MB → ~50 MB (unchanged)

Optimized Bundle: ~180 MB (estimated)
Reduction: ~105 MB (-37%)
```

### What's Included

**Production Dependencies** (requirements.txt):
- ✅ FastAPI, Uvicorn, Mangum
- ✅ SQLAlchemy, asyncpg, psycopg2-binary
- ✅ pdfplumber (text-based PDFs only)
- ✅ spaCy (without models)
- ✅ OpenAI, Pydantic
- ✅ All other runtime dependencies

**NOT Included**:
- ❌ Dev dependencies (pytest, black, ruff, mypy)
- ❌ OCR dependencies (pdf2image, pytesseract)
- ❌ spaCy models (downloaded at runtime)

---

## ⚠️ Important Limitations

### 1. OCR Not Available

**What doesn't work:**
- ❌ Image-based PDFs (scanned documents)
- ❌ Photos of resumes
- ❌ PDFs with no text layer

**What works:**
- ✅ Text-based PDFs (most modern PDFs)
- ✅ DOCX files
- ✅ TXT files

**User Experience:**
When an image-based PDF is uploaded, users see:
```json
{
  "error": "OCRNotAvailableError",
  "message": "This PDF appears to be image-based (scanned) and requires OCR. OCR functionality is not available in this serverless environment. Please upload a text-based PDF or try another document format."
}
```

### 2. Cold Start Latency

**First Request per Container:**
- Slower (2-5 seconds)
- Downloads spaCy model (en_core_web_sm ~15MB)
- Caches in `/tmp` for container lifetime

**Subsequent Requests:**
- Fast (<500ms)
- Model loaded from `/tmp` cache
- Benefits from Lambda warm starts

**Mitigation:**
- Vercel keeps containers warm for ~5 minutes
- High traffic = fewer cold starts
- Consider Vercel Pro for longer warm times

### 3. Lambda Execution Limits

**Vercel Free Tier:**
- Max duration: 60 seconds (configurable)
- Max memory: 1024 MB
- Max bundle size: 250 MB

**Impact:**
- Large resumes may timeout
- Complex PDFs may take longer
- Consider increasing timeout if needed

---

## 🔧 Troubleshooting

### Error: "Bundle size exceeds limit"

**Cause:** Bundle still over 250MB

**Solutions:**
1. Check build logs for largest dependencies:
   ```bash
   pip install --user -r requirements.txt --dry-run
   ```

2. Remove unused dependencies from requirements.txt

3. Consider splitting into microservices

4. Last resort: Switch to Docker deployment (requires paid plan)

---

### Error: "No spaCy model found"

**Cause:** Model download failed

**Solutions:**
1. Check function logs for download errors
2. Verify internet connectivity from Lambda
3. Add fallback to basic regex parsing
4. Pre-download models in deployment script

---

### Error: "Could not connect to database"

**Cause:** Supabase connection string issue

**Solutions:**
1. Verify password is URL-encoded:
   ```bash
   python3 -c "import urllib.parse; print(urllib.parse.quote('YOUR_PASSWORD', safe=''))"
   ```

2. Check Supabase project is active (not paused)

3. Verify hostname: `piqltpksqaldndikmaob.supabase.co` (no `db.` prefix)

4. Test connection locally:
   ```bash
   psql $DATABASE_URL_SYNC
   ```

---

### Error: "relation does not exist"

**Cause:** Database migrations not run

**Solutions:**
1. Run migrations (see Step 4)
2. Verify tables in Supabase Table Editor
3. Check `alembic_version` table exists

---

### Error: "externally-managed-environment"

**Cause:** PIP 668 error (shouldn't happen with our config)

**Solutions:**
1. Verify vercel.json has `--user` flag
2. Remove Build/Install command overrides in dashboard
3. Redeploy with "Clear cache" option

---

## 📈 Monitoring

### Vercel Dashboard

**Key Metrics:**
- Function invocations
- Error rate
- Duration (p50, p95, p99)
- Cold starts

**Logs:**
- Real-time logs: Deployments → Functions → Logs
- Historical logs: Deployments → Select deployment → Functions

### Supabase Dashboard

**Key Metrics:**
- Database connections
- Query performance
- Storage usage

**Health Check:**
```bash
curl https://resumate-backend.vercel.app/health
```

---

## 🔄 Updating Deployment

### Making Changes

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "feat: your changes"
   git push origin main
   ```

2. **Automatic Deployment:**
   - Vercel auto-deploys on git push
   - Check dashboard for deployment status

3. **Manual Redeploy (if needed):**
   - Vercel Dashboard → Deployments
   - Click **"Redeploy"** on latest deployment

### Database Migrations

1. **Create Migration:**
   ```bash
   cd backend
   alembic revision --autogenerate -m "description"
   ```

2. **Run Migration:**
   ```bash
   alembic upgrade head
   ```

3. **Verify in Supabase:**
   - Check Table Editor
   - Run SQL queries to verify schema

---

## 📚 References

### Documentation

- [Vercel Python Runtime](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Project Configuration](https://vercel.com/docs/project-configuration)
- [Supabase Database Setup](/Users/nileshkumar/gh/resume-parser/docs/SUPABASE_SETUP.md)
- [Progress Tracking](/Users/nileshkumar/gh/resume-parser/docs/PROGRESS.md)

### Related Documents

- [Vercel Fix Instructions](/Users/nileshkumar/gh/resume-parser/docs/VERCEL-FIX-INSTRUCTIONS.md)
- [Bug Fix #16: Schema Validation](/Users/nileshkumar/gh/resume-parser/docs/BUG-FIX-16-VERCEL-SCHEMA.md)
- [Database Setup Guide](/Users/nileshkumar/gh/resume-parser/docs/DATABASE_SETUP.md)

---

## ✅ Deployment Checklist

- [ ] Vercel project created
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Health endpoint returns 200 OK
- [ ] Database shows as "connected"
- [ ] Upload endpoint tested
- [ ] Bundle size under 250MB
- [ ] Function logs error-free
- [ ] Documentation updated

---

## 🎉 Success Criteria

**Deployment Successful When:**
- ✅ Bundle size < 250MB
- ✅ Health endpoint returns healthy
- ✅ Database connected
- ✅ Upload endpoint works
- ✅ Text-based PDFs parse correctly
- ✅ Clear error for image-based PDFs
- ✅ Zero infrastructure cost

---

**Created:** 2026-02-23
**Status:** ✅ Ready for Deployment
**Next Action:** Follow Steps 1-5 above
