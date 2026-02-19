"""
In-memory storage for share tokens.

This service manages shareable links for resumes, including token generation,
access tracking, expiration, and revocation.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import uuid


# In-memory store: {share_token: share_metadata}
_share_store: Dict[str, dict] = {}


def create_share(resume_id: str, expires_in_days: int = 30) -> dict:
    """
    Create a new share token for a resume.

    Args:
        resume_id: Unique identifier for the resume to share
        expires_in_days: Number of days until the share link expires (default: 30)

    Returns:
        Dictionary containing share_token and expires_at
    """
    share_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    share_metadata = {
        "share_token": share_token,
        "resume_id": resume_id,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat(),
        "access_count": 0,
        "is_active": True
    }

    _share_store[share_token] = share_metadata

    return {
        "share_token": share_token,
        "expires_at": expires_at.isoformat()
    }


def get_share(share_token: str) -> Optional[dict]:
    """
    Retrieve share metadata by token.

    Args:
        share_token: The share token to look up

    Returns:
        Share metadata dictionary, or None if not found
    """
    return _share_store.get(share_token)


def increment_access(share_token: str) -> bool:
    """
    Increment the access count for a share.

    Args:
        share_token: The share token to update

    Returns:
        True if incremented successfully, False if share not found
    """
    if share_token in _share_store:
        _share_store[share_token]["access_count"] += 1
        return True
    return False


def revoke_share(share_token: str) -> bool:
    """
    Revoke a share link by deactivating it.

    Args:
        share_token: The share token to revoke

    Returns:
        True if revoked successfully, False if share not found
    """
    if share_token in _share_store:
        _share_store[share_token]["is_active"] = False
        return True
    return False


def is_share_valid(share_token: str) -> bool:
    """
    Check if a share token is valid (active and not expired).

    Args:
        share_token: The share token to validate

    Returns:
        True if share is active and not expired, False otherwise
    """
    share = _share_store.get(share_token)
    if not share:
        return False

    # Check if active
    if not share["is_active"]:
        return False

    # Check expiration
    expires_at = datetime.fromisoformat(share["expires_at"])
    if datetime.utcnow() > expires_at:
        return False

    return True


def clear_all_shares() -> None:
    """
    Clear all stored shares (for testing).
    """
    global _share_store
    _share_store = {}
