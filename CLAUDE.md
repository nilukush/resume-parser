# ResuMate - AI-Powered Resume Parser

> **Updated**: 2026-02-24 | **Status**: Bug Fix #24 Complete, Awaiting Vercel Runtime Cache Expiration (~2026-02-25) | **Tests**: 228+

---

## Overview

ResuMate extracts structured data from resumes using **OCR -> NLP -> AI Enhancement**.

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

# Deploy (CRITICAL: Commit changes first - Vercel deploys from git!)
git add . && git commit -m "feat: description"
git push origin main
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

## Recent Fixes (#18-#24)

| # | Issue | Resolution |
|---|-------|------------|
| #18 | Function detection + lazy DB | Module-level handler + lazy init pattern |
| #19 | Python 3.12 + spaCy 3.7.2 incompatibility | Upgraded to spaCy 3.8+ |
| #20 | Pydantic v2 compatibility | Added confection>=0.1.4, thinc>=8.3.4 |
| #21 | Python 3.12.4 + Pydantic compatibility | Upgraded to pydantic>=2.7.4 |
| #22 | Mangum 0.17.0 + Python 3.12 | Upgraded to mangum>=0.21.0 in requirements.txt |
| #23 | Mangum version mismatch | Fixed pyproject.toml mangum>=0.21.0 |
| #24 | Bundle size 401MB (runtime cache trigger) | Removed Celery, Redis, Sentry (-54MB) |

**Current Status**: Bundle 394.92 MB, awaiting Vercel runtime cache expiration. TypeError persists until cache refreshes.

---

## Critical Patterns

### 1. Lazy Database Initialization
Serverless functions must NOT initialize resources at import time.
```python
# BROKEN
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
# BROKEN
def handler(event, context):
    return Mangum(app, lifespan="off")(event, context)

# WORKING
handler = Mangum(app, lifespan="off")  # Module-level variable
```

### 3. Python 3.12 Dependency Versions
```python
numpy==1.26.4        # Prebuilt wheels for Python 3.12
spacy>=3.8.0,<4.0.0  # Native Pydantic 2.x support
pydantic>=2.7.4      # Python 3.12.4 compatible
mangum>=0.21.0,<1.0.0 # Python 3.12 compatible
confection>=0.1.4    # Pydantic v2 support for spaCy
thinc>=8.3.4         # Pydantic v2 support for spaCy
```

### 4. Graceful Health Degradation
```python
health_status["status"] = "degraded"  # NOT "unhealthy" - always return 200 OK
```

### 5. PEP 668 Compliance
```bash
# Vercel/serverless containers
pip install --break-system-packages -r requirements.txt
```

---

## Vercel Deployment

### Deployment Workflow
1. **Code changes**: Edit files locally
2. **Test locally**: `python -m pytest` or `npm test`
3. **Commit**: `git add . && git commit -m "description"`
4. **Push**: `git push origin main` ← **Vercel deploys from git, not local files!**
5. **Deploy**: `vercel --prod --scope nilukushs-projects`
6. **Verify**: `vercel inspect <url> --wait && curl <url>/health`

### Current Bundle Status
| Metric | Value | Status |
|--------|-------|--------|
| Bundle size | 394.92 MB | ⚠️ Above 250MB threshold |
| Function size | 79.18 MB | ✅ Excellent |
| Runtime cache | Active | Expires ~2026-02-25 |

### Key Rules
- **Monorepo**: Run `vercel` from repo root, not subdirectories
- **Runtime cache**: Bundle >250MB triggers 24-48h cache (NO CLI clear available)
- **Build cache**: Cleared by `vercel --force` (does NOT affect runtime cache)
- **Projects**: `backend/` and `frontend/` are separate Vercel projects

### Debugging Commands
```bash
# Inspect deployment (bundle size, build logs)
vercel inspect <deployment-url> --wait

# Stream real-time logs (runtime errors)
vercel logs <deployment-url>

# Test health endpoint
curl -s <deployment-url>/health

# Monitor long-running deployments
vercel inspect <url> --wait  # Shows real-time build progress

# Check for TypeError in logs
vercel logs <url> --n 50 | grep -i "TypeError\|issubclass"

# Verify unused dependencies before removal
grep -r "import celery\|from celery" backend/app/  # Check if actually used
```

### Cache Status Indicators
| Log Message | Meaning |
|-------------|---------|
| "Using cached runtime dependencies" | Stale cache (wait 24-48h) |
| "Installing runtime dependencies" | Fresh install (good!) |
| "Skipping build cache" | Build cache bypassed |

### Bundle Size Targets
| Bundle Size | Runtime Cache | Cold Start | Recommendation |
|-------------|---------------|------------|----------------|
| <250MB | No | ~2s | ✅ Target |
| 250-400MB | Yes (24-48h) | ~5s | ⚠️ Reduce dependencies |
| >400MB | Yes (24-48h) | ~10s+ | ❌ Must optimize |

---

## Dependency Management

| Rule | Details |
|------|---------|
| Sync files | Always keep `pyproject.toml` and `requirements.txt` synchronized |
| Vercel priority | Vercel reads `pyproject.toml` first |
| Version specifiers | Use `>=` in pyproject.toml, `==` in requirements.txt |
| Verification | Compare Mangum/Pydantic/spaCy versions across both files before deploying |
| Mismatch symptoms | TypeError in Vercel runtime code (vc_init.py), not your code |
| Sync tools | Use `pip-compile` or Poetry for automatic consistency |
| **Before removing dependencies** | Verify usage: `grep -r "import <lib>" backend/app/` |
| **Git workflow** | Vercel deploys from git - commit & push before deploying! |

---

## Common Issues

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| TypeError in vc_init.py | Old Mangum version in runtime cache | Update pyproject.toml, wait 24-48h |
| FUNCTION_INVOCATION_FAILED | Runtime cache incompatibility | Same as above |
| ModuleNotFoundError | Missing dependency | Check pyproject.toml, redeploy |
| Build succeeds, invocation fails | Bundle size >250MB with stale cache | Reduce bundle or wait for expiration |
| **Vercel deploying old code** | **Forgot to commit/push git changes** | **`git add . && git commit && git push`** |
| **Changes not reflected** | **Vercel caches git repo** | **Force new deployment with `vercel --force`** |

---

## Deployment URLs

| Service | URL |
|---------|-----|
| Backend | https://resumate-backend.vercel.app |
| Frontend | https://resumate-frontend.vercel.app |

---

## Test Coverage

- Backend: 175+ tests passing
- Frontend: 53 tests passing
- Total: 228+ tests

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| `docs/PROGRESS.md` | Progress tracking with all bug fixes |
| `docs/BUG-FIX-24-BUNDLE-OPTIMIZATION.md` | Celery/Redis/Sentry removal |
| `docs/BUG-FIX-23-VERCEL-RUNTIME-CACHE.md` | Mangum version mismatch fix |
| `docs/DEPLOYMENT-TROUBLESHOOTING.md` | Full deployment guide |
| `docs/DATABASE_SETUP.md` | Database setup |
| `docs/SUPABASE_SETUP.md` | Supabase-specific setup |

---

## Session Learnings (2026-02-24)

**Vercel Git Workflow**: Always commit and push before deploying - Vercel reads from git repository, not local filesystem

**Dependency Removal Safety**: Before removing dependencies, verify they're unused: `grep -r "import <lib>" backend/app/`

**Runtime vs Build Cache**: `vercel --force` clears build cache only; runtime cache (24-48h expiration) has no CLI clear command when bundle >250MB

**Background Deployment Monitoring**: Use `vercel inspect <url> --wait` to monitor long-running deployments in real-time

**Bundle Size Strategy**: Target <250MB to avoid runtime caching. If unavoidable, optimize `.vercelignore` and remove heavy dependencies (Celery/Redis/Sentry = ~54MB savings potential)
