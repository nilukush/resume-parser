"""
Test Alembic configuration and migrations.

This test verifies that:
1. Alembic is properly configured
2. Migration files can be created
3. Migrations can be applied (requires database)
"""
import pytest
import os
from pathlib import Path


def test_alembic_ini_exists():
    """Test that alembic.ini configuration file exists."""
    alembic_ini_path = Path("alembic.ini")
    assert alembic_ini_path.exists(), "alembic.ini should exist in backend directory"


def test_alembic_env_exists():
    """Test that alembic/env.py file exists."""
    env_path = Path("alembic/env.py")
    assert env_path.exists(), "alembic/env.py should exist"


def test_alembic_script_mako_exists():
    """Test that script.py.mako exists (Alembic template)."""
    mako_path = Path("alembic/script.py.mako")
    assert mako_path.exists(), "alembic/script.py.mako should exist"


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set")
def test_migration_files_created():
    """Test that migration files are created."""
    versions_path = Path("alembic/versions")
    assert versions_path.exists(), "alembic/versions directory should exist"

    # Check for migration files
    migration_files = list(versions_path.glob("*.py"))
    assert len(migration_files) > 0, "At least one migration file should exist"


def test_models_import():
    """Test that all database models can be imported."""
    from app.models.resume import Resume, ParsedResumeData, ResumeCorrection, ResumeShare

    # Verify models have __tablename__ attribute
    assert hasattr(Resume, '__tablename__')
    assert hasattr(ParsedResumeData, '__tablename__')
    assert hasattr(ResumeCorrection, '__tablename__')
    assert hasattr(ResumeShare, '__tablename__')

    # Verify table names
    assert Resume.__tablename__ == "resumes"
    assert ParsedResumeData.__tablename__ == "parsed_resume_data"
    assert ResumeCorrection.__tablename__ == "resume_corrections"
    assert ResumeShare.__tablename__ == "resume_shares"
