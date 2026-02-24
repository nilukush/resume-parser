# Python Runtime and Dependency Version Requirements

**Last Updated:** 2026-02-24
**Related Bug Fix:** #22 (Mangum 0.21.0+ for Python 3.12 compatibility)

---

## Minimum Versions

| Component | Minimum Version | Recommended Version | Reason |
|-----------|----------------|---------------------|--------|
| **Python** | 3.10+ | 3.12.4 | Pydantic 2.x requirement; Production runtime |
| **Pydantic** | >=2.7.4 | 2.7.4+ | Python 3.12.4 `recursive_guard` fix (Bug Fix #21) |
| **Mangum** | >=0.21.0 | 0.21.0+ | Python 3.12 compatibility (Bug Fix #22) |
| **spaCy** | >=3.8.0 | 3.8.11+ | Pydantic 2.x native support (Bug Fix #19) |
| **numpy** | 1.26.4 | 1.26.4 | Python 3.12 prebuilt wheels |
| **FastAPI** | 0.109.0 | 0.109.0 | Project minimum (tested) |
| **confection** | >=0.1.4 | 0.1.4+ | Pydantic v2 compatibility (Bug Fix #20) |
| **thinc** | >=8.3.4 | 8.3.4+ | Pydantic v2 compatibility (Bug Fix #20) |

---

## Known Incompatibilities

### ❌ **DO NOT USE**

| Component | Version | Reason | Alternative |
|-----------|---------|--------|-------------|
| **Mangum** | 0.17.0 | Python 3.12 incompatible → `TypeError: issubclass()` | Use >=0.21.0 |
| **Pydantic** | 2.5.3 | Missing `recursive_guard` for Python 3.12.4 | Use >=2.7.4 |
| **spaCy** | 3.7.2 | Pydantic v1 compatibility layer only | Use >=3.8.0 |
| **numpy** | 1.24.4 | No Python 3.12 wheels (builds from source) | Use 1.26.4 |
| **Python** | <3.10 | Pydantic 2.x requires Python 3.10+ | Use Python 3.12.4 |

---

## Deployment Environment

### Vercel Serverless Functions

**Runtime:** Python 3.12.4
**Bundle Size Limit:** 250MB (after compression)
**Current Bundle Size:** ~407MB (triggers runtime dependency caching)

**Important Notes:**
- Vercel caches runtime dependencies when bundle > 250MB
- Cache persists for 24-48 hours
- To force cache refresh: Use `--force` flag or contact Vercel support
- Bundle size optimization is recommended long-term (remove Celery/Redis/Sentry)

---

## Verification

### Quick Version Check

```bash
# Check all critical versions
source .venv/bin/activate
python -c "
from importlib.metadata import version
versions = {
    'mangum': '0.21.0',
    'pydantic': '2.7.4',
    'spacy': '3.8.0',
    'numpy': '1.26.4'
}
for pkg, min_ver in versions.items():
    try:
        installed = version(pkg)
        print(f'{pkg}: {installed} (min: {min_ver})')
    except Exception as e:
        print(f'{pkg}: NOT INSTALLED')
"
```

### Run Tests

```bash
# Run Mangum version test
python -m pytest tests/test_mangum_version.py -v

# Run all tests
python -m pytest tests/ -v
```

---

## Bug Fix History

### Bug Fix #22 (2026-02-24)
**Problem:** TypeError: issubclass() arg 1 must be a class in Vercel deployment
**Root Cause:** Mangum 0.17.0 incompatible with Python 3.12.4
**Solution:** Upgrade to Mangum >=0.21.0
**Files Changed:**
- `requirements.txt` - Updated mangum==0.17.0 to mangum>=0.21.0,<1.0.0
- `tests/test_mangum_version.py` - Added version compatibility test

### Bug Fix #21 (2026-02-24)
**Problem:** Pydantic missing `recursive_guard` parameter for Python 3.12.4
**Root Cause:** Pydantic 2.5.3 incompatible with Python 3.12.4 ForwardRef changes
**Solution:** Upgrade to Pydantic >=2.7.4
**Documentation:** `docs/BUG-FIX-21-PYTHON-312-4-PYDANTIC-274-COMPATIBILITY.md`

### Bug Fix #20 (2026-02-23)
**Problem:** spaCy + confection + thinc Pydantic v2 compatibility
**Root Cause:** spaCy 3.8+ requires confection>=0.1.4, thinc>=8.3.4 for Pydantic v2
**Solution:** Added version constraints for confection and thinc
**Documentation:** `docs/BUG-FIX-20-PYDANTIC-V2-SPACY-COMPATIBILITY.md`

### Bug Fix #19 (2026-02-23)
**Problem:** spaCy 3.7.2 incompatible with Python 3.12
**Root Cause:** spaCy 3.7.2 uses Pydantic v1 compatibility layer
**Solution:** Upgrade to spaCy >=3.8.0
**Documentation:** `docs/BUG-FIX-19-PYTHON-312-SPACY-COMPATIBILITY.md`

---

## Deployment Commands

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Vercel Deployment

```bash
# From backend directory
cd /Users/nileshkumar/gh/resume-parser/backend

# Link project (first time only)
vercel link --scope nilukushs-projects

# Deploy to production (force rebuild without cache)
vercel --force --prod --scope nilukushs-projects
```

---

## Troubleshooting

### TypeError: issubclass() arg 1 must be a class

**Symptoms:**
```
File "/var/task/_vendor/vercel_runtime/vc_init.py", line 777, in <module>
    if not issubclass(base, BaseHTTPRequestHandler):
TypeError: issubclass() arg 1 must be a class
```

**Causes:**
1. Mangum 0.17.0 installed (incompatible with Python 3.12)
2. Stale Vercel runtime cache (old dependencies)

**Solutions:**
1. Verify Mangum version: `pip show mangum` (should be >=0.21.0)
2. Update requirements.txt: `mangum>=0.21.0,<1.0.0`
3. Force redeploy: `vercel --force --prod`
4. If cache persists: Contact Vercel support for manual cache invalidation

### ImportError: No module named 'mangum'

**Cause:** Mangum not installed or virtual environment not activated

**Solution:**
```bash
source .venv/bin/activate
pip install 'mangum>=0.21.0,<1.0.0'
```

### Vercel deployment succeeds but /health returns 500 error

**Possible Causes:**
1. Lazy database initialization failing (check DATABASE_URL)
2. Missing environment variables in Vercel dashboard
3. SpaCy model not downloaded (en_core_web_sm)

**Solutions:**
1. Check Vercel deployment logs
2. Verify environment variables in Vercel dashboard
3. Download spaCy model: `python -m spacy download en_core_web_sm`

---

## Support Resources

- [Mangum GitHub Repository](https://github.com/jordaneremieff/mangum)
- [Vercel Python Runtime Documentation](https://vercel.com/docs/functions/runtimes/python)
- [Pydantic 2.7.4 Release Notes](https://pypi.org/project/pydantic/2.7.4/)
- [spaCy 3.8+ Compatibility](https://github.com/explosion/spaCy/releases/tag/v3.8.0)

---

**Maintained by:** ResuMate Development Team
**Last Reviewed:** 2026-02-24
