# ResuMate - AI-Powered Resume Parser

> **Project Context for Claude AI Assistant**
> Last Updated: 2026-02-22 | Status: MVP + AI Enhancement + Database Persistence Complete

## Overview

ResuMate extracts structured data from resumes using a multi-stage hybrid approach: **OCR → NLP → AI Enhancement**. Users upload resumes, get real-time parsing progress, review/edit extracted data, and share results.

### Solution Architecture
```
Text Extraction (pdfplumber) + OCR Fallback (Tesseract)
    ↓
NLP Entity Extraction (spaCy)
    ↓
AI Enhancement (OpenAI GPT-4o-mini, optional)
```

**Graceful Degradation**: Parser works without AI if `OPENAI_API_KEY` is not set.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI 0.109.0, Python 3.11 |
| **OCR** | Tesseract + pdf2image 1.16.3 |
| **NLP** | spaCy 3.7.2 (en_core_web_sm/lg) |
| **AI** | OpenAI 1.10.0 (GPT-4o-mini) |
| **Database** | PostgreSQL with async SQLAlchemy |
| **Frontend** | React 18 + TypeScript 5.3 + Vite 5.0 |
| **Styling** | Tailwind CSS 3.4 (navy/gold theme) |
| **State** | Zustand 4.5 |
| **Testing** | pytest 7.4.4, pytest-asyncio 0.23.3 |

---

## Project Structure

```
resume-parser/
├── backend/app/
│   ├── api/                 # FastAPI routes
│   │   ├── resumes.py       # Upload, GET, PUT endpoints
│   │   ├── shares.py        # Share, export endpoints
│   │   └── websocket.py     # WebSocket connection manager
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
    ├── PROGRESS.md          # Detailed progress tracking
    └── plans/               # Implementation plans
```

---

## Data Flow & API Endpoints

### Upload Flow
```
POST /v1/resumes/upload → Returns { resume_id, websocket_url }
    ↓
WebSocket: ws://localhost:8000/ws/resumes/{resume_id}
    ↓
Parsing stages broadcast real-time progress:
    - TEXT_EXTRACTION (0-30%): Try pdfplumber, fallback to OCR if <100 chars
    - NLP_PARSING (30-60%): Extract entities with spaCy
    - AI_ENHANCEMENT (60-100%): Validate with GPT-4o-mini (optional)
    - COMPLETE: Redirect to /review/{id}
```

### Review & Edit
```
GET /v1/resumes/{id} → Display parsed data with confidence scores
PUT /v1/resumes/{id} → Save user corrections
```

### Share & Export
```
POST /v1/resumes/{id}/share → Returns { share_token, share_url, expires_at }
GET /v1/resumes/{id}/export/pdf → Download PDF
```

### WebSocket Message Format
```json
{
  "type": "progress_update",
  "stage": "text_extraction | nlp_parsing | ai_enhancement | complete",
  "progress": 50,
  "status": "Extracting text...",
  "timestamp": "2026-02-20T10:30:00.000000"
}
```

---

## Environment Configuration

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://resumate_user:resumate_password@localhost:5433/resumate
DATABASE_URL_SYNC=postgresql://resumate_user:resumate_password@localhost:5433/resumate
USE_DATABASE=true              # Enable PostgreSQL storage

# AI (Optional - graceful fallback)
OPENAI_API_KEY=sk-...

# OCR
TESSERACT_PATH=/usr/local/bin/tesseract  # macOS: brew install tesseract
ENABLE_OCR_FALLBACK=true

# App
SECRET_KEY=...
ALLOWED_ORIGINS=http://localhost:3000
USE_CELERY=false               # Celery async processing (future)
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws
```

---

## Common Commands

### Development
```bash
# Start database (Docker Compose)
docker compose up -d

# Initialize database (run migrations)
cd backend && ./scripts/init_database.sh

# Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm run dev
```

### Testing
```bash
# Backend
cd backend && python -m pytest tests/ -v

# Frontend
cd frontend && npm test -- --run
npm run type-check
```

### Database
```bash
# Migrations
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Connect
docker exec -it resumate-postgres psql -U resumate_user resumate
```

---

## Implementation Status

### Complete (MVP + Phase 2 + Database Persistence + Bug Fixes)
- Project setup (Python 3.11, React 18, TypeScript)
- Database models with async SQLAlchemy
- Text extraction (PDF/DOCX/DOC/TXT) with OCR fallback
- NLP entity extraction (spaCy)
- AI enhancement (OpenAI GPT-4o-mini)
- FastAPI endpoints (upload, GET, PUT, share)
- WebSocket real-time progress
- React pages (Upload, Processing, Review, Share)
- Share tokens and export (PDF, WhatsApp, Telegram, Email)
- **Database persistence** (PostgreSQL with Alembic migrations)
- **Storage abstraction layer** (in-memory / database switchable)
- All critical bugs fixed (13 bug fix sessions)

### Test Coverage
- **Backend**: 136/136 tests passing (28 unit, 9 integration, 4 E2E)
- **Frontend**: 31/31 tests passing
- **Total**: 167+ tests

### Remaining (Phase 3+)
- Celery async task queue
- Redis for queue management
- Production deployment (Railway + Vercel)
- User authentication

---

## Recent Bug Fixes (2026-02-21)

### Bug Fix #13: Share Endpoint 404 & WebSocket Serialization ✅

**Issues Resolved:**
1. **Share 404 Error**: Shares used in-memory storage instead of database persistence
2. **WebSocket Closure**: Database objects (UUID, Decimal, datetime) not JSON-serializable

**Solutions:**
- Created `database_share_storage.py` with async CRUD operations
- Added storage abstraction layer routing based on `USE_DATABASE` flag
- Implemented `_serialize_for_websocket()` for UUID/datetime/Decimal conversion
- Enhanced error logging with exception types and stack traces

**Files Modified:**
- `app/services/database_share_storage.py` (new)
- `app/services/parser_orchestrator.py` (added serialization)
- `app/api/shares.py` (storage abstraction)
- `app/api/websocket.py` (improved error logging)

See: `docs/DEBUGGING-SESSION-2026-02-21-FIXES.md`

---

## Key Design Patterns

### 1. Graceful AI Degradation
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

### 4. WebSocket Serialization
- Always serialize at system boundaries
- Recursive conversion of UUID, datetime, Decimal
- Enhanced error logging with stack traces

---

## Documentation References

| Document | Purpose |
|----------|---------|
| `docs/PROGRESS.md` | Detailed task-by-task progress, commit references |
| `docs/DATABASE_SETUP.md` | Database setup, migrations, troubleshooting |
| `docs/DEBUGGING-SESSION-2026-02-21-FIXES.md` | Latest bug fixes (Share 404, WebSocket) |
| `docs/DEBUGGING-UUID-ISSUE-2026-02-21.md` | UUID generation bug fix |
| `docs/DEBUGGING-WEBSOCKET-2026-02-21.md` | WebSocket connection issues |
| `docs/plans/` | Implementation design documents |

---

## Next Steps

1. **Frontend Testing** - Verify complete flow in browser
2. **Celery Integration** - Async background job processing
3. **Authentication** - JWT-based user sessions
4. **Production Deployment** - Railway (backend) + Vercel (frontend)
5. **Monitoring** - Sentry error tracking

---

**Context Generated**: 2026-02-22
**Claude Model**: Opus 4.5
**Project Status**: ✅ MVP + AI Enhancement + Database Persistence Complete
