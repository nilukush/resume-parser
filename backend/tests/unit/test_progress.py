import pytest
from app.models.progress import ProgressUpdate, ProgressStage

def test_create_progress_update():
    """Test creating a progress update message"""
    update = ProgressUpdate(
        resume_id="test-123",
        stage=ProgressStage.TEXT_EXTRACTION,
        progress=50,
        status="Extracting text from PDF..."
    )

    assert update.resume_id == "test-123"
    assert update.stage == ProgressStage.TEXT_EXTRACTION
    assert update.progress == 50
    assert update.status == "Extracting text from PDF..."

def test_progress_update_to_dict():
    """Test converting progress update to dictionary"""
    update = ProgressUpdate(
        resume_id="test-123",
        stage=ProgressStage.NLP_PARSING,
        progress=75,
        status="Analyzing resume structure..."
    )

    data = update.to_dict()

    assert data["resume_id"] == "test-123"
    assert data["stage"] == "nlp_parsing"
    assert data["progress"] == 75
    assert data["status"] == "Analyzing resume structure..."
    assert "timestamp" in data
