"""
Test lazy database initialization for serverless functions.

This test suite verifies that database initialization happens lazily
(at request time) rather than at module import time.
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestLazyDatabaseInitialization:
    """Test that database initialization is lazy and doesn't happen at import."""

    def test_module_import_without_database(self):
        """
        Test that the database module can be imported without database connection.

        This is critical for serverless functions - the import should succeed
        even if the database is unavailable or credentials are wrong.
        """
        # Set invalid database URL to ensure no connection is made
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://invalid:invalid@localhost:9999/invalid'
        os.environ['USE_DATABASE'] = 'true'
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['SECRET_KEY'] = 'test'

        # This import should NOT raise an exception
        # If it does, the test fails (meaning database is being initialized at import)
        try:
            from app.core import database
            assert True, "Module imported successfully without database connection"
        except Exception as e:
            pytest.fail(f"Module import failed with: {e}. Database is being initialized at import time!")

    def test_engine_is_none_at_import(self):
        """
        Test that the engine is None after module import.

        This verifies that lazy initialization is working correctly.
        """
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://test:test@localhost/test'
        os.environ['USE_DATABASE'] = 'true'
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['SECRET_KEY'] = 'test'

        # Import module
        from app.core import database

        # Engine should be None at import time
        assert database.engine is None, "Engine should be None at import time"

    def test_get_engine_creates_engine(self):
        """
        Test that get_engine() creates the engine on first call.

        This is the lazy initialization behavior we want.
        """
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://test:test@localhost/test'
        os.environ['USE_DATABASE'] = 'true'
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['SECRET_KEY'] = 'test'

        from app.core import database

        # First call should create engine
        with patch('app.core.database.create_async_engine') as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            engine = database.get_engine()

            # Verify create_async_engine was called
            assert mock_create.called, "create_async_engine should be called on first get_engine()"

    def test_get_engine_returns_cached_engine(self):
        """
        Test that get_engine() returns the same engine on subsequent calls.

        This ensures we're not creating multiple engines.
        """
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://test:test@localhost/test'
        os.environ['USE_DATABASE'] = 'true'
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['SECRET_KEY'] = 'test'

        from app.core import database

        # Mock the engine creation
        with patch('app.core.database.create_async_engine') as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            # Call get_engine multiple times
            engine1 = database.get_engine()
            engine2 = database.get_engine()

            # Should only create once
            assert mock_create.call_count == 1, "Engine should only be created once"
            assert engine1 is engine2, "Should return the same engine instance"


class TestHealthCheckGracefulDegradation:
    """Test that health check degrades gracefully when database is unavailable."""

    @pytest.mark.asyncio
    async def test_health_check_without_database(self):
        """
        Test that health check returns degraded status when database is unavailable.

        The function should still return 200 OK, not crash.
        """
        # Set up environment with invalid database
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://invalid:invalid@localhost:9999/invalid'
        os.environ['USE_DATABASE'] = 'true'
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['SECRET_KEY'] = 'test'

        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Health check should not crash
        response = client.get("/health")

        # Should return 200 (service is running, even if degraded)
        assert response.status_code == 200

        # Should indicate degraded status
        data = response.json()
        assert data['status'] in ['degraded', 'healthy'], "Status should be degraded or healthy"
        assert data['database'] == 'disconnected', "Database should be marked as disconnected"

    @pytest.mark.asyncio
    async def test_health_check_with_database(self):
        """
        Test that health check returns healthy status when database is available.

        This is the happy path.
        """
        # Set up environment with valid database (will be mocked)
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://test:test@localhost/test'
        os.environ['USE_DATABASE'] = 'true'
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['SECRET_KEY'] = 'test'

        # We'll need to mock the actual database connection
        # This test will be implemented after the fix
        pass
