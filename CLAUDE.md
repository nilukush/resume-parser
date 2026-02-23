# ResuMate - AI-Powered Resume Parser

> **Project Context** | Updated: 2026-02-22 | Commit: bda8e90 | Status: MVP + DB + Platform Migration Complete

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
| Backend | FastAPI 0.109.0, Python 3.11 |
| OCR | Tesseract + pdf2image 1.16.3 |
| NLP | spaCy 3.7.2 (en_core_web_sm/lg) |
| AI | OpenAI 1.10.0 (GPT-4o-mini) |
| Database | Supabase PostgreSQL + async SQLAlchemy |
| Frontend | React 18 + TypeScript 5.3 + Vite 5.0 |
| Styling | Tailwind CSS 3.4 (navy/gold theme) |
| State | Zustand 4.5 |
| Deployment | Vercel (serverless) + Supabase (DB) |

---

## Project Structure

```
resume-parser/
├── backend/app/
│   ├── api/                 # FastAPI routes
│   │   ├── resumes.py       # Upload, GET, PUT endpoints
│   │   ├── shares.py        # Share, export endpoints
│   │   └── websocket.py     # WebSocket connection manager
├── backend/api/
│   └── index.py            # Vercel serverless handler (Mangum + FastAPI)
├── backend/app/
│   ├── core/
│   │   ├── config.py        # Pydantic settings + feature flags
│   │   ├── database.py      # SQLAlchemy async setup
│   │   └── storage.py       # In-memory resume storage
│   ├── models/
│   │   ├── progress.py      # ProgressStage enum, ParsedData
│   │   └── resume.py        # SQLAlchemy models
│   ├── services/
│   │   ├── text_extractor.py    # PDF/DOCX/DOC/TXT + OCR fallback
│   │   ├── ocr_extractor.py     # Tesseract OCR
│   │   ├── nlp_extractor.py     # spaCy entity extraction
│   │   ├── ai_extractor.py      # OpenAI GPT-4o-mini
│   │   ├── parser_orchestrator.py  # Pipeline orchestration
│   │   ├── export_service.py    # PDF/WhatsApp/Telegram/Email
│   │   ├── database_storage.py  # PostgreSQL CRUD operations
│   │   └── storage_adapter.py   # Storage abstraction layer
│   └── main.py              # FastAPI app
├── frontend/src/
│   ├── components/          # FileUpload, ProcessingStage, ShareLinkCard, etc.
│   ├── pages/               # Upload, Processing, Review, Share pages
│   ├── hooks/               # useWebSocket.ts
│   ├── services/            # api.ts (HTTP client)
│   └── types/               # TypeScript interfaces
└── docs/
    ├── DATABASE_SETUP.md    # Database setup guide
    ├── SUPABASE_SETUP.md    # Supabase-specific setup
    ├── VERCEL_DEPLOYMENT.md # Deployment instructions
    └── PROGRESS.md          # Progress tracking
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
| `/health` | GET | Health check with DB status |

### WebSocket Progress Stages

| Stage | Progress | Description |
|-------|----------|-------------|
| TEXT_EXTRACTION | 0-30% | Try pdfplumber, fallback to OCR if <100 chars |
| NLP_PARSING | 30-60% | Extract entities with spaCy |
| AI_ENHANCEMENT | 60-100% | Validate with GPT-4o-mini (optional) |
| COMPLETE | 100% | Ready for review |

**Message Format:**
```json
{"type": "progress_update", "stage": "text_extraction", "progress": 50, "status": "Extracting text...", "timestamp": "2026-02-20T10:30:00.000000"}
```

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
TESSERACT_PATH=/usr/local/bin/tesseract  # macOS: brew install tesseract
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

# Vercel Config Validation
cd backend && python3 -m json.tool vercel.json  # JSON syntax check
cd backend && python -m pytest tests/unit/test_vercel_config.py -v  # Vercel config tests
cd backend && python -c "from api.index import handler; print('✓ Handler OK')"  # Handler import check

# Migrations
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Database Connect
docker exec -it resumate-postgres psql -U resumate_user resumate
```

---

## Implementation Status

### Complete
- Project setup (Python 3.11, React 18, TypeScript)
- Text extraction (PDF/DOCX/DOC/TXT) with OCR fallback
- NLP entity extraction (spaCy)
- AI enhancement (OpenAI GPT-4o-mini)
- FastAPI endpoints (upload, GET, PUT, share)
- WebSocket real-time progress
- React pages (Upload, Processing, Review, Share)
- Share tokens and export (PDF, WhatsApp, Telegram, Email)
- **Database persistence** (PostgreSQL with Alembic)
- **Storage abstraction layer** (in-memory / database switchable)
- **Platform migration**: Render/Railway -> Vercel + Supabase
- **Vercel build configuration** (PEP 668 compliant)
- All critical bugs fixed (15+ bug fix sessions)

### Test Coverage
- Backend: 169 tests passing (including 7 Vercel config tests)
- Frontend: 53 tests passing
- Total: 222+ tests

### Remaining
- Celery async task queue + Redis
- User authentication (JWT)
- Production monitoring (Sentry configured)

---

## Key Design Patterns

### 1. Graceful Degradation
- No hard dependency on OpenAI API key
- Returns NLP-extracted data if AI unavailable
- Logs errors but doesn't break pipeline

### 2. OCR Automatic Fallback
- Try pdfplumber first for PDFs
- Trigger OCR if extracted text < 100 characters
- Handles multi-page PDFs with mixed content

### 3. Storage Abstraction
- `USE_DATABASE` flag controls persistence
- `StorageAdapter` provides unified interface
- Seamless migration from in-memory to database

### 4. JSON Serialization at Boundaries
```python
def _serialize_for_websocket(data: Any) -> Any:
    if isinstance(data, UUID): return str(data)
    if isinstance(data, datetime): return data.isoformat()
    if isinstance(data, Decimal): return float(data)
```

### 5. Serverless ASGI Adapter (Vercel)
- **Mangum** bridges FastAPI (ASGI) with AWS Lambda/Vercel serverless
- Entry point: `backend/api/index.py` exports `handler = Mangum(app, lifespan="off")`
- `lifespan="off"` for serverless (no startup/shutdown events)
- Required for FastAPI on Vercel - not optional

---

## Critical Gotchas

### Vercel Deployment
- Legacy `builds` array (pre-2021) causes schema validation failures
- Modern Vercel uses minimal config with automatic framework detection
- Schema validation happens BEFORE deployment - fails immediately with deprecated properties
- Always include `$schema` property in `vercel.json` for IDE validation
- Test for deprecated properties: `builds`, `routes`, `maxLambdaSize`, `version`

### Function Size Limits
- 250MB is a hard AWS Lambda limit (after compression)
- Cannot be configured via `vercel.json` - any `maxLambdaSize` property will fail schema validation
- Manage bundle size with `.vercelignore` and proper dependencies

---

## Platform Details

### Architecture
```
Vercel (Backend) -> Supabase PostgreSQL <- Vercel (Frontend)
  $0/month             $0/month               $0/month
  Serverless          500MB, 50K MAU          Edge CDN
```

### Deployment URLs
- Backend: `https://resumate-backend.vercel.app`
- Frontend: `https://resumate-frontend.vercel.app`
- Database: Supabase (db.piqltpksqaldndikmaob.supabase.co)

### Vercel Build Config
- Uses `pip install --user` for PEP 668 compliance
- **DO NOT use `maxLambdaSize`** - deprecated property (schema validation fails)
- Runtime: Python 3.11
- Serverless handler: `backend/api/index.py` with Mangum adapter
- Function size limit: 250MB (hard AWS limit, not configurable)

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| `docs/PROGRESS.md` | Progress tracking |
| `docs/DATABASE_SETUP.md` | Database setup guide |
| `docs/SUPABASE_SETUP.md` | Supabase-specific setup |
| `docs/VERCEL_DEPLOYMENT.md` | Vercel deployment instructions |
| `docs/PLATFORM-MIGRATION-COMPLETE.md` | Platform migration details |
| `docs/VERCEL-FIX-INSTRUCTIONS.md` | Build troubleshooting |
| `docs/DEBUGGING-INDEX.md` | Debugging sessions reference |
| `docs/BUG-FIX-16-VERCEL-SCHEMA.md` | Vercel schema validation fix (2026-02-22) |

---

**Context Generated**: 2026-02-23
**Claude Model**: Sonnet 4.5
**Project Status**: MVP + Database + Platform Migration Complete
