"""
Resume upload API endpoints.

This module provides endpoints for uploading and processing resumes.
The main endpoint is POST /v1/resumes/upload which accepts resume files
in PDF, DOCX, DOC, or TXT format.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from typing import Dict, Optional
from pydantic import BaseModel
import hashlib
import uuid
import asyncio

from app.api.websocket import manager
from app.services.parser_orchestrator import ParserOrchestrator
from app.core.storage import get_parsed_resume, update_parsed_resume

# File type validation constants
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}
ALLOWED_MIME_TYPES = {
    # PDF formats
    "application/pdf",
    # DOCX format
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # Legacy DOC format
    "application/msword",
    # Text format
    "text/plain",
}

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Create router with prefix and tags
router = APIRouter(prefix="/v1/resumes", tags=["resumes"])

# Create orchestrator instance for background parsing
orchestrator = ParserOrchestrator(manager)


# Pydantic models for request/response
class ResumeUpdateRequest(BaseModel):
    """Request model for updating parsed resume data"""
    personal_info: Optional[dict] = None
    work_experience: Optional[list] = None
    education: Optional[list] = None
    skills: Optional[dict] = None


class ResumeResponse(BaseModel):
    """Response model for resume data"""
    resume_id: str
    status: str
    data: Optional[dict] = None
    message: Optional[str] = None


def _validate_file_type(filename: str, content_type: str) -> tuple[bool, str | None]:
    """
    Validate file type by extension and MIME type.

    Args:
        filename: The uploaded file's name
        content_type: The file's MIME type from the upload

    Returns:
        tuple: (is_valid, error_message)
    """
    if not filename:
        return False, "No filename provided"

    # Check file extension
    file_extension = filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return False, f"Unsupported file type. Allowed: {allowed}"

    # Check MIME type (more reliable than extension)
    if content_type not in ALLOWED_MIME_TYPES:
        return False, f"Unsupported MIME type: {content_type}"

    return True, None


async def parse_resume_background(resume_id: str, filename: str, content: bytes):
    """
    Background task to parse resume and send progress updates.

    This function runs asynchronously after a file is uploaded,
    orchestrating the parsing pipeline and broadcasting progress
    updates via WebSocket to connected clients.

    Args:
        resume_id: Unique identifier for this resume
        filename: Original filename of the uploaded file
        content: Raw file content as bytes

    Note:
        Errors are logged but not raised to prevent background task
        failures from affecting the HTTP response.
    """
    try:
        await orchestrator.parse_resume(resume_id, filename, content)
    except Exception as e:
        # Log error but don't raise - background task should not fail visibly
        print(f"Background parsing error for {resume_id}: {e}")


@router.post("/upload", status_code=202)
async def upload_resume(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
) -> Dict:
    """
    Upload a resume for parsing and processing.

    This endpoint accepts resume files in PDF, DOCX, DOC, or TXT format.
    Files are validated for type and size before processing begins.
    Processing happens asynchronously in the background, so the endpoint
    returns 202 Accepted. Progress updates are sent via WebSocket.

    Args:
        file: The uploaded resume file
        background_tasks: FastAPI BackgroundTasks for async processing

    Returns:
        dict: Contains resume_id, status, estimated_time_seconds,
              file_hash, and websocket_url

    Raises:
        HTTPException: 400 if file type or size validation fails
    """
    # Validate file type
    is_valid, error_message = _validate_file_type(file.filename, file.content_type)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=error_message
        )

    # Read file content for validation and hashing
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {max_size_mb:.0f}MB"
        )

    # Generate unique resume ID
    resume_id = str(uuid.uuid4())

    # Generate SHA256 hash of file content for deduplication
    file_hash = hashlib.sha256(content).hexdigest()

    # Start background parsing task
    # BackgroundTasks is preferred for production
    if background_tasks:
        background_tasks.add_task(
            parse_resume_background,
            resume_id,
            file.filename,
            content
        )
    else:
        # For testing without BackgroundTasks, use asyncio.create_task
        # Note: In tests using TestClient, explicit task handling may be needed
        asyncio.create_task(parse_resume_background(resume_id, file.filename, content))

    # Return acceptance response with WebSocket URL for progress tracking
    return {
        "resume_id": resume_id,
        "status": "processing",
        "estimated_time_seconds": 30,
        "file_hash": file_hash,
        "websocket_url": f"/ws/resumes/{resume_id}"
    }


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str) -> ResumeResponse:
    """
    Retrieve parsed resume data by ID.

    Args:
        resume_id: Unique identifier for the resume

    Returns:
        ResumeResponse with parsed data if found

    Raises:
        HTTPException: 404 if resume not found
    """
    parsed_data = get_parsed_resume(resume_id)

    if parsed_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found or still processing"
        )

    return ResumeResponse(
        resume_id=resume_id,
        status="complete",
        data=parsed_data
    )


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: str,
    update_data: ResumeUpdateRequest
) -> ResumeResponse:
    """
    Update parsed resume data with user corrections.

    Args:
        resume_id: Unique identifier for the resume
        update_data: Updated resume data fields

    Returns:
        ResumeResponse with updated data

    Raises:
        HTTPException: 404 if resume not found
    """
    # Get current data
    current_data = get_parsed_resume(resume_id)

    if current_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )

    # Update only provided fields
    if update_data.personal_info is not None:
        current_data["personal_info"].update(update_data.personal_info)
    if update_data.work_experience is not None:
        current_data["work_experience"] = update_data.work_experience
    if update_data.education is not None:
        current_data["education"] = update_data.education
    if update_data.skills is not None:
        current_data["skills"].update(update_data.skills)

    # Save updated data
    update_success = update_parsed_resume(resume_id, current_data)

    if not update_success:
        raise HTTPException(
            status_code=500,
            detail="Failed to update resume data"
        )

    return ResumeResponse(
        resume_id=resume_id,
        status="updated",
        data=current_data,
        message="Resume updated successfully"
    )
