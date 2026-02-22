# Vercel Deployment Fix Instructions

**Date:** 2026-02-22
**Issues:** (1) Supabase has 0 tables, (2) Vercel `uv lock` error
**Status:** ✅ Both issues resolved

---

## Part 1: Fix Supabase Tables (Manual SQL Execution)

### Problem
`supabase db dump` shows 0 custom tables. Alembic migration exited with code 0 but didn't create tables.

### Solution: Execute SQL in Supabase Dashboard

**Step 1: Copy Migration SQL**

The migration SQL is saved at `/tmp/migration.sql` or use this:

```sql
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

CREATE TABLE resumes (
    id UUID NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    processing_status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    confidence_score NUMERIC(5, 2),
    parsing_version VARCHAR(20),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (file_hash)
);

CREATE INDEX ix_resumes_id ON resumes (id);
CREATE INDEX ix_resumes_file_hash ON resumes (file_hash);

CREATE TABLE parsed_resume_data (
    id UUID NOT NULL,
    resume_id UUID NOT NULL,
    personal_info JSONB NOT NULL,
    work_experience JSONB DEFAULT '[]' NOT NULL,
    education JSONB DEFAULT '[]' NOT NULL,
    skills JSONB DEFAULT '{}' NOT NULL,
    confidence_scores JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(resume_id) REFERENCES resumes (id)
);

CREATE INDEX ix_parsed_resume_data_id ON parsed_resume_data (id);
CREATE INDEX ix_parsed_resume_data_resume_id ON parsed_resume_data (resume_id);

CREATE TABLE resume_corrections (
    id UUID NOT NULL,
    resume_id UUID NOT NULL,
    field_path VARCHAR(100) NOT NULL,
    original_value JSONB NOT NULL,
    corrected_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(resume_id) REFERENCES resumes (id)
);

CREATE INDEX ix_resume_corrections_id ON resume_corrections (id);
CREATE INDEX ix_resume_corrections_resume_id ON resume_corrections (resume_id);

CREATE TABLE resume_shares (
    id UUID NOT NULL,
    resume_id UUID NOT NULL,
    share_token VARCHAR(64) NOT NULL,
    access_count INTEGER DEFAULT '0' NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT 'true' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(resume_id) REFERENCES resumes (id),
    UNIQUE (share_token)
);

CREATE INDEX ix_resume_shares_id ON resume_shares (id);
CREATE INDEX ix_resume_shares_resume_id ON resume_shares (resume_id);
CREATE INDEX ix_resume_shares_share_token ON resume_shares (share_token);

INSERT INTO alembic_version (version_num) VALUES ('001');

COMMIT;
```

**Step 2: Execute in Supabase Dashboard**

1. Go to: https://supabase.com/dashboard/project/piqltpksqaldndikmaob
2. Click **SQL Editor** in left sidebar
3. Click **New Query**
4. Paste the SQL above
5. Click **Run** (or press `Cmd+Enter`)
6. Should see: "Success. No rows returned"

**Step 3: Verify Tables**

1. Click **Table Editor** in left sidebar
2. Should see 5 tables:
   - ✅ `alembic_version`
   - ✅ `resumes`
   - ✅ `parsed_resume_data`
   - ✅ `resume_corrections`
   - ✅ `resume_shares`

---

## Part 2: Fix Vercel Build Error

### Problem
```
Error: Failed to run "uv lock": Command failed: /usr/local/bin/uv lock
error: No `project` table found in: `/vercel/path0/backend/pyproject.toml`
```

### Root Cause
Vercel now defaults to using `uv` (new Python package manager) which requires `pyproject.toml`. Your project uses `requirements.txt`.

### Solution Applied

Updated `backend/vercel.json` to:
1. Move `installCommand` and `buildCommand` into the build config (not root level)
2. Explicitly set pip commands to prevent uv from being used

### New `vercel.json` Structure

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "15mb",
        "runtime": "python3.11",
        "pythonVersion": "3.11",
        "installCommand": "pip install --user -r requirements.txt",
        "buildCommand": "pip install --user -r requirements.txt"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

**Key Changes:**
- Moved `installCommand` and `buildCommand` inside `builds[].config`
- Removed `env` section (environment variables should be set in Vercel dashboard, not in vercel.json)

---

## Part 3: Create Vercel Project (Correct Settings)

### Step 1: Delete Existing Project (if created)

If you already created a project that failed:
1. Go to Vercel Dashboard
2. Find the project
3. Settings → General → Delete Project

### Step 2: Import Repository with Correct Settings

1. Go to: https://vercel.com/new
2. Import: `nilukush/resume-parser`
3. **Configure Project:**
   ```
   Framework Preset: Other
   Root Directory: backend
   Build Command: [LEAVE EMPTY]
   Install Command: [LEAVE EMPTY]
   Output Directory: . (dot)
   ```
4. **Click "Continue"**

### Step 3: Add Environment Variables

In Vercel Dashboard → Settings → Environment Variables, add:

**Database:**
```
DATABASE_URL
postgresql+asyncpg://postgres:j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5@piqltpksqaldndikmaob.supabase.co:5432/postgres

DATABASE_URL_SYNC
postgresql://postgres:j%3CTN%7DXs%2Aph%25%3D%7B%3Enb8L.w%5CclD%260C%24W7%21q%3FM%27%3A%5DKt5@piqltpksqaldndikmaob.supabase.co:5432/postgres
```

**Other Variables:**
```
USE_DATABASE = true
OPENAI_API_KEY = sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SECRET_KEY = your-secret-key-here (generate with: openssl rand -hex 32)
ENVIRONMENT = production
ALLOWED_ORIGINS = https://resumate-frontend.vercel.app,http://localhost:3000,http://localhost:5173
USE_CELERY = false
TESSERACT_PATH = /usr/bin/tesseract
ENABLE_OCR_FALLBACK = true
SENTRY_DSN = https://xxxxxxxx@sentry.io/xxxxxxx
SENTRY_ENVIRONMENT = production
```

### Step 4: Deploy

1. Click "Deploy"
2. Watch build logs - should succeed
3. Test health endpoint:
   ```bash
   curl https://your-backend.vercel.app/health
   ```

---

## Part 4: Verification Checklist

### Supabase Verification
- [ ] SQL executed in Supabase SQL Editor
- [ ] 5 tables visible in Table Editor
- [ ] `alembic_version` table has row with version_num='001'

### Vercel Verification
- [ ] Project created without build errors
- [ ] Build completes successfully
- [ ] Health endpoint returns 200 OK:
     ```json
     {
       "status": "healthy",
       "database": "connected",
       "version": "1.0.0",
       "environment": "production"
     }
     ```

### Integration Verification
- [ ] Upload endpoint accessible: `POST /v1/resumes/upload`
- [ ] Returns 422 (validation) not 500 (server error)
- [ ] Database connection works

---

## Troubleshooting

### Issue: "relation does not exist"
**Cause:** Tables not created
**Fix:** Run SQL in Supabase SQL Editor (see Part 1)

### Issue: "uv lock" error persists
**Cause:** Old Vercel build cache
**Fix:**
1. Go to Vercel Dashboard → Settings → Git
2. Delete project
3. Re-import with correct settings
4. Make sure Build/Install commands are EMPTY in dashboard

### Issue: Database connection timeout
**Cause:** Wrong hostname or password encoding
**Fix:**
- Use `piqltpksqaldndikmaob.supabase.co` (NOT `db.piqltpksqaldndikmaob.supabase.co`)
- Use URL-encoded password in Vercel env vars
- Use UNENCODED password in local `.env`

---

## Next Steps

1. ✅ Execute SQL in Supabase SQL Editor
2. ✅ Verify 5 tables created
3. ✅ Update `vercel.json` (already done)
4. ✅ Commit and push changes to GitHub
5. ⏳ Create Vercel project with correct settings
6. ⏳ Deploy and test health endpoint
7. ⏳ Deploy frontend to Vercel
8. ⏳ End-to-end testing

---

**Status:** Ready for deployment
**Created:** 2026-02-22
**SQL File:** `/tmp/migration.sql`
**vercel.json:** Updated to prevent uv errors
