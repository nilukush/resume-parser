"""
Integration tests for database connection and configuration.
These tests verify that the database can be properly configured and connections established.
"""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


def test_database_connection():
    """Test that database connection can be established."""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost:5432/test",
        pool_pre_ping=True,
    )
    assert engine is not None
    assert hasattr(engine, 'connect')
    # Dispose engine to clean up
    engine.dispose()


@pytest.mark.asyncio
async def test_database_module_imports():
    """Test that database module can be imported and has expected attributes."""
    from app.core.database import engine, Base, get_db
    assert engine is not None
    assert Base is not None
    assert callable(get_db)


@pytest.mark.asyncio
async def test_config_module_imports():
    """Test that config module can be imported and has expected settings."""
    from app.core.config import settings
    assert hasattr(settings, 'DATABASE_URL')
    assert hasattr(settings, 'REDIS_URL')
    assert hasattr(settings, 'OPENAI_API_KEY')
    assert hasattr(settings, 'SECRET_KEY')
    assert hasattr(settings, 'ENVIRONMENT')


@pytest.mark.asyncio
async def test_resume_model_exists():
    """Test that Resume model exists and has expected fields."""
    from app.models.resume import Resume
    assert hasattr(Resume, '__tablename__')
    assert Resume.__tablename__ == 'resumes'
    # Check for expected columns
    columns = [c.name for c in Resume.__table__.columns]
    expected_columns = [
        'id', 'file_name', 'file_type', 'file_size',
        'raw_text', 'extracted_data', 'parsed_data',
        'processing_status', 'error_message',
        'created_at', 'updated_at'
    ]
    for col in expected_columns:
        assert col in columns, f"Expected column '{col}' not found in Resume model"


@pytest.mark.asyncio
async def test_models_init_exports():
    """Test that models __init__.py exports Resume model."""
    from app.models import Resume
    assert Resume is not None
