"""
Vercel serverless function entry point for ResuMate API.

This file wraps the FastAPI application with Mangum to work
with Vercel's serverless functions (AWS Lambda).

CRITICAL: The handler must be a module-level variable for Vercel's
function detection to work correctly. Do NOT wrap this in a function.
"""

from mangum import Mangum
from app.main import app

# Wrap FastAPI app with Mangum for AWS Lambda compatibility
# NOTE: This must be a module-level variable named "handler"
handler = Mangum(app, lifespan="off")
