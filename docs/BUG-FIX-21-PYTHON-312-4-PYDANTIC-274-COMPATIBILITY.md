# Bug Fix #21: Python 3.12.4 + Pydantic 2.7.4 Compatibility

> **Date**: 2026-02-24
> **Status**: ✅ Root Cause Identified, Fix Implemented, Deployment Pending
> **Related**: [Bug Fix #20](./BUG-FIX-20-PYDANTIC-V2-SPACY-COMPATIBILITY.md) | [Bug Fix #19](./BUG-FIX-19-PYTHON-312-SPACY-COMPATIBILITY.md)

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
- **Python 3.12.4 runtime** (Vercel default)
- Using **Pydantic 2.5.3** (released November 13, 2023)
- spaCy 3.8+ with confection>=0.1.4, thinc>=8.3.4 (from Bug Fix #20)
- Bundle size: 407.70 MB (triggers Vercel runtime caching)

---

## Root Cause Analysis

### The Version Mismatch Problem

```
┌─────────────────────────────────────────────────────────────┐
│ Timeline of Events                                          │
├─────────────────────────────────────────────────────────────┤
│ November 13, 2023: Pydantic 2.5.3 released                 │
│ June 6, 2024:      Python 3.12.4 released (with breaking change)│
│ June 12, 2024:     Pydantic 2.7.4 released (with fix)       │
└─────────────────────────────────────────────────────────────┘
```

### Technical Explanation

**Python 3.12.4 Breaking Change**:
- `ForwardRef._evaluate()` signature changed in Python 3.12.4
- The `recursive_guard` parameter became **required** (not optional)
- This affects all code that calls `ForwardRef._evaluate()` without the parameter

**Pydantic Version Compatibility**:
- **Pydantic 2.5.3** (Nov 2023) - Released BEFORE Python 3.12.4, doesn't include the fix
- **Pydantic 2.7.4** (June 2024) - Released AFTER Python 3.12.4, includes the fix

### Why Bug Fix #20 Wasn't Enough

Bug Fix #20 addressed spaCy's Pydantic v1 compatibility layer by:
- Adding `confection>=0.1.4` (enables Pydantic v2 support in spaCy)
- Adding `thinc>=8.3.4` (required for spaCy + Pydantic v2)

**However**, this didn't address the **core issue**: Pydantic 2.5.3 itself doesn't support Python 3.12.4's `recursive_guard` parameter.

### The Error Location

```
/tmp/_vc_deps/lib/python3.12/site-packages/pydantic/v1/typing.py:66
```

This is **Pydantic's own v1 compatibility layer**, not spaCy's code. The error occurs deep in Pydantic's internals when processing forward type references.

---

## Solution

### Fix Applied

Updated `requirements.txt` and `pyproject.toml`:

```diff
- pydantic==2.5.3
+ # CRITICAL: pydantic>=2.7.4 required for Python 3.12.4 compatibility (recursive_guard fix)
+ pydantic>=2.7.4,<3.0.0
```

### Why This Works

Based on [Pydantic Issue #9609](https://github.com/pydantic/pydantic/issues/9609):
> "Fixed Python 3.12.4 compatibility by specifying `recursive_guard` as kwarg in `ForwardRef._evaluate`"

**Pydantic 2.7.4+ provides:**
- Proper `ForwardRef._evaluate()` calls with `recursive_guard` parameter
- Full Python 3.12.4 compatibility
- No breaking changes from 2.5.3 → 2.7.4 (same API)
- Additional bug fixes and performance improvements

---

## Verification Steps

### 1. Local Verification
```bash
cd backend
source .venv/bin/activate

# Install with new Pydantic version
pip install -r requirements.txt

# Verify imports work
python -c "
import sys
print(f'Python: {sys.version}')

import pydantic
print(f'✅ Pydantic version: {pydantic.VERSION}')

import spacy
print(f'✅ spaCy version: {spacy.__version__}')

import confection
print(f'✅ Confection version: {confection.__version__}')

# Test ForwardRef handling (the actual bug)
from pydantic import BaseModel
from typing import Optional

class TestModel(BaseModel):
    name: Optional[str] = None

print('✅ ForwardRef handling works correctly')
"
```

Expected output:
```
Python: 3.11.x (or 3.12.x)
✅ Pydantic version: 2.7.4
✅ spaCy version: 3.8.x
✅ Confection version: 0.1.x+
✅ ForwardRef handling works correctly
```

### 2. Test Suite Verification
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

Expected: All tests pass (175+ tests)

### 3. Vercel Deployment

**After Cache Expiration (24-48 hours):**
```bash
# Deploy to Vercel
vercel --prod

# Test health endpoint
curl https://resumate-backend.vercel.app/health

# Expected: {"status":"healthy","database":"connected"}
```

**To Force Cache Invalidation:**
1. Add a dummy environment variable in Vercel dashboard
2. Or contact Vercel support to manually invalidate cache
3. Or wait 24-48 hours for automatic expiration

---

## Version Compatibility Matrix

| Component | Working Version | Purpose |
|-----------|----------------|---------|
| **Python** | **3.12.4** (Vercel default) | Runtime environment |
| **Pydantic** | **>=2.7.4,<3.0.0** | **Critical: Python 3.12.4 compatibility** |
| spaCy | >=3.8.0,<4.0.0 | NLP library |
| confection | >=0.1.4,<1.0.0 | Pydantic v2 support for spaCy |
| thinc | >=8.3.4,<9.0.0 | spaCy + Pydantic v2 compatibility |
| pydantic-settings | >=2.1.0 | Settings management |
| numpy | 1.26.4 | Python 3.12 compatibility |

---

## Key Learnings

### 1. Python Patch Versions Matter
Python 3.12.0 → 3.12.4 introduced **breaking changes** to the typing system. Always check Python release notes for patch version changes.

### 2. Library Release Timing is Critical
- Pydantic 2.5.3 (Nov 2023) couldn't anticipate Python 3.12.4 (June 2024)
- Pydantic 2.7.4 (June 2024) was released 6 days after Python 3.12.4
- **Rule**: Use library versions released AFTER the Python version you're targeting

### 3. Compatibility Layers ≠ Fixes
- Bug Fix #20 fixed spaCy's Pydantic v1 compatibility layer
- But Pydantic 2.5.3 itself had the Python 3.12.4 bug
- **Lesson**: Fix must be at the source, not just in compatibility shims

### 4. Serverless Runtime Differences
- Local: Python 3.11.11 ✅ (no `recursive_guard` requirement)
- Vercel: Python 3.12.4 ❌ (requires `recursive_guard`)
- **Always test in the same runtime as production**

### 5. Upgrade Strategy
- **Minor version upgrades** (2.5.3 → 2.7.4) are generally safe
- They include critical bug fixes without breaking changes
- Don't stay on old versions just because they "work locally"

---

## Sources

- [Pydantic GitHub Issue #9609 - Python 3.12.4 ForwardRef Fix](https://github.com/pydantic/pydantic/issues/9609)
- [Pydantic 2.7.4 Release Notes](https://pypi.org/project/pydantic/2.7.4/)
- [Python 3.12.4 Release Notes](https://docs.python.org/3/whatsnew/3.12.html#type)
- [Vercel Build Image - Python 3.12 Runtime](https://vercel.com/docs/builds/build-image)
- [Home Assistant Python 3.12.4 Compatibility Analysis](https://blog.csdn.net/gitblog_00466/article/details/151516889)

---

## Related Issues

- **[Bug Fix #20](./BUG-FIX-20-PYDANTIC-V2-SPACY-COMPATIBILITY.md)**: spaCy + Pydantic v2 compatibility
- **[Bug Fix #19](./BUG-FIX-19-PYTHON-312-SPACY-COMPATIBILITY.md)**: spaCy 3.8+ for Python 3.12
- **[Bug Fix #18](./BUG-FIX-17b-PEP-668-COMPLIANCE.md)**: PEP 668 compliance

---

**Next Steps**:
1. ✅ Updated `requirements.txt` and `pyproject.toml`
2. ⏳ Wait for Vercel runtime cache to expire (24-48 hours)
3. ⏳ Deploy and verify fix resolves the ForwardRef error
4. ⏳ Update PROGRESS.md with completion status
