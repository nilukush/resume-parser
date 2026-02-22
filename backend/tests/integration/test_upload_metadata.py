"""
Integration tests for resume upload metadata persistence.

These tests verify that the upload endpoint correctly saves resume
metadata to the database before starting the background parsing task.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from httpx import AsyncClient

from app.main import app
from app.core.database import db_manager, AsyncSessionLocal
from app.models.resume import Resume


@pytest.mark.asyncio
async def test_upload_creates_resume_metadata_in_database():
    """
    Test that uploading a resume creates a Resume record in the database.

    Expected behavior:
    - POST /v1/resumes/upload returns 202 Accepted
    - Resume record exists in database with correct metadata
    - file_hash is correctly computed and stored
    - processing_status is "processing"
    """
    import uuid
    # Create test file content with unique data to avoid conflicts
    unique_id = str(uuid.uuid4())
    test_content = f"Test resume content for upload {unique_id}".encode()
    test_filename = f"test_resume_{unique_id}.pdf"

    # Create async client
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Upload file
        files = {"file": (test_filename, test_content, "application/pdf")}
        response = await client.post("/v1/resumes/upload", files=files)

    # Assert upload was accepted
    assert response.status_code == 202
    data = response.json()
    assert "resume_id" in data
    assert data["status"] == "processing"
    assert "file_hash" in data

    resume_id = data["resume_id"]
    file_hash = data["file_hash"]

    # Verify Resume record exists in database
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        resume = result.scalar_one_or_none()

        # Assert resume metadata was saved
        assert resume is not None, "Resume record should exist in database"
        assert resume.original_filename == test_filename
        assert resume.file_type == "pdf"
        assert resume.file_size_bytes == len(test_content)
        assert resume.file_hash == file_hash
        assert resume.processing_status == "processing"


@pytest.mark.asyncio
async def test_duplicate_file_hash_rejected():
    """
    Test that uploading the same file twice is rejected.

    Expected behavior:
    - First upload succeeds (202)
    - Second upload with identical content fails (400)
    - Error message mentions duplicate file
    """
    # Create test file content
    test_content = b"Duplicate test resume content"
    test_filename = "duplicate_resume.pdf"

    # Create async client
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First upload
        files = {"file": (test_filename, test_content, "application/pdf")}
        response1 = await client.post("/v1/resumes/upload", files=files)

        # Assert first upload succeeded
        assert response1.status_code == 202

        # Second upload with same content (different filename)
        files = {"file": ("another_resume.pdf", test_content, "application/pdf")}
        response2 = await client.post("/v1/resumes/upload", files=files)

        # Assert second upload was rejected
        assert response2.status_code == 400
        assert "duplicate" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_metadata_fields_are_correct():
    """
    Test that all metadata fields are correctly saved.

    Expected behavior:
    - All Resume model fields are populated correctly
    - file_hash is SHA256 hash of content
    - uploaded_at timestamp is set automatically
    """
    import hashlib
    import uuid

    # Create test file with known content and unique data
    unique_id = str(uuid.uuid4())
    test_content = f"Known resume content for hash verification {unique_id}".encode()
    test_filename = f"hash_verification_resume_{unique_id}.pdf"

    # Compute expected SHA256 hash
    expected_hash = hashlib.sha256(test_content).hexdigest()

    # Create async client
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Upload file
        files = {"file": (test_filename, test_content, "application/pdf")}
        response = await client.post("/v1/resumes/upload", files=files)

    assert response.status_code == 202
    resume_id = response.json()["resume_id"]

    # Verify all fields in database
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        resume = result.scalar_one()

        # Assert all fields
        assert resume.file_hash == expected_hash
        assert resume.file_size_bytes == len(test_content)
        assert resume.file_type == "pdf"
        assert resume.original_filename == test_filename
        assert resume.storage_path == ""  # Empty for now (will implement file storage later)
        assert resume.processing_status == "processing"
        assert resume.uploaded_at is not None
        assert resume.id is not None
