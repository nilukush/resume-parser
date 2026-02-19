"""
Unit tests for share storage service.
"""

import pytest
from datetime import datetime, timedelta
from app.core.share_storage import (
    create_share,
    get_share,
    increment_access,
    revoke_share,
    is_share_valid
)


def test_create_share_generates_unique_token():
    """Test that create_share generates a unique token"""
    resume_id = "resume-123"
    share1 = create_share(resume_id, expires_in_days=7)
    share2 = create_share(resume_id, expires_in_days=7)
    assert share1["share_token"] != share2["share_token"]
    assert "share_token" in share1
    assert len(share1["share_token"]) == 36  # UUID format


def test_create_share_sets_expiration_correctly():
    """Test that create_share sets expiration date"""
    resume_id = "resume-123"
    expires_in_days = 7
    share = create_share(resume_id, expires_in_days=expires_in_days)
    assert "expires_at" in share
    expires_at = datetime.fromisoformat(share["expires_at"])
    expected_expires = datetime.utcnow() + timedelta(days=expires_in_days)
    # Allow 1 minute tolerance
    assert abs((expires_at - expected_expires).total_seconds()) < 60


def test_get_share_returns_metadata():
    """Test that get_share returns share metadata"""
    resume_id = "resume-123"
    created_share = create_share(resume_id, expires_in_days=7)
    share_token = created_share["share_token"]
    retrieved_share = get_share(share_token)
    assert retrieved_share is not None
    assert retrieved_share["share_token"] == share_token
    assert retrieved_share["resume_id"] == resume_id
    assert retrieved_share["access_count"] == 0
    assert retrieved_share["is_active"] is True


def test_get_share_returns_none_for_invalid_token():
    """Test that get_share returns None for invalid token"""
    result = get_share("invalid-token-123")
    assert result is None


def test_increment_access_increases_count():
    """Test that increment_access increases access count"""
    resume_id = "resume-123"
    created_share = create_share(resume_id, expires_in_days=7)
    share_token = created_share["share_token"]
    increment_access(share_token)
    share = get_share(share_token)
    assert share["access_count"] == 1
    increment_access(share_token)
    share = get_share(share_token)
    assert share["access_count"] == 2


def test_revoke_share_deactivates_link():
    """Test that revoke_share deactivates the link"""
    resume_id = "resume-123"
    created_share = create_share(resume_id, expires_in_days=7)
    share_token = created_share["share_token"]
    revoke_share(share_token)
    share = get_share(share_token)
    assert share["is_active"] is False


def test_is_share_valid_checks_active_status():
    """Test that is_share_valid checks active status"""
    resume_id = "resume-123"
    created_share = create_share(resume_id, expires_in_days=7)
    share_token = created_share["share_token"]
    assert is_share_valid(share_token) is True
    revoke_share(share_token)
    assert is_share_valid(share_token) is False


def test_is_share_valid_checks_expiration():
    """Test that is_share_valid checks expiration"""
    resume_id = "resume-123"
    # Create share that expires in the past
    created_share = create_share(resume_id, expires_in_days=-1)
    share_token = created_share["share_token"]
    assert is_share_valid(share_token) is False
