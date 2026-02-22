"""
Vercel serverless function handler for ResuMate FastAPI application.

This module serves as the entry point for Vercel's serverless functions,
adapting the FastAPI ASGI application to work with Vercel's Python runtime
using the Mangum adapter.

The handler is automatically detected by Vercel when deployed to the
/platforms environment.

See: https://vercel.com/docs/functions/runtimes/python
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mangum import Mangum
from app.main import app

"""
Vercel serverless handler.

This handler adapts the FastAPI ASGI application to work with Vercel's
serverless Python runtime. Mangum transforms the ASGI application into
a AWS Lambda-compatible handler function.

FastAPI → Mangum Adapter → Vercel Serverless Function

Example:
    When deployed, Vercel automatically discovers this file and uses
    the 'handler' as the entry point for all HTTP requests.

    Request → Vercel → handler → Mangum → FastAPI → Response
"""
handler = Mangum(app, lifespan="off")

__all__ = ["handler"]
