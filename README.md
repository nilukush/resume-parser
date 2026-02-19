# ResuMate - Smart Resume Parser

An intelligent resume parsing platform that extracts structured data from resumes using OCR, NLP, and AI.

## Tech Stack

- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** React 18+ with TypeScript
- **Database:** PostgreSQL with JSONB
- **AI/ML:** Tesseract OCR, spaCy NLP, OpenAI GPT-4
- **Deployment:** Railway (backend), Vercel (frontend)

## Project Structure

```
resume-parser/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── models/   # SQLAlchemy models
│   │   ├── services/ # Business logic (parser, etc.)
│   │   └── main.py   # FastAPI app entry
│   ├── tests/
│   └── requirements.txt
├── frontend/         # React application
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── lib/
│   └── package.json
└── docs/
    └── plans/
```

## Getting Started

See [Backend Setup](./backend/README.md) and [Frontend Setup](./frontend/README.md)

## License

MIT
