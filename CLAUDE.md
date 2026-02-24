# ResuMate - AI-Powered Resume Parser

> **Updated**: 2026-02-24 | **Status**: Bug Fix #23 Fixed, Awaiting Vercel Cache Expiration | **Tests**: 228+

---

## Overview

ResuMate extracts structured data from resumes using **OCR -> NLP -> AI Enhancement**. Users upload resumes, get real-time parsing progress, review/edit extracted data, and share results.

```
Text Extraction (pdfplumber) + OCR Fallback (Tesseract)
         -> NLP Entity Extraction (spaCy 3.8+)
         -> AI Enhancement (OpenAI GPT-4o-mini, optional)
```

**Graceful Degradation**: Works without AI if `OPENAI_API_KEY` not set.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI 0.109.0, Python 3.12 |
| OCR | Tesseract + pdf2image 1.16.3 |
| NLP | spaCy 3.8+ (Pydantic 2.x compatible) |
| AI | OpenAI 1.10.0 (GPT-4o-mini) |
| Database | Supabase PostgreSQL + async SQLAlchemy |
| Frontend | React 18 + TypeScript 5.3 + Vite 5.0 |
| Styling | Tailwind CSS 3.4 (navy/gold theme) |
| State | Zustand 4.5 |
| Deployment | Vercel serverless + Supabase |

---

## Quick Start

```bash
# Clone & database setup
git clone <repo> && cd resume-parser
docker compose up -d
cd backend && ./scripts/init_database.sh

# Backend development
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd frontend && npm install && npm run dev

# Testing
cd backend && python -m pytest tests/ -v
cd frontend && npm test -- --run && npm run type-check

# Deploy
vercel --prod --scope nilukushs-projects
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/resumes/upload` | POST | Upload resume, returns {resume_id, websocket_url} |
| `/v1/resumes/{id}` | GET | Fetch parsed resume data |
| `/v1/resumes/{id}` | PUT | Save user edits |
| `/v1/resumes/{id}/share` | POST | Create share token, returns {share_token, share_url, expires_at} |
| `/v1/resumes/{id}/export/pdf` | GET | Download PDF export |
| `/ws/resumes/{id}` | WebSocket | Real-time parsing progress |
| `/health` | GET | Health check with graceful degradation |

---

## Environment Configuration

### Backend (.env)
```bash
# Database (Supabase) - URL-encode passwords
DATABASE_URL=postgresql+asyncpg://postgres:ENCODED_PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
DATABASE_URL_SYNC=postgresql://postgres:ENCODED_PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
USE_DATABASE=true

# AI (Optional - graceful fallback)
OPENAI_API_KEY=sk-...

# OCR
TESSERACT_PATH=/usr/local/bin/tesseract
ENABLE_OCR_FALLBACK=true

# App
SECRET_KEY=...
ALLOWED_ORIGINS=https://resumate-frontend.vercel.app,http://localhost:3000
USE_CELERY=false
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=https://resumate-backend.vercel.app/v1
VITE_WS_BASE_URL=wss://resumate-backend.vercel.app/ws
```

---

## Implementation Status

### Complete Features
- Full-stack resume parsing with OCR fallback
- Lazy database initialization (serverless-ready)
- Graceful health check degradation
- Real-time WebSocket progress updates
- Share tokens and export functionality
- Frontend and backend deployment configs

### Recent Fixes
| # | Issue | Resolution |
|---|-------|------------|
| #18 | Function detection + lazy DB | Module-level handler + lazy init pattern |
| #19 | Python 3.12 + spaCy 3.7.2 incompatibility | Upgraded to spaCy 3.8+ |
| #20 | Pydantic v2 compatibility | Added confection>=0.1.4, thinc>=8.3.4 |
| #21 | Python 3.12.4 + Pydantic compatibility | Upgraded to pydantic>=2.7.4 |
| #22 | Mangum 0.17.0 + Python 3.12 | Upgraded to mangum>=0.21.0 in requirements.txt |
| #23 | Mangum version mismatch | Fixed pyproject.toml mangum>=0.21.0, awaiting Vercel runtime cache expiration |

### Test Coverage
- Backend: 175+ tests passing
- Frontend: 53 tests passing
- Total: 228+ tests

---

## Critical Patterns

### 1. Lazy Database Initialization
Serverless functions must NOT initialize resources at import time.
```python
# BROKEN for serverless
engine = db_manager.init_engine(...)  # Crashes at import!

# WORKING
def get_engine():
    global engine
    if engine is None:
        engine = db_manager.init_engine(...)
    return engine
```

### 2. Vercel Function Detection
Handler must be module-level variable for AST detection.
```python
# BROKEN - Vercel cannot detect
def handler(event, context):
    return Mangum(app, lifespan="off")(event, context)

# WORKING
handler = Mangum(app, lifespan="off")  # Module-level variable
```

### 3. Dependency Version Compatibility
Python 3.12 requires specific versions:
```python
numpy==1.26.4        # Prebuilt wheels for Python 3.12
spacy>=3.8.0,<4.0.0  # Native Pydantic 2.x support
pydantic>=2.7.4      # Python 3.12.4 compatible
mangum>=0.21.0,<1.0.0 # Python 3.12 compatible
confection>=0.1.4    # Pydantic v2 support for spaCy
thinc>=8.3.4         # Pydantic v2 support for spaCy
```
**Always keep pyproject.toml and requirements.txt in sync.**

### 4. Vercel Runtime Cache
When bundle exceeds 250MB (current: ~401MB), Vercel caches runtime dependencies for 24-48 hours.
- **Build cache**: Cleared by `vercel --force`
- **Runtime cache**: NO CLI command to clear, must wait 24-48h or contact support
- **Best practice**: Reduce bundle below 250MB to avoid runtime caching entirely

### 5. Graceful Health Degradation
Health check returns 200 OK even when database is down.
```python
health_status["status"] = "degraded"  # NOT "unhealthy"
```

### 6. PEP 668 Compliance
Modern Python (3.11+) uses externally-managed environments.
```bash
# Vercel/serverless containers
pip install --break-system-packages -r requirements.txt
```

---

## Deployment URLs

| Service | URL |
|---------|-----|
| Backend (target) | https://resumate-backend.vercel.app |
| Frontend | https://resumate-frontend.vercel.app |

---

## Critical Gotchas

### Serverless Functions (Vercel/AWS Lambda)
| Rule | Don't | Do |
|------|-------|-----|
| Init | `engine = create_engine(...)` | `def get_engine(): if not engine: ...` |
| Handler | `def handler(event, context):` | `handler = Mangum(app, lifespan="off")` |

### Vercel Deployment
- **Monorepo**: Run `vercel` from repo root, not subdirectories
- **Function size check**: `vercel inspect <url>` shows bundle size (target: <250MB)
- **Runtime logs**: `vercel logs <url>` streams real-time errors
- **Cache indicators**: "Using cached runtime dependencies" = stale cache, "Installing runtime dependencies" = fresh
- Bundle size >250MB triggers runtime dependency caching (24-48h expiration, no CLI clear)
- `vercel --force` clears build cache, NOT runtime cache
- `backend/` and `frontend/` are separate Vercel projects

### Dependency Management
- Always keep pyproject.toml and requirements.txt synchronized
- Vercel prioritizes pyproject.toml over requirements.txt
- Use `>=` in pyproject.toml, `==` in requirements.txt for exact versions
- **Version mismatch symptoms**: TypeError in Vercel runtime code (not your code)
- **Verification**: Compare Mangum/Pydantic/spaCy versions across both files before deploying
- **Sync tools**: Use `pip-compile` or Poetry to maintain consistency automatically

---

## Quick Reference: Vercel Debugging

### Check Deployment Health
```bash
# 1. Inspect deployment (shows function size, build logs)
vercel inspect <deployment-url> --wait

# 2. Stream real-time logs (shows runtime errors)
vercel logs <deployment-url>

# 3. Test health endpoint
curl -s <deployment-url>/health
```

### Cache Status Indicators
| Log Message | Meaning | Action |
|-------------|---------|--------|
| "Using cached runtime dependencies" | Old cached Python packages | Wait 24-48h or reduce bundle size |
| "Installing runtime dependencies" | Fresh installation | Good! Proceed with testing |
| "Skipping build cache" | Build cache bypassed | Expected with `--force` flag |

### Function Size Targets
| Size | Runtime Cache | Cold Start | Recommendation |
|------|---------------|------------|----------------|
| <250MB | No | Fast (~2s) | ✅ Target |
| 250-400MB | Yes (24-48h) | Medium (~5s) | ⚠️ Reduce dependencies |
| >400MB | Yes (24-48h) | Slow (~10s+) | ❌ Must optimize |

### Common Issues & Quick Fixes
| Symptom | Root Cause | Fix |
|---------|------------|-----|
| TypeError in vc_init.py | Old Mangum version in cache | Update pyproject.toml, wait 24-48h |
| FUNCTION_INVOCATION_FAILED | Runtime cache incompatibility | Same as above |
| ModuleNotFoundError | Missing dependency | Check pyproject.toml, redeploy |
| Build succeeds, invocation fails | Bundle size >250MB with old cache | Reduce bundle or wait for expiration |

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| `docs/PROGRESS.md` | Progress tracking with all bug fixes |
| `docs/BUG-FIX-23-VERCEL-RUNTIME-CACHE.md` | Mangum version mismatch fix |
| `docs/BUG-FIX-22-MANGUM-021-PYTHON312-COMPATIBILITY.md` | Mangum upgrade |
| `docs/BUG-FIX-21-PYTHON-312-4-PYDANTIC-274-COMPATIBILITY.md` | Pydantic upgrade |
| `docs/BUG-FIX-20-PYDANTIC-V2-SPACY-COMPATIBILITY.md` | Pydantic v2 support |
| `docs/BUG-FIX-19-PYTHON-312-SPACY-COMPATIBILITY.md` | spaCy 3.8+ upgrade |
| `docs/BUG-FIX-17b-PEP-668-COMPLIANCE.md` | PEP 668 compliance |
| `docs/BUG-FIX-17-VERCEL-RUNTIME-ERROR.md` | Runtime configuration fix |
| `docs/DEPLOYMENT-TROUBLESHOOTING.md` | Deployment guide |
| `docs/DATABASE_SETUP.md` | Database setup |
| `docs/SUPABASE_SETUP.md` | Supabase-specific setup |
