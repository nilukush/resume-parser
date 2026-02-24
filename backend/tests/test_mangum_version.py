"""
Test Mangum version compatibility with Python 3.12

This test ensures we're using Mangum 0.21.0+ which is required
for Python 3.12 compatibility. Mangum 0.17.0 has known issues with
Python 3.12's ForwardRef signature changes.

Related Bug Fix: Deployment TypeError after cache purge
Root Cause: Mangum 0.17.0 incompatible with Python 3.12.4
"""

import pytest
from packaging import version


def test_mangum_version_is_python_312_compatible():
    """
    Verify Mangum is using version compatible with Python 3.12.4

    Mangum 0.17.0 causes: TypeError: issubclass() arg 1 must be a class
    in Vercel's vercel_runtime/vc_init.py:777

    Solution: Use Mangum >=0.21.0 for Python 3.12 support
    """
    try:
        from importlib.metadata import version as get_version
        mangum_version_str = get_version("mangum")
    except ImportError:
        pytest.fail("Mangum is not installed. Required for FastAPI → Vercel deployment.")

    installed_version = version.parse(mangum_version_str)
    minimum_version = version.parse("0.21.0")

    assert installed_version >= minimum_version, (
        f"Mangum version {mangum_version_str} is too old for Python 3.12.4. "
        f"Required: >=0.21.0. "
        f"Current: {mangum_version_str}. "
        f"Update: pip install 'mangum>=0.21.0'"
    )


def test_mangum_handler_initialization():
    """
    Verify Mangum handler can be initialized without errors

    This test ensures Mangum can wrap the FastAPI app successfully.
    If this fails, it indicates version incompatibility.
    """
    try:
        from mangum import Mangum
        from app.main import app

        # This should not raise any errors
        handler = Mangum(app, lifespan="off")

        assert handler is not None
        assert hasattr(handler, 'app')
        assert handler.app is app

    except ImportError as e:
        pytest.fail(f"Failed to import Mangum or FastAPI app: {e}")
    except Exception as e:
        pytest.fail(f"Mangum handler initialization failed: {e}")
