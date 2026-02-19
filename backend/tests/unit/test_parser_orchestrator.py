"""
Unit tests for Parser Orchestrator Service.

Tests follow TDD discipline:
1. Write failing test FIRST (RED phase)
2. Implement minimal code to pass tests (GREEN phase)
3. Refactor for quality (REFACTOR phase)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.parser_orchestrator import ParserOrchestrator
from app.models.progress import ProgressStage


@pytest.mark.asyncio
async def test_orchestrator_sends_progress_updates():
    """Test that orchestrator sends progress updates during parsing"""
    mock_websocket_manager = Mock()
    mock_websocket_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_websocket_manager)

    resume_id = "test-123"
    file_content = b"Sample resume text for John Doe\nEmail: john@example.com"

    await orchestrator.parse_resume(resume_id, "test.txt", file_content)

    # Verify progress updates were sent
    assert mock_websocket_manager.broadcast_to_resume.call_count >= 3

    # Check that stages were called in order
    calls = mock_websocket_manager.broadcast_to_resume.call_args_list
    stages = [call[0][0]["stage"] for call in calls]

    assert ProgressStage.TEXT_EXTRACTION.value in stages
    assert ProgressStage.NLP_PARSING.value in stages
    assert ProgressStage.COMPLETE.value in stages


@pytest.mark.asyncio
async def test_orchestrator_returns_parsed_data():
    """Test that orchestrator returns parsed resume data"""
    mock_websocket_manager = Mock()
    mock_websocket_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_websocket_manager)

    resume_id = "test-456"
    file_content = b"John Doe\nEmail: john@example.com"

    result = await orchestrator.parse_resume(resume_id, "test.txt", file_content)

    # Verify result structure
    assert isinstance(result, dict)
    assert "personal_info" in result
    assert "work_experience" in result
    assert "education" in result
    assert "skills" in result
    assert "confidence_scores" in result


@pytest.mark.asyncio
async def test_orchestrator_sends_complete_progress_with_data():
    """Test that orchestrator sends complete progress with parsed data"""
    mock_websocket_manager = Mock()
    mock_websocket_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_websocket_manager)

    resume_id = "test-789"
    file_content = b"Sample resume"

    await orchestrator.parse_resume(resume_id, "test.txt", file_content)

    # Get the last call which should be COMPLETE
    calls = mock_websocket_manager.broadcast_to_resume.call_args_list
    last_call = calls[-1]
    last_message = last_call[0][0]

    assert last_message["stage"] == ProgressStage.COMPLETE.value
    assert last_message["progress"] == 100
    assert "data" in last_message
    # The parsed data is directly in the data field (not nested under "parsed_data")
    assert "personal_info" in last_message["data"]
    assert "work_experience" in last_message["data"]
    assert "education" in last_message["data"]
    assert "skills" in last_message["data"]
    assert "confidence_scores" in last_message["data"]


@pytest.mark.asyncio
async def test_orchestrator_handles_text_extraction_error():
    """Test that orchestrator handles text extraction errors"""
    mock_websocket_manager = Mock()
    mock_websocket_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_websocket_manager)

    resume_id = "test-error"

    # Use unsupported file type to trigger error
    with pytest.raises(Exception):
        await orchestrator.parse_resume(resume_id, "test.xyz", b"some content")

    # Verify error was sent
    calls = mock_websocket_manager.broadcast_to_resume.call_args_list
    error_calls = [call for call in calls if call[0][0]["stage"] == ProgressStage.ERROR.value]
    assert len(error_calls) > 0


@pytest.mark.asyncio
async def test_orchestrator_sends_progress_during_extraction():
    """Test that orchestrator sends intermediate progress during text extraction"""
    mock_websocket_manager = Mock()
    mock_websocket_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_websocket_manager)

    resume_id = "test-progress"
    file_content = b"Sample resume text"

    await orchestrator.parse_resume(resume_id, "test.txt", file_content)

    calls = mock_websocket_manager.broadcast_to_resume.call_args_list

    # Filter for text_extraction stage updates
    extraction_calls = [
        call for call in calls
        if call[0][0]["stage"] == ProgressStage.TEXT_EXTRACTION.value
    ]

    # Should have at least one text_extraction update
    assert len(extraction_calls) >= 1


@pytest.mark.asyncio
async def test_orchestrator_sends_progress_during_nlp_parsing():
    """Test that orchestrator sends intermediate progress during NLP parsing"""
    mock_websocket_manager = Mock()
    mock_websocket_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_websocket_manager)

    resume_id = "test-nlp-progress"
    file_content = b"Sample resume text"

    await orchestrator.parse_resume(resume_id, "test.txt", file_content)

    calls = mock_websocket_manager.broadcast_to_resume.call_args_list

    # Filter for nlp_parsing stage updates
    nlp_calls = [
        call for call in calls
        if call[0][0]["stage"] == ProgressStage.NLP_PARSING.value
    ]

    # Should have at least one nlp_parsing update
    assert len(nlp_calls) >= 1
