# Debugging Session: Share Links & Export Buttons Broken

**Date:** 2026-02-22
**Session:** Bug Fix #15
**Severity:** Critical (blocking core functionality)
**Status:** ✅ RESOLVED

---

## Problem Statement

After database integration was completed (Bug Fix #13), two critical issues emerged:

1. **Share Links Return "Failed to Fetch"**: When users open a public share link (e.g., `/shared/{token}`), the frontend shows "Failed to load shared resume. Failed to fetch."

2. **Export Buttons Do Nothing**: Clicking "Export as PDF", "Share via WhatsApp", or "Share via Email" buttons does nothing. Only Telegram export works.

**User Impact**: High - Share and export are core features of the application.

---

## Investigation Process

### Step 1: Reproduce the Issue

**Share Link Test:**
```bash
curl http://localhost:8000/v1/share/184f0edd-122f-4986-b1ba-50f93bebae5e
# Result: 500 Internal Server Error
```

**Backend Log Analysis:**
```
File "database_share_storage.py", line 161, in is_share_valid
    if datetime.utcnow() > expires_at:
                    ^^^^^^^^
NameError: name 'timezone' is not defined
```

Wait, the error said `timezone` is not defined, but we were calling `datetime.utcnow()`! Let me check the code more carefully...

**PDF Export Test:**
```bash
curl http://localhost:8000/v1/resumes/{id}/export/pdf
# Result: 500 Internal Server Error
```

**Backend Log Analysis:**
```
File "shares.py", line 369, in export_resume_pdf
    resume_data = await _get_parsed_resume(resume_id, db)
                                                      ^^
NameError: name 'db' is not defined
```

### Step 2: Root Cause Analysis

#### Issue #1: Datetime Comparison Bug

**Location:** `backend/app/services/database_share_storage.py:161`

**The Code:**
```python
# Check expiration
expires_at = datetime.fromisoformat(share["expires_at"])
if datetime.utcnow() > expires_at:  # ❌ BUG!
    return False
```

**Why It Failed:**
1. PostgreSQL `TIMESTAMP WITH TIME ZONE` columns return timezone-aware datetimes
   - Example: `2026-03-24T02:32:13.711392+00:00`
2. `datetime.fromisoformat()` preserves the timezone information
3. `datetime.utcnow()` returns a **timezone-naive** datetime
4. Python 3 **strictly prohibits** comparing naive vs aware datetimes
5. Result: `TypeError: can't compare offset-naive and offset-aware datetimes`

**Why It Wasn't Caught Earlier:**
- In-memory storage used naive datetimes, so comparison worked
- Database integration switched to PostgreSQL which uses timezone-aware datetimes
- The existing tests for `is_share_valid()` were broken (missing resume in database due to foreign key)

**Additional Issue - Missing Import:**
When I first tried to fix it by changing to `datetime.now(timezone.utc)`, I got:
```
NameError: name 'timezone' is not defined
```

The `timezone` module wasn't imported! This needed to be added:
```python
from datetime import datetime, timedelta, timezone  # ✅ Added timezone
```

#### Issue #2: Missing FastAPI Dependencies

**Location:** `backend/app/api/shares.py` lines 352, 394, 472

**The Code:**
```python
@router.get("/v1/resumes/{resume_id}/export/pdf")
async def export_resume_pdf(resume_id: str) -> FastAPIResponse:  # ❌ Missing db parameter
    resume_data = await _get_parsed_resume(resume_id, db)  # db is undefined!
```

**Why It Failed:**
1. FastAPI's `Depends()` injects dependencies into route handlers
2. The `db` dependency must be **explicitly declared** in the function signature
3. These three endpoints were missing the `db=Depends(get_db)` parameter
4. When the code tried to use `db`, it was undefined
5. Result: `NameError: name 'db' is not defined`

**Why Telegram Export Worked:**
```python
@router.get("/v1/resumes/{resume_id}/export/telegram", response_model=TelegramExportResponse)
async def export_resume_telegram(resume_id: str, db=Depends(get_db)) -> Dict:  # ✅ Has db parameter!
```

The Telegram export endpoint (line 428) had the correct parameter. The other three endpoints were likely copied from an older version before database integration, or the parameter was accidentally removed during refactoring.

---

## Solution

### Fix #1: Datetime Comparison

**File:** `backend/app/services/database_share_storage.py`

**Line 12 - Add Missing Import:**
```python
from datetime import datetime, timedelta, timezone  # ✅ Added timezone
```

**Line 161 - Fix Comparison:**
```python
# OLD (naive datetime):
if datetime.utcnow() > expires_at:  # ❌ TypeError

# NEW (timezone-aware):
if datetime.now(timezone.utc) > expires_at:  # ✅ Works!
```

**Why This Fix Is Correct:**
- `datetime.now(timezone.utc)` returns a timezone-aware datetime in UTC
- Both sides of the comparison are now timezone-aware
- No more TypeError
- Follows Python 3 best practices (`datetime.utcnow()` is deprecated in Python 3.12+)

### Fix #2: Export Endpoint Dependencies

**File:** `backend/app/api/shares.py`

**Line 352 - PDF Export:**
```python
@router.get("/v1/resumes/{resume_id}/export/pdf")
async def export_resume_pdf(resume_id: str, db=Depends(get_db)) -> FastAPIResponse:  # ✅ Added db parameter
```

**Line 394 - WhatsApp Export:**
```python
@router.get("/v1/resumes/{resume_id}/export/whatsapp", response_model=WhatsAppExportResponse)
async def export_resume_whatsapp(resume_id: str, db=Depends(get_db)) -> Dict:  # ✅ Added db parameter
```

**Line 472 - Email Export:**
```python
@router.get("/v1/resumes/{resume_id}/export/email", response_model=EmailExportResponse)
async def export_resume_email(resume_id: str, db=Depends(get_db)) -> Dict:  # ✅ Added db parameter
```

---

## Verification

### Automated Tests

**Test Script:** `/tmp/test_share_and_export.py`

```python
import requests

BASE_URL = "http://localhost:8000"
RESUME_ID = "2b837bc9-7af5-460f-a7c2-55f1cbf0b5d1"
SHARE_TOKEN = "184f0edd-122f-4986-b1ba-50f93bebae5e"

# Test 1: Public Share
response = requests.get(f"{BASE_URL}/v1/share/{SHARE_TOKEN}")
assert response.status_code == 200
assert response.json()["personal_info"]["full_name"] == "Radhakanta Ghosh"

# Test 2: PDF Export
response = requests.get(f"{BASE_URL}/v1/resumes/{RESUME_ID}/export/pdf")
assert response.status_code == 200
assert response.headers["content-type"] == "application/pdf"

# Test 3: WhatsApp Export
response = requests.get(f"{BASE_URL}/v1/resumes/{RESUME_ID}/export/whatsapp")
assert response.status_code == 200
assert response.json()["whatsapp_url"].startswith("https://wa.me/")

# Test 4: Email Export
response = requests.get(f"{BASE_URL}/v1/resumes/{RESUME_ID}/export/email")
assert response.status_code == 200
assert response.json()["mailto_url"].startswith("mailto:")

# Test 5: Telegram Export (Regression Test)
response = requests.get(f"{BASE_URL}/v1/resumes/{RESUME_ID}/export/telegram")
assert response.status_code == 200
```

**Result:** ✅ All 5 tests passed!

### Manual Browser Testing

1. **Share Link Test:**
   - Opened: `http://localhost:3000/shared/184f0edd-122f-4986-b1ba-50f93bebae5e`
   - Result: ✅ Page loaded with full resume data

2. **Export Buttons Test:**
   - PDF Export: ✅ Downloaded PDF file
   - WhatsApp Export: ✅ Opened WhatsApp URL
   - Email Export: ✅ Opened email client
   - Telegram Export: ✅ Opened Telegram (regression test passed)

---

## Lessons Learned

### 1. Timezone Handling Best Practices

**❌ Avoid:**
```python
datetime.utcnow()  # Deprecated in Python 3.12+, returns naive datetime
```

**✅ Use:**
```python
datetime.now(timezone.utc)  # Returns timezone-aware datetime
```

**Why:**
- PostgreSQL stores timestamps as timezone-aware by default
- Comparing naive vs aware datetimes raises TypeError
- Timezone-aware datetimes prevent bugs in distributed systems
- `datetime.utcnow()` is deprecated and will be removed in Python 3.12+

### 2. FastAPI Dependency Injection

**❌ Common Mistake:**
```python
async def endpoint(id: str):
    data = await some_function(id, db)  # ❌ db is undefined!
```

**✅ Correct Pattern:**
```python
async def endpoint(id: str, db=Depends(get_db)):
    data = await some_function(id, db)  # ✅ db is injected
```

**Why:**
- FastAPI dependencies are NOT automatically available
- They must be explicitly declared in function signatures
- When copying endpoint code, always verify all parameters
- Static analysis tools can't catch this (dependencies injected at runtime)

### 3. Testing Strategy

**When Integration Tests Are Broken:**
- Use direct API testing with `curl` for quick verification
- Test with real data from the database
- Don't rely solely on unit tests for database-related bugs

**Event Loop Issues in Tests:**
- If tests fail with "Task attached to a different loop", check event loop setup
- Ensure test database has proper schema and foreign key relationships
- Consider using API testing tools (Postman, curl) for faster iteration

---

## Related Documentation

- [Database Setup Guide](DATABASE_SETUP.md)
- [Bug Fix #13: Share Endpoint 404](DEBUGGING-SESSION-2026-02-21-FIXES.md)
- [PROGRESS.md - Bug Fix #15](../PROGRESS.md)

---

## Files Modified

1. **`backend/app/services/database_share_storage.py`**
   - Line 12: Added `timezone` to imports
   - Line 161: Changed `datetime.utcnow()` to `datetime.now(timezone.utc)`

2. **`backend/app/api/shares.py`**
   - Line 352: Added `db=Depends(get_db)` to PDF export endpoint
   - Line 394: Added `db=Depends(get_db)` to WhatsApp export endpoint
   - Line 472: Added `db=Depends(get_db)` to Email export endpoint

---

## Conclusion

Both issues were straightforward bugs that emerged during database integration:

1. **Datetime bug**: Language-level protection (TypeError) prevented a subtle timezone bug
2. **Missing dependencies**: Runtime error when undefined variable was accessed

The fixes were minimal (4 lines total) but critical for functionality. All share and export features are now fully operational with database persistence.
