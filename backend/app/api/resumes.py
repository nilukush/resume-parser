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
from app.core.database import get_db
from app.services.storage_adapter import StorageAdapter

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


async def parse_resume_background(
    resume_id: str,
    filename: str,
    content: bytes,
    file_hash: str,
    file_size: int,
    file_type: str
):
    """
    Background task to parse resume and send progress updates.

    This function runs asynchronously after a file is uploaded,
    orchestrating the parsing pipeline and broadcasting progress
    updates via WebSocket to connected clients.

    Args:
        resume_id: Unique identifier for this resume
        filename: Original filename of the uploaded file
        content: Raw file content as bytes
        file_hash: SHA256 hash of file content
        file_size: File size in bytes
        file_type: File extension (pdf, docx, doc, txt)

    Note:
        Errors are logged but not raised to prevent background task
        failures from affecting the HTTP response.
    """
    try:
        await orchestrator.parse_resume(
            resume_id,
            filename,
            content,
            file_hash=file_hash,
            file_size=file_size,
            file_type=file_type
        )
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
    from app.core.database import db_manager
    from app.models.resume import Resume
    from sqlalchemy import select

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

    # Extract file extension for file_type field
    file_extension = file.filename.split(".")[-1].lower() if file.filename else "unknown"

    # Save resume metadata to database BEFORE starting background task
    # This ensures the resume record exists when the background task tries to update it
    from app.core.config import settings

    if settings.USE_DATABASE:
        async with db_manager.get_session() as db:
            # Check for duplicate file hash
            existing = await db.execute(
                select(Resume).where(Resume.file_hash == file_hash)
            )
            existing_resume = existing.scalar_one_or_none()

            if existing_resume:
                # Check if existing resume has been processed
                from app.services.storage_adapter import StorageAdapter
                adapter = StorageAdapter(db)
                existing_data = await adapter.get_parsed_data(str(existing_resume.id))

                # Return existing resume info instead of error
                return {
                    "resume_id": str(existing_resume.id),
                    "status": "already_processed" if existing_resume.processing_status == "complete" else "processing",
                    "message": "This file was already uploaded",
                    "file_hash": file_hash,
                    "original_filename": existing_resume.original_filename,
                    "uploaded_at": existing_resume.uploaded_at.isoformat() if existing_resume.uploaded_at else None,
                    "processed_at": existing_resume.processed_at.isoformat() if existing_resume.processed_at else None,
                    "websocket_url": f"/ws/resumes/{existing_resume.id}",
                    "has_parsed_data": existing_data is not None,
                    # If complete, include the parsed data for immediate display
                    "existing_data": existing_data if existing_data else None
                }

            # Create resume metadata record
            resume = Resume(
                id=resume_id,
                original_filename=file.filename,
                file_type=file_extension,
                file_size_bytes=len(content),
                file_hash=file_hash,
                storage_path="",  # Will implement file storage later
                processing_status="processing"
            )
            db.add(resume)
            await db.commit()

    # Start background parsing task with metadata parameters
    # BackgroundTasks is preferred for production
    if background_tasks:
        background_tasks.add_task(
            parse_resume_background,
            resume_id,
            file.filename,
            content,
            file_hash,
            len(content),
            file_extension
        )
    else:
        # For testing without BackgroundTasks, use asyncio.create_task
        # Note: In tests using TestClient, explicit task handling may be needed
        asyncio.create_task(
            parse_resume_background(
                resume_id,
                file.filename,
                content,
                file_hash,
                len(content),
                file_extension
            )
        )

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
        HTTPException: 404 if resume not found, 202 if still processing
    """
    import asyncio
    from app.core.config import settings
    from app.core.database import db_manager
    from app.models.resume import Resume
    from sqlalchemy import select

    # When using database, check resume processing status
    if settings.USE_DATABASE:
        async with db_manager.get_session() as db:
            # First check if resume exists and its processing status
            result = await db.execute(
                select(Resume).where(Resume.id == resume_id)
            )
            resume = result.scalar_one_or_none()

            if not resume:
                raise HTTPException(
                    status_code=404,
                    detail=f"Resume {resume_id} not found"
                )

            # If resume is still being processed, return 202 Accepted
            if resume.processing_status == "processing":
                raise HTTPException(
                    status_code=202,
                    detail=f"Resume {resume_id} is still being processed. Please try again in a few seconds."
                )

            # Resume exists and is marked complete, try to get parsed data
            adapter = StorageAdapter(db)
            parsed_data = await adapter.get_parsed_data(resume_id)

            # Handle race condition: Resume marked complete but data not yet committed
            # Retry up to 3 times with 100ms delay between retries
            if parsed_data is None:
                for attempt in range(3):
                    await asyncio.sleep(0.1)  # Wait 100ms
                    await db.rollback()  # Clear any transaction state
                    parsed_data = await adapter.get_parsed_data(resume_id)
                    if parsed_data is not None:
                        break

            if parsed_data is None:
                # Data still not available after retries
                raise HTTPException(
                    status_code=404,
                    detail=f"Resume {resume_id} not found or still processing"
                )

            return ResumeResponse(
                resume_id=resume_id,
                status="complete",
                data=parsed_data
            )
    else:
        # In-memory storage path
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
    from app.core.config import settings
    from app.core.database import db_manager

    # Get current data
    if settings.USE_DATABASE:
        async with db_manager.get_session() as db:
            adapter = StorageAdapter(db)
            current_data = await adapter.get_parsed_data(resume_id)
    else:
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
    if settings.USE_DATABASE:
        async with db_manager.get_session() as db:
            adapter = StorageAdapter(db)
            update_success = await adapter.update_parsed_data(resume_id, current_data)
    else:
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
