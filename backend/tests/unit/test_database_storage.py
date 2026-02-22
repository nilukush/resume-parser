"""
Test DatabaseStorageService for persistent resume storage.

This test suite verifies:
1. Saving resume and parsed data to database
2. Retrieving resume by ID
3. Updating parsed resume data
4. Managing share tokens
5. Tracking user corrections
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database_storage import DatabaseStorageService
from app.models.resume import Resume, ParsedResumeData, ResumeShare, ResumeCorrection
from app.models.progress import ParsedData


@pytest.mark.asyncio
async def test_save_resume_metadata(db_session: AsyncSession):
    """Test saving resume metadata to database"""
    service = DatabaseStorageService(db_session)

    resume_id = uuid4()
    resume_data = {
        "id": resume_id,
        "original_filename": "test_resume.pdf",
        "file_type": "pdf",
        "file_size": 1024,
        "file_hash": "abc123",
        "uploaded_at": datetime.utcnow(),
    }

    await service.save_resume_metadata(resume_data)

    # Verify saved to database
    retrieved = await service.get_resume(resume_id)
    assert retrieved is not None
    assert retrieved.original_filename == "test_resume.pdf"
    assert retrieved.file_type == "pdf"
    assert retrieved.file_size == 1024


@pytest.mark.asyncio
async def test_save_and_retrieve_parsed_data(db_session: AsyncSession):
    """Test saving and retrieving parsed resume data"""
    service = DatabaseStorageService(db_session)

    resume_id = uuid4()
    parsed_data = ParsedData(
        full_name="John Doe",
        email="john@example.com",
        phone="+1234567890",
        location="San Francisco, CA",
        skills=["Python", "FastAPI", "React"],
        work_experience=[{
            "company": "Tech Corp",
            "title": "Software Engineer",
            "years": "2020-2023"
        }],
        extraction_confidence=0.95
    )

    await service.save_parsed_data(resume_id, parsed_data)

    # Retrieve and verify
    retrieved = await service.get_parsed_data(resume_id)
    assert retrieved is not None
    assert retrieved.full_name == "John Doe"
    assert retrieved.email == "john@example.com"
    assert "Python" in retrieved.skills
    assert retrieved.extraction_confidence == 0.95


@pytest.mark.asyncio
async def test_update_parsed_data(db_session: AsyncSession):
    """Test updating existing parsed resume data"""
    service = DatabaseStorageService(db_session)

    resume_id = uuid4()

    # Save initial data
    initial_data = ParsedData(full_name="John Doe", email="john@example.com")
    await service.save_parsed_data(resume_id, initial_data)

    # Update with corrections
    updated_data = ParsedData(
        full_name="John Smith",  # Corrected name
        email="john@example.com",
        phone="+1234567890"  # Added phone
    )
    await service.update_parsed_data(resume_id, updated_data)

    # Verify updates
    retrieved = await service.get_parsed_data(resume_id)
    assert retrieved.full_name == "John Smith"
    assert retrieved.phone == "+1234567890"


@pytest.mark.asyncio
async def test_create_share_token(db_session: AsyncSession):
    """Test creating shareable link token"""
    service = DatabaseStorageService(db_session)

    resume_id = uuid4()
    share_token = await service.create_share_token(
        resume_id,
        expires_in_days=7,
        max_access_count=10
    )

    assert share_token is not None
    assert len(share_token) == 64  # SHA256 hash length

    # Verify share record created
    share = await service.get_share_by_token(share_token)
    assert share is not None
    assert share.resume_id == resume_id
    assert share.is_active is True
    assert share.max_access_count == 10


@pytest.mark.asyncio
async def test_track_access_count(db_session: AsyncSession):
    """Test tracking share access count"""
    service = DatabaseStorageService(db_session)

    resume_id = uuid4()
    share_token = await service.create_share_token(resume_id)

    # Increment access
    await service.increment_share_access(share_token)

    # Verify count incremented
    share = await service.get_share_by_token(share_token)
    assert share.access_count == 1

    # Increment again
    await service.increment_share_access(share_token)
    share = await service.get_share_by_token(share_token)
    assert share.access_count == 2


@pytest.mark.asyncio
async def test_save_user_correction(db_session: AsyncSession):
    """Test saving user corrections for AI learning"""
    service = DatabaseStorageService(db_session)

    resume_id = uuid4()

    await service.save_correction(
        resume_id=resume_id,
        field_name="personal_info.email",
        original_value="john@old.com",
        corrected_value="john@new.com"
    )

    # Retrieve corrections
    corrections = await service.get_corrections(resume_id)
    assert len(corrections) == 1
    assert corrections[0].field_name == "personal_info.email"
    assert corrections[0].original_value == "john@old.com"
    assert corrections[0].corrected_value == "john@new.com"


@pytest.mark.asyncio
async def test_share_token_expiration(db_session: AsyncSession):
    """Test that expired share tokens are rejected"""
    service = DatabaseStorageService(db_session)

    resume_id = uuid4()

    # Create share that expires in 1 day
    share_token = await service.create_share_token(
        resume_id,
        expires_in_days=1
    )

    # Manually expire the share (for testing)
    share = await service.get_share_by_token(share_token)
    share.expires_at = datetime.utcnow() - timedelta(days=1)
    await db_session.commit()

    # Verify share is marked inactive
    is_valid = await service.validate_share_token(share_token)
    assert is_valid is False


@pytest.mark.asyncio
async def test_resume_not_found(db_session: AsyncSession):
    """Test retrieving non-existent resume returns None"""
    service = DatabaseStorageService(db_session)

    result = await service.get_resume(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_recent_resumes(db_session: AsyncSession):
    """Test retrieving recent resumes with pagination"""
    service = DatabaseStorageService(db_session)

    # Create multiple resumes
    for i in range(5):
        resume_id = uuid4()
        await service.save_resume_metadata({
            "id": resume_id,
            "original_filename": f"resume_{i}.pdf",
            "file_type": "pdf",
            "file_size": 1000 + i,
            "file_hash": f"hash_{i}",
            "uploaded_at": datetime.utcnow(),
        })

    # Get recent resumes (limit 3)
    recent = await service.get_recent_resumes(limit=3)
    assert len(recent) == 3

    # Get all
    all_resumes = await service.get_recent_resumes(limit=10)
    assert len(all_resumes) == 5
