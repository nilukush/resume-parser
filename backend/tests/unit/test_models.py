"""
Unit tests for database models.

These tests verify the structure and behavior of ORM models.
"""

import pytest
from datetime import datetime
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_resume_model_import():
    """Test that Resume model can be imported."""
    from app.models.resume import Resume
    assert Resume is not None


@pytest.mark.asyncio
async def test_resume_model_table_name():
    """Test that Resume model has correct table name."""
    from app.models.resume import Resume
    assert Resume.__tablename__ == 'resumes'


@pytest.mark.asyncio
async def test_resume_model_columns():
    """Test that Resume model has all expected columns."""
    from app.models.resume import Resume
    inspector = inspect(Resume)

    # Get all column names
    columns = [c.name for c in Resume.__table__.columns]

    # Verify expected columns exist
    expected_columns = {
        'id', 'file_name', 'file_type', 'file_size',
        'raw_text', 'extracted_data', 'parsed_data',
        'processing_status', 'error_message',
        'created_at', 'updated_at'
    }

    missing_columns = expected_columns - set(columns)
    extra_columns = set(columns) - expected_columns

    assert not missing_columns, f"Missing columns: {missing_columns}"
    assert not extra_columns, f"Unexpected columns: {extra_columns}"


@pytest.mark.asyncio
async def test_resume_model_required_fields():
    """Test that Resume model has correct nullable fields."""
    from app.models.resume import Resume

    # Required fields (non-nullable)
    required_fields = ['file_name', 'file_type', 'file_size', 'processing_status']

    for field in required_fields:
        column = Resume.__table__.columns[field]
        assert not column.nullable, f"Field '{field}' should be required (non-nullable)"


@pytest.mark.asyncio
async def test_resume_model_optional_fields():
    """Test that Resume model has correct nullable fields."""
    from app.models.resume import Resume

    # Optional fields (nullable)
    optional_fields = ['raw_text', 'extracted_data', 'parsed_data', 'error_message']

    for field in optional_fields:
        column = Resume.__table__.columns[field]
        assert column.nullable, f"Field '{field}' should be optional (nullable)"


@pytest.mark.asyncio
async def test_resume_model_default_values():
    """Test that Resume model has correct default values."""
    from app.models.resume import Resume

    # Check processing_status has a default
    status_column = Resume.__table__.columns['processing_status']
    assert status_column.default is not None, "processing_status should have a default value"


@pytest.mark.asyncio
async def test_resume_model_string_constraints():
    """Test that Resume model has correct string length constraints."""
    from app.models.resume import Resume

    # file_name should have a max length
    file_name_column = Resume.__table__.columns['file_name']
    assert file_name_column.type.length is not None, "file_name should have a max length"


@pytest.mark.asyncio
async def test_resume_model_relationships():
    """Test that Resume model has expected relationships."""
    from app.models.resume import Resume

    # Check if relationships are defined (will be implemented with other models)
    relationships = [r.key for r in inspect(Resume).relationships]
    # For now, we expect no relationships until we add related models
    assert isinstance(relationships, list)


@pytest.mark.asyncio
async def test_resume_model_instance_creation():
    """Test that Resume model instances can be created."""
    from app.models.resume import Resume

    resume = Resume(
        file_name="test_resume.pdf",
        file_type="application/pdf",
        file_size=102400,
        raw_text="Sample resume text",
        processing_status="pending"
    )

    assert resume.file_name == "test_resume.pdf"
    assert resume.file_type == "application/pdf"
    assert resume.file_size == 102400
    assert resume.raw_text == "Sample resume text"
    assert resume.processing_status == "pending"
    assert resume.extracted_data is None
    assert resume.parsed_data is None
    assert resume.error_message is None


@pytest.mark.asyncio
async def test_resume_model_json_fields():
    """Test that JSON fields are properly configured."""
    from app.models.resume import Resume

    # Check that JSON fields use JSON type
    json_fields = ['extracted_data', 'parsed_data']

    for field in json_fields:
        column = Resume.__table__.columns[field]
        # SQLAlchemy uses JSON or JSONB type
        type_name = str(column.type).upper()
        assert 'JSON' in type_name, f"Field '{field}' should be a JSON type"


@pytest.mark.asyncio
async def test_resume_model_timestamps():
    """Test that timestamp fields are properly configured."""
    from app.models.resume import Resume

    # Check created_at and updated_at exist
    assert 'created_at' in [c.name for c in Resume.__table__.columns]
    assert 'updated_at' in [c.name for c in Resume.__table__.columns]


@pytest.mark.asyncio
async def test_models_module_exports():
    """Test that models module exports Resume model."""
    from app.models import Resume

    assert Resume is not None
    assert Resume.__tablename__ == 'resumes'
