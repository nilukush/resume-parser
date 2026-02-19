# ResuMate Design Document

**Product:** ResuMate - Smart Resume Parser
**Date:** 2026-02-19
**Status:** Approved
**Version:** 1.0

---

## Executive Summary

ResuMate is an intelligent resume parsing platform that extracts structured data from resume files (PDF, DOCX, DOC, TXT) using a multi-stage hybrid approach combining OCR, NLP, and AI. Users can upload resumes, review extracted information with confidence scoring, make corrections, and share the validated data across multiple platforms (Email, WhatsApp, Telegram, PDF).

**Business Problem:** Most career websites have inaccurate resume parsers that fail to extract information correctly, forcing users to manually re-enter data.

**Solution:** ResuMate provides accurate, intelligent resume extraction with human-in-the-loop validation, learning from corrections to continuously improve accuracy.

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│                    (React + TypeScript Frontend)                │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Vercel)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Upload Page  │  │ Review Page  │  │ Share Page   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Backend API Gateway (FastAPI)                   │
│                    (Railway/Render Deployment)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │ Parser  │    │ Database │    │ Storage  │
    │ Service │    │(Postgres)│    │  (S3)    │
    └─────────┘    └──────────┘    └──────────┘
```

### Technology Stack

**Frontend:**
- React 18+ with TypeScript
- Zustand for state management
- Tailwind CSS + shadcn/ui components
- React Hook Form + Zod validation
- Vercel deployment

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 ORM
- PostgreSQL 15+ database
- S3-compatible storage (Railway Volume)
- Celery + Redis for async processing
- Railway deployment

**AI/ML:**
- Tesseract OCR
- spaCy 3.7+ NLP
- OpenAI GPT-4 API (initially)
- Future: Fine-tuned open-source models (LLaMA, Mistral)

---

## Multi-Stage Hybrid Parser Pipeline

```
Resume Upload
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: Document Processing & Text Extraction              │
│ • File type detection (PDF, DOCX, DOC, TXT)                │
│ • OCR for scanned PDFs/images (Tesseract)                  │
│ • Text extraction: pdfplumber, python-docx                 │
│ Output: Raw text content                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: Initial Entity Extraction (NLP)                    │
│ • spaCy NER model for entities                             │
│ • Custom regex patterns for URLs, emails, phones           │
│ • Skills extraction using keyword matching                 │
│ Output: Structured entities with confidence scores         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: Intelligent Parsing & Validation (AI)             │
│ • GPT-4 API for intelligent parsing                        │
│ • Validate extracted information                           │
│ • Fill missing gaps, resolve ambiguities                   │
│ • Confidence scoring (0-100) for each field                │
│ Output: Complete structured resume data                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 4: Human Review & Feedback Loop                      │
│ • Display parsed data to user                              │
│ • Flag low-confidence fields (<80%) for review             │
│ • User confirms/corrects information                       │
│ • Store corrections as training data                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 5: Continuous Learning                               │
│ • Store feedback in training database                      │
│ • Periodic retraining of spaCy model                       │
│ • Fine-tune open-source LLMs                               │
│ • A/B test new models before deployment                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

**resumes** - File metadata and processing status
- id (UUID, PK)
- user_id (UUID, nullable for anonymous)
- original_filename, file_type, file_size_bytes
- file_hash (SHA-256 for deduplication)
- storage_path (S3 location)
- processing_status (pending/processing/completed/failed)
- confidence_score (overall 0-100)
- Timestamps: uploaded_at, processed_at, created_at, updated_at
- UNIQUE constraint on file_hash

**parsed_resume_data** - Structured parsed information (JSONB)
- id (UUID, PK)
- resume_id (FK to resumes)
- personal_info (JSONB): name, email, phone, location, URLs, summary
- work_experience (JSONB array): company, title, dates, description
- education (JSONB array): institution, degree, dates, GPA
- skills (JSONB): technical, soft_skills, languages, certifications
- confidence_scores (JSONB): per-section scores

**resume_corrections** - Training data from user feedback
- id (UUID, PK)
- resume_id (FK to resumes)
- field_path (e.g., "personal_info.email")
- original_value, corrected_value (JSONB)
- created_at timestamp

**resume_shares** - Sharing functionality
- id (UUID, PK)
- resume_id (FK to resumes)
- share_token (UUID-based, unique)
- access_count, expires_at, is_active
- created_at timestamp

---

## API Design

### Key Endpoints

**Resume Operations:**
- `POST /v1/resumes/upload` - Upload resume for parsing
- `GET /v1/resumes/{id}` - Get parsed resume data
- `GET /v1/resumes/{id}/status` - Check processing status
- `PATCH /v1/resumes/{id}` - Update parsed data (user corrections)
- `POST /v1/resumes/{id}/confirm` - Mark as verified, get share token

**Sharing:**
- `GET /v1/resumes/{id}/share` - Get or create share link
- `PATCH /v1/resumes/{id}/share` - Update share settings (expiration)
- `DELETE /v1/resumes/{id}/share` - Revoke share link
- `GET /v1/share/{token}` - Access shared resume (public)

**Export:**
- `GET /v1/resumes/{id}/export/pdf` - Download as PDF
- `POST /v1/resumes/{id}/export/email` - Email parsed data
- `GET /v1/resumes/{id}/export/whatsapp` - Generate WhatsApp link
- `GET /v1/resumes/{id}/export/telegram` - Generate Telegram link

**WebSocket:**
- `wss://api.resumate.app/ws/resumes/{id}` - Real-time progress updates

---

## User Interface Flow

### Page Structure

1. **Landing Page (/)**
   - Clean upload interface with drag-and-drop
   - Supported formats: PDF, DOCX, DOC, TXT
   - File size limit: 10MB

2. **Processing Page (/processing)**
   - Real-time progress updates via WebSocket
   - Stage-by-stage progress indicator
   - Estimated time remaining

3. **Review Page (/review/:id)**
   - Display parsed data in organized sections
   - Confidence indicators: ✓ (95%+), ⚠️ (80-94%), ❌ (<80%)
   - Low-confidence fields highlighted for review
   - Inline editing capabilities
   - Confirm/continue button

4. **Share Page (/share/:id)**
   - Shareable link with copy button
   - Expiration settings
   - Platform share buttons (Email, WhatsApp, Telegram)
   - PDF download
   - Live preview of parsed data

### Visual Design

- **Color Scheme:** Deep navy blues, gold accents, clean white backgrounds
- **Typography:** Modern sans-serif, generous whitespace
- **Feedback:** Visual confidence indicators, progress animations
- **Responsiveness:** Mobile-first design, works on all devices

---

## Security & Privacy

### Data Protection

- Encrypted storage at rest (AES-256)
- Automatic deletion after 90 days (user-adjustable)
- Share token revocation anytime
- No search engine indexing of share pages
- No AI training on user data without consent

### API Security

- HTTPS-only communication
- CORS restricted to resumate.app domains
- File type whitelist (PDF, DOCX, DOC, TXT)
- MIME type verification
- Virus scanning (ClamAV)
- Rate limiting: 50 uploads/day per IP, 100/day per email
- SQL injection prevention via ORM
- XSS prevention via React auto-escaping

### GDPR Compliance

- Right to access (export all data)
- Right to deletion (immediate)
- Right to portability (JSON/PDF download)
- Clear privacy policy
- Essential cookies only (marketing optional)

---

## Error Handling

### File Upload Errors

- Unsupported file type
- File too large (>10MB)
- Corrupted file
- Password-protected files

### Parsing Errors

- OCR failed (low quality scans)
- No text found (image-only documents)
- Low confidence overall
- AI API timeout/fallback to NLP-only

### System Errors

- Rate limit exceeded
- Storage unavailable
- Database connection lost

### Feedback Loop

User corrections are logged, analyzed for patterns, and used to:
- Flag model retraining needs
- Adjust regex patterns
- Fine-tune NLP models
- Improve confidence thresholds

---

## Development Roadmap

### Phase 1: Core Parser (2-3 weeks)
- Basic file upload (PDF, DOCX, TXT)
- Text extraction (pdfplumber, python-docx)
- Basic NLP parsing (spaCy)
- Simple confidence scoring
- Minimal UI (upload → results)
- PostgreSQL setup

**Deliverable:** Working parser extracting name, email, phone, basic experience/education/skills

### Phase 2: AI Enhancement (2 weeks)
- Integrate GPT-4 API
- Advanced confidence scoring per field
- OCR for scanned PDFs (Tesseract)
- Review page with edit capabilities
- User correction system
- Training data collection

**Deliverable:** Significantly improved accuracy (70% → 90%+), human-in-the-loop feedback

### Phase 3: Sharing & Export (1-2 weeks)
- Share tokens with expiration
- WhatsApp, Telegram, Email export
- PDF generation
- Public share page
- Access tracking

**Deliverable:** Complete sharing flow across all major platforms

### Phase 4: Polish & Production (1 week)
- Royal elegant UI (final design)
- Comprehensive error handling
- Security hardening
- Performance optimization
- Monitoring & logging (Sentry)
- Documentation

**Deliverable:** Production-ready application deployed to Vercel + Railway

**Total Timeline:** 6-8 weeks to production MVP

---

## Success Criteria

- **Accuracy:** 90%+ correct extraction on standard resumes
- **User Satisfaction:** <5% correction rate after Phase 2
- **Performance:** <30 second average processing time
- **Reliability:** 99% uptime in production
- **Privacy:** 100% GDPR compliance from day 1

---

## Appendix: Technology Justification

### Why FastAPI + React?

- **FastAPI:** Modern, fast, automatic API docs, async support, great for production
- **React:** Type safety with TypeScript, huge ecosystem, elegant UI components
- **Python:** Best-in-class AI/ML libraries (spaCy, pdfplumber, transformers)
- **PostgreSQL:** JSONB flexibility for variable resume structures
- **Vercel + Railway:** Fastest time to production, automatic scaling, free tiers for MVP

### Why Multi-Stage Hybrid Parser?

1. **Best accuracy:** Combines OCR + NLP + AI strengths
2. **Learns from feedback:** Continuous improvement over time
3. **Handles any format:** Flexible pipeline for complex layouts
4. **Cost-effective:** After initial setup, marginal cost per resume is low
5. **Competitive advantage:** Unique IP vs generic APIs

---

**Document Status:** ✅ Approved
**Next Step:** Create detailed implementation plan with TDD steps
