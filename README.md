# ResuMate - Smart Resume Parser

An intelligent resume parsing platform that extracts structured data from resumes using OCR, NLP, and AI.

## Tech Stack

- **Backend:** FastAPI (Python 3.11+) with WebSocket support
- **Frontend:** React 18+ with TypeScript and WebSocket hooks
- **Database:** PostgreSQL with JSONB
- **AI/ML:** Tesseract OCR, spaCy NLP, OpenAI GPT-4
- **Deployment:** Railway (backend), Vercel (frontend)

## Features

- Multi-format support (PDF, DOCX, DOC, TXT)
- Real-time parsing progress via WebSocket
- NLP-based entity extraction
- Confidence scoring
- AI enhancement (coming soon)
- Review & edit capabilities (coming soon)
- Share & export (coming soon)

## Project Structure

```
resume-parser/
|-- backend/          # FastAPI application
|   |-- app/
|   |   |-- api/      # API routes & WebSocket handlers
|   |   |-- models/   # SQLAlchemy models & progress types
|   |   |-- services/ # Business logic (parser, orchestrator)
|   |   `-- main.py   # FastAPI app entry
|   |-- tests/
|   `-- requirements.txt
|-- frontend/         # React application
|   |-- src/
|   |   |-- components/ # React components
|   |   |-- pages/      # Page components
|   |   |-- hooks/      # Custom React hooks (WebSocket)
|   |   `-- lib/
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

WebSocket endpoint: `ws://localhost:8000/ws/resumes/{resume_id}`

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
python -m pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm test
npm run type-check
```

## Usage Flow

1. **Upload** - Upload resume (PDF, DOCX, DOC, TXT) at http://localhost:3000
2. **Processing** - Watch real-time parsing progress via WebSocket
3. **Review** - (Coming soon) Review extracted data with confidence scores
4. **Share** - (Coming soon) Export and share parsed data

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

## License

MIT
