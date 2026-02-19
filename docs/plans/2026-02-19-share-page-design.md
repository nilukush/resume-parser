# Share Page Design Document

**Feature:** ResuMate Share Page with Export Functionality
**Date:** 2026-02-19
**Status:** ✅ Approved
**Version:** 1.0

---

## Executive Summary

The Share Page completes the ResuMate user journey by allowing users to share their parsed resume data across multiple platforms. Users can generate shareable links with expiration controls, export to WhatsApp/Telegram/Email, and download professional PDF resumes.

**Business Value:** Enables users to easily share their resume data with recruiters, colleagues, and across platforms, completing the core MVP value proposition.

---

## Architecture Overview

### High-Level Flow

```
┌──────────────┐
│ Review Page  │
│ (User clicks  │
│  "Share")     │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              Backend API (FastAPI)                       │
│  ┌────────────────┐  ┌────────────────┐                │
│  │ Share Token    │  │ Export         │                │
│  │ Generation     │  │ Endpoints      │                │
│  └────────────────┘  └────────────────┘                │
└──────┬──────────────────────────┬───────────────────────┘
       │                          │
       ▼                          ▼
┌──────────────┐          ┌──────────────┐
│ Share Page   │          │ PDF/Link     │
│ (Frontend)   │          │ Generation   │
└──────────────┘          └──────────────┘
```

### Technology Stack

**Backend:**
- FastAPI endpoints for share management
- In-memory share storage (similar to current resume storage)
- ReportLab for PDF generation
- Platform-specific link formatting (WhatsApp, Telegram)

**Frontend:**
- React 18 + TypeScript
- lucide-react icons
- Copy-to-clipboard functionality
- Royal elegant UI (navy/gold theme)

---

## Database Schema

### Share Storage Model

**For MVP:** In-memory storage (following `storage.py` pattern)

```python
# In-memory store: {share_token: share_metadata}
_share_store: Dict[str, dict] = {}

{
  "abc123xyz": {
    "resume_id": "uuid-123",
    "share_token": "abc123xyz",
    "access_count": 23,
    "expires_at": "2026-02-26T12:00:00Z",
    "is_active": True,
    "created_at": "2026-02-19T12:00:00Z"
  }
}
```

**Future Production:** PostgreSQL `resume_shares` table (already defined in models)

### Storage Operations

- `create_share(resume_id, expires_at)` - Generate unique token, store metadata
- `get_share(share_token)` - Retrieve share metadata
- `increment_access(share_token)` - Track access count
- `revoke_share(share_token)` - Deactivate share link
- `is_share_valid(share_token)` - Check expiration and active status

---

## API Design

### Share Management Endpoints

#### 1. Create/Get Share Token
```
POST /v1/resumes/{resume_id}/share
```

**Request:**
```json
{
  "expires_in_days": 7  // Optional, defaults to 30
}
```

**Response (202):**
```json
{
  "share_token": "abc123xyz",
  "share_url": "https://resumate.app/share/abc123xyz",
  "expires_at": "2026-03-19T12:00:00Z",
  "created_at": "2026-02-19T12:00:00Z"
}
```

**Behavior:**
- Generate UUID-based share token
- If share exists for resume, return existing (unless expired)
- Store in `_share_store`
- Calculate expiration timestamp

---

#### 2. Get Share Details
```
GET /v1/resumes/{resume_id}/share
```

**Response (200):**
```json
{
  "share_token": "abc123xyz",
  "share_url": "https://resumate.app/share/abc123xyz",
  "access_count": 23,
  "expires_at": "2026-03-19T12:00:00Z",
  "is_active": true,
  "created_at": "2026-02-19T12:00:00Z"
}
```

---

#### 3. Update Share Settings
```
PATCH /v1/resumes/{resume_id}/share
```

**Request:**
```json
{
  "expires_in_days": 14,  // Update expiration
  "is_active": false       // Or revoke
}
```

**Response (200):**
```json
{
  "share_token": "abc123xyz",
  "updated": true,
  "expires_at": "2026-03-05T12:00:00Z"
}
```

---

#### 4. Revoke Share
```
DELETE /v1/resumes/{resume_id}/share
```

**Response (200):**
```json
{
  "revoked": true,
  "message": "Share link has been revoked"
}
```

---

### Public Access Endpoint

#### 5. Access Shared Resume (Public)
```
GET /v1/share/{share_token}
```

**Response (200):**
```json
{
  "resume_id": "uuid-123",
  "personal_info": { /* parsed data */ },
  "work_experience": [ /* ... */ ],
  "education": [ /* ... */ ],
  "skills": { /* ... */ },
  "shared_at": "2026-02-19T12:00:00Z",
  "access_count": 24  // Incremented
}
```

**Error Responses:**
- `404` - Share token not found
- `410` - Share link expired
- `403` - Share link revoked

---

### Export Endpoints

#### 6. Export as PDF
```
GET /v1/resumes/{resume_id}/export/pdf
```

**Response:** Binary PDF file
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="john_doe_resume.pdf"
```

**PDF Layout:**
```
┌──────────────────────────────────────┐
│         JOHN DOE                     │
│         Software Engineer            │
│                                      │
│  📧 john@example.com                 │
│  📱 +1-555-0123                      │
│  📍 San Francisco, CA                │
│  🔔 linkedin.com/in/johndoe          │
│                                      │
│  WORK EXPERIENCE                     │
│  ──────────────────────────────────  │
│  Senior Software Engineer            │
│  Tech Corp (2020 - Present)          │
│  • Led team of 5 engineers           │
│  • Implemented microservices         │
│                                      │
│  Software Engineer                   │
│  StartupXYZ (2018 - 2020)            │
│  • Full-stack development            │
│                                      │
│  EDUCATION                           │
│  ──────────────────────────────────  │
│  B.S. Computer Science               │
│  MIT (2014 - 2018)                   │
│                                      │
│  SKILLS                              │
│  ──────────────────────────────────  │
│  Technical: Python, React, AWS       │
│  Soft Skills: Leadership, Agile      │
│  Languages: English, Spanish         │
└──────────────────────────────────────┘
```

---

#### 7. Export to WhatsApp
```
GET /v1/resumes/{resume_id}/export/whatsapp
```

**Response (200):**
```json
{
  "whatsapp_url": "https://wa.me/?text=...",
  "message": "WhatsApp link generated successfully"
}
```

**Text Format:**
```
📄 *John Doe - Software Engineer*

📧 Email: john@example.com
📱 Phone: +1-555-0123
📍 Location: San Francisco, CA

💼 *Work Experience:*
• Senior Software Engineer at Tech Corp (2020-Present)
• Software Engineer at StartupXYZ (2018-2020)

🎓 *Education:*
• B.S. Computer Science at MIT (2014-2018)

🛠️ *Skills:*
• Technical: Python, React, AWS
• Languages: English, Spanish
```

---

#### 8. Export to Telegram
```
GET /v1/resumes/{resume_id}/export/telegram
```

**Response (200):**
```json
{
  "telegram_url": "https://t.me/share/url?url=...",
  "message": "Telegram link generated successfully"
}
```

**Text Format:** Similar to WhatsApp, Telegram Markdown formatted

---

#### 9. Export to Email
```
POST /v1/resumes/{resume_id}/export/email
```

**Request:**
```json
{
  "to": "recruiter@company.com",
  "subject": "My Resume - John Doe",
  "body": "Dear Hiring Manager,\n\nPlease find my resume attached..."
}
```

**Response (202):**
```json
{
  "sent": true,
  "message": "Email sent successfully"
}
```

**MVP Alternative:** Generate `mailto:` link for client-side email

---

## Frontend Design

### Share Page Component

**Route:** `/share/:id`

**Component Structure:**
```typescript
<SharePage>
  <ShareHeader />
  <ShareLinkCard />
  <ExportButtons />
  <ShareSettings />
  <LivePreview />
</SharePage>
```

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│                    ResuMate                             │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  📤 Share Your Resume                                    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 🔗 Share Link                                    │    │
│  │                                                   │    │
│  │ https://resumate.app/share/abc123...              │    │
│  │                                                   │    │
│  │        [📋 Copy to Clipboard]                     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  Export As:                                               │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │    │
│  │  📄    │ │ 📱     │ │ ✈️     │ │  ✉️    │        │    │
│  │  PDF   │ │WhatsApp│ │Telegram│ │ Email  │        │    │
│  └────────┘ └────────┘ └────────┘ └────────┘        │    │
│                                                           │
│  ⚙️ Share Settings                                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │ ⏰ Expires in:  [7 days ▼]                       │    │
│  │ 👁️ Accessed:     23 times                        │    │
│  │ 🚫 [Revoke Link]                                  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  👁️ Live Preview                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  John Doe                                        │    │
│  │  Software Engineer                               │    │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━       │    │
│  │                                                   │    │
│  │  📧 john@example.com  |  📱 +1-555-0123          │    │
│  │  📍 San Francisco, CA                           │    │
│  │                                                   │    │
│  │  💼 Work Experience                               │    │
│  │  • Senior Software Engineer at Tech Corp          │    │
│  │  • Software Engineer at StartupXYZ                │    │
│  │                                                   │    │
│  │  [View Full Resume]                               │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  [← Back to Review]                                      │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### User Interactions

**1. Copy Link to Clipboard**
- Click "Copy to Clipboard" button
- Show success toast: "Link copied!"
- Button changes briefly to "✓ Copied"

**2. Export to PDF**
- Click "Download PDF" button
- Show loading state: "Generating PDF..."
- Browser downloads file
- Show success toast: "PDF downloaded!"

**3. Export to WhatsApp/Telegram**
- Click platform button
- Open new tab with pre-filled share link
- User confirms send in app

**4. Export to Email**
- Click "Email" button
- Open email client with `mailto:` link
- Pre-filled subject and body

**5. Update Expiration**
- Change dropdown (7 days, 14 days, 30 days, Never)
- Auto-save with optimistic update
- Show success toast: "Expiration updated!"

**6. Revoke Link**
- Click "Revoke Link" button
- Show confirmation dialog
- On confirm, deactivate link
- Show message: "Link revoked. Share page no longer accessible."

---

## Error Handling

### Error Scenarios

**1. Share Token Not Found (404)**
```typescript
// Frontend display
<div className="text-center py-12">
  <AlertCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
  <h2 className="text-2xl font-bold text-navy-900 mb-2">
    Link Not Found
  </h2>
  <p className="text-gray-600 mb-6">
    This share link doesn't exist or has been removed.
  </p>
  <Link to="/" className="btn-primary">
    Upload Your Resume
  </Link>
</div>
```

**2. Share Link Expired (410)**
```typescript
<div className="text-center py-12">
  <Clock className="h-16 w-16 text-orange-600 mx-auto mb-4" />
  <h2 className="text-2xl font-bold text-navy-900 mb-2">
    Link Expired
  </h2>
  <p className="text-gray-600 mb-2">
    This link expired on {expirationDate}.
  </p>
  <p className="text-gray-600 mb-6">
    Please contact the resume owner to request a new link.
  </p>
</div>
```

**3. Share Link Revoked (403)**
```typescript
<div className="text-center py-12">
  <XCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
  <h2 className="text-2xl font-bold text-navy-900 mb-2">
    Link Revoked
  </h2>
  <p className="text-gray-600 mb-6">
    This link has been revoked by the owner.
  </p>
</div>
```

**4. PDF Generation Failure (500)**
```typescript
// Fallback to text export
<div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
  <div className="flex">
    <AlertCircle className="h-6 w-6 text-yellow-400 mr-2" />
    <p className="text-yellow-700">
      Unable to generate PDF. Please try again or use WhatsApp/Telegram export.
    </p>
  </div>
</div>
```

**5. Network Errors**
```typescript
// Toast notification
toast.error('Network error. Please check your connection and try again.', {
  position: 'top-right',
  autoClose: 5000
})
```

---

## Security Considerations

### Share Token Security

**Token Generation:**
- Use `uuid.uuid4()` for uniqueness (128-bit random)
- No sequential or predictable patterns
- 64-character hexadecimal representation

**Access Control:**
- Public access via share token (no authentication required)
- Revocation capability for owner control
- Expiration time limits exposure window

**Rate Limiting:**
- Prevent abuse: Max 10 share creations per resume per hour
- Public endpoint: Max 100 requests per IP per minute
- Use in-memory counters for MVP (Redis in production)

### Data Privacy

**No Sensitive Data in URLs:**
- Share tokens are random UUIDs, not resume IDs
- No PII exposed in URLs or logs

**GDPR Compliance:**
- Share metadata includes creation timestamp
- Data deletion on resume deletion
- Revocation = data access removal

---

## Testing Strategy

### Backend Tests

**Unit Tests (`backend/tests/unit/test_share_storage.py`):**
```python
def test_create_share_generates_unique_token()
def test_create_share_sets_expiration_correctly()
def test_get_share_returns_metadata()
def test_get_share_returns_none_for_invalid_token()
def test_increment_access_increases_count()
def test_revoke_share_deactivates_link()
def test_is_share_valid_checks_expiration()
def test_is_share_valid_checks_active_status()
```

**Integration Tests (`backend/tests/integration/test_api_shares.py`):**
```python
def test_create_share_returns_202()
def test_create_share_generates_unique_url()
def test_get_share_returns_200()
def test_get_share_returns_404_for_invalid_resume()
def test_update_share_modifies_expiration()
def test_revoke_share_deactivates_link()
def test_public_share_access_returns_resume_data()
def test_public_share_access_increments_count()
def test_expired_share_returns_410()
def test_revoked_share_returns_403()
```

**Export Tests (`backend/tests/integration/test_api_exports.py`):**
```python
def test_export_pdf_returns_binary_pdf()
def test_export_pdf_sets_content_type()
def test_export_whatsapp_generates_correct_url()
def test_export_telegram_generates_correct_url()
def test_export_email_returns_mailto_link()
```

### Frontend Tests

**Component Tests (`frontend/src/pages/__tests__/SharePage.test.tsx`):**
```typescript
describe('SharePage', () => {
  it('renders share link correctly')
  it('copies link to clipboard on button click')
  it('displays export buttons')
  it('shows loading state during PDF generation')
  it('displays error message for invalid share token')
  it('displays expired link message')
  it('updates expiration on dropdown change')
  it('revokes link on confirmation')
})
```

**Integration Tests:**
```typescript
describe('Share Flow Integration', () => {
  it('navigates from review to share page')
  it('loads share data from API')
  it('exports to PDF successfully')
  it('exports to WhatsApp opens new tab')
  it('handles export errors gracefully')
})
```

### E2E Test

**Complete Flow (`backend/tests/e2e/test_share_flow.py`):**
```python
def test_complete_share_flow():
    """
    Test: Upload → Process → Review → Share → Export
    """
    # Upload resume
    # Get parsed data
    # Create share token
    # Access public share page
    # Verify resume data matches
    # Export PDF
    # Verify PDF download
    # Revoke share
    # Verify access denied
```

---

## Implementation Tasks

### Task 1: Share Storage Service
**Files:**
- Create: `backend/app/core/share_storage.py`
- Create: `backend/tests/unit/test_share_storage.py`

**Step 1:** Write failing tests for share storage
**Step 2:** Implement in-memory share store
**Step 3:** Run tests to verify passing
**Step 4:** Commit

---

### Task 2: Share API Endpoints
**Files:**
- Create: `backend/app/api/shares.py`
- Create: `backend/tests/integration/test_api_shares.py`
- Modify: `backend/app/main.py` (include shares router)

**Step 1:** Write failing tests for share endpoints
**Step 2:** Implement CRUD endpoints for shares
**Step 3:** Run tests to verify passing
**Step 4:** Commit

---

### Task 3: Export Endpoints
**Files:**
- Create: `backend/app/services/export_service.py`
- Create: `backend/tests/integration/test_api_exports.py`

**Step 1:** Write failing tests for export endpoints
**Step 2:** Implement PDF generation (ReportLab)
**Step 3:** Implement WhatsApp/Telegram link generation
**Step 4:** Run tests to verify passing
**Step 5:** Commit

---

### Task 4: Share Page UI Components
**Files:**
- Create: `frontend/src/pages/SharePage.tsx`
- Create: `frontend/src/components/ShareLinkCard.tsx`
- Create: `frontend/src/components/ExportButtons.tsx`
- Create: `frontend/src/components/ShareSettings.tsx`
- Create: `frontend/src/pages/__tests__/SharePage.test.tsx`

**Step 1:** Write failing component tests
**Step 2:** Implement SharePage component
**Step 3:** Implement child components
**Step 4:** Run tests to verify passing
**Step 5:** Run TypeScript type-check
**Step 6:** Commit

---

### Task 5: Frontend API Integration
**Files:**
- Modify: `frontend/src/services/api.ts` (add share methods)
- Modify: `frontend/src/types/index.ts` (add share types)
- Modify: `frontend/src/pages/ReviewPage.tsx` (add Share button)

**Step 1:** Add share API methods to api service
**Step 2:** Update ReviewPage with "Share" button
**Step 3:** Add navigation to Share page
**Step 4:** Test integration manually
**Step 5:** Commit

---

### Task 6: Testing & Polish
**Files:**
- Create: `backend/tests/e2e/test_share_flow.py`
- Modify: `README.md` (document share functionality)
- Modify: `docs/PROGRESS.md` (update progress)

**Step 1:** Write E2E test for complete share flow
**Step 2:** Run all tests (backend + frontend)
**Step 3:** Manual testing of all export methods
**Step 4:** Update documentation
**Step 5:** Final commit

---

## Dependencies

### Backend Dependencies (Add to `requirements.txt`)

```txt
# PDF Generation
reportlab==4.0.7
# or
fpdf2==2.7.6

# Alternative: WeasyPrint (HTML to PDF)
# weasyprint==60.1
```

### Frontend Dependencies (Add to `package.json`)

```json
{
  "dependencies": {
    "react-hot-toast": "^2.4.1"  // Toast notifications
  }
}
```

---

## Success Criteria

### Functional Requirements
- ✅ Users can generate shareable links
- ✅ Share links have configurable expiration
- ✅ Users can download PDF resumes
- ✅ Users can export to WhatsApp, Telegram, Email
- ✅ Share access is tracked (access count)
- ✅ Share links can be revoked
- ✅ Public share page displays formatted resume data

### Non-Functional Requirements
- ✅ Share tokens are cryptographically unique
- ✅ PDF generation completes in <5 seconds
- ✅ All endpoints have comprehensive error handling
- ✅ 100% test coverage for share functionality
- ✅ UI is responsive and mobile-friendly
- ✅ Royal elegant design consistent with existing pages

### User Experience
- ✅ Copy-to-clipboard works seamlessly
- ✅ Export buttons provide clear feedback
- ✅ Error messages are user-friendly
- ✅ Loading states indicate progress
- ✅ Live preview matches exported data

---

## Future Enhancements

### Post-MVP Features
1. **Database Persistence** - Replace in-memory with PostgreSQL
2. **Custom Themes** - Allow users to customize PDF appearance
3. **Multiple Templates** - Offer different resume PDF layouts
4. **Analytics Dashboard** - Track share link engagement
5. **QR Code Generation** - Generate QR codes for share links
6. **Password Protection** - Optional password for shared links
7. **Bulk Export** - Export multiple resumes at once
8. **Integration APIs** - API for third-party integrations (LinkedIn, etc.)

---

**Document Status:** ✅ Approved
**Next Step:** Create detailed TDD implementation plan
**Created:** 2026-02-19
