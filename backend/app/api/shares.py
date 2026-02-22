"""
Share API endpoints.

This module provides endpoints for managing resume share links, including:
- Creating shareable links
- Retrieving share details
- Revoking shares
- Public access to shared resumes
- Export functionality (PDF, WhatsApp, Telegram, Email)
"""

from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import Response as FastAPIResponse
from typing import Dict, Optional
from pydantic import BaseModel

# Import both storage implementations
from app.core.share_storage import (
    create_share as create_share_inmemory,
    get_share as get_share_inmemory,
    increment_access as increment_access_inmemory,
    revoke_share as revoke_share_inmemory,
    is_share_valid as is_share_valid_inmemory,
)
from app.services.database_share_storage import (
    create_share as create_share_db,
    get_share as get_share_db,
    increment_access as increment_access_db,
    revoke_share as revoke_share_db,
    is_share_valid as is_share_valid_db,
    get_share_token_by_resume_id as get_share_token_by_resume_id_db,
)
from app.core.storage import get_parsed_resume as get_parsed_resume_inmemory
from app.services.storage_adapter import StorageAdapter
from app.core.config import settings
from app.core.database import get_db
from app.services.export_service import (
    generate_pdf,
    generate_whatsapp_link,
    generate_telegram_link,
    generate_email_link,
)


# Default base URL for share links if not configured
DEFAULT_BASE_URL = "http://localhost:3000"


# Create router with prefix and tags
router = APIRouter(tags=["shares"])


# Storage abstraction layer
async def _create_share(resume_id: str, db=None):
    """Create share using database or in-memory storage based on settings"""
    if settings.USE_DATABASE and db:
        return await create_share_db(resume_id, db)
    return create_share_inmemory(resume_id)


async def _get_share(share_token: str, db=None):
    """Get share using database or in-memory storage based on settings"""
    if settings.USE_DATABASE and db:
        return await get_share_db(share_token, db)
    return get_share_inmemory(share_token)


async def _increment_access(share_token: str, db=None):
    """Increment access using database or in-memory storage based on settings"""
    if settings.USE_DATABASE and db:
        return await increment_access_db(share_token, db)
    return increment_access_inmemory(share_token)


async def _revoke_share(share_token: str, db=None):
    """Revoke share using database or in-memory storage based on settings"""
    if settings.USE_DATABASE and db:
        return await revoke_share_db(share_token, db)
    return revoke_share_inmemory(share_token)


async def _is_share_valid(share_token: str, db=None):
    """Check share validity using database or in-memory storage based on settings"""
    if settings.USE_DATABASE and db:
        return await is_share_valid_db(share_token, db)
    return is_share_valid_inmemory(share_token)


async def _get_share_token_by_resume_id(resume_id: str, db=None):
    """Get share token by resume ID using database or in-memory storage"""
    if settings.USE_DATABASE and db:
        return await get_share_token_by_resume_id_db(resume_id, db)
    # In-memory implementation
    from app.core.share_storage import _share_store
    for token, metadata in _share_store.items():
        if metadata.get("resume_id") == resume_id:
            return token
    return None


async def _get_parsed_resume(resume_id: str, db=None):
    """Get parsed resume using database or in-memory storage"""
    if settings.USE_DATABASE and db:
        adapter = StorageAdapter(db)
        return await adapter.get_parsed_data(resume_id)
    return get_parsed_resume_inmemory(resume_id)


# Pydantic models for request/response
class ShareCreateResponse(BaseModel):
    """Response model for creating a share"""
    share_token: str
    share_url: str
    expires_at: str


class ShareDetailsResponse(BaseModel):
    """Response model for share details"""
    share_token: str
    share_url: str
    resume_id: str
    created_at: str
    expires_at: str
    access_count: int
    is_active: bool


class PublicShareResponse(BaseModel):
    """Response model for public share access"""
    resume_id: str
    personal_info: dict
    work_experience: list
    education: list
    skills: dict
    confidence_scores: dict


@router.post("/v1/resumes/{resume_id}/share", status_code=202, response_model=ShareCreateResponse)
async def create_resume_share(resume_id: str, db=Depends(get_db)) -> Dict:
    """
    Create a shareable link for a resume.

    This endpoint generates a unique share token for a resume that can be
    used to publicly access the parsed resume data. The link expires after
    a configurable number of days (default: 30).

    Args:
        resume_id: Unique identifier for the resume to share

    Returns:
        dict: Contains share_token, share_url, and expires_at

    Raises:
        HTTPException: 404 if resume not found
    """
    # Verify resume exists
    resume_data = await _get_parsed_resume(resume_id, db)
    if resume_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )

    # Create the share using database or in-memory storage
    share_data = await _create_share(resume_id, db)

    # Construct share URL with /shared/ prefix for public access
    share_url = f"{settings.allowed_origins_list[0]}/shared/{share_data['share_token']}"

    return {
        "share_token": share_data["share_token"],
        "share_url": share_url,
        "expires_at": share_data["expires_at"]
    }


@router.get("/v1/resumes/{resume_id}/share", response_model=ShareDetailsResponse)
async def get_resume_share(resume_id: str, db=Depends(get_db)) -> Dict:
    """
    Retrieve share details for a resume.

    This endpoint returns the current share details for a resume,
    including access statistics and expiration information.

    Args:
        resume_id: Unique identifier for the resume

    Returns:
        dict: Share details including token, created_at, expires_at,
              access_count, and is_active status

    Raises:
        HTTPException: 404 if no share exists for this resume
    """
    # Find the share token for this resume
    share_token = await _get_share_token_by_resume_id(resume_id, db)

    if not share_token:
        raise HTTPException(
            status_code=404,
            detail=f"No share found for resume {resume_id}"
        )

    # Get share metadata
    share = await _get_share(share_token, db)
    if not share:
        raise HTTPException(
            status_code=404,
            detail=f"Share not found"
        )

    # Construct share URL with /shared/ prefix for public access
    share_url = f"{settings.allowed_origins_list[0]}/shared/{share['share_token']}"

    return {
        "share_token": share["share_token"],
        "share_url": share_url,
        "resume_id": share["resume_id"],
        "created_at": share["created_at"],
        "expires_at": share["expires_at"],
        "access_count": share["access_count"],
        "is_active": share["is_active"]
    }


@router.delete("/v1/resumes/{resume_id}/share", status_code=200)
async def revoke_resume_share(resume_id: str, db=Depends(get_db)) -> Dict:
    """
    Revoke a shareable link for a resume.

    This endpoint deactivates the share link for a resume, making it
    inaccessible via the public share endpoint. A new share can be
    created by calling POST again.

    Args:
        resume_id: Unique identifier for the resume

    Returns:
        dict: Success message

    Raises:
        HTTPException: 404 if no share exists for this resume
    """
    # Find the share token for this resume
    share_token = await _get_share_token_by_resume_id(resume_id, db)

    if not share_token:
        raise HTTPException(
            status_code=404,
            detail=f"No share found for resume {resume_id}"
        )

    # Revoke the share
    revoked = await _revoke_share(share_token, db)

    if not revoked:
        raise HTTPException(
            status_code=404,
            detail=f"Share not found"
        )

    return {
        "message": "Share revoked successfully",
        "resume_id": resume_id
    }


@router.get("/v1/share/{share_token}", response_model=PublicShareResponse)
async def get_public_share(share_token: str, db=Depends(get_db)) -> Dict:
    """
    Public endpoint to access a shared resume.

    This endpoint allows anyone with a valid share token to access
    the resume data without authentication. The share must be active
    and not expired.

    Args:
        share_token: The share token from the share URL

    Returns:
        dict: The parsed resume data

    Raises:
        HTTPException: 404 if share not found
        HTTPException: 403 if share has been revoked
        HTTPException: 410 if share has expired
    """
    # Get share metadata
    share = await _get_share(share_token, db)

    if not share:
        raise HTTPException(
            status_code=404,
            detail="Share not found"
        )

    # Check if share is valid (active and not expired)
    if not await _is_share_valid(share_token, db):
        # Check specific failure reason
        if not share["is_active"]:
            raise HTTPException(
                status_code=403,
                detail="This share has been revoked"
            )

        # Must be expired
        raise HTTPException(
            status_code=410,
            detail="This share has expired"
        )

    # Get resume data
    resume_id = share["resume_id"]
    resume_data = await _get_parsed_resume(resume_id, db)

    if resume_data is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    # Increment access count
    await _increment_access(share_token, db)

    return {
        "resume_id": resume_id,
        "personal_info": resume_data.get("personal_info", {}),
        "work_experience": resume_data.get("work_experience", []),
        "education": resume_data.get("education", []),
        "skills": resume_data.get("skills", {}),
        "confidence_scores": resume_data.get("confidence_scores", {})
    }


# Export response models
class WhatsAppExportResponse(BaseModel):
    """Response model for WhatsApp export"""
    whatsapp_url: str


class TelegramExportResponse(BaseModel):
    """Response model for Telegram export"""
    telegram_url: str


class EmailExportResponse(BaseModel):
    """Response model for email export"""
    mailto_url: str


@router.get("/v1/resumes/{resume_id}/export/pdf")
async def export_resume_pdf(resume_id: str, db=Depends(get_db)) -> FastAPIResponse:
    """
    Export a resume as a PDF file.

    This endpoint generates a PDF document from the parsed resume data,
    including personal information, work experience, education, and skills.

    Args:
        resume_id: Unique identifier for the resume to export

    Returns:
        PDF file as binary response with application/pdf content-type

    Raises:
        HTTPException: 404 if resume not found
    """
    # Get resume data
    resume_data = await _get_parsed_resume(resume_id, db)
    if resume_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )

    # Generate PDF
    pdf_bytes = generate_pdf(resume_data)

    # Get filename from resume data
    personal_info = resume_data.get("personal_info", {})
    name = personal_info.get("full_name", "resume").replace(" ", "_")
    filename = f"{name}_resume.pdf"

    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/v1/resumes/{resume_id}/export/whatsapp", response_model=WhatsAppExportResponse)
async def export_resume_whatsapp(resume_id: str, db=Depends(get_db)) -> Dict:
    """
    Generate a WhatsApp share link for a resume.

    This endpoint creates a WhatsApp URL that pre-fills a message
    with the resume content.

    Args:
        resume_id: Unique identifier for the resume to export

    Returns:
        dict: Contains whatsapp_url

    Raises:
        HTTPException: 404 if resume not found
    """
    # Get resume data
    resume_data = await _get_parsed_resume(resume_id, db)
    if resume_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )

    # Generate WhatsApp link
    base_url = settings.allowed_origins_list[0] if settings.allowed_origins_list else DEFAULT_BASE_URL
    whatsapp_url = generate_whatsapp_link(resume_data, base_url)

    return {
        "whatsapp_url": whatsapp_url
    }


@router.get("/v1/resumes/{resume_id}/export/telegram", response_model=TelegramExportResponse)
async def export_resume_telegram(resume_id: str, db=Depends(get_db)) -> Dict:
    """
    Generate a Telegram share link for a resume.

    This endpoint creates a Telegram URL that pre-fills a message
    with the resume content.

    Args:
        resume_id: Unique identifier for the resume to export

    Returns:
        dict: Contains telegram_url

    Raises:
        HTTPException: 404 if resume not found
    """
    # Get resume data
    resume_data = await _get_parsed_resume(resume_id, db)
    if resume_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )

    # Get or create share for the resume to obtain share URL
    share_token = await _get_share_token_by_resume_id(resume_id, db)
    if not share_token:
        # Share doesn't exist, create it first
        share_data = await _create_share(resume_id, db)
        share_token = share_data["share_token"]

    # Construct share URL
    base_url = settings.allowed_origins_list[0] if settings.allowed_origins_list else DEFAULT_BASE_URL
    share_url = f"{base_url}/shared/{share_token}"

    # Generate Telegram link with share URL
    telegram_url = generate_telegram_link(resume_data, share_url, base_url)

    return {
        "telegram_url": telegram_url
    }


@router.get("/v1/resumes/{resume_id}/export/email", response_model=EmailExportResponse)
async def export_resume_email(resume_id: str, db=Depends(get_db)) -> Dict:
    """
    Generate an email mailto link for sharing a resume.

    This endpoint creates a mailto URL that pre-fills the subject and body
    with resume information.

    Args:
        resume_id: Unique identifier for the resume to export

    Returns:
        dict: Contains mailto_url

    Raises:
        HTTPException: 404 if resume not found
    """
    # Get resume data
    resume_data = await _get_parsed_resume(resume_id, db)
    if resume_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )

    # Generate email link
    base_url = settings.allowed_origins_list[0] if settings.allowed_origins_list else DEFAULT_BASE_URL
    mailto_url = generate_email_link(resume_data, base_url)

    return {
        "mailto_url": mailto_url
    }
