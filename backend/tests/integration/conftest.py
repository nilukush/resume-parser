"""
Pytest configuration and fixtures for integration tests.

This module provides shared fixtures for integration tests that require
real database connections.
"""

import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db, Base


# Use test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://resumate_user:resumate_password@localhost:5433/resumate_test"

# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

# Create async session maker
TestAsyncSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    This fixture creates a new database session for each test function
    and ensures proper cleanup after the test completes.

    Yields:
        Async database session
    """
    # Create session
    async with TestAsyncSessionLocal() as session:
        yield session

    # Cleanup is automatic when context manager exits


@pytest.fixture(scope="session")
async def setup_test_database():
    """
    Set up test database schema.

    This fixture runs once per test session to create all required tables.
    """
    async with test_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup: Drop all tables after tests complete
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
