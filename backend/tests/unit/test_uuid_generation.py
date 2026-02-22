"""
Test UUID generation in database models.

This test verifies that all database models with UUID columns
generate proper UUID values, not random strings.
"""
import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database_storage import DatabaseStorageService
from app.models.progress import ParsedData


@pytest.mark.asyncio
async def test_parsed_resume_data_has_valid_uuid_id(db_session: AsyncSession):
    """
    Test that ParsedResumeData.id is a valid UUID.

    This test fails with the current implementation because
    secrets.token_urlsafe(16) generates a 22-char string,
    not a proper UUID.
    """
    service = DatabaseStorageService(db_session)

    resume_id = uuid4()
    parsed_data = ParsedData(
        full_name="Test User",
        email="test@example.com",
        skills=["Python"],
        extraction_confidence=0.9
    )

    # This should create a ParsedResumeData with a valid UUID id
    parsed_resume = await service.save_parsed_data(resume_id, parsed_data)

    # Verify the id is a valid UUID object, not a string
    assert isinstance(parsed_resume.id, UUID), f"Expected UUID, got {type(parsed_resume.id)}: {parsed_resume.id}"

    # Verify it can be converted to string and back to UUID
    id_str = str(parsed_resume.id)
    assert len(id_str) == 36, f"UUID string should be 36 chars, got {len(id_str)}"

    # Verify it's a valid UUID format
    parsed_uuid = UUID(id_str)
    assert parsed_uuid == parsed_resume.id


@pytest.mark.asyncio
async def test_resume_share_has_valid_uuid_id(db_session: AsyncSession):
    """
    Test that ResumeShare.id is a valid UUID.
    """
    service = DatabaseStorageService(db_session)

    resume_id = uuid4()
    share_token = await service.create_share_token(resume_id)

    # Get the share record
    share = await service.get_share_by_token(share_token)

    # Verify the id is a valid UUID object
    assert isinstance(share.id, UUID), f"Expected UUID, got {type(share.id)}: {share.id}"

    # Verify it's a valid UUID format
    id_str = str(share.id)
    assert len(id_str) == 36, f"UUID string should be 36 chars, got {len(id_str)}"


@pytest.mark.asyncio
async def test_resume_correction_has_valid_uuid_id(db_session: AsyncSession):
    """
    Test that ResumeCorrection.id is a valid UUID.
    """
    service = DatabaseStorageService(db_session)

    resume_id = uuid4()
    correction = await service.save_correction(
        resume_id,
        "personal_info.email",
        "old@example.com",
        "new@example.com"
    )

    # Verify the id is a valid UUID object
    assert isinstance(correction.id, UUID), f"Expected UUID, got {type(correction.id)}: {correction.id}"

    # Verify it's a valid UUID format
    id_str = str(correction.id)
    assert len(id_str) == 36, f"UUID string should be 36 chars, got {len(id_str)}"
