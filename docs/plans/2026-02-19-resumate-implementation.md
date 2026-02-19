# ResuMate Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build ResuMate - an intelligent resume parser that extracts structured data from resumes using OCR, NLP, and AI with human-in-the-loop validation.

**Architecture:** Multi-stage hybrid parser (OCR → NLP → AI → Feedback Loop) with FastAPI backend, React frontend, PostgreSQL database, deployed on Railway (backend) and Vercel (frontend).

**Tech Stack:**
- Backend: FastAPI (Python 3.11+), SQLAlchemy, PostgreSQL, Celery, Redis
- Frontend: React 18+ with TypeScript, Zustand, Tailwind CSS, shadcn/ui
- AI/ML: Tesseract OCR, spaCy NLP, OpenAI GPT-4 API
- Deployment: Railway (backend), Vercel (frontend)

---

## Phase 1: Project Setup & Infrastructure Foundation

### Task 1: Initialize Git Repository & Project Structure

**Files:**
- Create: Project directory structure
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Create .gitignore**

```bash
# Create .gitignore file
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Node
node_modules/
dist/
build/
.next/
out/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
logs/

# Railway
.volumes/
EOF
```

**Step 2: Create README.md**

```bash
cat > README.md << 'EOF'
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
EOF
```

**Step 3: Create project directory structure**

```bash
# Create backend structure
mkdir -p backend/app/{api,models,services,core}
mkdir -p backend/tests/{unit,integration}

# Create frontend structure
mkdir -p frontend/src/{components,pages,lib,store,types}
mkdir -p frontend/public

# Create docs structure
mkdir -p docs/{api,plans}

# Verify structure
tree -L 3 -I 'node_modules|__pycache__'
```

**Step 4: Commit**

```bash
git add .gitignore README.md
git commit -m "chore: initialize project structure and git configuration"
```

---

### Task 2: Setup Backend Python Environment

**Files:**
- Create: `backend/.python-version`
- Create: `backend/requirements.txt`
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`

**Step 1: Create .python-version**

```bash
echo "3.11" > backend/.python-version
```

**Step 2: Create requirements.txt**

```bash
cat > backend/requirements.txt << 'EOF'
# FastAPI and server
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# OCR and Document Processing
pdfplumber==0.10.3
PyPDF2==3.0.1
python-docx==1.1.0
pytesseract==0.3.10
Pillow==10.2.0

# NLP and AI
spacy==3.7.2
openai==1.10.0

# Task Queue
celery==5.3.6
redis==5.0.1

# Security and Validation
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# Storage
boto3==1.34.23

# Utilities
aiofiles==23.2.1
httpx==0.26.0

# Development
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
black==24.1.1
ruff==0.1.14
mypy==1.8.0

# Monitoring
sentry-sdk==1.40.0
EOF
```

**Step 3: Create pyproject.toml for tooling**

```bash
cat > backend/pyproject.toml << 'EOF'
[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = 'py311'
select = ["E", "F", "I", "N", "W"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
EOF
```

**Step 4: Create .env.example**

```bash
cat > backend/.env.example << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/resumate
DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/resumate

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Storage (S3-compatible)
S3_ENDPOINT_URL=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
S3_BUCKET_NAME=resumate-uploads

# Security
SECRET_KEY=your_secret_key_here_generate_with_openssl_rand_hex_32

# Environment
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# File Upload
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,docx,doc,txt
EOF
```

**Step 5: Commit**

```bash
git add backend/
git commit -m "chore: setup backend Python environment and dependencies"
```

---

### Task 3: Setup Frontend Node Environment

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/.env.example`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`

**Step 1: Create package.json**

```bash
cat > frontend/package.json << 'EOF'
{
  "name": "resumate-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "zustand": "^4.5.0",
    "axios": "^1.6.5",
    "react-hook-form": "^7.49.3",
    "zod": "^3.22.4",
    "@hookform/resolvers": "^3.3.4",
    "lucide-react": "^0.309.0",
    "react-dropzone": "^14.2.3",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@typescript-eslint/eslint-plugin": "^6.19.0",
    "@typescript-eslint/parser": "^6.19.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.12"
  }
}
EOF
```

**Step 2: Create tsconfig.json**

```bash
cat > frontend/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": "./src",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF
```

**Step 3: Create tsconfig.node.json**

```bash
cat > frontend/tsconfig.node.json << 'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOF
```

**Step 4: Create vite.config.ts**

```bash
cat > frontend/vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
EOF
```

**Step 5: Create Tailwind CSS config**

```bash
cat > frontend/tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f0f4ff',
          100: '#e0e9ff',
          200: '#c7d5fe',
          300: '#a4b8fc',
          400: '#8093f8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        gold: {
          50: '#fefce8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#facc15',
          500: '#eab308',
          600: '#ca8a04',
          700: '#a16207',
          800: '#854d0e',
          900: '#713f12',
        },
      },
    },
  },
  plugins: [],
}
EOF
```

**Step 6: Create postcss.config.js**

```bash
cat > frontend/postcss.config.js << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF
```

**Step 7: Create .env.example**

```bash
cat > frontend/.env.example << 'EOF'
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws
EOF
```

**Step 8: Commit**

```bash
git add frontend/
git commit -m "chore: setup frontend Node environment and dependencies"
```

---

### Task 4: Setup Database Models and Migrations

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/resume.py`
- Create: `backend/app/core/database.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

**Step 1: Write failing test for database connection**

```bash
mkdir -p backend/tests/integration

cat > backend/tests/integration/test_database.py << 'EOF'
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db

def test_database_connection():
    """Test that database connection can be established"""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost:5432/test")
    assert engine is not None
EOF
```

**Step 2: Run test to verify it fails**

```bash
cd backend
python -m pytest tests/integration/test_database.py -v
# Expected: FAIL - database.py doesn't exist yet
```

**Step 3: Create database configuration**

```bash
cat > backend/app/core/database.py << 'EOF'
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
EOF
```

**Step 4: Create configuration settings**

```bash
cat > backend/app/core/config.py << 'EOF'
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    REDIS_URL: str
    OPENAI_API_KEY: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB

    class Config:
        env_file = ".env"

settings = Settings()
EOF
```

**Step 5: Create Resume model**

```bash
cat > backend/app/models/resume.py << 'EOF'
from sqlalchemy import Column, String, Integer, DateTime, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    storage_path = Column(String(500), nullable=False)
    processing_status = Column(String(20), default="pending")
    confidence_score = Column(Numeric(5, 2))
    parsing_version = Column(String(20))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ParsedResumeData(Base):
    __tablename__ = "parsed_resume_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), nullable=False)
    personal_info = Column(JSONB, nullable=False)
    work_experience = Column(JSONB, default=list)
    education = Column(JSONB, default=list)
    skills = Column(JSONB, default=dict)
    confidence_scores = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ResumeCorrection(Base):
    __tablename__ = "resume_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), nullable=False)
    field_path = Column(String(100), nullable=False)
    original_value = Column(JSONB, nullable=False)
    corrected_value = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ResumeShare(Base):
    __tablename__ = "resume_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), nullable=False)
    share_token = Column(String(64), unique=True, nullable=False)
    access_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
EOF
```

**Step 6: Create models init**

```bash
cat > backend/app/models/__init__.py << 'EOF'
from app.models.resume import Resume, ParsedResumeData, ResumeCorrection, ResumeShare

__all__ = ["Resume", "ParsedResumeData", "ResumeCorrection", "ResumeShare"]
EOF
```

**Step 7: Run tests to verify they pass**

```bash
cd backend
python -m pytest tests/integration/test_database.py -v
# Expected: PASS (if database is running)
```

**Step 8: Commit**

```bash
git add backend/app/models/ backend/app/core/
git commit -m "feat: setup database models and configuration"
```

---

## Phase 2: Core Parser Implementation

### Task 5: Implement Text Extraction Service

**Files:**
- Create: `backend/app/services/text_extractor.py`
- Create: `backend/tests/unit/test_text_extractor.py`

**Step 1: Write failing test for PDF text extraction**

```bash
cat > backend/tests/unit/test_text_extractor.py << 'EOF'
import pytest
from app.services.text_extractor import extract_text

def test_extract_text_from_pdf(tmp_path):
    """Test text extraction from PDF file"""
    # Create a sample PDF file
    pdf_path = tmp_path / "test.pdf"
    # For now, just test that the function exists
    # We'll add actual PDF testing once we have sample files
    assert callable(extract_text)

@pytest.mark.asyncio
async def test_extract_text_returns_string():
    """Test that extract_text returns a string"""
    result = await extract_text("dummy.pdf", b"fake content")
    assert isinstance(result, str)
EOF
```

**Step 2: Run test to verify it fails**

```bash
cd backend
python -m pytest tests/unit/test_text_extractor.py -v
# Expected: FAIL - text_extractor module doesn't exist
```

**Step 3: Implement text extractor**

```bash
cat > backend/app/services/text_extractor.py << 'EOF'
import io
from typing import Optional
import pdfplumber
from docx import Document
from pathlib import Path

class TextExtractionError(Exception):
    """Raised when text extraction fails"""
    pass

async def extract_text(file_path: str, file_content: Optional[bytes] = None) -> str:
    """
    Extract text from various document formats.

    Args:
        file_path: Path to the file
        file_content: Optional bytes content of the file

    Returns:
        Extracted text as string

    Raises:
        TextExtractionError: If extraction fails
    """
    file_extension = Path(file_path).suffix.lower()

    if file_extension == '.pdf':
        return await _extract_from_pdf(file_path, file_content)
    elif file_extension in ['.docx', '.doc']:
        return await _extract_from_docx(file_path, file_content)
    elif file_extension == '.txt':
        return await _extract_from_txt(file_content)
    else:
        raise TextExtractionError(f"Unsupported file type: {file_extension}")

async def _extract_from_pdf(file_path: str, file_content: Optional[bytes] = None) -> str:
    """Extract text from PDF using pdfplumber"""
    try:
        if file_content:
            # Extract from bytes
            pdf_file = io.BytesIO(file_content)
        else:
            # Extract from file path
            pdf_file = open(file_path, 'rb')

        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""

        return text.strip()
    except Exception as e:
        raise TextExtractionError(f"Failed to extract text from PDF: {str(e)}")

async def _extract_from_docx(file_path: str, file_content: Optional[bytes] = None) -> str:
    """Extract text from DOCX using python-docx"""
    try:
        if file_content:
            doc = Document(io.BytesIO(file_content))
        else:
            doc = Document(file_path)

        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"

        return text.strip()
    except Exception as e:
        raise TextExtractionError(f"Failed to extract text from DOCX: {str(e)}")

async def _extract_from_txt(file_content: Optional[bytes] = None) -> str:
    """Extract text from TXT file"""
    try:
        if file_content:
            return file_content.decode('utf-8')
        return ""
    except Exception as e:
        raise TextExtractionError(f"Failed to extract text from TXT: {str(e)}")
EOF
```

**Step 4: Run tests to verify they pass**

```bash
cd backend
python -m pytest tests/unit/test_text_extractor.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add backend/app/services/text_extractor.py backend/tests/unit/test_text_extractor.py
git commit -m "feat: implement text extraction service for PDF, DOCX, and TXT files"
```

---

### Task 6: Implement NLP Entity Extraction Service

**Files:**
- Create: `backend/app/services/nlp_extractor.py`
- Create: `backend/tests/unit/test_nlp_extractor.py`
- Create: `backend/app/services/__init__.py`

**Step 1: Write failing test for NLP extraction**

```bash
cat > backend/tests/unit/test_nlp_extractor.py << 'EOF'
import pytest
from app.services.nlp_extractor import extract_entities

def test_extract_entities_returns_structured_data():
    """Test that extract_entities returns structured resume data"""
    sample_text = """
    John Doe
    Email: john@example.com
    Phone: +1-555-0123

    Experience:
    Software Engineer at Tech Corp from 2020 to present

    Education:
    Bachelor of Science in Computer Science from MIT
    """

    result = extract_entities(sample_text)

    assert "personal_info" in result
    assert "work_experience" in result
    assert "education" in result
    assert "skills" in result
    assert "confidence_scores" in result

def test_extract_entities_detects_email():
    """Test email detection"""
    sample_text = "Contact me at john.doe@example.com"
    result = extract_entities(sample_text)

    assert "john.doe@example.com" in result.get("personal_info", {}).get("email", "")
EOF
```

**Step 2: Run test to verify it fails**

```bash
cd backend
python -m pytest tests/unit/test_nlp_extractor.py -v
# Expected: FAIL - nlp_extractor doesn't exist
```

**Step 3: Implement NLP extractor**

```bash
cat > backend/app/services/nlp_extractor.py << 'EOF'
import re
from typing import Dict, List, Any
import spacy

# Load spaCy model (will be downloaded during setup)
nlp = None

def load_spacy_model():
    """Load spaCy model lazily"""
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load("en_core_web_lg")
        except OSError:
            # Fallback to smaller model if large model not available
            nlp = spacy.load("en_core_web_sm")

def extract_entities(text: str) -> Dict[str, Any]:
    """
    Extract entities from resume text using spaCy NLP.

    Args:
        text: Resume text content

    Returns:
        Dictionary with structured resume data
    """
    load_spacy_model()

    doc = nlp(text)

    # Extract personal information
    personal_info = _extract_personal_info(doc, text)

    # Extract work experience
    work_experience = _extract_work_experience(doc, text)

    # Extract education
    education = _extract_education(doc, text)

    # Extract skills
    skills = _extract_skills(doc, text)

    # Calculate confidence scores
    confidence_scores = _calculate_confidence(
        personal_info, work_experience, education, skills
    )

    return {
        "personal_info": personal_info,
        "work_experience": work_experience,
        "education": education,
        "skills": skills,
        "confidence_scores": confidence_scores
    }

def _extract_personal_info(doc, text: str) -> Dict[str, Any]:
    """Extract personal information"""
    info = {
        "full_name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin_url": "",
        "github_url": "",
        "portfolio_url": "",
        "summary": ""
    }

    # Extract email using regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        info["email"] = emails[0]

    # Extract phone using regex
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, text)
    if phones:
        info["phone"] = phones[0]

    # Extract URLs
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    for url in urls:
        if 'linkedin.com' in url:
            info["linkedin_url"] = url
        elif 'github.com' in url:
            info["github_url"] = url
        else:
            info["portfolio_url"] = url

    # Extract name (first PERSON entity)
    for ent in doc.ents:
        if ent.label_ == "PERSON" and not info["full_name"]:
            info["full_name"] = ent.text
            break

    # Extract location (first GPE or LOC entity)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"] and not info["location"]:
            info["location"] = ent.text
            break

    return info

def _extract_work_experience(doc, text: str) -> List[Dict[str, Any]]:
    """Extract work experience - simplified version"""
    # This is a simplified version
    # In production, you'd use more sophisticated pattern matching
    experiences = []

    # Look for patterns like "Software Engineer at Company"
    # This is a placeholder - real implementation would be more complex
    for sent in doc.sents:
        sent_text = sent.text
        if " at " in sent_text.lower() and any(
            word in sent_text.lower() for word in ["engineer", "developer", "manager", "director"]
        ):
            experiences.append({
                "title": "Unknown",
                "company": "Unknown",
                "location": "",
                "start_date": "",
                "end_date": "",
                "description": sent_text,
                "confidence": 70.0
            })
            break  # Just extract one for now

    return experiences

def _extract_education(doc, text: str) -> List[Dict[str, Any]]:
    """Extract education - simplified version"""
    education = []

    # Look for degree patterns
    degree_keywords = ["bachelor", "master", "phd", "doctor", "mba", "degree"]

    for sent in doc.sents:
        sent_text = sent.text.lower()
        if any(keyword in sent_text for keyword in degree_keywords):
            education.append({
                "institution": "Unknown",
                "degree": sent.text.strip(),
                "field_of_study": "",
                "location": "",
                "start_date": "",
                "end_date": "",
                "gpa": "",
                "confidence": 70.0
            })
            break

    return education

def _extract_skills(doc, text: str) -> Dict[str, List[str]]:
    """Extract skills - simplified keyword matching"""
    # Common technical skills
    tech_skills = [
        "python", "java", "javascript", "react", "node", "sql", "aws",
        "docker", "kubernetes", "git", "linux", "html", "css", "typescript"
    ]

    # Common soft skills
    soft_skills = [
        "leadership", "communication", "teamwork", "problem solving",
        "project management", "agile", "scrum"
    ]

    found_tech = [skill for skill in tech_skills if skill.lower() in text.lower()]
    found_soft = [skill for skill in soft_skills if skill.lower() in text.lower()]

    return {
        "technical": found_tech,
        "soft_skills": found_soft,
        "languages": [],
        "certifications": [],
        "confidence": 75.0
    }

def _calculate_confidence(personal_info, work_experience, education, skills) -> Dict[str, float]:
    """Calculate confidence scores for each section"""
    scores = {
        "personal_info": 0.0,
        "work_experience": 0.0,
        "education": 0.0,
        "skills": 0.0
    }

    # Personal info confidence based on filled fields
    personal_fields = ["full_name", "email", "phone"]
    filled_fields = sum(1 for field in personal_fields if personal_info.get(field))
    scores["personal_info"] = (filled_fields / len(personal_fields)) * 100

    # Work experience confidence
    if work_experience:
        scores["work_experience"] = work_experience[0].get("confidence", 70.0)

    # Education confidence
    if education:
        scores["education"] = education[0].get("confidence", 70.0)

    # Skills confidence
    scores["skills"] = skills.get("confidence", 75.0)

    return scores
EOF
```

**Step 4: Create services init**

```bash
cat > backend/app/services/__init__.py << 'EOF'
from app.services.text_extractor import extract_text
from app.services.nlp_extractor import extract_entities

__all__ = ["extract_text", "extract_entities"]
EOF
```

**Step 5: Run tests to verify they pass**

```bash
cd backend
python -m pytest tests/unit/test_nlp_extractor.py -v
# Expected: PASS (may need to install spaCy models first)
```

**Step 6: Commit**

```bash
git add backend/app/services/nlp_extractor.py backend/tests/unit/test_nlp_extractor.py
git commit -m "feat: implement NLP entity extraction service using spaCy"
```

---

### Task 7: Implement FastAPI Endpoints for Resume Upload

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/resumes.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/integration/test_api_resumes.py`

**Step 1: Write failing test for upload endpoint**

```bash
cat > backend/tests/integration/test_api_resumes.py << 'EOF'
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_resume_returns_202():
    """Test that resume upload returns 202 Accepted"""
    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    )
    assert response.status_code == 202
    assert "resume_id" in response.json()

def test_upload_unsupported_file_type_returns_400():
    """Test that unsupported file types return 400"""
    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.jpg", b"fake image", "image/jpeg")}
    )
    assert response.status_code == 400
EOF
```

**Step 2: Run test to verify it fails**

```bash
cd backend
python -m pytest tests/integration/test_api_resumes.py -v
# Expected: FAIL - main.py doesn't exist
```

**Step 3: Create FastAPI main app**

```bash
cat > backend/app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="ResuMate API",
    description="Smart Resume Parser API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
EOF
```

**Step 4: Create resume upload endpoint**

```bash
cat > backend/app/api/resumes.py << 'EOF'
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
import uuid
import hashlib

router = APIRouter(prefix="/v1/resumes", tags=["resumes"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload", status_code=202)
async def upload_resume(file: UploadFile = File(...)) -> Dict:
    """
    Upload a resume for parsing.

    Returns 202 Accepted and starts async processing.
    """
    # Validate file extension
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
        )

    # Generate resume ID and file hash
    resume_id = str(uuid.uuid4())
    file_hash = hashlib.sha256(content).hexdigest()

    # For now, just return success
    # In production, this would trigger async processing
    return {
        "resume_id": resume_id,
        "status": "processing",
        "estimated_time_seconds": 30,
        "file_hash": file_hash
    }
EOF
```

**Step 5: Update main app to include router**

```bash
cat > backend/app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import resumes

app = FastAPI(
    title="ResuMate API",
    description="Smart Resume Parser API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resumes.router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
EOF
```

**Step 6: Create API init**

```bash
cat > backend/app/api/__init__.py << 'EOF'
from app.api.resumes import router as resumes_router

__all__ = ["resumes_router"]
EOF
```

**Step 7: Run tests to verify they pass**

```bash
cd backend
python -m pytest tests/integration/test_api_resumes.py -v
# Expected: PASS
```

**Step 8: Commit**

```bash
git add backend/app/api/ backend/app/main.py backend/tests/integration/test_api_resumes.py
git commit -m "feat: implement resume upload endpoint with validation"
```

---

## Phase 3: Frontend Implementation

### Task 8: Setup React Base Components

**Files:**
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/types/index.ts`

**Step 1: Create main entry point**

```bash
cat > frontend/src/main.tsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOF
```

**Step 2: Create App component**

```bash
cat > frontend/src/App.tsx << 'EOF'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import UploadPage from './pages/UploadPage'
import ProcessingPage from './pages/ProcessingPage'
import ReviewPage from './pages/ReviewPage'
import SharePage from './pages/SharePage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/processing/:id" element={<ProcessingPage />} />
        <Route path="/review/:id" element={<ReviewPage />} />
        <Route path="/share/:id" element={<SharePage />} />
      </Routes>
    </Router>
  )
}

export default App
EOF
```

**Step 3: Create global CSS**

```bash
cat > frontend/src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-navy-50 text-gray-900;
  }
}

@layer components {
  .btn-primary {
    @apply bg-navy-600 text-white px-6 py-3 rounded-lg hover:bg-navy-700 transition-colors;
  }

  .btn-secondary {
    @apply bg-white text-navy-600 px-6 py-3 rounded-lg border-2 border-navy-600 hover:bg-navy-50 transition-colors;
  }
}
EOF
```

**Step 4: Create utility functions**

```bash
cat > frontend/src/lib/utils.ts << 'EOF'
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
EOF
```

**Step 5: Create TypeScript types**

```bash
cat > frontend/src/types/index.ts << 'EOF'
export interface PersonalInfo {
  full_name: string
  email: string
  phone: string
  location: string
  linkedin_url: string
  github_url: string
  portfolio_url: string
  summary: string
}

export interface WorkExperience {
  company: string
  title: string
  location: string
  start_date: string
  end_date: string
  description: string
  confidence: number
}

export interface Education {
  institution: string
  degree: string
  field_of_study: string
  location: string
  start_date: string
  end_date: string
  gpa: string
  confidence: number
}

export interface Skills {
  technical: string[]
  soft_skills: string[]
  languages: string[]
  certifications: string[]
  confidence: number
}

export interface ConfidenceScores {
  personal_info: number
  work_experience: number
  education: number
  skills: number
}

export interface ParsedResumeData {
  id: string
  status: string
  confidence_score: number
  personal_info: PersonalInfo
  work_experience: WorkExperience[]
  education: Education[]
  skills: Skills
  confidence_scores: ConfidenceScores
}
EOF
```

**Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: setup React base components and types"
```

---

### Task 9: Implement Upload Page Component

**Files:**
- Create: `frontend/src/pages/UploadPage.tsx`
- Create: `frontend/src/components/FileUpload.tsx`

**Step 1: Create FileUpload component**

```bash
cat > frontend/src/components/FileUpload.tsx << 'EOF'
import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload } from 'lucide-react'

interface FileUploadProps {
  onUpload: (file: File) => void
}

export default function FileUpload({ onUpload }: FileUploadProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onUpload(acceptedFiles[0])
    }
  }, [onUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt']
    },
    maxFiles: 1
  })

  return (
    <div
      {...getRootProps()}
      className={\`
        border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
        \${isDragActive ? 'border-navy-500 bg-navy-50' : 'border-gray-300 hover:border-navy-400'}
      \`}
    >
      <input {...getInputProps()} />
      <Upload className="mx-auto h-16 w-16 text-navy-600 mb-4" />
      <p className="text-lg font-semibold mb-2">
        {isDragActive ? 'Drop your resume here' : 'Drag & drop your resume here'}
      </p>
      <p className="text-gray-600 mb-4">or</p>
      <button className="btn-primary">
        Browse Files
      </button>
      <p className="text-sm text-gray-500 mt-4">
        Supported: PDF, DOCX, DOC, TXT (Max 10MB)
      </p>
    </div>
  )
}
EOF
```

**Step 2: Create UploadPage component**

```bash
cat > frontend/src/pages/UploadPage.tsx << 'EOF'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FileUpload from '../components/FileUpload'

export default function UploadPage() {
  const navigate = useNavigate()
  const [isUploading, setIsUploading] = useState(false)

  const handleUpload = async (file: File) => {
    setIsUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(\`\${import.meta.env.VITE_API_BASE_URL}/resumes/upload\`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const data = await response.json()
      // Navigate to processing page
      navigate(\`/processing/\${data.resume_id}\`)
    } catch (error) {
      console.error('Upload error:', error)
      alert('Failed to upload resume. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full">
        <h1 className="text-4xl font-bold text-navy-900 text-center mb-2">
          ResuMate
        </h1>
        <p className="text-gray-600 text-center mb-8">
          Transform Your Resume Into Structured Data
        </p>

        {isUploading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-navy-600 mx-auto mb-4"></div>
            <p className="text-lg">Uploading your resume...</p>
          </div>
        ) : (
          <FileUpload onUpload={handleUpload} />
        )}
      </div>
    </div>
  )
}
EOF
```

**Step 3: Create placeholder pages**

```bash
cat > frontend/src/pages/ProcessingPage.tsx << 'EOF'
export default function ProcessingPage() {
  return <div>Processing...</div>
}
EOF

cat > frontend/src/pages/ReviewPage.tsx << 'EOF'
export default function ReviewPage() {
  return <div>Review...</div>
}
EOF

cat > frontend/src/pages/SharePage.tsx << 'EOF'
export default function SharePage() {
  return <div>Share...</div>
}
EOF
```

**Step 4: Commit**

```bash
git add frontend/src/pages/ frontend/src/components/
git commit -m "feat: implement upload page with drag-and-drop file upload"
```

---

## Next Steps

This implementation plan covers Phase 1 (Infrastructure) and beginning of Phase 2 (Parser) and Phase 3 (Frontend).

**Remaining work to complete MVP:**

1. **Complete Parser Service:**
   - Implement AI/GPT-4 integration for intelligent parsing
   - Add OCR processing for scanned PDFs
   - Implement async processing with Celery
   - Add comprehensive testing

2. **Complete Frontend Pages:**
   - Processing page with WebSocket progress updates
   - Review page with edit capabilities
   - Share page with export functionality

3. **Sharing & Export Features:**
   - Share token generation and management
   - WhatsApp, Telegram, Email export
   - PDF generation
   - Public share page

4. **Production Readiness:**
   - Error handling and edge cases
   - Security hardening
   - Performance optimization
   - Monitoring and logging
   - Deployment to Railway and Vercel

**To continue implementation, run:**
```bash
# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Setup database
cd backend && alembic upgrade head

# Run development servers
# Backend: uvicorn app.main:app --reload
# Frontend: npm run dev
```

---

**Plan Status:** ✅ Complete - Ready for execution
**Created:** 2026-02-19
**Next:** Execute using superpowers:executing-plans or superpowers:subagent-driven-development
