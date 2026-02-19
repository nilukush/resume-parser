"""
Resume upload API endpoints.

This module provides endpoints for uploading and processing resumes.
The main endpoint is POST /v1/resumes/upload which accepts resume files
in PDF, DOCX, DOC, or TXT format.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Dict
import hashlib
import uuid

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


@router.post("/upload", status_code=202)
async def upload_resume(file: UploadFile = File(...)) -> Dict:
    """
    Upload a resume for parsing and processing.

    This endpoint accepts resume files in PDF, DOCX, DOC, or TXT format.
    Files are validated for type and size before processing begins.
    Processing happens asynchronously, so the endpoint returns 202 Accepted.

    Args:
        file: The uploaded resume file

    Returns:
        dict: Contains resume_id, status, estimated_time_seconds, and file_hash

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

    # Return acceptance response
    # In production, this would trigger async processing via Celery
    return {
        "resume_id": resume_id,
        "status": "processing",
        "estimated_time_seconds": 30,
        "file_hash": file_hash,
    }
