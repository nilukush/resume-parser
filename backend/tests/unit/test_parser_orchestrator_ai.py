"""
Unit tests for Parser Orchestrator AI integration.

These tests verify that AI enhancement is properly integrated
into the parser orchestrator pipeline.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_parse_resume_calls_ai_enhancement():
    """Test that parse_resume calls AI enhancement when enabled."""
    from app.services.parser_orchestrator import ParserOrchestrator
    from app.models.progress import ProgressStage

    mock_ws_manager = MagicMock()
    mock_ws_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_ws_manager)

    sample_text = "John Doe\nSoftware Engineer"
    sample_nlp_data = {
        "personal_info": {"full_name": "John Doe", "email": "", "phone": ""},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {"personal_info": 70, "overall": 70}
    }
    sample_ai_data = {
        "personal_info": {"full_name": "John Doe", "email": "john@example.com", "phone": "+1-555-0123"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {"personal_info": 95, "overall": 92}
    }

    with patch('app.services.parser_orchestrator.extract_text') as mock_extract:
        mock_extract.return_value = sample_text

        with patch('app.services.parser_orchestrator.extract_entities') as mock_nlp:
            mock_nlp.return_value = sample_nlp_data

            with patch('app.services.parser_orchestrator.enhance_with_ai') as mock_ai:
                mock_ai.return_value = sample_ai_data

                with patch('app.services.parser_orchestrator.save_parsed_resume'):
                    result = await orchestrator.parse_resume(
                        "resume-123",
                        "resume.pdf",
                        b"fake pdf content",
                        enable_ai=True
                    )

                    # AI enhancement should have been called
                    mock_ai.assert_called_once_with(sample_text, sample_nlp_data)

                    # Result should have AI-enhanced data
                    assert result["personal_info"]["email"] == "john@example.com"
                    assert result["confidence_scores"]["overall"] == 92


@pytest.mark.asyncio
async def test_parse_resume_skips_ai_when_disabled():
    """Test that parse_resume skips AI enhancement when disabled."""
    from app.services.parser_orchestrator import ParserOrchestrator

    mock_ws_manager = MagicMock()
    mock_ws_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_ws_manager)

    sample_text = "John Doe\nSoftware Engineer"
    sample_nlp_data = {
        "personal_info": {"full_name": "John Doe", "email": "", "phone": ""},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {"personal_info": 70, "overall": 70}
    }

    with patch('app.services.parser_orchestrator.extract_text') as mock_extract:
        mock_extract.return_value = sample_text

        with patch('app.services.parser_orchestrator.extract_entities') as mock_nlp:
            mock_nlp.return_value = sample_nlp_data

            with patch('app.services.parser_orchestrator.enhance_with_ai') as mock_ai:
                with patch('app.services.parser_orchestrator.save_parsed_resume'):
                    result = await orchestrator.parse_resume(
                        "resume-123",
                        "resume.pdf",
                        b"fake pdf content",
                        enable_ai=False
                    )

                    # AI enhancement should NOT have been called
                    mock_ai.assert_not_called()

                    # Result should have original NLP data
                    assert result["personal_info"]["email"] == ""
                    assert result["confidence_scores"]["overall"] == 70


@pytest.mark.asyncio
async def test_parse_resume_handles_ai_failure_gracefully():
    """Test that parse_resume continues when AI enhancement fails."""
    from app.services.parser_orchestrator import ParserOrchestrator

    mock_ws_manager = MagicMock()
    mock_ws_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_ws_manager)

    sample_text = "John Doe\nSoftware Engineer"
    sample_nlp_data = {
        "personal_info": {"full_name": "John Doe", "email": "", "phone": ""},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {"personal_info": 70, "overall": 70}
    }

    with patch('app.services.parser_orchestrator.extract_text') as mock_extract:
        mock_extract.return_value = sample_text

        with patch('app.services.parser_orchestrator.extract_entities') as mock_nlp:
            mock_nlp.return_value = sample_nlp_data

            with patch('app.services.parser_orchestrator.enhance_with_ai') as mock_ai:
                # AI fails - returns original data (graceful fallback)
                mock_ai.return_value = sample_nlp_data

                with patch('app.services.parser_orchestrator.save_parsed_resume'):
                    result = await orchestrator.parse_resume(
                        "resume-123",
                        "resume.pdf",
                        b"fake pdf content",
                        enable_ai=True
                    )

                    # Should still complete with NLP data
                    assert result is not None
                    assert result["personal_info"]["full_name"] == "John Doe"


@pytest.mark.asyncio
async def test_enhance_with_ai_progress_sends_updates():
    """Test that _enhance_with_ai_progress sends progress updates."""
    from app.services.parser_orchestrator import ParserOrchestrator
    from app.models.progress import ProgressStage

    mock_ws_manager = MagicMock()
    mock_ws_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_ws_manager)

    raw_text = "Resume text here..."
    parsed_data = {"personal_info": {"full_name": "John"}}

    with patch('app.services.parser_orchestrator.enhance_with_ai') as mock_ai:
        mock_ai.return_value = {"personal_info": {"full_name": "John Doe"}}

        result = await orchestrator._enhance_with_ai_progress(
            "resume-123",
            raw_text,
            parsed_data
        )

        # Should have sent progress updates
        assert mock_ws_manager.broadcast_to_resume.call_count >= 2

        # Check that progress stages include AI_ENHANCEMENT
        calls = mock_ws_manager.broadcast_to_resume.call_args_list
        stages = [call[0][0].get("stage") for call in calls]

        assert "ai_enhancement" in stages

        # Result should be enhanced
        assert result["personal_info"]["full_name"] == "John Doe"


@pytest.mark.asyncio
async def test_enhance_with_ai_progress_returns_original_on_error():
    """Test that _enhance_with_ai_progress returns original data on error."""
    from app.services.parser_orchestrator import ParserOrchestrator

    mock_ws_manager = MagicMock()
    mock_ws_manager.broadcast_to_resume = AsyncMock()

    orchestrator = ParserOrchestrator(mock_ws_manager)

    original_data = {"personal_info": {"full_name": "John"}}

    with patch('app.services.parser_orchestrator.enhance_with_ai') as mock_ai:
        mock_ai.side_effect = Exception("AI service unavailable")

        result = await orchestrator._enhance_with_ai_progress(
            "resume-123",
            "text",
            original_data
        )

        # Should return original data
        assert result == original_data
