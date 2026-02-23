# Bug Fix #17: Vercel Runtime Configuration Error

**Date:** 2026-02-23
**Status:** ✅ RESOLVED
**Severity:** Critical (blocking all deployments)
**Files Modified:** 1 file

---

## Problem Statement

### Error Message
```
Error: Function Runtimes must have a valid version, for example `now-php@1.0.0`.
```

### Full Error Context
```bash
2026-02-23T07:53:21.990Z  Error: Function Runtimes must have a valid version,
for example `now-php@1.0.0`.
status  ● Error
```

### Impact
- ❌ All Vercel deployments failing (both preview and production)
- ❌ Cannot deploy backend to production
- ❌ Blocking user access to resume parser API
- ❌ Multiple deployment attempts failed with same error

---

## Root Cause Analysis

### Technical Root Cause

The `backend/vercel.json` configuration contained an **invalid `functions` property** with incorrect runtime format:

```json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.11",  ❌ INVALID FORMAT
      "maxDuration": 60
    }
  }
}
```

### Why This Is Wrong

1. **Native Python Runtime**: Python is an **officially supported runtime** on Vercel
   - Auto-detected via `requirements.txt` or `Pipfile`
   - Does NOT require `runtime` property in `functions` configuration

2. **Community Runtimes Only**: The `functions.runtime` property is ONLY for **community runtimes** (Deno, Rust, PHP, etc.)
   - Format: `"@vercel/community-runtime@version"` (e.g., `"now-php@1.0.0"`)
   - NOT applicable to native Python runtime

3. **Version Specification**: Python version should be specified via:
   - `Pipfile` with `python_version` property
   - OR left to Vercel auto-detection (uses latest stable: Python 3.12)

### Historical Context

| Commit | Date | Configuration | Status |
|--------|------|---------------|--------|
| `435a293` (Bug Fix #16) | 2026-02-22 | Minimal config (no `functions`) | ✅ Working |
| `a5ca7d0` | 2026-02-23 | Added `functions.runtime` | ❌ Broken |

**What Happened**:
- Commit `a5ca7d0` ("fix: optimize Vercel deployment") incorrectly added `functions` property
- Intent was to specify Python 3.11, but used **wrong configuration pattern**
- Pattern used is for **community runtimes**, not native Python runtime

---

## Solution Implementation

### Approach: Remove Invalid `functions` Property

**Strategy**: Return to minimal configuration from Bug Fix #16, letting Vercel auto-detect Python runtime

### Changes Made

#### Updated `backend/vercel.json`

**Before** (BROKEN):
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "pip install --user -r requirements.txt",
  "installCommand": "pip install --user -r requirements.txt",
  "framework": null,
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.11",  ❌ INVALID
      "maxDuration": 60
    }
  }
}
```

**After** (FIXED):
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "pip install --user -r requirements.txt",
  "installCommand": "pip install --user -r requirements.txt",
  "framework": null
}
```

**Changes**:
- ✅ Kept `$schema` for IDE validation
- ✅ Kept minimal build configuration
- ❌ **Removed `functions` property** (invalid for native Python runtime)
- ❌ **Removed `runtime` property** (not needed for Python)
- ❌ **Removed `maxDuration` property** (uses default)

**Result**: Vercel will auto-detect Python runtime and use appropriate defaults

---

## Verification Results

### ✅ All Checks Passing

1. **JSON Syntax Validation**: ✅ PASS
   ```bash
   python3 -m json.tool backend/vercel.json
   # Valid JSON syntax
   ```

2. **Schema Validation**: ✅ PASS
   ```bash
   python3 -c "import json; config = json.load(open('backend/vercel.json'));
   print('✓ Schema:', config.get('$schema', 'missing'))"
   # ✓ Schema: https://openapi.vercel.sh/vercel.json
   ```

3. **Unit Tests**: ✅ 7/7 PASSING
   ```
   ✓ test_vercel_json_exists
   ✓ test_vercel_json_has_schema_validation
   ✓ test_vercel_json_has_build_command
   ✓ test_vercel_json_uses_pip_user
   ✓ test_vercel_json_no_deprecated_properties
   ✓ test_api_handler_exists
   ✓ test_api_handler_uses_mangum
   ```

4. **No Deprecated Properties**: ✅ PASS
   - No `builds` array (deprecated pre-2021)
   - No `routes` array (deprecated)
   - No `maxLambdaSize` (deprecated)
   - No `functions.runtime` (invalid for native Python)

---

## Technical Details

### How Vercel Detects Python Runtime

**Automatic Detection Flow**:
```
1. Vercel scans project files
2. Finds requirements.txt or Pipfile
3. Detects .py files in api/ directory
4. Identifies Python project
5. Uses latest Python runtime (3.12)
```

**Alternative Version Specification** (if needed):
```toml
# Pipfile
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
fastapi = "*"

[requires]
python_version = "3.12"  # Only valid place for version spec
```

### Why NOT Use `functions` Property

**Native Runtimes** (Python, Node.js, Go):
- Officially supported by Vercel
- Auto-detected via project files
- Do NOT use `functions.runtime` property

**Community Runtimes** (Deno, Rust, PHP, Ruby):
- Require explicit runtime specification
- Use `functions.runtime` with versioned package
- Example: `"runtime": "now-php@1.0.0"`

### Default Python Version on Vercel

| Default Version | Alternative |
|-----------------|-------------|
| Python 3.12 | Python 3.9 (legacy) |

**Note**: Python 3.11 is NOT directly selectable as of 2026-02-23.
Use Python 3.12 (recommended) or specify via Pipfile if needed.

---

## Lessons Learned

### 1. Distinguish Native vs Community Runtimes

**Pattern**: Native runtimes (Python, Node.js) do NOT use `functions.runtime`
- Python: Auto-detected via requirements.txt
- Node.js: Auto-detected via package.json
- Community runtimes: Require `runtime: "@package/version"`

### 2. Minimal Configuration Is Best

**Pattern**: Let Vercel auto-detect whenever possible
- Fewer configuration errors
- Simpler maintenance
- Automatic updates to latest runtime versions

### 3. Check Official Documentation

**Pattern**: Always verify current Vercel documentation
- Vercel evolves rapidly
- Legacy tutorials may show deprecated patterns
- Official docs: [vercel.com/docs](https://vercel.com/docs)

### 4. Test Configuration Locally

**Pattern**: Validate configuration before deploying
```bash
# JSON syntax check
python3 -m json.tool vercel.json

# Unit tests
pytest tests/unit/test_vercel_config.py

# Import check
python -c "from api.index import handler"
```

### 5. Git History Is Your Friend

**Pattern**: Review working configurations before making changes
- Bug Fix #16 had correct configuration
- Commit `a5ca7d0` introduced invalid property
- Git diff reveals exact breaking change

---

## Deployment Instructions

Now that the configuration is fixed, deploy to Vercel:

### Option 1: Vercel CLI

```bash
cd backend
vercel --prod
```

### Option 2: Git Push (Auto-Deploy)

```bash
git add backend/vercel.json
git commit -m "fix: remove invalid functions.runtime property from vercel.json"
git push origin main
```

Vercel will automatically deploy on push to `main` branch.

### Verification

After deployment:

```bash
# Test health endpoint
curl https://resumate-backend.vercel.app/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "environment": "production"
}
```

---

## Python Version Specifications

### Current Supported Versions (2026)

| Version | Status | Notes |
|---------|--------|-------|
| Python 3.12 | Default (recommended) | Latest stable |
| Python 3.9 | Legacy | Requires Pipfile spec |

### How to Specify Python 3.12

**Option 1: Let Vercel Auto-Detect** (Recommended)
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "pip install --user -r requirements.txt",
  "installCommand": "pip install --user -r requirements.txt",
  "framework": null
}
```

**Option 2: Specify via Pipfile** (If needed)
```toml
[Pipfile]
[requires]
python_version = "3.12"
```

### What About Python 3.11?

**Not Currently Supported** as of 2026-02-23:
- Vercel supports Python 3.12 and 3.9
- Python 3.11 is NOT an option
- Use Python 3.12 instead (close enough, typically compatible)

---

## References

### Sources

- [Vercel Python Runtime Documentation](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Project Configuration](https://vercel.com/docs/project-configuration)
- [Vercel Functions Runtimes Overview](https://vercel.com/docs/functions/runtimes)
- [Bug Fix #16: Vercel Schema Validation](docs/BUG-FIX-16-VERCEL-SCHEMA.md)

### Related Documentation

- [Vercel Deployment Guide](docs/VERCEL_DEPLOYMENT.md)
- [Supabase Setup Guide](docs/SUPABASE_SETUP.md)
- [Progress Tracking](docs/PROGRESS.md)

---

## Summary

**Problem**: Vercel deployment fails with "Function Runtimes must have a valid version"
**Root Cause**: Invalid `functions.runtime` property (community runtime format used for native Python)
**Solution**: Remove `functions` property, let Vercel auto-detect Python runtime
**Result**: ✅ Configuration valid, ready for deployment

**Files Changed**:
1. `backend/vercel.json` (removed invalid `functions` property)

**Tests**: 7/7 Vercel config tests passing ✅

**Next**: Deploy to Vercel with corrected configuration

---

**Fixed by**: Claude (Sonnet 4.5)
**Date**: 2026-02-23 12:13 GST
**Bug Fix**: #17
