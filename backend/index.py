"""
Vercel serverless function entry point for ResuMate API.

This file wraps the FastAPI application with Mangum to work
with Vercel's serverless functions.
"""

import sys
from pathlib import Path

# Add backend directory to Python path for imports
# backend/index.py needs to find app.main in the same directory
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from mangum import Mangum
from app.main import app

# Vercel requires a module-level 'handler' variable
# This wraps the FastAPI ASGI app for AWS Lambda compatibility
handler = Mangum(app, lifespan="off")
