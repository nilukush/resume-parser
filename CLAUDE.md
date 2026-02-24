# ResuMate - AI-Powered Resume Parser

> **Project Context** | Updated: 2026-02-24 | Commits: 1708939 | Status: ✅ Bug Fix #19 Complete - Python 3.12 + spaCy 3.8+ Compatible

---

## Overview

ResuMate extracts structured data from resumes using **OCR -> NLP -> AI Enhancement**. Users upload resumes, get real-time parsing progress, review/edit extracted data, and share results.

```
Text Extraction (pdfplumber) + OCR Fallback (Tesseract)
         -> NLP Entity Extraction (spaCy)
         -> AI Enhancement (OpenAI GPT-4o-mini, optional)
```

**Graceful Degradation**: Works without AI if `OPENAI_API_KEY` not set.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI 0.109.0, Python 3.12 |
| OCR | Tesseract + pdf2image 1.16.3 |
| NLP | spaCy 3.8+ (Pydantic 2.x compatible, en_core_web_sm/lg) |
| AI | OpenAI 1.10.0 (GPT-4o-mini) |
| Database | Supabase PostgreSQL + async SQLAlchemy |
| Frontend | React 18 + TypeScript 5.3 + Vite 5.0 |
| Styling | Tailwind CSS 3.4 (navy/gold theme) |
| State | Zustand 4.5 |
| Deployment | Vercel (serverless) + Supabase (DB) |

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
# Database (Supabase)
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

## Common Commands

```bash
# Database (Docker)
docker compose up -d
cd backend && ./scripts/init_database.sh

# Backend Dev
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend Dev
cd frontend && npm run dev

# Testing
cd backend && python -m pytest tests/ -v
cd frontend && npm test -- --run && npm run type-check

# Vercel Deploy
cd .. && vercel --prod --scope nilukushs-projects
```

---

## Implementation Status

### ✅ Complete
- Full-stack resume parsing with OCR fallback
- Lazy database initialization (serverless-ready)
- Graceful health check degradation
- Real-time WebSocket progress updates
- Share tokens and export functionality
- Frontend and backend deployment configs fixed

### 🚧 Known Issues
- ✅ **Resolved**: Function detection issue (Bug Fix #18, commit 1d9fd7b)
  - Root cause: Handler was function instead of module-level variable
  - Fixed: Restored `handler = Mangum(app, lifespan="off")` pattern
- ✅ **Resolved**: Python 3.12 + spaCy 3.7.2 incompatibility (Bug Fix #19, commit 1708939)
  - Root cause: spaCy 3.7.2 incompatible with Python 3.12's ForwardRef signature
  - Fixed: Upgraded to spaCy 3.8+ (>=3.8.0,<4.0.0) in pyproject.toml, requirements.txt, requirements-full.txt
  - Verified: Deployment builds successfully with spaCy 3.8.11 on Python 3.12

### Test Coverage
- Backend: 175+ tests passing (including lazy DB tests)
- Frontend: 53 tests passing
- Total: 228+ tests

---

## Key Design Patterns

### 1. Lazy Database Initialization (Serverless Best Practice) ⭐ NEW
**Pattern**: Database connections created on first access, not import time
```python
# Before (BROKEN for serverless)
engine = db_manager.init_engine(...)  # ❌ Crashes at import!

# After (WORKS for serverless)
def get_engine():
    global engine
    if engine is None:
        engine = db_manager.init_engine(...)  # ✅ Lazy init
    return engine
```
**Why**: Serverless functions need to import without dependencies. Follows AWS Lambda, Vercel, and 12-factor app best practices.

### 3. Dependency Version Compatibility (Critical) ⭐ NEW
**Pattern**: spaCy, numpy, and Pydantic versions must be mutually compatible
```python
# REQUIREMENTS.TXT PATTERN
numpy==1.26.4        # Python 3.12 needs 1.26.4+ (has prebuilt wheels)
spacy>=3.8.0,<4.0.0  # 3.8+ required for Pydantic 2.x compatibility
pydantic==2.5.3       # spaCy 3.8+ supports Pydantic 2.x natively
```
**Why**:
- spaCy 3.7.2 uses Pydantic v1 compatibility layer (incompatible with Pydantic 2.x)
- spaCy 3.8+ has native Pydantic 2.x support (no compatibility layer needed)
- numpy 1.24.4 lacks Python 3.12 wheels (causes build-from-source failures)
- numpy 1.26.4+ has prebuilt wheels for Python 3.12

### 4. Vercel Runtime Dependency Caching ⭐ NEW
**Pattern**: Vercel caches runtime dependencies aggressively when bundle > 250MB
```bash
# SYMPTOM: Code changes don't take effect, old errors persist
"Using cached runtime dependencies"

# ROOT CAUSE: Bundle exceeds 250MB limit
"Bundle size (407.70 MB) exceeds limit. Enabling runtime dependency installation."

# SOLUTION: Wait 24-48h for cache expiration OR contact Vercel support
```
**Why**: Vercel's runtime cache persists across deployments when bundles exceed the 250MB threshold. Changing requirements.txt versions doesn't force cache refresh. Cache expires automatically in 24-48 hours.

### 2. Vercel Function Detection (Critical Pattern)
**Pattern**: Handler must be module-level variable, NOT a function
```python
# BROKEN (Vercel cannot detect)
def handler(event, context):
    mangum_handler = Mangum(app, lifespan="off")
    return mangum_handler(event, context)

# WORKING (Vercel detects via AST analysis)
from mangum import Mangum
from app.main import app
handler = Mangum(app, lifespan="off")  # Module-level variable!
```
**Why**: Vercel's build system performs static AST analysis to find serverless function exports. Module-level variable assignment is required for automatic detection.

### 5. Graceful Health Check Degradation
- Health check returns 200 OK even when database is down
- Service status: "healthy" → "degraded" (not "unhealthy")
- Enables monitoring during outages

### 6. OCR Automatic Fallback
- Try pdfplumber first for PDFs
- Trigger OCR if extracted text < 100 characters
- Handles multi-page PDFs with mixed content

### 7. Storage Abstraction
- `USE_DATABASE` flag controls persistence
- `StorageAdapter` provides unified interface
- Seamless migration from in-memory to database

---

## Deployment URLs

### Backend
- **Working**: https://resumate-backend-4yl17dd45-nilukushs-projects.vercel.app
- **Target**: https://resumate-backend.vercel.app (after configuration fix)

### Frontend
- **Target**: https://resumate-frontend.vercel.app

---

## Critical Gotchas

### Serverless Functions (Vercel/AWS Lambda)

**Rule #1**: Never initialize heavy resources at module import time
- ❌ DON'T: `engine = create_engine(...)  # At import`
- ✅ DO: `def get_engine(): if not engine: engine = create_engine(...)`

**Rule #2**: Handler must be module-level variable for function detection
- ❌ DON'T: `def handler(event, context): ...`  # Function definition
- ✅ DO: `handler = Mangum(app, lifespan="off")`  # Module-level variable

**Why**:
- Faster cold starts
- Function can start even when dependencies are down
- Better debugging (can see actual errors)
- Vercel requires AST-visible exports for detection

### Vercel Deployment Gotchas
- Legacy `builds` array causes schema validation failures
- Modern Vercel uses minimal config with automatic detection
- Schema validation happens BEFORE deployment
- Always include `$schema` property for IDE validation
- **Runtime dependency cache**: When bundle > 250MB, Vercel caches runtime deps for 24-48h
- **Project structure**: `backend/` and `frontend/` are separate Vercel projects with own configs
- **Cache invalidation**: Adding comments to requirements.txt doesn't force cache refresh

### Function Size Limits
- 250MB is a hard AWS Lambda limit (after compression)
- Cannot be configured via `vercel.json`
- Manage bundle size with `.vercelignore`
- **Current size**: 407.70 MB (triggers runtime installation with caching)
- **Optimization target**: Remove Celery/Redis/Sentry to reduce below 250MB

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| `docs/BUG-FIX-19-PYTHON-312-SPACY-COMPATIBILITY.md` | Python 3.12 + spaCy 3.8+ compatibility fix |
| `docs/PROGRESS.md` | Progress tracking (includes all bug fixes) |
| `docs/BUG-FIX-17b-PEP-668-COMPLIANCE.md` | PEP 668 compliance fix |
| `docs/BUG-FIX-17b-PEP-668-COMPLIANCE.md` | PEP 668 compliance fix |
| `docs/DEPLOYMENT-TROUBLESHOOTING.md` | Deployment troubleshooting guide |
| `docs/DATABASE_SETUP.md` | Database setup guide |
| `docs/SUPABASE_SETUP.md` | Supabase-specific setup |

---

**Context Generated**: 2026-02-24
**Claude Model**: Sonnet 4.5
**Project Status**: MVP + Database + Serverless Ready (Bug Fix #19 Complete - Python 3.12 Compatible)

---

## Quick Start

1. **Clone & Setup**:
   ```bash
   git clone <repo>
   cd resume-parser
   docker compose up -d  # Start database
   ```

2. **Backend**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Deploy to Vercel**:
   ```bash
   # From repository root
   vercel --prod --scope nilukushs-projects
   ```
