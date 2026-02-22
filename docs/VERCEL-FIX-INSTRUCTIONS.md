# Vercel Deployment Fix - Complete Instructions

**Date:** 2026-02-22
**Purpose:** Fix Vercel build errors and database connection issues
**Status:** Ready to execute

---

## 🎯 Problem Summary

### Issue 1: Build Error - Externally Managed Environment
```
error: externally-managed-environment
× This environment is externally managed
╰─> This Python installation is managed by uv and should not be modified.
```

**Root Cause:** Vercel's build environment implements PEP 668, which prevents `pip install` from modifying the system Python environment.

**Solution:** Use `pip install --user` flag to install to user directory instead.

### Issue 2: Special Characters in Database Password
```
zsh: event not found: q?M'
```

**Root Cause:** Your Supabase password contains special shell characters (`?`, `'`, `}`, `{`, etc.)

**Solution:** URL-encode the password for use in connection strings.

---

## ✅ SOLUTION APPLIED

### 1. Fixed `backend/vercel.json`

Updated the build configuration to use `--user` flag:

```json
{
  "installCommand": "pip install --user -r requirements.txt",
  "buildCommand": "pip install --user -r requirements.txt"
}
```

### 2. Generated URL-Encoded Connection Strings

**Raw Password (DO NOT USE):**
```
j<TN}Xs*ph%={>nb8L.w\clD&0C$W7!q?M':]Kt5
```

**Encoded Password (Safe for Connection Strings):**
```
j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5
```

---

## 📋 STEP-BY-STEP DEPLOYMENT INSTRUCTIONS

### Step 1: Update Vercel Environment Variables

1. **Go to your Vercel project dashboard:**
   - Visit: https://vercel.com/nilukushs-projects
   - Find your backend project (likely named "resume-parser" or similar)
   - Click on the project
   - Go to **Settings** → **Environment Variables**

2. **Delete existing DATABASE_URL and DATABASE_URL_SYNC variables** (if they exist)

3. **Add new environment variables** with these exact values:

   **DATABASE_URL:**
   ```
   postgresql+asyncpg://postgres:j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5@db.piqltpksqaldndikmaob.supabase.co:5432/postgres
   ```

   **DATABASE_URL_SYNC:**
   ```
   postgresql://postgres:j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5@db.piqltpksqaldndikmaob.supabase.co:5432/postgres
   ```

4. **Verify other environment variables are set:**
   - `OPENAI_API_KEY` = `[Your OpenAI API key from Vercel dashboard]`
   - `SECRET_KEY` = `6796cb1a326759a2fb772f26a7fd3f41b380588bac425d9ad21172997d896fce`
   - `SENTRY_DSN` = `https://6fa87eafe68b535a6c05ff1e91494bb8@o4510928853860352.ingest.de.sentry.io/4510928858841168`
   - `USE_DATABASE` = `true`
   - `USE_CELERY` = `false`
   - `ENVIRONMENT` = `production`
   - `ALLOWED_ORIGINS` = `https://resumate-frontend.vercel.app`

5. **Select environment:**
   - Choose **Production** (and Preview if you want it for all deployments)
   - Click **Save**

### Step 2: Remove Conflicting Build Settings

1. In your Vercel project dashboard, go to **Settings** → **Git**
2. **Remove** any override for **Build Command** if set
3. **Remove** any override for **Install Command** if set
4. **Remove** any override for **Output Directory** if set

The `vercel.json` file now controls all these settings.

### Step 3: Commit and Push Changes

The updated `backend/vercel.json` needs to be pushed to GitHub:

```bash
cd /Users/nileshkumar/gh/resume-parser

# Check git status
git status

# Add the updated vercel.json
git add backend/vercel.json
git add backend/scripts/encode_password.py

# Commit with descriptive message
git commit -m "fix: resolve Vercel build error with PEP 668 and URL-encoded database password

- Update vercel.json to use --user flag for pip install
- Add password encoding script for safe connection strings
- URL-encode Supabase password for environment variables

Resolves:
- externally-managed-environment error
- Shell interpretation errors with special characters in password"

# Push to GitHub
git push origin main
```

### Step 4: Redeploy on Vercel

**Option A: Automatic Redeploy (Recommended)**
- After pushing to GitHub, Vercel will automatically detect the changes
- Go to your Vercel project dashboard
- Click on **Deployments** tab
- Wait for automatic deployment to trigger
- Click into the deployment to watch real-time logs

**Option B: Manual Redeploy**
- Go to your Vercel project dashboard
- Click on **Deployments** tab
- Click the **...** menu on the latest deployment
- Click **Redeploy**

### Step 5: Monitor Build Logs

1. Watch the build logs in real-time:
   - Look for: `Running "pip install --user -r requirements.txt"`
   - Should see: `Successfully installed ...`
   - Build should complete without errors

2. If you still see errors:
   - Copy the error message
   - Check the Troubleshooting section below

### Step 6: Run Database Migrations

Once the deployment succeeds, you need to create the database tables:

**Option A: Using Vercel CLI (Recommended)**

```bash
# Install Vercel CLI if not already installed
npm i -g vercel@latest

# Login to Vercel
vercel login

# Link to your project
cd backend
vercel link

# Set environment variables locally from Vercel
vercel env pull .env.local

# Run migrations
alembic upgrade head
```

**Option B: Temporary Remote Execution**

1. Go to Supabase Dashboard → SQL Editor
2. Run this query to verify connection works:
   ```sql
   SELECT current_database(), current_user, version();
   ```
3. Copy your migration files from `backend/alembic/versions/`
4. Run each migration SQL manually in Supabase SQL Editor
5. Check tables created in Supabase → Table Editor

**Option C: Create Migration Script**

```bash
# Create a script to run migrations against Supabase
cd backend

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5@db.piqltpksqaldndikmaob.supabase.co:5432/postgres"
export DATABASE_URL_SYNC="postgresql://postgres:j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5@db.piqltpksqaldndikmaob.supabase.co:5432/postgres"

# Run migrations
alembic upgrade head

# Verify
alembic current
alembic history
```

### Step 7: Verify Deployment

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
     "timestamp": "2026-02-22T..."
   }
   ```

2. **Check Supabase Tables:**
   - Go to Supabase Dashboard → Table Editor
   - Verify tables exist: `resumes`, `shares`, `alembic_version`

3. **Test API Endpoint:**
   ```bash
   # Test upload endpoint (should return structured error without file)
   curl -X POST https://resumate-backend.vercel.app/v1/resumes/upload
   ```

---

## 🔧 Troubleshooting

### Error: "externally-managed-environment" persists

**Cause:** Old build cache or incorrect build settings

**Solution:**
1. Go to Vercel Dashboard → Settings → Git
2. Remove all Build Command overrides
3. Remove all Install Command overrides
4. Redeploy with "Clear cache" option
5. Verify `vercel.json` is being used

### Error: "Could not connect to database"

**Cause:** URL encoding issue or wrong connection string

**Solution:**
1. Verify connection string format:
   ```
   postgresql+asyncpg://postgres:ENCODED_PASSWORD@db.piqltpksqaldndikmaob.supabase.co:5432/postgres
   ```
2. Check Supabase project is active (not paused)
3. Verify password encoding: run `python3 scripts/encode_password.py` again
4. Check Supabase Dashboard → Settings → Database → Connection info

### Error: "relation does not exist"

**Cause:** Database migrations haven't been run

**Solution:**
1. Run Alembic migrations (see Step 6)
2. Verify in Supabase Table Editor
3. Check `alembic_version` table exists

### Error: Build timeout

**Cause:** Dependencies taking too long to install

**Solution:**
1. Check `requirements.txt` for unnecessary packages
2. Consider removing dev dependencies from production build
3. Increase Vercel function timeout (upgrade plan needed)

---

## 📊 Connection String Reference

### For Local Development (`.env` file)

Create a `.env` file in `backend/` directory:

```bash
# Database (Supabase - Production)
DATABASE_URL=postgresql+asyncpg://postgres:j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5@db.piqltpksqaldndikmaob.supabase.co:5432/postgres
DATABASE_URL_SYNC=postgresql://postgres:j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5@db.piqltpksqaldndikmaob.supabase.co:5432/postgres
USE_DATABASE=true

# AI Services
OPENAI_API_KEY=[Your OpenAI API key from Vercel dashboard]

# Security
SECRET_KEY=6796cb1a326759a2fb772f26a7fd3f41b380588bac425d9ad21172997d896fce

# Application
ENVIRONMENT=production
ALLOWED_ORIGINS=https://resumate-frontend.vercel.app,http://localhost:3000
USE_CELERY=false

# OCR
TESSERACT_PATH=/usr/local/bin/tesseract
ENABLE_OCR_FALLBACK=true

# Monitoring
SENTRY_DSN=https://6fa87eafe68b535a6c05ff1e91494bb8@o4510928853860352.ingest.de.sentry.io/4510928858841168
SENTRY_ENVIRONMENT=production
```

### For Vercel Environment Variables

Use the same values in Vercel dashboard (Settings → Environment Variables):

| Variable Name | Value |
|---------------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5@db.piqltpksqaldndikmaob.supabase.co:5432/postgres` |
| `DATABASE_URL_SYNC` | `postgresql://postgres:j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5@db.piqltpksqaldndikmaob.supabase.co:5432/postgres` |
| `OPENAI_API_KEY` | (your OpenAI key) |
| `SECRET_KEY` | `6796cb1a326759a2fb772f26a7fd3f41b380588bac425d9ad21172997d896fce` |
| `SENTRY_DSN` | `https://6fa87eafe68b535a6c05ff1e91494bb8@o4510928853860352.ingest.de.sentry.io/4510928858841168` |
| `USE_DATABASE` | `true` |
| `USE_CELERY` | `false` |
| `ENVIRONMENT` | `production` |
| `ALLOWED_ORIGINS` | `https://resumate-frontend.vercel.app` |
| `TESSERACT_PATH` | `/usr/bin/tesseract` |
| `ENABLE_OCR_FALLBACK` | `true` |

---

## 🎯 Success Checklist

- [ ] `vercel.json` updated with `--user` flag
- [ ] Connection strings URL-encoded
- [ ] Vercel environment variables updated
- [ ] Conflicting build settings removed
- [ ] Code pushed to GitHub
- [ ] Vercel deployment successful
- [ ] Database migrations run
- [ ] Health endpoint returns 200 OK
- [ ] Database shows as "connected"
- [ ] Tables created in Supabase
- [ ] Full application tested

---

## 📚 Additional Resources

**Vercel Python Documentation:**
- [Python Runtime](https://vercel.com/docs/functions/runtimes/python)
- [Environment Variables](https://vercel.com/docs/projects/environment-variables)
- [Configuration](https://vercel.com/docs/projects/project-configuration)

**Supabase Documentation:**
- [Connection Strings](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Migrations](https://supabase.com/docs/guides/database/migrations)

**PEP 668 Information:**
- [Externally Managed Environments](https://peps.python.org/pep-0668/)
- [Pip Install Solutions](https://www.cnblogs.com/JosiahBristow/articles/18695807)

**URL Encoding Reference:**
- [SQLAlchemy URL Encoding](https://m.blog.csdn.net/yutu75/article/details/144825776)
- [Supabase Password Issue](https://github.com/supabase/supabase/issues/21933)

---

**Created:** 2026-02-22
**Status:** ✅ Ready for deployment
**Next Action:** Follow Step 1-7 above
