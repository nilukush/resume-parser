"""
Pytest configuration and fixtures for the ResuMate application.

This module provides shared fixtures and configuration for all tests.
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the event loop for the test session.

    Yields:
        The event loop instance.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings(monkeypatch):
    """
    Mock settings for testing.

    Args:
        monkeypatch: pytest monkeypatch fixture.

    Yields:
        Mocked settings object.
    """
    from app.core.config import Settings

    mock_settings = MagicMock(spec=Settings)
    mock_settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    mock_settings.DATABASE_URL_SYNC = "sqlite:///:memory:"
    mock_settings.REDIS_URL = "redis://localhost:6379/0"
    mock_settings.OPENAI_API_KEY = "test-api-key"
    mock_settings.SECRET_KEY = "test-secret-key"
    mock_settings.ENVIRONMENT = "testing"
    mock_settings.ALLOWED_ORIGINS = "http://localhost:3000"
    mock_settings.MAX_UPLOAD_SIZE = 10485760
    mock_settings.is_development = False
    mock_settings.is_production = False
    mock_settings.is_testing = True

    monkeypatch.setattr("app.core.config.settings", mock_settings)
    monkeypatch.setattr("app.core.database.settings", mock_settings)

    yield mock_settings


@pytest.fixture
async def mock_db_session():
    """
    Mock database session for testing.

    Yields:
        AsyncMock database session.
    """
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=[])))
    yield session
