"""
API module for ResuMate application.

This module initializes and exports all API routers.
"""

from app.api.resumes import router as resumes_router

__all__ = ["resumes_router"]
