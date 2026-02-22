# ResuMate Implementation Plan: Tasks 34-40

## Production Readiness & Scalability Enhancement

**Date:** 2026-02-21
**Status:** Planning Phase
**Methodology:** TDD (Test-Driven Development)

---

## PART 1: HIGH-LEVEL ANALYSIS

### 1. Business Problem Definition

**Current State:**
ResuMate MVP is complete with all core features working:

- Resume parsing (OCR → NLP → AI Enhancement)
- Real-time WebSocket progress updates
- Review and edit functionality
- Share and export capabilities
- In-memory storage (sufficient for development/testing)

**Problem:**
The current implementation is not production-ready due to:

1. **Scalability Limitation**: In-memory storage means data loss on server restart
2. **Performance Bottleneck**: Synchronous processing blocks requests during heavy parsing
3. **Missing Observability**: No monitoring or logging for production issues
4. **Deployment Gaps**: No CI/CD or production infrastructure configured

**Success Criteria:**

- ✅ Persistent database storage with PostgreSQL
- ✅ Asynchronous task processing with Celery + Redis
- ✅ Production deployment on Railway (backend) and Vercel (frontend)
- ✅ Comprehensive monitoring and logging
- ✅ Complete documentation for operations
- ✅ Zero data loss during deployments
- ✅ System handles 100+ concurrent users

### 2. Codebase Investigation Summary

**Existing Infrastructure:**

- **Backend:** FastAPI 0.109.0, Python 3.11, 136 passing tests
- **Frontend:** React 18, TypeScript, Vite, 52 passing tests
- **Services:**
  - `text_extractor.py` - PDF/DOCX/DOC/TXT extraction with OCR fallback
  - `nlp_extractor.py` - spaCy-based entity extraction
  - `ocr_extractor.py` - Tesseract OCR for scanned PDFs
  - `ai_extractor.py` - GPT-4o-mini enhancement
  - `parser_orchestrator.py` - Coordinates parsing pipeline
  - `export_service.py` - PDF/WhatsApp/Telegram/Email export

**Current Storage:**

- `backend/app/core/storage.py` - In-memory resume storage
- `backend/app/core/share_storage.py` - In-memory share token storage

**Database Models Defined but Not Used:**

- `backend/app/models/resume.py` - SQLAlchemy models (Resume, ParsedResumeData, ResumeCorrection, ResumeShare)
- `backend/app/core/database.py` - Async SQLAlchemy setup

**Current Limitations:**

1. No async task queue (parsing happens synchronously)
2. No database migrations (models defined but not used)
3. No production deployment configuration
4. No monitoring/error tracking setup
5. User feedback not captured for AI improvement

### 3. Technical Approach Evaluation

#### Approach A: Incremental Migration (RECOMMENDED)

**Strategy:**

- Implement each system independently with feature flags
- Keep in-memory storage as fallback during transition
- Deploy to staging environment first
- Roll back features individually if issues arise

**Benefits:**

- ✅ Lower risk - can roll back individual features
- ✅ Continuous deployment possible
- ✅ Easier to debug issues in isolation
- ✅ Testing can happen incrementally

**Trade-offs:**

- ⚠️ Longer implementation timeline
- ⚠️ More complex codebase during transition
- ⚠️ Requires feature flag management

**Implementation Order:**

1. Database persistence (Tasks 38-39)
2. Celery async processing (Tasks 35-36)
3. Production deployment (Task 37)
4. User feedback system (Task 34)
5. Monitoring & documentation (Task 40)

---

#### Approach B: Big Bang Migration

**Strategy:**

- Implement all systems together
- Switch from in-memory to full production stack at once
- Deploy directly to production

**Benefits:**

- ✅ Clean architecture from day one
- ✅ No technical debt from transition
- ✅ Faster delivery (theoretically)

**Trade-offs:**

- ❌ Extremely high risk
- ❌ Difficult to debug issues
- ❌ Cannot easily roll back
- ❌ Testing complexity exponential
- ❌ Deployment risk unacceptable

**Verdict:** ❌ **REJECTED** - Too risky for production system

---

#### Approach C: Parallel Development with Blue-Green Deployment

**Strategy:**

- Build new production system in parallel
- Run both old (in-memory) and new (production) systems
- Use blue-green deployment for zero-downtime cutover

**Benefits:**

- ✅ Zero downtime deployment
- ✅ Old system remains as rollback option
- ✅ Clean separation of concerns

**Trade-offs:**

- ⚠️ Higher infrastructure cost during transition
- ⚠️ Data migration complexity
- ⚠️ More complex CI/CD pipeline

**Verdict:** ✅ **VIABLE** - Consider for final production deployment

### 4. Recommended Approach: Incremental Migration with Staging

**Final Decision:** **Approach A (Incremental Migration)**

**Rationale:**

1. **Risk Mitigation**: Each feature tested independently before production
2. **Operational Excellence**: Team learns production systems incrementally
3. **Cost Effective**: No duplicate infrastructure during transition
4. **Rollback Safety**: Individual features can be disabled without full rollback
5. **Testing Efficiency**: E2E tests can validate each increment

**Migration Path:**

```
Phase 1: Database Layer (Tasks 38-39)
  ├─ Implement PostgreSQL persistence
  ├─ Data migration from in-memory
  ├─ Feature flag: USE_DATABASE = true/false
  └─ Testing: Staging environment only

Phase 2: Async Processing (Tasks 35-36)
  ├─ Implement Celery + Redis
  ├─ Feature flag: USE_CELERY = true/false
  ├─ Keep synchronous fallback
  └─ Testing: Load testing with 100+ concurrent uploads

Phase 3: Production Deployment (Task 37)
  ├─ Railway (backend) + Vercel (frontend)
  ├─ CI/CD pipeline setup
  ├─ Environment configuration
  └─ Testing: Blue-green deployment to production

Phase 4: AI Enhancement (Task 34)
  ├─ User feedback capture
  ├─ Correction storage
  ├─ Fine-tuning data preparation
  └─ Testing: Validate AI improvement over time

Phase 5: Observability (Task 40)
  ├─ Logging (structured JSON logs)
  ├─ Monitoring (Sentry for errors)
  ├─ Metrics (parsing times, success rates)
  ├─ Documentation (runbooks, API docs)
  └─ Testing: Simulate failures, validate alerts
```

---

### 5. System Boundaries and Constraints

**System Boundaries:**

- **Scope:** Tasks 34-40 only (production readiness)
- **Out of Scope:** New features, UI redesign, NLP model changes
- **Dependencies:** Render, Fly.io, Supabase/Redis Cloud, Vercel, Sentry accounts

**Integration Points:**

- **Render** (FastAPI backend deployment + PostgreSQL)
- **Fly.io** (Celery worker - doesn't sleep)
- **Supabase** (PostgreSQL database - alternative to Render's)
- **Redis Cloud or Upstash** (Redis for Celery broker)
- **Vercel** (frontend deployment)
- **Sentry** (error tracking)
- **OpenAI API** (existing, no changes)

**Platform Selection Rationale:**

Since Railway limits free projects, we're using a **multi-platform approach**:

1. **Render** for FastAPI backend - Best Python support, 750 free hours/month
2. **Fly.io** for Celery worker - 3 free VMs that stay running (no sleep mode)
3. **Supabase** for PostgreSQL - 500MB free tier with excellent UI
4. **Redis Cloud** for Redis - 30K commands/month free tier
5. **Vercel** for frontend - Unlimited projects for frontend

**Benefits of Multi-Platform Approach:**

- ✅ Maximize free tier utilization across platforms
- ✅ No single platform's project limits
- ✅ Best-in-class service for each component
- ✅ Easy migration to paid tiers if needed

**Constraints:**

- **Downtime Budget:** Maximum 1 hour maintenance window
- **Data Loss:** Zero tolerance for data loss
- **Rollback Time:** Must be able to rollback in < 15 minutes
- **Cost Target:** $0/month using free tiers (can scale to paid tiers later)
- **Performance:** p95 latency < 5 seconds for parsing

**Risks:**

1. **Data Migration:** In-memory to PostgreSQL migration complexity
2. **Celery Configuration:** Redis connection issues in production
3. **Environment Variables:** Secrets management across environments
4. **WebSocket Scaling:** Sticky sessions required for WebSocket connections
5. **AI API Costs:** OpenAI costs may spike with production traffic

---

## PART 2: DETAILED IMPLEMENTATION PLAN

---

## Task 34: User Feedback & AI Learning System

**Priority:** High
**Complexity:** Medium
**Estimated Time:** 3-4 days

### Step 1: Design Feedback Data Model

**Objective:**
Create database schema to store user corrections for AI learning.

**Prerequisites:**

- Database models from Task 38 must be complete
- SQLAlchemy async session configured

**Test First:**

```python
# backend/tests/unit/test_feedback_model.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resume import ResumeCorrection

@pytest.mark.asyncio
async def test_create_resume_correction(db_session: AsyncSession):
    """Test creating a resume correction record"""
    correction = ResumeCorrection(
        resume_id="uuid-here",
        field_path="personal_info.email",
        original_value="wrong@email.com",
        corrected_value="correct@email.com"
    )
    db_session.add(correction)
    await db_session.commit()
    await db_session.refresh(correction)

    assert correction.id is not None
    assert correction.created_at is not None
```

**Expected:** Test fails (ResumeCorrection model or table doesn't exist yet)

**Implementation:**

- ResumeCorrection model already exists in `backend/app/models/resume.py`
- Create Alembic migration to add the table
- Update `backend/app/models/resume.py` if needed

**Acceptance Criteria:**

- ✅ Test passes
- ✅ Alembic migration created and tested
- ✅ Can insert and query corrections

---

### Step 2: Implement Feedback Capture Service

**Objective:**
Capture user corrections when they save edited resume data.

**Prerequisites:**

- Step 1 complete (database table exists)
- PUT `/v1/resumes/{id}` endpoint exists (already implemented)

**Test First:**

```python
# backend/tests/unit/test_feedback_service.py
import pytest
from app.services.feedback_service import FeedbackCaptureService

@pytest.mark.asyncio
async def test_capture_field_correction():
    """Test capturing a single field correction"""
    service = FeedbackCaptureService()

    await service.capture_correction(
        resume_id="test-resume-id",
        field_path="personal_info.phone",
        original_value="+1-555-0100",
        corrected_value="+1-555-0199"
    )

    # Verify correction was saved to database
    # (assertion details in implementation)
```

**Expected:** Test fails (FeedbackCaptureService doesn't exist)

**Implementation:**

- Create `backend/app/services/feedback_service.py`
- Implement `capture_correction()` method
- Integrate with existing PUT endpoint in `backend/app/api/resumes.py`

**Scope:**

- Only capture corrections, don't process them yet
- Store original and corrected values
- Track field path (e.g., "personal_info.email")

**Constraints:**

- Must not slow down the PUT endpoint response
- Use async/await throughout
- Handle database errors gracefully

**Acceptance Criteria:**

- ✅ Test passes
- ✅ Corrections saved to database on PUT
- ✅ No performance degradation (< 100ms overhead)
- ✅ All existing tests still pass

---

### Step 3: Export Feedback Data for AI Training

**Objective:**
Create endpoint to export corrections for AI fine-tuning.

**Prerequisites:**

- Steps 1-2 complete
- At least 10 correction records in database

**Test First:**

```python
# backend/tests/integration/test_feedback_api.py
import pytest
from fastapi.testclient import TestClient

def test_export_corrections_requires_auth(client):
    """Test that export endpoint requires authentication"""
    response = client.get("/v1/admin/corrections/export")
    assert response.status_code == 401

def test_export_corrections_returns_csv(client, admin_token):
    """Test that export returns valid CSV"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/v1/admin/corrections/export", headers=headers)

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
```

**Expected:** Test fails (endpoint doesn't exist)

**Implementation:**

- Create GET `/v1/admin/corrections/export` endpoint
- Implement CSV export format
- Add basic API key authentication (for MVP)

**Scope:**

- Export all corrections as CSV
- Format: `field_path,original_value,corrected_value,resume_id,created_at`
- No authentication for MVP (add in production hardening)

**Constraints:**

- Use streaming response for large datasets
- Include proper CSV headers

**Acceptance Criteria:**

- ✅ Tests pass
- ✅ CSV can be downloaded
- ✅ Format is valid CSV
- ✅ Can be used for GPT fine-tuning

---

### Step 4: Document AI Improvement Process

**Objective:**
Create documentation for using feedback data to improve AI model.

**Prerequisites:**

- Steps 1-3 complete
- CSV export working

**Test First:**

```bash
# Manual test: Follow documentation to export and fine-tune
# Expected: Documentation is clear and complete
```

**Implementation:**

- Create `docs/ai-improvement-guide.md`
- Document:
  - How to export correction data
  - How to format data for OpenAI fine-tuning
  - How to test improved model
  - How to deploy new model

**Scope:**

- Step-by-step instructions
- Code examples for data transformation
- Cost estimates for fine-tuning

**Acceptance Criteria:**

- ✅ Documentation exists
- ✅ Another developer can follow it independently
- ✅ Includes examples and code snippets

---

**Verification for Task 34:**

- ✅ All unit tests pass (feedback capture, export)
- ✅ All integration tests pass (API endpoints)
- ✅ Documentation complete and reviewed
- ✅ No regressions in existing tests

**Stop/Go Decision:**

- ✅ **GO** to Task 35-36 if all criteria met
- ⏸️ **PAUSE** if database migrations fail or regressions detected

---

## Task 35-36: Celery + Redis Async Processing

**Priority:** High
**Complexity:** Medium
**Estimated Time:** 5-6 days

### Step 1: Setup Redis and Celery Infrastructure

**Objective:**
Configure Celery with Redis broker for async task processing.

**Prerequisites:**

- Redis server running (local: `brew install redis`, production: Railway Redis)
- backend/requirements.txt already includes celery==5.3.6 and redis==5.0.1

**Test First:**

```python
# backend/tests/unit/test_celery_config.py
import pytest
from app.core.celery_app import celery_app

def test_celery_app_configured():
    """Test that Celery app is properly configured"""
    assert celery_app.broker_url is not None
    assert "redis" in celery_app.broker_url
    assert celery_app.conf.task_serializer == "json"
```

**Expected:** Test fails (celery_app doesn't exist)

**Implementation:**

- Create `backend/app/core/celery_app.py`
- Configure Celery with Redis broker
- Add environment variable `REDIS_URL` to `.env.example`

**Scope:**

- Basic Celery configuration
- Redis connection setup
- JSON serialization for tasks

**Constraints:**

- Use async Celery patterns
- Configure task timeouts
- Enable task result backend (Redis)

**Acceptance Criteria:**

- ✅ Test passes
- ✅ Celery worker can start successfully
- ✅ Redis connection working

---

### Step 2: Create Celery Task for Resume Parsing

**Objective:**
Move parsing logic from synchronous to Celery async task.

**Prerequisites:**

- Step 1 complete (Celery configured)
- Parser orchestrator exists and tested

**Test First:**

```python
# backend/tests/integration/test_celery_tasks.py
import pytest
from app.tasks.parse_resume import parse_resume_task

@pytest.mark.asyncio
async def test_parse_resume_task_creates_result():
    """Test that parsing task completes successfully"""
    result = parse_resume_task.delay(
        resume_id="test-id",
        file_path="/tmp/test.pdf",
        file_content=b"fake pdf content"
    )

    # Wait for task to complete (max 30 seconds)
    from celery.result import AsyncResult
    task_result = AsyncResult(result.id)
    task_result.get(timeout=30)

    assert task_result.successful()
```

**Expected:** Test fails (parse_resume_task doesn't exist)

**Implementation:**

- Create `backend/app/tasks/parse_resume.py`
- Move parsing logic from `parser_orchestrator.py` to Celery task
- Update orchestrator to call Celery task instead of synchronous parsing

**Scope:**

- Create `parse_resume_task()` Celery task
- Integrate with existing parser services
- Update WebSocket to poll for task status

**Constraints:**

- Task must be idempotent (can retry safely)
- Include proper error handling
- Set task timeout (5 minutes)
- Use task routing for scalability

**Acceptance Criteria:**

- ✅ Test passes
- ✅ Task completes within timeout
- ✅ WebSocket still receives progress updates
- ✅ All existing tests still pass (with feature flag)

---

### Step 3: Update WebSocket for Async Task Status

**Objective:**
Modify WebSocket connection to poll Celery task status instead of waiting synchronously.

**Prerequisites:**

- Step 2 complete (Celery task working)
- Existing WebSocket connection manager

**Test First:**

```python
# backend/tests/integration/test_websocket_celery.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from app.tasks.parse_resume import parse_resume_task

@pytest.mark.asyncio
async def test_websocket_receives_celery_task_updates():
    """Test that WebSocket receives progress from Celery task"""
    # Trigger parsing (now async)
    result = parse_resume_task.delay(resume_id="ws-test", ...)

    # Connect WebSocket
    with TestClient(app).websocket_connect(f"/ws/resumes/ws-test") as websocket:
        # Should receive progress updates
        data = websocket.receive_json()
        assert data["type"] == "progress_update"
        assert data["stage"] in ["text_extraction", "nlp_parsing", "ai_enhancement"]
```

**Expected:** Test needs modification (WebSocket polling logic doesn't exist)

**Implementation:**

- Update `backend/app/api/websocket.py` to poll Celery task status
- Implement task result polling every 1 second
- Broadcast progress updates as before

**Scope:**

- Poll Celery task result backend
- Convert Celery task status to WebSocket messages
- Maintain backward compatibility with sync mode

**Constraints:**

- Polling interval: 1 second
- Connection timeout: 5 minutes
- Handle task failures gracefully

**Acceptance Criteria:**

- ✅ Test passes
- ✅ WebSocket receives all progress stages
- ✅ Task failures broadcast error messages
- ✅ No WebSocket connection leaks

---

### Step 4: Add Feature Flag for Async Mode

**Objective:**
Allow switching between sync and async parsing modes.

**Prerequisites:**

- Steps 1-3 complete
- Both sync and async modes working

**Test First:**

```python
# backend/tests/integration/test_feature_flags.py
import pytest
import os

def test_sync_mode_when_feature_flag_disabled(monkeypatch):
    """Test that sync mode works when USE_CELERY=false"""
    monkeypatch.setenv("USE_CELERY", "false")
    # Test synchronous parsing

def test_async_mode_when_feature_flag_enabled(monkeypatch):
    """Test that async mode works when USE_CELERY=true"""
    monkeypatch.setenv("USE_CELERY", "true")
    # Test Celery task execution
```

**Expected:** Test fails (feature flag doesn't exist)

**Implementation:**

- Add `USE_CELERY` environment variable to `backend/app/core/config.py`
- Update upload endpoint to check flag
- Route to sync or async path accordingly

**Scope:**

- Simple boolean feature flag
- Default: `false` (sync mode)
- Update documentation

**Constraints:**

- Feature flag check at runtime
- No code duplication between sync/async paths

**Acceptance Criteria:**

- ✅ Tests pass
- ✅ Can switch modes via environment variable
- ✅ Sync mode remains as fallback

---

### Step 5: Deploy Redis and Configure Celery Workers

**Objective:**
Deploy Redis instance and configure Celery worker processes.

**Prerequisites:**

- Steps 1-4 complete (local development tested)
- Railway account configured

**Test First:**

```bash
# Manual test: Deploy Redis and verify connection
# Expected: Celery worker connects to Railway Redis successfully
```

**Implementation:**

- Deploy Railway Redis instance
- Update `REDIS_URL` in Railway environment variables
- Create Procfile for Celery worker: `celery_worker: celery -A app.core.celery_app worker --loglevel=info`
- Deploy Celery worker as separate Railway service

**Scope:**

- Single Redis instance (MVP)
- Single Celery worker (MVP, scale later)
- Basic health monitoring

**Constraints:**

- Redis connection secured with password
- Celery worker auto-restart on failure
- Log aggregation configured

**Acceptance Criteria:**

- ✅ Redis deployed and accessible
- ✅ Celery worker running and processing tasks
- ✅ End-to-end test: upload → parse → complete
- ✅ Worker logs visible in Railway dashboard

---

### Step 6: Load Testing and Performance Tuning

**Objective:**
Validate system handles 100+ concurrent parsing requests.

**Prerequisites:**

- Steps 1-5 complete
- Production-like environment configured

**Test First:**

```python
# backend/tests/performance/test_load.py
import pytest
import asyncio
from locust import HttpUser, task, between

class ResumeUploadUser(HttpUser):
    wait_time = between(1, 3)
    host = "https://resumate-backend.railway.app"

    @task
    def upload_resume(self):
        # Simulate resume upload
        files = {"file": ("test.pdf", b"content", "application/pdf")}
        self.client.post("/v1/resumes/upload", files=files)

# Run: locust -f backend/tests/performance/test_load.py --users 100 --spawn-rate 10
```

**Expected:** Test may fail or show performance issues

**Implementation:**

- Run Locust load tests
- Identify bottlenecks (Celery worker count, Redis connections)
- Tune Celery worker configuration (concurrency, prefetch)
- Scale Redis if needed

**Scope:**

- Target: 100 concurrent users
- Target: p95 latency < 30 seconds (end-to-end)
- Target: 0% task failures

**Constraints:**

- Test on staging environment first
- Monitor costs during load test
- Clean up test data after

**Acceptance Criteria:**

- ✅ 100 concurrent uploads successful
- ✅ p95 latency meets target
- ✅ No task failures
- ✅ Celery worker stable under load

---

**Verification for Task 35-36:**

- ✅ All unit tests pass (Celery config, tasks)
- ✅ All integration tests pass (WebSocket, upload flow)
- ✅ Load tests pass (100 concurrent users)
- ✅ Redis and Celery workers deployed
- ✅ Feature flag allows rollback
- ✅ No regressions in existing tests

**Stop/Go Decision:**

- ✅ **GO** to Task 37 if performance targets met
- ⏸️ **PAUSE** if load tests fail or Celery unstable

---

## Task 37: Production Deployment

**Priority:** Critical
**Complexity:** Medium
**Estimated Time:** 4-5 days

### Step 1: Configure Railway Backend Deployment

**Objective:**
Deploy backend to Railway with production environment.

**Prerequisites:**

- Railway account configured
- Backend code tested locally

**Test First:**

```bash
# Manual test: Deploy to Railway
# Expected: Backend service starts successfully
```

**Implementation:**

- Create `backend/railway.json` configuration
- Create `backend/Procfile` for process management
- Configure environment variables in Railway dashboard
- Deploy using Railway CLI: `railway up`

**Scope:**

- Single service (API + Celery worker)
- PostgreSQL database
- Redis for Celery
- Automatic deploys from main branch

**Constraints:**

- Use Railway's PostgreSQL (managed)
- Use Railway's Redis (managed)
- Environment variables for secrets
- Health check endpoint configured

**Acceptance Criteria:**

- ✅ Backend deployed to Railway
- ✅ Health check returns 200
- ✅ Database connections working
- ✅ CORS configured for Vercel domain

---

### Step 2: Configure Vercel Frontend Deployment

**Objective:**
Deploy frontend to Vercel with production build.

**Prerequisites:**

- Vercel account configured
- Frontend builds successfully locally

**Test First:**

```bash
# Manual test: Deploy to Vercel
# Expected: Frontend builds and deploys successfully
```

**Implementation:**

- Create `frontend/vercel.json` configuration
- Configure environment variables in Vercel dashboard
- Connect GitHub repository for auto-deploys
- Deploy: `vercel --prod`

**Scope:**

- Single Vercel project
- Production environment variables
- Automatic deploys from main branch
- Custom domain (optional)

**Constraints:**

- API base URL points to Railway backend
- WebSocket base URL points to Railway backend
- Build optimization enabled

**Acceptance Criteria:**

- ✅ Frontend deployed to Vercel
- ✅ All pages load successfully
- ✅ API calls to backend working
- ✅ WebSocket connections working

---

### Step 3: Setup CI/CD Pipeline

**Objective:**
Automate testing and deployment on push to main branch.

**Prerequisites:**

- Railway and Vercel deployments manual
- GitHub repository connected

**Test First:**

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Backend
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/ -v
      - name: Test Frontend
        run: |
          cd frontend
          npm install
          npm test -- --run
```

**Expected:** Workflow runs on push to GitHub

**Implementation:**

- Create `.github/workflows/test.yml` for testing
- Create `.github/workflows/deploy.yml` for deployment
- Configure Railway to auto-deploy on test pass
- Configure Vercel to auto-deploy on test pass

**Scope:**

- Run all tests on every push
- Deploy to staging on PR merge
- Deploy to production on main branch push
- Manual approval for production (optional)

**Constraints:**

- Tests must pass before deployment
- Deployment notifications configured
- Rollback automation ready

**Acceptance Criteria:**

- ✅ CI pipeline runs tests on every push
- ✅ CD pipeline deploys on successful tests
- ✅ Deployment notifications working
- ✅ Can rollback to previous version

---

### Step 4: Configure Production Environment Variables

**Objective:**
Setup all required environment variables for production.

**Prerequisites:**

- Railway and Vercel deployments active
- CI/CD pipeline configured

**Test First:**

```bash
# Manual test: Verify all environment variables are set
# Expected: Application starts without errors
```

**Implementation:**

**Backend (Railway):**

```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://default:password@host.redislabs.com:port
OPENAI_API_KEY=sk-...
SECRET_KEY=... (generate with openssl rand -hex 32)
ENVIRONMENT=production
ALLOWED_ORIGINS=https://resumate-frontend.vercel.app
USE_CELERY=true
TESSERACT_PATH=/usr/bin/tesseract
ENABLE_OCR_FALLBACK=true
SENTRY_DSN=https://...
```

**Frontend (Vercel):**

```bash
VITE_API_BASE_URL=https://resumate-backend.railway.app/v1
VITE_WS_BASE_URL=wss://resumate-backend.railway.app/ws
```

**Scope:**

- All secrets stored in platform dashboards
- No secrets in code repository
- Separate staging and production configs

**Constraints:**

- Use strong SECRET_KEY (32+ characters)
- OPENAI_API_KEY has usage limits
- SENTRY_DSN for error tracking

**Acceptance Criteria:**

- ✅ All environment variables configured
- ✅ No secrets in repository
- ✅ Application starts successfully
- ✅ All features working in production

---

### Step 5: Domain and SSL Configuration

**Objective:**
Configure custom domains and SSL certificates.

**Prerequisites:**

- Railway and Vercel deployments working
- Domain names purchased (optional)

**Test First:**

```bash
# Manual test: Access application via custom domain
# Expected: Application loads with valid SSL certificate
```

**Implementation:**

- Configure custom domain in Railway dashboard
- Configure custom domain in Vercel dashboard
- Verify SSL certificates (automatic on both platforms)
- Update CORS allowed origins

**Scope:**

- Backend domain: `api.resumate.app` (example)
- Frontend domain: `resumate.app` (example)
- SSL certificates managed by platforms

**Constraints:**

- DNS propagation may take 24-48 hours
- Update ALLOWED_ORIGINS after DNS propagation

**Acceptance Criteria:**

- ✅ Custom domains accessible
- ✅ Valid SSL certificates
- ✅ No mixed content warnings
- ✅ CORS configured correctly

---

### Step 6: Production Smoke Tests

**Objective:**
Validate all functionality works in production environment.

**Prerequisites:**

- Steps 1-5 complete
- Production environment live

**Test First:**

```python
# backend/tests/e2e/test_production_smoke.py
import pytest
import requests

def test_production_backend_health():
    """Test that production backend is healthy"""
    response = requests.get("https://resumate-backend.railway.app/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_production_file_upload():
    """Test that file upload works in production"""
    # Upload a test resume
    # Verify parsing completes
    # Verify WebSocket connection

def test_production_frontend_loads():
    """Test that production frontend loads"""
    response = requests.get("https://resumate.app")
    assert response.status_code == 200
```

**Expected:** All smoke tests pass

**Implementation:**

- Run smoke tests against production
- Test all user flows:
  - File upload
  - Parsing progress
  - Review and edit
  - Share and export
- Verify WebSocket connections

**Scope:**

- Critical path testing only
- No need for comprehensive testing (covered by CI)
- Manual testing recommended

**Constraints:**

- Use real test data
- Clean up test data after
- Monitor production logs during tests

**Acceptance Criteria:**

- ✅ All smoke tests pass
- ✅ No errors in production logs
- ✅ All features working
- ✅ WebSocket connections stable

---

**Verification for Task 37:**

- ✅ Backend deployed to Railway
- ✅ Frontend deployed to Vercel
- ✅ CI/CD pipeline automated
- ✅ Environment variables configured
- ✅ Custom domains and SSL working
- ✅ Smoke tests passing
- ✅ Zero errors in production logs

**Stop/Go Decision:**

- ✅ **GO** to Task 38-39 if production deployment stable
- ⏸️ **PAUSE** if deployment issues or smoke tests failing

---

## Task 38-39: Database Persistence

**Priority:** Critical
**Complexity:** Medium
**Estimated Time:** 4-5 days

### Step 1: Setup Alembic Migrations

**Objective:**
Configure Alembic for database schema management.

**Prerequisites:**

- Database models exist (`backend/app/models/resume.py`)
- PostgreSQL database running (local or Railway)

**Test First:**

```bash
# Manual test: Initialize Alembic
# Expected: alembic/ directory created
```

**Implementation:**

- Run: `alembic init alembic` (if not already done)
- Configure `alembic.ini` with database URL
- Create `alembic/env.py` for async support
- Create first migration: `alembic revision --autogenerate -m "Initial schema"`

**Scope:**

- Async Alembic configuration
- Migration for all models:
  - Resume
  - ParsedResumeData
  - ResumeCorrection
  - ResumeShare

**Constraints:**

- Use async SQLAlchemy
- Migration must be reversible
- Test on local database first

**Acceptance Criteria:**

- ✅ Alembic initialized
- ✅ First migration created
- ✅ Migration applies successfully
- ✅ Migration rolls back successfully

---

### Step 2: Create Database Migration

**Objective:**
Create migration to add all required tables.

**Prerequisites:**

- Step 1 complete (Alembic configured)
- Models defined in `backend/app/models/resume.py`

**Test First:**

```bash
# Manual test: Apply migration to test database
# Expected: All tables created successfully
```

**Implementation:**

- Generate migration: `alembic revision --autogenerate -m "Initial schema"`
- Review generated migration file
- Apply migration: `alembic upgrade head`
- Verify tables created

**Scope:**

- Create all tables
- Add indexes for performance:
  - resumes(file_hash) - for duplicate detection
  - parsed_resume_data(resume_id) - for lookups
  - resume_shares(share_token) - for share lookups
  - resume_corrections(resume_id) - for feedback

**Constraints:**

- Foreign key constraints
- Cascade deletes where appropriate
- Proper column types (UUID, JSONB, etc.)

**Acceptance Criteria:**

- ✅ Migration applies without errors
- ✅ All tables created
- ✅ Indexes created
- ✅ Can query tables

---

### Step 3: Implement Database Storage Service

**Objective:**
Replace in-memory storage with PostgreSQL persistence.

**Prerequisites:**

- Steps 1-2 complete (migrations applied)
- Async SQLAlchemy session configured

**Test First:**

```python
# backend/tests/unit/test_database_storage.py
import pytest
from app.services.database_storage import DatabaseStorageService

@pytest.mark.asyncio
async def test_save_resume_data(db_session):
    """Test saving parsed resume data to database"""
    service = DatabaseStorageService()

    await service.save_resume(
        resume_id="test-id",
        original_filename="test.pdf",
        parsed_data={...}
    )

    # Verify data was saved
    resume = await service.get_resume("test-id")
    assert resume is not None
    assert resume.original_filename == "test.pdf"
```

**Expected:** Test fails (DatabaseStorageService doesn't exist)

**Implementation:**

- Create `backend/app/services/database_storage.py`
- Implement methods:
  - `save_resume()` - Save resume and parsed data
  - `get_resume()` - Retrieve resume by ID
  - `update_resume()` - Update parsed data
  - `delete_resume()` - Delete resume (optional)
- Replace in-memory storage calls

**Scope:**

- CRUD operations for resumes
- CRUD operations for shares
- Use async SQLAlchemy
- Proper error handling

**Constraints:**

- All database operations async
- Proper session management
- Handle database errors gracefully

**Acceptance Criteria:**

- ✅ Tests pass
- ✅ Data persists across server restarts
- ✅ No data loss on concurrent writes
- ✅ All existing tests pass (with feature flag)

---

### Step 4: Migrate Existing In-Memory Data

**Objective:**
Create migration script to move existing in-memory data to database.

**Prerequisites:**

- Steps 1-3 complete (database storage working)
- Existing in-memory data to migrate

**Test First:**

```bash
# Manual test: Run migration script
# Expected: All in-memory data transferred to database
```

**Implementation:**

- Create `backend/scripts/migrate_in_memory.py`
- Script should:
  - Load all in-memory resumes
  - Insert into database
  - Verify all data migrated
  - Report statistics

**Scope:**

- One-time migration script
- Migrate resumes, parsed data, shares
- Validation after migration

**Constraints:**

- Stop server before migration
- Backup database before migration
- Verify data integrity after migration

**Acceptance Criteria:**

- ✅ Migration script runs successfully
- ✅ All data migrated to database
- ✅ No data corruption
- ✅ Can delete in-memory storage code

---

### Step 5: Update Endpoints to Use Database

**Objective:**
Modify API endpoints to use database storage instead of in-memory.

**Prerequisites:**

- Steps 1-4 complete (database storage working)
- Feature flag implemented

**Test First:**

```python
# backend/tests/integration/test_database_api.py
import pytest
from fastapi.testclient import TestClient

def test_upload_saves_to_database(client):
    """Test that upload saves to database"""
    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.pdf", b"content", "application/pdf")}
    )

    resume_id = response.json()["resume_id"]

    # Verify data in database
    # (assertion details)
```

**Expected:** Test passes (with feature flag enabled)

**Implementation:**

- Update PUT `/v1/resumes/{id}` to use database
- Update GET `/v1/resumes/{id}` to use database
- Update share endpoints to use database
- Add feature flag: `USE_DATABASE=true/false`

**Scope:**

- All CRUD operations use database
- Feature flag for rollback
- Update error handling

**Constraints:**

- Feature flag check at runtime
- Maintain backward compatibility
- No performance degradation

**Acceptance Criteria:**

- ✅ Tests pass
- ✅ Data persists in database
- ✅ Feature flag works
- ✅ All existing tests pass

---

### Step 6: Enable Database in Production

**Objective:**
Switch production to use database storage.

**Prerequisites:**

- Steps 1-5 complete (database storage working in staging)
- All tests passing
- Migration tested on staging

**Test First:**

```bash
# Manual test: Run database migration on production
# Expected: Migration applies successfully
```

**Implementation:**

- Set `USE_DATABASE=true` in production
- Run Alembic migrations on production database
- Verify all endpoints working
- Monitor for errors

**Scope:**

- Production deployment
- Database migration
- Feature flag enabled

**Constraints:**

- Run migrations during low-traffic period
- Have rollback plan ready
- Monitor production logs

**Acceptance Criteria:**

- ✅ Migration successful
- ✅ All endpoints working
- ✅ Data persisting correctly
- ✅ No errors in logs
- ✅ Performance acceptable

---

**Verification for Task 38-39:**

- ✅ Alembic migrations created and tested
- ✅ Database storage service implemented
- ✅ All data migrated from in-memory
- ✅ API endpoints using database
- ✅ Feature flag allows rollback
- ✅ Production using database storage
- ✅ No data loss
- ✅ All tests passing

**Stop/Go Decision:**

- ✅ **GO** to Task 40 if database stable
- ⏸️ **PAUSE** if migration issues or performance problems

---

## Task 40: Documentation & Monitoring Setup

**Priority:** Important
**Complexity:** Low
**Estimated Time:** 2-3 days

### Step 1: Setup Structured Logging

**Objective:**
Implement structured JSON logging for production observability.

**Prerequisites:**

- Backend deployed to production
- Logs accessible (Railway dashboard)

**Test First:**

```python
# backend/tests/unit/test_logging.py
import pytest
import json
import logging

def test_logs_are_structured_json(caplog):
    """Test that logs are structured JSON"""
    with caplog.at_level(logging.INFO):
        logger.info("Resume uploaded", resume_id="test-id", filename="test.pdf")

    log_record = caplog.records[0]
    assert hasattr(log_record, "resume_id")
    assert log_record.resume_id == "test-id"
```

**Expected:** Test fails (structured logging not configured)

**Implementation:**

- Install python-json-logger
- Configure JSON formatter in `backend/app/core/logging.py`
- Update FastAPI logging configuration
- Add correlation IDs to requests

**Scope:**

- Structured JSON logs
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log sensitive data redaction

**Constraints:**

- No sensitive data in logs (emails, phone numbers)
- Include request ID in all logs
- JSON format for parsing

**Acceptance Criteria:**

- ✅ Tests pass
- ✅ Logs output valid JSON
- ✅ Correlation IDs present
- ✅ Sensitive data redacted

---

### Step 2: Setup Sentry Error Tracking

**Objective:**
Configure Sentry for production error monitoring.

**Prerequisites:**

- Sentry account configured
- Backend deployed to production

**Test First:**

```bash
# Manual test: Trigger an error and verify Sentry captures it
# Expected: Error appears in Sentry dashboard
```

**Implementation:**

- Install sentry-sdk
- Configure Sentry in `backend/app/main.py`
- Add `SENTRY_DSN` to environment variables
- Test error capture

**Scope:**

- Automatic error reporting
- Performance monitoring
- Release tracking

**Constraints:**

- Sample rate for transactions (10% for MVP)
- Filter out sensitive data
- Test Sentry integration before production

**Acceptance Criteria:**

- ✅ Errors captured in Sentry
- ✅ Stack traces visible
- ✅ Request data included (sanitized)
- ✅ Performance data collected

---

### Step 3: Create Health Check and Metrics Endpoints

**Objective:**
Add endpoints for monitoring system health.

**Prerequisites:**

- Backend deployed to production

**Test First:**

```python
# backend/tests/integration/test_monitoring.py
import pytest
from fastapi.testclient import TestClient

def test_health_check_returns_system_status(client):
    """Test that health check returns detailed status"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
```

**Expected:** Test passes (endpoint exists but needs enhancement)

**Implementation:**

- Enhance `/health` endpoint
- Add `/metrics` endpoint (optional, for Prometheus)
- Check database connectivity
- Check Redis connectivity
- Check Celery worker status

**Scope:**

- Database connection check
- Redis connection check
- Celery worker status
- Response time metrics

**Constraints:**

- Health check must return quickly (< 1 second)
- Don't expose sensitive information
- Cache status checks (5 seconds)

**Acceptance Criteria:**

- ✅ Health check endpoint working
- ✅ All dependencies checked
- ✅ Metrics endpoint available (optional)
- ✅ Response time acceptable

---

### Step 4: Create Operations Documentation

**Objective:**
Write comprehensive documentation for system operations.

**Prerequisites:**

- All previous steps complete
- Production system operational

**Test First:**

```bash
# Manual test: Follow documentation to perform common operations
# Expected: Documentation is clear and complete
```

**Implementation:**

Create documentation files:

**`docs/DEPLOYMENT.md`:**

- Prerequisites (accounts, tools)
- Step-by-step deployment guide
- Environment configuration
- Troubleshooting common issues

**`docs/OPERATIONS.md`:**

- Daily operations checklist
- Monitoring dashboards
- Common operational tasks
- Incident response procedures

**`docs/SCALING.md`:**

- When to scale Celery workers
- Database indexing strategy
- Caching strategy (future)
- CDN configuration (future)

**`docs/API.md`:**

- All API endpoints documented
- Request/response examples
- Error codes and handling
- WebSocket protocol

**Scope:**

- Complete deployment guide
- Operations runbook
- Scaling guide
- API documentation

**Constraints:**

- Use clear, non-technical language where possible
- Include code examples
- Keep documentation up to date

**Acceptance Criteria:**

- ✅ All documentation files created
- ✅ Another person can deploy using docs
- ✅ Common issues documented with solutions
- ✅ API documentation complete

---

### Step 5: Setup Alerts and Notifications

**Objective:**
Configure alerts for critical system issues.

**Prerequisites:**

- Sentry configured
- System metrics collected

**Test First:**

```bash
# Manual test: Trigger alert condition
# Expected: Alert notification received
```

**Implementation:**

Configure Sentry alerts:

- Error rate > 5% in 5 minutes
- Response time p95 > 10 seconds
- Any database connection errors
- Any Redis connection errors
- Celery task failure rate > 10%

Configure Railway alerts (if available):

- Service restart
- Memory/CPU usage > 80%
- Deployment failures

**Scope:**

- Error rate alerts
- Performance alerts
- Infrastructure alerts

**Constraints:**

- Don't spam with alerts
- Set appropriate thresholds
- Include actionable information in alerts

**Acceptance Criteria:**

- ✅ Alerts configured
- ✅ Test alerts trigger successfully
- ✅ Notification channel working (email/Slack)
- ✅ Alert thresholds appropriate

---

### Step 6: Create Runbooks for Common Issues

**Objective:**
Document troubleshooting procedures for common production issues.

**Prerequisites:**

- Steps 1-5 complete
- Some operational experience gained

**Test First:**

```bash
# Manual test: Follow runbook to resolve simulated issue
# Expected: Issue resolved successfully
```

**Implementation:**

Create `docs/RUNBOOKS.md` with sections:

**Issue: Database Connection Pool Exhausted**

- Symptoms
- Diagnosis steps
- Resolution steps
- Prevention

**Issue: Celery Tasks Not Processing**

- Symptoms
- Diagnosis steps
- Resolution steps
- Prevention

**Issue: High Memory Usage**

- Symptoms
- Diagnosis steps
- Resolution steps
- Prevention

**Issue: WebSocket Connection Failures**

- Symptoms
- Diagnosis steps
- Resolution steps
- Prevention

**Issue: Slow Parsing Performance**

- Symptoms
- Diagnosis steps
- Resolution steps
- Prevention

**Scope:**

- Top 5 most common issues
- Clear step-by-step instructions
- Include commands to run

**Constraints:**

- Keep instructions simple
- Include expected outputs
- Update based on real incidents

**Acceptance Criteria:**

- ✅ Runbooks created for top issues
- ✅ Each runbook tested
- ✅ Easy to follow
- ✅ Includes prevention tips

---

**Verification for Task 40:**

- ✅ Structured logging implemented
- ✅ Sentry error tracking configured
- ✅ Health check endpoint enhanced
- ✅ Operations documentation complete
- ✅ Alerts configured and tested
- ✅ Runbooks created and tested

**Stop/Go Decision:**

- ✅ **COMPLETE** - All tasks 34-40 finished
- 🎉 **PRODUCTION READY** - System fully operational

---

## REGRESSION PROTECTION STRATEGY

### Tests That Must Pass After Each Step:

**Backend Tests (136 total):**

- 28 unit tests (all services)
- 40 integration tests (API endpoints, WebSocket, Celery)
- 4 E2E tests (complete flows)

**Frontend Tests (52 total):**

- 16 component/hook tests
- 26 page tests
- 5 routing tests
- 5 additional tests

### Regression Test Execution:

After **each** step:

1. Run backend tests: `cd backend && pytest tests/ -v`
2. Run frontend tests: `cd frontend && npm test -- --run`
3. Run type check: `cd frontend && npm run type-check`
4. Verify count: Must have 188 passing tests (136 backend + 52 frontend)

### Contingency for Test Failures:

**If new tests fail:**

- Fix implementation until tests pass
- Do not proceed to next step

**If existing tests fail (regression):**

- Stop immediately
- Investigate root cause
- Fix regression before proceeding
- May need to revert changes

**After 3 failed attempts:**

- **STOP** - Request human guidance
- Do not make 4th attempt without review
- Re-evaluate approach

---

## TRANSPARENCY REQUIREMENTS

### Progress Tracking:

Each step will:

- ✅ Start with clear objective
- ✅ Write failing tests first
- ✅ Implement minimal code
- ✅ Verify all tests pass
- ✅ Document completion

### Blocker Visibility:

Blockers will be immediately visible via:

- Test failures (red in test output)
- Step not marked as complete
- Explicit pause in plan execution

### Rollback Conditions:

Rollback if:

- ✅ Regressions detected (> 5 tests failing)
- ✅ Performance degradation (> 20% slower)
- ✅ Data loss or corruption
- ✅ Security vulnerability introduced

---

## FINAL SUCCESS CRITERIA

### All Tasks Complete When:

✅ **Task 34 (User Feedback):**

- Corrections captured and stored
- Export endpoint working
- AI improvement guide documented

✅ **Task 35-36 (Celery + Redis):**

- Async processing working
- Load tests pass (100 concurrent users)
- Feature flag allows rollback

✅ **Task 37 (Production Deployment):**

- Railway backend deployed
- Vercel frontend deployed
- CI/CD automated
- Custom domains configured
- Smoke tests passing

✅ **Task 38-39 (Database Persistence):**

- PostgreSQL database configured
- All data migrated from in-memory
- Production using database
- Zero data loss

✅ **Task 40 (Documentation & Monitoring):**

- Structured logging implemented
- Sentry error tracking configured
- Health checks working
- Documentation complete
- Alerts configured
- Runbooks created

### System Metrics:

- ✅ 188/188 tests passing (zero regressions)
- ✅ Production deployment stable
- ✅ p95 parsing latency < 30 seconds
- ✅ Error rate < 1%
- ✅ Uptime > 99.5%

### Production Readiness Checklist:

- ✅ Deployed to production (Railway + Vercel)
- ✅ Database persistence active
- ✅ Async processing enabled
- ✅ Monitoring configured (Sentry)
- ✅ Logging structured (JSON)
- ✅ Alerts configured
- ✅ Documentation complete
- ✅ Runbooks tested
- ✅ CI/CD automated
- ✅ Zero critical bugs

---

## EXECUTION NOTES

### Model Selection Guide:

- **Simple Steps** (config changes, docs): Use **haiku** (fast, cost-effective)
- **Complex Steps** (database, Celery): Use **sonnet** (balanced)
- **Critical Steps** (production deployment): Use **opus** (most capable)

### Parallelization Opportunities:

- **Task 35 & 38** can be worked in parallel (independent systems)
- **Task 34** depends on Task 38 (database)
- **Task 37** depends on Tasks 35 & 38 (deployment)

### Risk Mitigation:

- **Feature Flags** for all major changes
- **Staging Environment** for testing before production
- **Rollback Plans** for each task
- **Incremental Rollout** (10% → 50% → 100%)

---

**Plan Status:** ✅ READY FOR EXECUTION
**Created:** 2026-02-21
**Author:** Claude Sonnet 4.5
**Methodology:** TDD (Test-Driven Development)
**Next:** Begin Task 34, Step 1

---

## APPENDIX: QUICK REFERENCE

### Environment Variables Summary:

**Backend:**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://...
USE_DATABASE=true

# Redis & Celery
REDIS_URL=redis://...
USE_CELERY=true

# OpenAI
OPENAI_API_KEY=sk-...
ENABLE_OCR_FALLBACK=true

# Security
SECRET_KEY=...
ENVIRONMENT=production
ALLOWED_ORIGINS=https://resumate.app

# Monitoring
SENTRY_DSN=https://...
```

**Frontend:**

```bash
VITE_API_BASE_URL=https://resumate-backend.railway.app/v1
VITE_WS_BASE_URL=wss://resumate-backend.railway.app/ws
```

### Test Commands:

```bash
# Backend
cd backend
pytest tests/ -v
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Frontend
cd frontend
npm test -- --run
npm run type-check

# Load Test
locust -f backend/tests/performance/test_load.py --users 100 --spawn-rate 10
```

### Deployment Commands:

```bash
# Railway
railway login
railway init
railway up
railway logs

# Vercel
vercel login
vercel link
vercel --prod
```

---

**END OF IMPLEMENTATION PLAN**
