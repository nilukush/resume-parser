# Database Setup Guide for ResuMate

**Date:** 2026-02-21
**Purpose:** Local development database setup

---

## Quick Start

### 1. Start Database Services

```bash
# From project root
docker compose up -d

# Verify services are running
docker compose ps
```

Expected output:
```
NAME                  STATUS          PORTS
resumate-postgres    Up              0.0.0.0:5433->5432
resumate-redis       Up              0.0.0.0:6379->6379
```

**⚠️ Important:** PostgreSQL uses port **5433** (not 5432) to avoid conflicts with any native PostgreSQL instances on macOS.

### 2. Initialize Database

```bash
# From project root
cd backend
./scripts/init_database.sh
```

This will:
- Auto-detect Docker Compose V2 or V1
- Start services if not running
- Wait for PostgreSQL to be ready
- Run Alembic migrations to create tables
- Verify database is ready

### 3. Stop Database Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

---

## Database Connection Information

**Development (Local):**

```bash
# Async (for application)
DATABASE_URL=postgresql+asyncpg://resumate_user:resumate_password@localhost:5433/resumate

# Sync (for Alembic migrations)
DATABASE_URL=postgresql://resumate_user:resumate_password@localhost:5433/resumate
```

**⚠️ Port Note:** Port **5433** is used to avoid conflicts with native PostgreSQL on macOS (which uses 5432).

---

## Common Commands

### Run Migrations

```bash
cd backend
source .venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "Description"

# Upgrade to latest
alembic upgrade head

# Rollback one step
alembic downgrade -1

# View migration history
alembic history
```

### Connect to Database

```bash
# From within Docker container (recommended)
docker exec -it resumate-postgres psql -U resumate_user resumate

# From host (if psql client installed)
PGPASSWORD=resumate_password psql -h localhost -p 5433 -U resumate_user -d resumate
```

### View Tables

```sql
\dt  -- List tables
\d resumes  -- Describe resumes table
\d parsed_resume_data  -- Describe parsed_resume_data table
```

### Test Queries

```sql
-- Check resumes
SELECT id, original_filename, processing_status, uploaded_at FROM resumes ORDER BY uploaded_at DESC LIMIT 5;

-- Check parsed data
SELECT resume_id, personal_info->>'full_name' as name FROM parsed_resume_data;

-- Count records
SELECT
    (SELECT COUNT(*) FROM resumes) as resumes,
    (SELECT COUNT(*) FROM parsed_resume_data) as parsed_data,
    (SELECT COUNT(*) FROM resume_shares) as shares;
```

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 5432 or 5433
lsof -i :5432
lsof -i :5433
```

**Issue:** If native PostgreSQL is running on port 5432 (common on macOS), Docker PostgreSQL uses port 5433 automatically.

**Solution:** Update your connection string to use port 5433:
```bash
DATABASE_URL=postgresql+asyncpg://resumate_user:resumate_password@localhost:5433/resumate
```

### Backend Startup Issues

**Symptom:** `ModuleNotFoundError: No module named 'docx'` when running backend

**Cause:** Running backend from Conda base environment instead of project's virtual environment

**Solution:** Always activate the virtual environment first:
```bash
cd backend
source .venv/bin/activate  # CRITICAL - use project venv, not Conda
uvicorn app.main:app --reload
```

### Database Connection Issues

```bash
# Check if PostgreSQL container is running
docker compose ps

# Check PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL container
docker compose restart postgres
```

### Migration Errors

**Symptom:** `role "resumate_user" does not exist` or `database "resumate_user" does not exist`

**Cause:** Connecting to wrong PostgreSQL instance (native vs Docker)

**Solution:**
1. Verify you're using port 5433 (not 5432)
2. Check DATABASE_URL includes correct port
3. Use docker exec to connect directly: `docker exec resumate-postgres psql -U resumate_user -d resumate`

```bash
# Drop and recreate database (⚠️ deletes all data)
docker exec resumate-postgres psql -U resumate_user -d postgres -c "DROP DATABASE resumate;"
docker exec resumate-postgres psql -U resumate_user -d postgres -c "CREATE DATABASE resumate OWNER resumate_user;"
alembic upgrade head
```

---

## Integration with Application

### Enable Database Storage

In `backend/.env`:

```bash
USE_DATABASE=true  # Enable PostgreSQL storage
DATABASE_URL=postgresql+asyncpg://resumate_user:resumate_password@localhost:5432/resumate
```

### Verify Database is Working

```bash
# Upload a resume via API
curl -X POST http://localhost:8000/v1/resumes/upload \
  -F "file=@test-resume.pdf"

# Check data was saved
psql postgresql://resumate_user:resumate_password@localhost:5432/resumate \
  -c "SELECT id, original_filename FROM resumes ORDER BY uploaded_at DESC LIMIT 1;"
```

---

## Production Deployment

See: `docs/plans/2026-02-21-platform-update-renders-flyio.md`

**Key Differences:**

| Local | Production |
|-------|-------------|
| `localhost:5432` | Render PostgreSQL URL |
| `resumate_user` | Database user from Render |
| `resumate_password` | Auto-generated password |
| Docker Compose | Render managed service |

---

## Data Export/Import

### Export Data

```bash
# Dump all data
pg_dump $DATABASE_URL_SYNC > backup_$(date +%Y%m%d).sql

# Dump schema only
pg_dump -schema-only $DATABASE_URL_SYNC > schema.sql
```

### Import Data

```bash
# Import from backup
psql $DATABASE_URL_SYNC < backup_20260221.sql
```

---

**Status:** ✅ Ready for local development
**Last Updated:** 2026-02-21
