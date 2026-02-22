"""
Integration tests for database-backed share storage service.

These tests verify that share tokens are correctly persisted to the database
and can be retrieved across different sessions (unlike in-memory storage).
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.database_share_storage import (
    create_share,
    get_share,
    increment_access,
    revoke_share,
    is_share_valid,
)
from app.models.resume import ResumeShare


@pytest.mark.asyncio
async def test_create_share_persists_to_database(db_session: AsyncSession):
    """Test that create_share persists share to database"""
    resume_id = "ecfd221a-5e8b-4fbe-82d0-4f9b2ace58ce"
    expires_in_days = 30

    # Create share
    share_data = await create_share(resume_id, db_session, expires_in_days)

    # Verify share was created in database
    result = await db_session.execute(
        select(ResumeShare).where(ResumeShare.share_token == share_data["share_token"])
    )
    share_from_db = result.scalar_one_or_none()

    assert share_from_db is not None
    assert share_from_db.resume_id == resume_id
    assert share_from_db.share_token == share_data["share_token"]
    assert share_from_db.access_count == 0
    assert share_from_db.is_active is True


@pytest.mark.asyncio
async def test_get_share_retrieves_from_database(db_session: AsyncSession):
    """Test that get_share retrieves share from database"""
    resume_id = "ecfd221a-5e8b-4fbe-82d0-4f9b2ace58ce"

    # Create share in database
    created_share = await create_share(resume_id, db_session, expires_in_days=30)
    share_token = created_share["share_token"]

    # Retrieve share
    retrieved_share = await get_share(share_token, db_session)

    assert retrieved_share is not None
    assert retrieved_share["share_token"] == share_token
    assert retrieved_share["resume_id"] == resume_id
    assert retrieved_share["access_count"] == 0
    assert retrieved_share["is_active"] is True


@pytest.mark.asyncio
async def test_get_share_returns_none_for_invalid_token(db_session: AsyncSession):
    """Test that get_share returns None for invalid token"""
    result = await get_share("invalid-token-123", db_session)
    assert result is None


@pytest.mark.asyncio
async def test_increment_access_persists_to_database(db_session: AsyncSession):
    """Test that increment_access persists count to database"""
    resume_id = "ecfd221a-5e8b-4fbe-82d0-4f9b2ace58ce"

    # Create share
    created_share = await create_share(resume_id, db_session, expires_in_days=30)
    share_token = created_share["share_token"]

    # Increment access
    await increment_access(share_token, db_session)

    # Verify in database
    result = await db_session.execute(
        select(ResumeShare).where(ResumeShare.share_token == share_token)
    )
    share_from_db = result.scalar_one_or_none()
    assert share_from_db.access_count == 1


@pytest.mark.asyncio
async def test_revoke_share_persists_to_database(db_session: AsyncSession):
    """Test that revoke_share persists deactivation to database"""
    resume_id = "ecfd221a-5e8b-4fbe-82d0-4f9b2ace58ce"

    # Create share
    created_share = await create_share(resume_id, db_session, expires_in_days=30)
    share_token = created_share["share_token"]

    # Revoke share
    await revoke_share(share_token, db_session)

    # Verify in database
    result = await db_session.execute(
        select(ResumeShare).where(ResumeShare.share_token == share_token)
    )
    share_from_db = result.scalar_one_or_none()
    assert share_from_db.is_active is False


@pytest.mark.asyncio
async def test_is_share_valid_checks_active_status(db_session: AsyncSession):
    """Test that is_share_valid checks active status from database"""
    resume_id = "ecfd221a-5e8b-4fbe-82d0-4f9b2ace58ce"

    # Create share
    created_share = await create_share(resume_id, db_session, expires_in_days=30)
    share_token = created_share["share_token"]

    # Should be valid initially
    assert await is_share_valid(share_token, db_session) is True

    # Revoke share
    await revoke_share(share_token, db_session)

    # Should be invalid after revocation
    assert await is_share_valid(share_token, db_session) is False


@pytest.mark.asyncio
async def test_is_share_valid_checks_expiration(db_session: AsyncSession):
    """Test that is_share_valid checks expiration from database"""
    resume_id = "ecfd221a-5e8b-4fbe-82d0-4f9b2ace58ce"

    # Create share that expires in the past
    created_share = await create_share(resume_id, db_session, expires_in_days=-1)
    share_token = created_share["share_token"]

    # Should be invalid due to expiration
    assert await is_share_valid(share_token, db_session) is False


@pytest.mark.asyncio
async def test_share_persists_across_sessions(db_session: AsyncSession):
    """Test that shares persist across different database sessions (REGRESSION TEST)"""
    from app.core.database import AsyncSessionLocal

    resume_id = "ecfd221a-5e8b-4fbe-82d0-4f9b2ace58ce"

    # Create share in first session
    async with AsyncSessionLocal() as session1:
        created_share = await create_share(resume_id, session1, expires_in_days=30)
        share_token = created_share["share_token"]

    # Retrieve share in different session
    async with AsyncSessionLocal() as session2:
        retrieved_share = await get_share(share_token, session2)

    # This should NOT return None (regression test for in-memory storage bug)
    assert retrieved_share is not None
    assert retrieved_share["share_token"] == share_token
