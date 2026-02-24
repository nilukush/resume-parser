# Bug Fix #20: Pydantic v2 + spaCy Compatibility on Python 3.12

> **Date**: 2026-02-24
> **Status**: ✅ Root Cause Identified, Fix Implemented, Awaiting Deployment
> **Related**: [Bug Fix #19](./BUG-FIX-19-PYTHON-312-SPACY-COMPATIBILITY.md)

---

## Problem Statement

### Error
```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
```

### Stack Trace
```
File "/tmp/_vc_deps/lib/python3.12/site-packages/pydantic/v1/typing.py", line 66, in evaluate_forwardref
    return cast(Any, type_)._evaluate(globalns, localns, set())
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
```

### Context
- Deploying to Vercel serverless
- Python 3.12 runtime
- Using spaCy 3.8+ with Pydantic 2.5.3
- Bundle size: 407.70 MB (triggers Vercel runtime caching)

---

## Root Cause Analysis

### The Three-Layer Problem

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Vercel Runtime Cache (407.70 MB bundle)           │
│     → /tmp/_vc_deps/ (Cached dependencies, ignores req.txt)│
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Pydantic v1 Compatibility Layer                   │
│     → Old spaCy imports pydantic.v1 instead of pydantic v2 │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Missing confection >= 0.1.4                        │
│     → confection < 0.1.4 doesn't support Pydantic v2       │
└─────────────────────────────────────────────────────────────┘
```

### Technical Explanation

**Python 3.12 Change**: `ForwardRef._evaluate()` signature changed
```python
# Python 3.11 and earlier
def _evaluate(self, globalns, localns, frozenset()): ...

# Python 3.12+
def _evaluate(self, globalns, localns, recursive_guard): ...  # recursive_guard is REQUIRED
```

**spaCy + Pydantic v2 Compatibility**:
- spaCy uses `confection` package for configuration
- `confection < 0.1.4` uses `pydantic.v1` compatibility layer
- `pydantic.v1` compatibility layer has Python 3.12 ForwardRef bug
- **Solution**: `confection >= 0.1.4` has native Pydantic v2 support

### Why requirements.txt Changes Didn't Work

**Vercel Runtime Caching Behavior**:
- When bundle > 250MB, Vercel caches runtime dependencies for 24-48 hours
- Cached deps are installed at `/tmp/_vc_deps/` (as seen in error)
- These cached dependencies IGNORE your `requirements.txt` changes
- Cache expires automatically after 24-48 hours OR via support request

---

## Solution

### Fix Applied

Updated `requirements.txt` and `pyproject.toml` to include:

```diff
+# CRITICAL: confection>=0.1.4 enables Pydantic v2 support for spaCy
+confection>=0.1.4,<1.0.0
+# CRITICAL: thinc>=8.3.4 required for spaCy + Pydantic v2 compatibility
+thinc>=8.3.4,<9.0.0
```

### Why This Works

Based on [spaCy GitHub Discussion #13350](https://github.com/explosion/spaCy/discussions/13350):
> "Upgraded confection==0.1.4 and I can import spacy 3.7.4 with pydantic 2.6.1!!"

`confection >= 0.1.4` provides:
- Native Pydantic v2 support (no compatibility layer)
- Proper ForwardRef handling for Python 3.12
- Direct integration with pydantic 2.x types

---

## Verification Steps

### 1. Local Verification
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Verify imports work
python -c "
import spacy
print('✅ spaCy imported successfully')

import pydantic
print(f'✅ Pydantic version: {pydantic.VERSION}')

import confection
print(f'✅ Confection version: {confection.__version__}')

from spacy.tokens import Doc
print('✅ spacy.tokens.Doc imported successfully')
"
```

Expected output:
```
✅ spaCy imported successfully
✅ Pydantic version: 2.5.3
✅ Confection version: 0.1.4
✅ spacy.tokens.Doc imported successfully
```

### 2. Vercel Deployment

**Option A: Wait for Cache Expiration (24-48 hours)**
- Vercel's runtime cache expires automatically
- After expiration, new requirements will be used

**Option B: Force Cache Invalidation**
1. Add a dummy environment variable change in Vercel dashboard
2. Or contact Vercel support to invalidate cache manually

**Option C: Reduce Bundle Size Below 250MB (Long-term Solution)**
- Remove Celery/Redis dependencies (not needed for serverless)
- Remove Sentry if not critical
- Use `.vercelignore` to exclude unnecessary files

### 3. Post-Deployment Verification
```bash
# Check deployment logs
vercel logs --build

# Test health endpoint
curl https://resumate-backend.vercel.app/health

# Expected: {"status":"healthy","database":"connected"}
```

---

## Version Compatibility Matrix

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12.x | Runtime environment |
| spaCy | >=3.8.0,<4.0.0 | NLP library |
| **confection** | **>=0.1.4,<1.0.0** | **Critical: Pydantic v2 support** |
| **thinc** | **>=8.3.4,<9.0.0** | **Required for spaCy + Pydantic v2** |
| Pydantic | 2.5.3 | Validation library |
| numpy | 1.26.4 | Python 3.12 compatibility |

---

## Sources

- [spaCy GitHub Discussion #13350 - Pydantic v2 Compatibility](https://github.com/explosion/spaCy/discussions/13350)
- [spaCy GitHub Issue #13550 - Python 3.12 ForwardRef Error](https://github.com/explosion/spaCy/issues/13550)
- [Python 3.12 Release Notes - typing.ForwardRef changes](https://docs.python.org/3/whatsnew/3.12.html#type)
- [Pydantic Python 3.12 Compatibility](https://github.com/pydantic/pydantic/issues/9609)

---

## Related Issues

- **[Bug Fix #19](./BUG-FIX-19-PYTHON-312-SPACY-COMPATIBILITY.md)**: Initial spaCy 3.8+ upgrade
- **[Bug Fix #18](./BUG-FIX-17b-PEP-668-COMPLIANCE.md)**: PEP 668 compliance

---

## Lessons Learned

### 1. Always Check Transitive Dependencies
`confection` is a transitive dependency of `spaCy`, but version constraints matter!

### 2. Vercel Runtime Cache Can Block Dependency Updates
When bundle > 250MB, cached dependencies at `/tmp/_vc_deps/` ignore requirements.txt changes.

### 3. Pydantic v1 Compatibility Layer is a Trap
Old packages importing `pydantic.v1` will break on Python 3.12+. Use packages with native v2 support.

### 4. Native Support > Compatibility Layers
`confection >= 0.1.4` uses native Pydantic v2, avoiding the `pydantic.v1` compatibility issues.

---

**Next Steps**: Deploy to Vercel and verify the fix resolves the ForwardRef error.
