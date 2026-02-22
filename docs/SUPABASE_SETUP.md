# Supabase Database Setup Guide

**Date:** 2026-02-22
**Purpose:** Setup free PostgreSQL database on Supabase for ResuMate backend

---

## 🎯 **Why Supabase?**

**Free Tier Benefits:**
- ✅ **500MB database storage** (sufficient for MVP)
- ✅ **2 databases** per project
- ✅ **50,000 Monthly Active Users** (MAU)
- ✅ **100 concurrent connections**
- ✅ **200MB daily bandwidth**
- ✅ **No credit card required**
- ✅ **Unlimited projects** (unlike Railway/Render)
- ✅ **No sleep policy** (always available)
- ✅ **Built-in authentication** (future feature)

**Source:** [Supabase Pricing](https://supabase.com/pricing)

---

## 📋 **Step-by-Step Setup Instructions**

### **Step 1: Create Supabase Account**

1. **Go to:** https://supabase.com
2. **Click:** "Start your project"
3. **Sign up with:** GitHub / Google / Microsoft (no credit card needed)
4. **Verify email address**

**Expected:** Free account created successfully

---

### **Step 2: Create New Project**

1. **Click:** "New Project"
2. **Project name:** `resumate-backend`
3. **Database Password:** Generate secure password (save it!)
4. **Region:** Choose region closest to users (e.g., Singapore for Dubai)
5. **Click:** "Create new project"

**Expected:** Project created in 30-60 seconds

---

### **Step 3: Get Database Connection Details**

1. **Navigate:** SQL Editor → Connection string
2. **Copy:** Connection pooling URI
3. **Format:** `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`

**Example:**
```
postgresql://postgres:your-password@db.abcdefghijklmn.supabase.co:5432/postgres
```

**Save this!** You'll need it for environment variables.

---

### **Step 4: Run Alembic Migrations on Supabase**

**Prerequisites:**
- Supabase project created
- Database connection string ready
- Backend code ready

**Process:**

1. **Set DATABASE_URL temporarily:**
```bash
# Use your Supabase connection string
export DATABASE_URL="postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
export DATABASE_URL_SYNC="postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
```

2. **Run migrations:**
```bash
cd /Users/nileshkumar/gh/resume-parser/backend
source .venv/bin/activate
alembic upgrade head
```

3. **Verify tables created:**
   - Go to Supabase Dashboard → Table Editor
   - You should see tables:
     - `alembic_version`
     - `resumes`
     - `parsed_resume_data`
     - `resume_corrections`
     - `resume_shares`

**Expected Output:**
```
✅ All migrations applied successfully
✅ 5 tables created in Supabase
```

---

### **Step 5: Test Database Connection Locally**

1. **Update your local `.env`:**
```bash
# Use Supabase connection for testing
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
DATABASE_URL_SYNC=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
USE_DATABASE=true
```

2. **Start backend:**
```bash
cd /Users/nileshkumar/gh/resume-parser/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. **Test health endpoint:**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## 🔐 **Security Best Practices**

### **1. Store Credentials Securely**

**NEVER commit your database password!** ✅

Use environment variables instead:
```bash
# ✅ GOOD - Use environment variables
DATABASE_URL="postgresql+asyncpg://postgres:[PASSWORD]@..."

# ❌ BAD - Never hardcode in code
DATABASE_URL="postgresql+asyncpg://postgres:my-password-123@..."
```

### **2. Database URL Format for Vercel**

For Vercel deployment, you'll add the database as a **Vercel Environment Variable**:

**Vercel Dashboard → resumate-backend → Settings → Environment Variables:**

```
DATABASE_URL: postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
```

**Vercel will automatically inject this into your serverless function at runtime.**

---

## 📊 **Database Management**

### **View Data in Supabase Dashboard:**

1. **Table Editor:** View and edit data directly
2. **SQL Editor:** Run raw SQL queries
3. **Database Settings:** Connection pooling, SSL mode

### **Monitor Usage:**

- Free tier limits: 500MB storage, 200MB/day bandwidth
- Monitor at: Supabase Dashboard → Project Settings → Usage

---

## 🚨 **Troubleshooting**

### **Issue: Migration Fails**

**Solution:**
1. Check DATABASE_URL is correct (asyncpg vs postgresql)
2. Verify password is correct
3. Check Supabase database is active

### **Issue: Connection Timeout**

**Solution:**
1. Check Supabase project status (not paused)
2. Verify your IP is not blocked
3. Check firewall settings

### **Issue: "database does not exist"**

**Solution:**
1. Verify project name is correct
2. Check database name is `postgres` (default in Supabase)
3. Wait 1-2 minutes for project to fully initialize

---

## 🎯 **Next Steps After Setup**

Once Supabase is configured:

1. ✅ Add DATABASE_URL to Vercel environment variables
2. ✅ Deploy backend to Vercel
3. ✅ Test production API endpoints
4. ✅ Verify database connectivity in production

---

## 📚 **Additional Resources**

**Supabase Documentation:**
- [Getting Started](https://supabase.com/docs/guides/getting-started)
- [Database Management](https://supabase.com/docs/guides/database)
- [Connection Strings](https://supabase.com/docs/guides/database/connecting-to-postgres)

**Vercel Documentation:**
- [Environment Variables](https://vercel.com/docs/projects/environment-variables)
- [PostgreSQL on Vercel](https://vercel.com/docs/storage/postgres)

---

## ✅ **Completion Checklist**

- [ ] Supabase account created
- [ ] Project "resumate-backend" created
- [ ] Database connection string saved
- [ ] Alembic migrations run successfully
- [ ] Tables verified in Supabase Dashboard
- [ ] Health check returns "database: connected"
- [ ] Ready for Vercel deployment

---

**Status:** ⏳ **READY TO EXECUTE**

**Created:** 2026-02-22
**Platform:** Supabase (PostgreSQL hosting)
**Cost:** $0/month (free tier)

**Next:** Proceed to Vercel Backend Deployment
