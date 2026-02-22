"""
Unit tests for StorageAdapter.

Tests the adapter's routing logic between database and in-memory storage.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.storage_adapter import StorageAdapter
from app.models.progress import ParsedData


@pytest.mark.unit
class TestStorageAdapterRouting:
    """Test storage adapter routes correctly based on feature flag"""

    @pytest.mark.asyncio
    async def test_adapter_uses_database_when_enabled(
        self,
        monkeypatch
    ):
        """Test adapter uses database service when USE_DATABASE=true"""
        # Enable database
        monkeypatch.setenv("USE_DATABASE", "true")

        # Clear settings cache to reload environment variables
        from app.core.config import clear_settings_cache
        clear_settings_cache()

        # Create mock db session
        mock_db = AsyncMock()

        adapter = StorageAdapter(mock_db)

        assert adapter.use_database is True
        assert adapter.db_service is not None

    @pytest.mark.asyncio
    async def test_adapter_uses_memory_when_disabled(
        self,
        monkeypatch
    ):
        """Test adapter uses in-memory storage when USE_DATABASE=false"""
        # Disable database
        monkeypatch.setenv("USE_DATABASE", "false")

        # Clear settings cache to reload environment variables
        from app.core.config import clear_settings_cache
        clear_settings_cache()

        # Create mock db session
        mock_db = AsyncMock()

        adapter = StorageAdapter(mock_db)

        assert adapter.use_database is False
        assert not hasattr(adapter, 'db_service') or adapter.db_service is None


@pytest.mark.unit
class TestStorageAdapterOperations:
    """Test storage adapter CRUD operations"""

    @pytest.mark.asyncio
    async def test_save_and_get_parsed_data_memory(
        self,
        monkeypatch
    ):
        """Test save and get operations with in-memory storage"""
        monkeypatch.setenv("USE_DATABASE", "false")

        # Clear settings cache to reload environment variables
        from app.core.config import clear_settings_cache
        clear_settings_cache()

        # Create mock db session
        mock_db = AsyncMock()

        adapter = StorageAdapter(mock_db)

        # Test data
        resume_id = "test-resume-123"
        parsed_data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "+1-555-0100",
            "skills": {"all": ["Python", "FastAPI"]},
            "work_experience": [],
            "education": [],
            "certifications": [],
            "languages": [],
            "projects": [],
            "additional_info": {},
            "extraction_confidence": 0.9
        }

        # Save
        await adapter.save_parsed_data(resume_id, parsed_data)

        # Get
        retrieved = await adapter.get_parsed_data(resume_id)

        assert retrieved is not None
        assert retrieved["full_name"] == "Test User"
        assert retrieved["email"] == "test@example.com"

        # Clean up
        from app.core.storage import delete_parsed_resume
        delete_parsed_resume(resume_id)

    @pytest.mark.asyncio
    async def test_update_parsed_data_memory(
        self,
        monkeypatch
    ):
        """Test update operation with in-memory storage"""
        monkeypatch.setenv("USE_DATABASE", "false")

        # Clear settings cache to reload environment variables
        from app.core.config import clear_settings_cache
        clear_settings_cache()

        # Create mock db session
        mock_db = AsyncMock()

        adapter = StorageAdapter(mock_db)

        # Save initial data
        resume_id = "test-update-456"
        initial_data = {
            "full_name": "Original Name",
            "email": "original@example.com",
            "skills": {"all": ["Python"]},
            "work_experience": [],
            "education": [],
            "certifications": [],
            "languages": [],
            "projects": [],
            "additional_info": {},
            "extraction_confidence": 0.8
        }

        await adapter.save_parsed_data(resume_id, initial_data)

        # Update
        updated_data = initial_data.copy()
        updated_data["email"] = "updated@example.com"
        updated_data["phone"] = "+1-555-9999"

        success = await adapter.update_parsed_data(resume_id, updated_data)

        assert success is True

        # Verify update
        retrieved = await adapter.get_parsed_data(resume_id)

        assert retrieved["email"] == "updated@example.com"
        assert retrieved["phone"] == "+1-555-9999"

        # Clean up
        from app.core.storage import delete_parsed_resume
        delete_parsed_resume(resume_id)

    @pytest.mark.asyncio
    async def test_get_nonexistent_resume_returns_none(
        self,
        monkeypatch
    ):
        """Test that getting non-existent resume returns None"""
        monkeypatch.setenv("USE_DATABASE", "false")

        # Clear settings cache to reload environment variables
        from app.core.config import clear_settings_cache
        clear_settings_cache()

        # Create mock db session
        mock_db = AsyncMock()

        adapter = StorageAdapter(mock_db)

        retrieved = await adapter.get_parsed_data("nonexistent-id")

        assert retrieved is None
