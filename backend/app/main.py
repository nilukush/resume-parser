"""
FastAPI application entry point for ResuMate API.

This module initializes the FastAPI application with CORS middleware,
includes all API routers, and defines health check endpoints.
"""

import logging
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api import resumes, shares
from app.api.websocket import manager

# Setup logging
logger = logging.getLogger(__name__)

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
app.include_router(shares.router)


@app.websocket("/ws/resumes/{resume_id}")
async def websocket_endpoint(websocket: WebSocket, resume_id: str):
    """
    WebSocket endpoint for real-time resume parsing updates.

    This endpoint establishes a WebSocket connection for a specific resume
    and maintains it for the duration of the parsing operation, sending
    real-time progress updates to the client.

    Args:
        websocket: The WebSocket connection instance
        resume_id: The unique identifier for the resume being processed
    """
    await manager.connect(websocket, resume_id)
    try:
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle any client messages (like ping/pong)
            if data == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "message": "alive"},
                    websocket,
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket, resume_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, resume_id)


@app.get("/health", tags=["health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint for monitoring and load balancers.

    Returns system status including database connectivity.
    This endpoint is used by Render, load balancers, and monitoring systems
    to verify the API is running and healthy.

    Returns:
        JSONResponse: Health status with database connectivity check

    Status Codes:
        200: System is healthy (database connected)
        503: System is unhealthy (database disconnected)
    """
    from sqlalchemy import text
    from fastapi.responses import JSONResponse
    from datetime import datetime

    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "unknown",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Check database connectivity
    try:
        # Simple query to verify database connection
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = "disconnected"
        health_status["status"] = "unhealthy"
        health_status["database_error"] = str(e)
        logger.error(f"Health check failed: {e}")

    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(content=health_status, status_code=status_code)
