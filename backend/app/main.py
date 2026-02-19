"""
FastAPI application entry point for ResuMate API.

This module initializes the FastAPI application with CORS middleware,
includes all API routers, and defines health check endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import resumes

# Create FastAPI application instance
app = FastAPI(
    title="ResuMate API",
    description="Smart Resume Parser API",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(resumes.router)


@app.get("/health")
def health_check() -> dict:
    """
    Health check endpoint.

    Returns the current health status and version of the API.
    This endpoint is used by load balancers and monitoring systems
    to verify the API is running.

    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
