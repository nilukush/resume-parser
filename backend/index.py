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

try:
    from mangum import Mangum
    from app.main import app

    # Vercel requires a module-level 'handler' variable
    # This wraps the FastAPI ASGI app for AWS Lambda compatibility
    handler = Mangum(app, lifespan="off")
except Exception as e:
    # Create a fallback handler that returns error details
    import traceback
    error_details = {
        "error": str(e),
        "traceback": traceback.format_exc(),
        "python_version": sys.version
    }

    def handler(event, context):
        return {
            "statusCode": 500,
            "body": str(error_details),
            "headers": {"Content-Type": "application/json"}
        }
