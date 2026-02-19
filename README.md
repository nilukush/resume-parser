# ResuMate - Smart Resume Parser

An intelligent resume parsing platform that extracts structured data from resumes using OCR, NLP, and AI.

## Tech Stack

- **Backend:** FastAPI (Python 3.11+) with WebSocket support
- **Frontend:** React 18+ with TypeScript and WebSocket hooks
- **Database:** PostgreSQL with JSONB
- **AI/ML:** Tesseract OCR, spaCy NLP, OpenAI GPT-4
- **Deployment:** Railway (backend), Vercel (frontend)
- **Testing:** Pytest (backend), Vitest (frontend)

## Features

- Multi-format support (PDF, DOCX, DOC, TXT)
- Real-time parsing progress via WebSocket
- NLP-based entity extraction
- Confidence scoring
- Review and edit parsed data
- **Shareable links** with configurable expiration
- **Export to PDF** with professional formatting
- **Social sharing** (WhatsApp, Telegram, Email)
- Access tracking and share revocation

## Project Structure

```
resume-parser/
|-- backend/          # FastAPI application
|   |-- app/
|   |   |-- api/      # API routes & WebSocket handlers
|   |   |-- models/   # SQLAlchemy models & progress types
|   |   |-- services/ # Business logic (parser, orchestrator, export)
|   |   |-- core/     # Storage, config, database
|   |   `-- main.py   # FastAPI app entry
|   |-- tests/
|   |   |-- unit/     # Unit tests
|   |   |-- integration/  # Integration tests
|   |   `-- e2e/      # End-to-end tests
|   `-- requirements.txt
|-- frontend/         # React application
|   |-- src/
|   |   |-- components/ # React components
|   |   |-- pages/      # Page components
|   |   |-- hooks/      # Custom React hooks (WebSocket)
|   |   |-- services/   # API client
|   |   `-- lib/        # Utilities
|   `-- package.json
`-- docs/
    `-- plans/
```

## Getting Started

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env if needed (defaults to http://localhost:8000)

# Run development server
npm run dev
```

Frontend will be available at http://localhost:3000

### Testing

**Backend:**
```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm test -- --run
npm run type-check
```

## Usage Flow

1. **Upload** - Upload resume (PDF, DOCX, DOC, TXT) at http://localhost:3000
2. **Processing** - Watch real-time parsing progress via WebSocket
3. **Review** - Review extracted data with confidence scores, make corrections
4. **Share** - Create shareable links, export to PDF, or share via social media

## WebSocket Communication

**Connection:**
```
ws://localhost:8000/ws/resumes/{resume_id}
```

**Progress Update Message:**
```json
{
  "type": "progress_update",
  "stage": "text_extraction | nlp_parsing | ai_enhancement | complete",
  "progress": 50,
  "status": "Extracting text...",
  "estimated_seconds_remaining": 15
}
```

## Share and Export API

### Create Shareable Link

```http
POST /v1/resumes/{resume_id}/share
```

**Response:**
```json
{
  "share_token": "uuid-v4-token",
  "share_url": "http://localhost:3000/share/uuid-v4-token",
  "expires_at": "2026-03-20T12:00:00"
}
```

### Export Resume

**PDF:**
```http
GET /v1/resumes/{resume_id}/export/pdf
```
Returns PDF file with `Content-Type: application/pdf`

**WhatsApp:**
```http
GET /v1/resumes/{resume_id}/export/whatsapp
```
```json
{
  "whatsapp_url": "https://wa.me/?text=..."
}
```

**Telegram:**
```http
GET /v1/resumes/{resume_id}/export/telegram
```
```json
{
  "telegram_url": "https://t.me/share/url?url=&text=..."
}
```

**Email:**
```http
GET /v1/resumes/{resume_id}/export/email
```
```json
{
  "mailto_url": "mailto:?subject=...&body=..."
}
```

### Public Share Access

```http
GET /v1/share/{share_token}
```

Returns resume data without authentication. Status codes:
- `200` - Success
- `403` - Share has been revoked
- `404` - Share not found
- `410` - Share has expired

### Revoke Share

```http
DELETE /v1/resumes/{resume_id}/share
```

**Response:**
```json
{
  "message": "Share revoked successfully",
  "resume_id": "resume-id"
}
```

## Environment Variables

**Backend (.env):**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection for Celery
- `OPENAI_API_KEY` - OpenAI API key (optional)
- `SECRET_KEY` - Secret key for signing
- `ALLOWED_ORIGINS` - CORS allowed origins

**Frontend (.env):**
- `VITE_API_BASE_URL` - Backend API base URL
- `VITE_WS_BASE_URL` - WebSocket base URL

## Test Results

### Backend Tests: 120/120 Passing
- Unit tests: 67 tests
- Integration tests: 50 tests
- E2E tests: 4 tests

### Frontend Tests: 31/31 Passing
- Component tests: 31 tests
- Type check: Passed (TypeScript strict mode)

## License

MIT
