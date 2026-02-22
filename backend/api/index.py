"""
Vercel serverless function entry point for ResuMate API.

This file serves as the adapter between Vercel's Python runtime
and our FastAPI application. Vercel's Python runtime expects
a handler function in the api/ directory.
"""

from app.main import app

# Vercel Python runtime looks for this handler
# ASGI applications are supported directly
handler = app
