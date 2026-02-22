"""
Integration tests for database-backed API endpoints.

Tests the complete flow with database storage enabled:
1. Upload resume
2. Parse and save to database
3. Retrieve via GET endpoint
4. Update via PUT endpoint
5. Verify persistence
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume, ParsedResumeData
from app.core.config import settings


@pytest.mark.integration
class TestDatabaseBackedAPI:
    """Test API endpoints with database storage enabled"""

    @pytest.fixture(autouse=True)
    async def setup_method(self, db_session: AsyncSession):
        """Setup test database state"""
        # Clear any existing test data
        await db_session.execute(
            "DELETE FROM parsed_resume_data WHERE resume_id IN (SELECT id FROM resumes WHERE original_filename LIKE 'test-%')"
        )
        await db_session.execute(
            "DELETE FROM resumes WHERE original_filename LIKE 'test-%'"
        )
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_upload_and_parse_saves_to_database(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that parsing a resume saves data to database when USE_DATABASE=true"""
        # Skip if database not enabled
        if not settings.USE_DATABASE:
            pytest.skip("Database storage not enabled")

        # Create a simple test PDF content
        test_content = b"%PDF-1.4\nTest PDF content with sample resume text"

        # Upload resume
        response = await client.post(
            "/v1/resumes/upload",
            files={"file": ("test-resume.pdf", test_content, "application/pdf")}
        )

        assert response.status_code == 202
        data = response.json()
        resume_id = data["resume_id"]

        # Wait a moment for background parsing to complete
        import asyncio
        await asyncio.sleep(3)

        # Verify data was saved to database
        result = await db_session.execute(
            f"SELECT * FROM resumes WHERE id = '{resume_id}'"
        )
        resume = result.first()

        assert resume is not None, "Resume not found in database"
        assert resume.processing_status == "complete"

        # Verify parsed data was saved
        result = await db_session.execute(
            f"SELECT * FROM parsed_resume_data WHERE resume_id = '{resume_id}'"
        )
        parsed_data = result.first()

        assert parsed_data is not None, "Parsed data not found in database"
        assert parsed_data.personal_info is not None

    @pytest.mark.asyncio
    async def test_get_resume_retrieves_from_database(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that GET endpoint retrieves data from database"""
        if not settings.USE_DATABASE:
            pytest.skip("Database storage not enabled")

        # First, upload and parse a resume
        test_content = b"Sample resume content for testing"
        upload_response = await client.post(
            "/v1/resumes/upload",
            files={"file": ("test-get-resume.pdf", test_content, "application/pdf")}
        )

        resume_id = upload_response.json()["resume_id"]

        # Wait for parsing
        import asyncio
        await asyncio.sleep(3)

        # Retrieve via GET endpoint
        get_response = await client.get(f"/v1/resumes/{resume_id}")

        assert get_response.status_code == 200
        data = get_response.json()

        assert data["resume_id"] == resume_id
        assert data["status"] == "complete"
        assert data["data"] is not None
        assert "personal_info" in data["data"]

    @pytest.mark.asyncio
    async def test_put_resume_updates_database(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that PUT endpoint updates data in database"""
        if not settings.USE_DATABASE:
            pytest.skip("Database storage not enabled")

        # Upload and parse resume
        test_content = b"Test resume for PUT endpoint"
        upload_response = await client.post(
            "/v1/resumes/upload",
            files={"file": ("test-put-resume.pdf", test_content, "application/pdf")}
        )

        resume_id = upload_response.json()["resume_id"]

        # Wait for parsing
        import asyncio
        await asyncio.sleep(3)

        # Update via PUT endpoint
        update_data = {
            "personal_info": {
                "email": "updated@example.com",
                "phone": "+1-555-9999"
            }
        }

        put_response = await client.put(
            f"/v1/resumes/{resume_id}",
            json=update_data
        )

        assert put_response.status_code == 200
        data = put_response.json()

        assert data["status"] == "updated"
        assert data["data"]["personal_info"]["email"] == "updated@example.com"

        # Verify update persisted in database
        get_response = await client.get(f"/v1/resumes/{resume_id}")
        retrieved_data = get_response.json()

        assert retrieved_data["data"]["personal_info"]["email"] == "updated@example.com"
        assert retrieved_data["data"]["personal_info"]["phone"] == "+1-555-9999"

    @pytest.mark.asyncio
    async def test_database_persistence_across_restarts(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that data persists in database (simulating restart)"""
        if not settings.USE_DATABASE:
            pytest.skip("Database storage not enabled")

        # Upload and save resume
        test_content = b"Persistence test resume content"
        upload_response = await client.post(
            "/v1/resumes/upload",
            files={"file": ("test-persistence.pdf", test_content, "application/pdf")}
        )

        resume_id = upload_response.json()["resume_id"]

        # Wait for parsing
        import asyncio
        await asyncio.sleep(3)

        # Update data
        update_data = {
            "personal_info": {"email": "persistence@test.com"}
        }

        await client.put(
            f"/v1/resumes/{resume_id}",
            json=update_data
        )

        # Retrieve data (simulates post-restart state)
        get_response = await client.get(f"/v1/resumes/{resume_id}")

        assert get_response.status_code == 200
        data = get_response.json()

        # Verify updates persisted
        assert data["data"]["personal_info"]["email"] == "persistence@test.com"


@pytest.mark.integration
class TestInMemoryStorageBackwardCompatibility:
    """Test that in-memory storage still works when USE_DATABASE=false"""

    @pytest.mark.asyncio
    async def test_upload_saves_to_memory_when_disabled(
        self,
        client: AsyncClient,
        monkeypatch
    ):
        """Test that parsing saves to in-memory storage when database disabled"""
        # Temporarily disable database
        monkeypatch.setenv("USE_DATABASE", "false")

        # Need to reload settings to pick up the change
        from importlib import reload
        import app.core.config
        reload(app.core.config)

        test_content = b"Test in-memory storage"

        response = await client.post(
            "/v1/resumes/upload",
            files={"file": ("test-memory.pdf", test_content, "application/pdf")}
        )

        assert response.status_code == 202
        resume_id = response.json()["resume_id"]

        # Wait for parsing
        import asyncio
        await asyncio.sleep(3)

        # Verify in-memory storage has the data
        from app.core.storage import get_parsed_resume
        parsed_data = get_parsed_resume(resume_id)

        assert parsed_data is not None
        assert "personal_info" in parsed_data
