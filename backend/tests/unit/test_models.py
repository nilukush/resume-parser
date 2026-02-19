"""
Unit tests for database models.

These tests verify the structure and behavior of ORM models.
"""

import pytest
from datetime import datetime
from sqlalchemy import inspect
import uuid


@pytest.mark.asyncio
async def test_resume_model_import():
    """Test that Resume model can be imported."""
    from app.models.resume import Resume
    assert Resume is not None


@pytest.mark.asyncio
async def test_all_models_import():
    """Test that all 4 models can be imported."""
    from app.models import Resume, ParsedResumeData, ResumeCorrection, ResumeShare
    assert Resume is not None
    assert ParsedResumeData is not None
    assert ResumeCorrection is not None
    assert ResumeShare is not None


@pytest.mark.asyncio
async def test_resume_model_table_name():
    """Test that Resume model has correct table name."""
    from app.models.resume import Resume
    assert Resume.__tablename__ == 'resumes'


@pytest.mark.asyncio
async def test_resume_model_primary_key_is_uuid():
    """Test that Resume model uses UUID as primary key."""
    from app.models.resume import Resume
    pk_column = Resume.__table__.columns['id']
    assert str(pk_column.type) == 'UUID' or 'UUID' in str(pk_column.type)


@pytest.mark.asyncio
async def test_resume_model_columns():
    """Test that Resume model has all expected columns per spec."""
    from app.models.resume import Resume

    columns = [c.name for c in Resume.__table__.columns]

    # Expected columns per specification
    expected_columns = {
        'id', 'original_filename', 'file_type', 'file_size_bytes',
        'file_hash', 'storage_path', 'processing_status', 'confidence_score',
        'parsing_version', 'uploaded_at', 'processed_at', 'created_at', 'updated_at'
    }

    missing_columns = expected_columns - set(columns)
    extra_columns = set(columns) - expected_columns

    assert not missing_columns, f"Missing columns: {missing_columns}"
    assert not extra_columns, f"Unexpected columns: {extra_columns}"


@pytest.mark.asyncio
async def test_resume_model_required_fields():
    """Test that Resume model has correct nullable fields per spec."""
    from app.models.resume import Resume

    # Required fields (non-nullable) per spec
    required_fields = [
        'original_filename', 'file_type', 'file_size_bytes',
        'file_hash', 'storage_path'
    ]

    for field in required_fields:
        column = Resume.__table__.columns[field]
        assert not column.nullable, f"Field '{field}' should be required (non-nullable)"


@pytest.mark.asyncio
async def test_resume_model_optional_fields():
    """Test that Resume model has correct nullable fields per spec."""
    from app.models.resume import Resume

    # Optional fields (nullable) per spec
    optional_fields = ['confidence_score', 'parsing_version', 'processed_at']

    for field in optional_fields:
        column = Resume.__table__.columns[field]
        assert column.nullable, f"Field '{field}' should be optional (nullable)"


@pytest.mark.asyncio
async def test_resume_model_file_hash_unique():
    """Test that file_hash is unique."""
    from app.models.resume import Resume
    column = Resume.__table__.columns['file_hash']
    assert column.unique, "file_hash should be unique"


@pytest.mark.asyncio
async def test_parsed_resume_data_model_exists():
    """Test that ParsedResumeData model exists."""
    from app.models.resume import ParsedResumeData
    assert ParsedResumeData is not None
    assert ParsedResumeData.__tablename__ == 'parsed_resume_data'


@pytest.mark.asyncio
async def test_parsed_resume_data_columns():
    """Test that ParsedResumeData has all expected columns per spec."""
    from app.models.resume import ParsedResumeData

    columns = [c.name for c in ParsedResumeData.__table__.columns]

    expected_columns = {
        'id', 'resume_id', 'personal_info', 'work_experience',
        'education', 'skills', 'confidence_scores', 'created_at', 'updated_at'
    }

    missing_columns = expected_columns - set(columns)
    assert not missing_columns, f"Missing columns: {missing_columns}"


@pytest.mark.asyncio
async def test_parsed_resume_data_jsonb_fields():
    """Test that JSONB fields are properly configured."""
    from app.models.resume import ParsedResumeData

    jsonb_fields = ['personal_info', 'work_experience', 'education', 'skills', 'confidence_scores']

    for field in jsonb_fields:
        column = ParsedResumeData.__table__.columns[field]
        type_str = str(column.type).upper()
        assert 'JSON' in type_str, f"Field '{field}' should be a JSON/JSONB type"


@pytest.mark.asyncio
async def test_resume_correction_model_exists():
    """Test that ResumeCorrection model exists."""
    from app.models.resume import ResumeCorrection
    assert ResumeCorrection is not None
    assert ResumeCorrection.__tablename__ == 'resume_corrections'


@pytest.mark.asyncio
async def test_resume_correction_columns():
    """Test that ResumeCorrection has all expected columns per spec."""
    from app.models.resume import ResumeCorrection

    columns = [c.name for c in ResumeCorrection.__table__.columns]

    expected_columns = {
        'id', 'resume_id', 'field_path', 'original_value',
        'corrected_value', 'created_at'
    }

    assert set(columns) == expected_columns, f"Expected {expected_columns}, got {set(columns)}"


@pytest.mark.asyncio
async def test_resume_correction_jsonb_fields():
    """Test that original_value and corrected_value are JSONB."""
    from app.models.resume import ResumeCorrection

    for field in ['original_value', 'corrected_value']:
        column = ResumeCorrection.__table__.columns[field]
        type_str = str(column.type).upper()
        assert 'JSON' in type_str, f"Field '{field}' should be a JSON/JSONB type"


@pytest.mark.asyncio
async def test_resume_share_model_exists():
    """Test that ResumeShare model exists."""
    from app.models.resume import ResumeShare
    assert ResumeShare is not None
    assert ResumeShare.__tablename__ == 'resume_shares'


@pytest.mark.asyncio
async def test_resume_share_columns():
    """Test that ResumeShare has all expected columns per spec."""
    from app.models.resume import ResumeShare

    columns = [c.name for c in ResumeShare.__table__.columns]

    expected_columns = {
        'id', 'resume_id', 'share_token', 'access_count',
        'expires_at', 'is_active', 'created_at'
    }

    assert set(columns) == expected_columns, f"Expected {expected_columns}, got {set(columns)}"


@pytest.mark.asyncio
async def test_resume_share_token_unique():
    """Test that share_token is unique."""
    from app.models.resume import ResumeShare
    column = ResumeShare.__table__.columns['share_token']
    assert column.unique, "share_token should be unique"


@pytest.mark.asyncio
async def test_resume_share_default_values():
    """Test that ResumeShare has correct default values."""
    from app.models.resume import ResumeShare

    # Check access_count defaults to 0
    access_count_column = ResumeShare.__table__.columns['access_count']
    assert access_count_column.default is not None, "access_count should have a default"

    # Check is_active defaults to True
    is_active_column = ResumeShare.__table__.columns['is_active']
    assert is_active_column.default is not None, "is_active should have a default"


@pytest.mark.asyncio
async def test_models_module_exports():
    """Test that models module exports all 4 models."""
    from app.models import Resume, ParsedResumeData, ResumeCorrection, ResumeShare

    assert Resume is not None
    assert Resume.__tablename__ == 'resumes'
    assert ParsedResumeData is not None
    assert ParsedResumeData.__tablename__ == 'parsed_resume_data'
    assert ResumeCorrection is not None
    assert ResumeCorrection.__tablename__ == 'resume_corrections'
    assert ResumeShare is not None
    assert ResumeShare.__tablename__ == 'resume_shares'


@pytest.mark.asyncio
async def test_all_models_use_uuid_primary_key():
    """Test that all models use UUID as primary key."""
    from app.models import Resume, ParsedResumeData, ResumeCorrection, ResumeShare

    for model in [Resume, ParsedResumeData, ResumeCorrection, ResumeShare]:
        pk_column = model.__table__.columns['id']
        type_str = str(pk_column.type)
        assert 'UUID' in type_str, f"{model.__name__} should use UUID as primary key, got {type_str}"
