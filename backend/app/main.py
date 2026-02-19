"""
FastAPI application entry point for ResuMate API.

This module initializes the FastAPI application with CORS middleware,
includes all API routers, and defines health check endpoints.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import resumes
from app.api.websocket import manager

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
