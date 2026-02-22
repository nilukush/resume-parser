"""
Database-backed storage for share tokens.

This service manages shareable links for resumes using PostgreSQL database,
including token generation, access tracking, expiration, and revocation.

This replaces the in-memory share_storage.py to ensure shares persist
across server restarts and can be accessed from multiple instances.
"""

from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from app.models.resume import ResumeShare


async def create_share(
    resume_id: str,
    db: AsyncSession,
    expires_in_days: int = 30
) -> dict:
    """
    Create a new share token for a resume in the database.

    Args:
        resume_id: Unique identifier for the resume to share
        db: Async database session
        expires_in_days: Number of days until the share link expires (default: 30)

    Returns:
        Dictionary containing share_token and expires_at
    """
    import uuid
    share_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    # Convert resume_id string to UUID if it's a string
    try:
        resume_uuid = UUID(resume_id) if isinstance(resume_id, str) else resume_id
    except ValueError:
        # If resume_id is not a valid UUID, use it as-is
        resume_uuid = resume_id

    share = ResumeShare(
        resume_id=resume_uuid,
        share_token=share_token,
        expires_at=expires_at,
        access_count=0,
        is_active=True
    )

    db.add(share)
    await db.commit()
    await db.refresh(share)

    return {
        "share_token": share_token,
        "expires_at": expires_at.isoformat()
    }


async def get_share(share_token: str, db: AsyncSession) -> Optional[dict]:
    """
    Retrieve share metadata by token from database.

    Args:
        share_token: The share token to look up
        db: Async database session

    Returns:
        Share metadata dictionary, or None if not found
    """
    result = await db.execute(
        select(ResumeShare).where(ResumeShare.share_token == share_token)
    )
    share = result.scalar_one_or_none()

    if not share:
        return None

    return {
        "share_token": share.share_token,
        "resume_id": str(share.resume_id),
        "created_at": share.created_at.isoformat(),
        "expires_at": share.expires_at.isoformat(),
        "access_count": share.access_count,
        "is_active": share.is_active
    }


async def increment_access(share_token: str, db: AsyncSession) -> bool:
    """
    Increment the access count for a share in database.

    Args:
        share_token: The share token to update
        db: Async database session

    Returns:
        True if incremented successfully, False if share not found
    """
    result = await db.execute(
        update(ResumeShare)
        .where(ResumeShare.share_token == share_token)
        .values(access_count=ResumeShare.access_count + 1)
    )

    await db.commit()

    # Check if any row was updated
    return result.rowcount > 0


async def revoke_share(share_token: str, db: AsyncSession) -> bool:
    """
    Revoke a share link by deactivating it in database.

    Args:
        share_token: The share token to revoke
        db: Async database session

    Returns:
        True if revoked successfully, False if share not found
    """
    result = await db.execute(
        update(ResumeShare)
        .where(ResumeShare.share_token == share_token)
        .values(is_active=False)
    )

    await db.commit()

    # Check if any row was updated
    return result.rowcount > 0


async def is_share_valid(share_token: str, db: AsyncSession) -> bool:
    """
    Check if a share token is valid (active and not expired) in database.

    Args:
        share_token: The share token to validate
        db: Async database session

    Returns:
        True if share is active and not expired, False otherwise
    """
    share = await get_share(share_token, db)
    if not share:
        return False

    # Check if active
    if not share["is_active"]:
        return False

    # Check expiration
    expires_at = datetime.fromisoformat(share["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        return False

    return True


async def get_share_token_by_resume_id(resume_id: str, db: AsyncSession) -> Optional[str]:
    """
    Find an active share token by resume_id in database.

    This is a helper function since share tokens are indexed by token,
    not by resume_id.

    Args:
        resume_id: The resume ID to find shares for
        db: Async database session

    Returns:
        The share token if found, None otherwise
    """
    try:
        resume_uuid = UUID(resume_id) if isinstance(resume_id, str) else resume_id
    except ValueError:
        resume_uuid = resume_id

    result = await db.execute(
        select(ResumeShare)
        .where(ResumeShare.resume_id == resume_uuid)
        .where(ResumeShare.is_active == True)
        .order_by(ResumeShare.created_at.desc())
        .limit(1)
    )

    share = result.scalar_one_or_none()
    return share.share_token if share else None
