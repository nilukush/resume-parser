"""
Share API endpoints.

This module provides endpoints for managing resume share links, including:
- Creating shareable links
- Retrieving share details
- Revoking shares
- Public access to shared resumes
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Optional
from pydantic import BaseModel

from app.core.share_storage import (
    create_share,
    get_share,
    increment_access,
    revoke_share,
    is_share_valid,
)
from app.core.storage import get_parsed_resume
from app.core.config import settings


# Create router with prefix and tags
router = APIRouter(tags=["shares"])


# Pydantic models for request/response
class ShareCreateResponse(BaseModel):
    """Response model for creating a share"""
    share_token: str
    share_url: str
    expires_at: str


class ShareDetailsResponse(BaseModel):
    """Response model for share details"""
    share_token: str
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


def get_share_token_by_resume_id(resume_id: str) -> Optional[str]:
    """
    Find an active share token by resume_id.

    This is a helper function since share_storage is indexed by token,
    not by resume_id.

    Args:
        resume_id: The resume ID to find shares for

    Returns:
        The share token if found, None otherwise
    """
    from app.core.share_storage import _share_store

    for token, metadata in _share_store.items():
        if metadata.get("resume_id") == resume_id:
            return token
    return None


@router.post("/v1/resumes/{resume_id}/share", status_code=202, response_model=ShareCreateResponse)
async def create_resume_share(resume_id: str) -> Dict:
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
    resume_data = get_parsed_resume(resume_id)
    if resume_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )

    # Create the share
    share_data = create_share(resume_id)

    # Construct share URL
    share_url = f"{settings.allowed_origins_list[0]}/share/{share_data['share_token']}"

    return {
        "share_token": share_data["share_token"],
        "share_url": share_url,
        "expires_at": share_data["expires_at"]
    }


@router.get("/v1/resumes/{resume_id}/share", response_model=ShareDetailsResponse)
async def get_resume_share(resume_id: str) -> Dict:
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
    share_token = get_share_token_by_resume_id(resume_id)

    if not share_token:
        raise HTTPException(
            status_code=404,
            detail=f"No share found for resume {resume_id}"
        )

    # Get share metadata
    share = get_share(share_token)
    if not share:
        raise HTTPException(
            status_code=404,
            detail=f"Share not found"
        )

    return {
        "share_token": share["share_token"],
        "resume_id": share["resume_id"],
        "created_at": share["created_at"],
        "expires_at": share["expires_at"],
        "access_count": share["access_count"],
        "is_active": share["is_active"]
    }


@router.delete("/v1/resumes/{resume_id}/share", status_code=200)
async def revoke_resume_share(resume_id: str) -> Dict:
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
    share_token = get_share_token_by_resume_id(resume_id)

    if not share_token:
        raise HTTPException(
            status_code=404,
            detail=f"No share found for resume {resume_id}"
        )

    # Revoke the share
    revoked = revoke_share(share_token)

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
async def get_public_share(share_token: str) -> Dict:
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
    share = get_share(share_token)

    if not share:
        raise HTTPException(
            status_code=404,
            detail="Share not found"
        )

    # Check if share is valid (active and not expired)
    if not is_share_valid(share_token):
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
    resume_data = get_parsed_resume(resume_id)

    if resume_data is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    # Increment access count
    increment_access(share_token)

    return {
        "resume_id": resume_id,
        "personal_info": resume_data.get("personal_info", {}),
        "work_experience": resume_data.get("work_experience", []),
        "education": resume_data.get("education", []),
        "skills": resume_data.get("skills", {}),
        "confidence_scores": resume_data.get("confidence_scores", {})
    }
