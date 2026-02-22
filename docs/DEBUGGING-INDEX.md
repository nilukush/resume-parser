# Debugging Sessions Index

**Last Updated:** 2026-02-22 | **Total Bug Fixes:** 15
**Purpose:** Quick reference for all debugging sessions and common solutions

---

## Quick Reference Table

| Date | Issue | Solution | File | Status |
|------|-------|----------|------|--------|
| 2026-02-21 | UUID generation format mismatch | Changed `secrets.token_urlsafe(16)` to `uuid4()` | [Details](./archive/DEBUGGING-UUID-ISSUE-2026-02-21.md) | RESOLVED |
| 2026-02-21 | WebSocket connection cleanup | State validation before send, connection deduplication | [Details](./archive/DEBUGGING-WEBSOCKET-2026-02-21.md) | RESOLVED |
| 2026-02-21 | Share endpoint 404, WebSocket serialization | Database-backed shares, JSON serialization helper | [Details](./archive/DEBUGGING-SESSION-2026-02-21-FIXES.md) | RESOLVED |
| 2026-02-21 | Upload flow failure | Upload endpoint saves metadata before background task | [Details](./archive/DEBUGGING-SESSION-2026-02-21.md) | RESOLVED |
| 2026-02-22 | Processing page stuck at 100% | Added handler for `stage: 'complete'` in WebSocket messages | See PROGRESS.md Bug Fix #14 | RESOLVED |
| 2026-02-22 | Share links & export buttons broken | Datetime comparison fix + missing db dependencies | [Details](./DEBUGGING-SESSION-2026-02-22-SHARE-EXPORT-FIXES.md) | RESOLVED |

**Files to check:** `backend/app/api/shares.py`

---

### Processing Page Stuck at 100%

**Symptoms:**
- All processing stages show 100% complete
- Page never redirects to review page
- WebSocket shows `complete` stage received

**Solution:**
- Backend sends `{type: "progress_update", stage: "complete"}`
- Frontend must handle `stage: 'complete'` case, not just `type: 'complete'`

**Files to check:** `frontend/src/pages/ProcessingPage.tsx`

**Code pattern:**
```typescript
case 'complete':
  // Mark all stages as complete and trigger redirect
  newStages[0] = { ...newStages[0], status: 'complete', progress: 100 }
  newStages[1] = { ...newStages[1], status: 'complete', progress: 100 }
  newStages[2] = { ...newStages[2], status: 'complete', progress: 100 }
  break

// After switch, trigger redirect
if (message.stage === 'complete') {
  handleComplete(message)
}
```

---

## Common Error Patterns

### UUID Format Errors

**Symptoms:**
- `invalid UUID 'xxx': length must be between 32..36 characters, got 22`
- Database inserts failing silently

**Solution:**
```python
# WRONG - generates 22-char strings
id = secrets.token_urlsafe(16)

# CORRECT - generates proper UUID
from uuid import uuid4
id = uuid4()
```

**Files to check:** `backend/app/services/database_storage.py`

---

### WebSocket Serialization Errors

**Symptoms:**
- `Object of type UUID is not JSON serializable`
- WebSocket closes unexpectedly after parsing completes

**Solution:**
```python
def _serialize_for_websocket(data: Any) -> Any:
    """Recursively convert complex types to JSON-serializable formats."""
    if isinstance(data, dict):
        return {k: _serialize_for_websocket(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_serialize_for_websocket(item) for item in data]
    elif isinstance(data, UUID):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, Decimal):
        return float(data)
    return data
```

**Files to check:** `backend/app/services/parser_orchestrator.py`

---

### Database Transaction Rollbacks

**Symptoms:**
- Data appears to save but disappears
- `UniqueViolationError` on file_hash

**Solution:**
- Save Resume metadata before background task
- Validate schema before insert
- Use proper async context managers

**Files to check:** `backend/app/api/resumes.py`, `backend/app/services/storage_adapter.py`

---

### Share Link 404 Errors

**Symptoms:**
- `POST /v1/resumes/{id}/share` returns 404
- Shares work in development but not production

**Solution:**
- Ensure `USE_DATABASE=true` in production
- Import from `database_share_storage` not `share_storage`
- Add `db=Depends(get_db)` to share endpoints

**Files to check:** `backend/app/api/shares.py`

---

### Datetime Comparison Errors

**Symptoms:**
- `TypeError: can't compare offset-naive and offset-aware datetimes`
- Share validation fails with 500 error

**Solution:**
```python
# WRONG - returns naive datetime
from datetime import datetime
if datetime.utcnow() > expires_at:  # ❌ TypeError

# CORRECT - returns timezone-aware datetime
from datetime import datetime, timezone
if datetime.now(timezone.utc) > expires_at:  # ✅ Works!
```

**Why This Happens:**
- PostgreSQL `TIMESTAMP WITH TIME ZONE` returns timezone-aware datetimes
- `datetime.utcnow()` returns naive datetime (no timezone info)
- Python 3 prohibits comparing naive vs aware datetimes
- `datetime.utcnow()` is deprecated in Python 3.12+

**Files to check:** `backend/app/services/database_share_storage.py`

---

### FastAPI Dependency Errors

**Symptoms:**
- `NameError: name 'db' is not defined`
- Endpoint works for one function but not another

**Solution:**
```python
# WRONG - missing db parameter
@router.get("/v1/resumes/{id}/export/pdf")
async def export_pdf(id: str):
    data = await get_resume(id, db)  # ❌ db is undefined

# CORRECT - db parameter declared
@router.get("/v1/resumes/{id}/export/pdf")
async def export_pdf(id: str, db=Depends(get_db)):
    data = await get_resume(id, db)  # ✅ db is injected
```

**Files to check:** `backend/app/api/shares.py`, `backend/app/api/resumes.py`

---

## Files Modified in Bug Fixes

### Bug Fix #8: UUID Generation
- `backend/app/services/database_storage.py` - Lines 21, 257, 372, 475

### Bug Fix #10: WebSocket Cleanup
- `backend/app/api/websocket.py` - State validation in `broadcast_to_resume()`
- `frontend/src/hooks/useWebSocket.ts` - Connection cleanup logic
- `backend/app/services/parser_orchestrator.py` - Removed artificial delay

### Bug Fix #13: Share Endpoint & Serialization
- `backend/app/services/database_share_storage.py` - NEW FILE
- `backend/app/api/shares.py` - Storage abstraction layer
- `backend/app/services/parser_orchestrator.py` - `_serialize_for_websocket()`

### Bug Fix #14: Processing Page Stuck at 100%
- `frontend/src/pages/ProcessingPage.tsx` - Added `complete` stage handler in `updateStageProgress()`

### Bug Fix #15: Share Links & Export Buttons Broken
- `backend/app/services/database_share_storage.py` - Fixed datetime comparison (line 161), added timezone import (line 12)
- `backend/app/api/shares.py` - Added `db=Depends(get_db)` to PDF, WhatsApp, Email export endpoints (lines 352, 394, 472)

---

## Debugging Checklist

When investigating new issues:

1. **Check logs first**
   ```bash
   tail -f /tmp/backend.log | grep -i error
   docker logs resumate-postgres
   ```

2. **Verify environment variables**
   ```bash
   grep USE_DATABASE backend/.env
   grep DATABASE_URL backend/.env
   ```

3. **Test database connection**
   ```bash
   docker exec resumate-postgres psql -U resumate_user -d resumate -c "SELECT 1;"
   ```

4. **Check WebSocket in browser console**
   - Network tab → WS filter
   - Look for connection close codes
   - Check message payload format

5. **Verify data types**
   - UUID columns must use `uuid.uuid4()`
   - DateTime objects need `.isoformat()` for JSON
   - Decimal needs `float()` for JSON

---

## Archived Debugging Sessions

Detailed logs of debugging sessions are archived in `./archive/`:
- `DEBUGGING-UUID-ISSUE-2026-02-21.md` - UUID format mismatch (351 lines)
- `DEBUGGING-WEBSOCKET-2026-02-21.md` - WebSocket connection issues (295 lines)
- `DEBUGGING-SESSION-2026-02-21.md` - Upload flow failure (59 lines)
- `DEBUGGING-SESSION-2026-02-21-FIXES.md` - Share endpoint fixes (489 lines)

**Total archived:** 1,194 lines

**Compaction ratio:** ~70% reduction (from 1,194 to ~200 index lines)

---

**Status:** Active
**Last Session:** 2026-02-22
**All Issues:** RESOLVED (15 total bug fixes)
