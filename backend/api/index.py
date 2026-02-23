"""
Vercel serverless function entry point for ResuMate API.

This file wraps the FastAPI application with Mangum to work
with Vercel's serverless functions (AWS Lambda).
"""

from mangum import Mangum
from app.main import app

# Wrap FastAPI app with Mangum for AWS Lambda compatibility
handler = Mangum(app, lifespan="off")
