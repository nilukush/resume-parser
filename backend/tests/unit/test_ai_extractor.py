"""
Unit tests for AI Extractor Service.

These tests verify GPT-4 based AI enhancement for resume parsing.
Following TDD discipline: tests written first, then implementation.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture
def mock_openai_api_key():
    """Set a mock OpenAI API key for testing."""
    original_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    yield
    if original_key is None:
        os.environ.pop("OPENAI_API_KEY", None)
    else:
        os.environ["OPENAI_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_enhance_with_ai_returns_structured_data(mock_openai_api_key):
    """Test that enhance_with_ai returns structured resume data."""
    from app.services.ai_extractor import enhance_with_ai

    raw_text = "John Doe\nSoftware Engineer\nEmail: john@example.com"

    # Mock OpenAI client response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''{
        "personal_info": {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "",
            "location": ""
        },
        "work_experience": [],
        "education": [],
        "skills": {"technical": [], "soft_skills": []},
        "confidence_scores": {"overall": 95}
    }'''

    with patch('app.services.ai_extractor._get_openai_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        result = await enhance_with_ai(raw_text, {"personal_info": {"full_name": "John"}})

        assert "personal_info" in result
        assert "confidence_scores" in result
        assert result["personal_info"]["full_name"] == "John Doe"


@pytest.mark.asyncio
async def test_enhance_with_ai_fills_missing_data(mock_openai_api_key):
    """Test that AI fills in missing data from raw text."""
    from app.services.ai_extractor import enhance_with_ai

    raw_text = "Jane Smith - Senior Data Scientist at Google - PhD from Stanford"

    # Mock OpenAI response with filled data
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''{
        "personal_info": {
            "full_name": "Jane Smith",
            "email": "",
            "phone": "",
            "location": "San Francisco, CA"
        },
        "work_experience": [
            {
                "company": "Google",
                "title": "Senior Data Scientist",
                "location": "San Francisco, CA",
                "start_date": "",
                "end_date": "",
                "description": "Senior role at Google"
            }
        ],
        "education": [
            {
                "institution": "Stanford University",
                "degree": "PhD",
                "field_of_study": "",
                "location": "",
                "start_date": "",
                "end_date": "",
                "gpa": ""
            }
        ],
        "skills": {"technical": ["Python", "Machine Learning"], "soft_skills": []},
        "confidence_scores": {"overall": 92}
    }'''

    with patch('app.services.ai_extractor._get_openai_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        initial_data = {"personal_info": {}, "work_experience": [], "education": [], "skills": {}}
        result = await enhance_with_ai(raw_text, initial_data)

        assert result["personal_info"]["full_name"] == "Jane Smith"
        assert len(result["work_experience"]) > 0
        assert result["work_experience"][0]["company"] == "Google"


@pytest.mark.asyncio
async def test_enhance_with_ai_validates_existing_data(mock_openai_api_key):
    """Test that AI validates and corrects existing parsed data."""
    from app.services.ai_extractor import enhance_with_ai

    raw_text = "Resume content here..."

    # Mock response that corrects the email
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''{
        "personal_info": {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "",
            "location": ""
        },
        "work_experience": [],
        "education": [],
        "skills": {"technical": [], "soft_skills": []},
        "confidence_scores": {"overall": 98}
    }'''

    with patch('app.services.ai_extractor._get_openai_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        initial_data = {
            "personal_info": {"full_name": "John", "email": "wrong@email"},  # Wrong data
            "work_experience": [],
            "education": [],
            "skills": {}
        }
        result = await enhance_with_ai(raw_text, initial_data)

        # AI should have corrected the data (merge prefers enhanced values)
        assert result["personal_info"]["full_name"] == "John Doe"
        assert result["personal_info"]["email"] == "john.doe@example.com"


@pytest.mark.asyncio
async def test_enhance_with_ai_handles_empty_api_key():
    """Test that enhance_with_ai returns original data when API key is missing."""
    from app.services.ai_extractor import enhance_with_ai

    raw_text = "Some resume text"
    initial_data = {"personal_info": {}, "work_experience": [], "education": [], "skills": {}}

    # Ensure no API key
    original_key = os.environ.get("OPENAI_API_KEY")
    os.environ.pop("OPENAI_API_KEY", None)

    try:
        result = await enhance_with_ai(raw_text, initial_data)

        # Should return original data unchanged
        assert result == initial_data
    finally:
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_enhance_with_ai_handles_openai_error(mock_openai_api_key):
    """Test that enhance_with_ai handles OpenAI API errors gracefully."""
    from app.services.ai_extractor import enhance_with_ai, AIEnhancementError

    raw_text = "Resume text"
    initial_data = {"personal_info": {}, "work_experience": [], "education": [], "skills": {}}

    # Mock OpenAI to raise an error
    with patch('app.services.ai_extractor._get_openai_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        # Should return original data on error (error handling)
        result = await enhance_with_ai(raw_text, initial_data)
        assert result == initial_data


@pytest.mark.asyncio
async def test_enhance_with_ai_calculates_confidence_scores(mock_openai_api_key):
    """Test that AI calculates per-section confidence scores."""
    from app.services.ai_extractor import enhance_with_ai

    raw_text = "Complete resume..."

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''{
        "personal_info": {"full_name": "John", "email": "john@example.com", "phone": "", "location": ""},
        "work_experience": [],
        "education": [],
        "skills": {"technical": [], "soft_skills": []},
        "confidence_scores": {
            "personal_info": 95,
            "work_experience": 70,
            "education": 85,
            "skills": 90,
            "overall": 85
        }
    }'''

    with patch('app.services.ai_extractor._get_openai_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        result = await enhance_with_ai(raw_text, {})

        assert "confidence_scores" in result
        assert result["confidence_scores"]["personal_info"] == 95
        assert result["confidence_scores"]["overall"] == 85


@pytest.mark.asyncio
async def test_enhance_with_ai_uses_gpt4_model(mock_openai_api_key):
    """Test that enhance_with_ai uses GPT-4 model by default."""
    from app.services.ai_extractor import enhance_with_ai

    raw_text = "Resume text"
    initial_data = {"personal_info": {}, "work_experience": [], "education": [], "skills": {}}

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"personal_info": {}, "work_experience": [], "education": [], "skills": {}, "confidence_scores": {"overall": 80}}'

    with patch('app.services.ai_extractor._get_openai_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        await enhance_with_ai(raw_text, initial_data)

        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        # Check model in kwargs
        assert call_args.kwargs["model"] == "gpt-4o-mini"


def test_ai_enhancement_error_exists():
    """Test that AIEnhancementError exception exists."""
    from app.services.ai_extractor import AIEnhancementError
    assert issubclass(AIEnhancementError, Exception)


@pytest.mark.asyncio
async def test_extract_skills_with_ai(mock_openai_api_key):
    """Test AI-based skill extraction and categorization."""
    from app.services.ai_extractor import extract_skills_with_ai

    raw_text = "Skills: Python, JavaScript, React, Node.js, Docker, Kubernetes, AWS, Leadership, Communication"

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''{
        "technical": ["Python", "JavaScript", "React", "Node.js", "Docker", "Kubernetes", "AWS"],
        "soft_skills": ["Leadership", "Communication"],
        "languages": [],
        "certifications": []
    }'''

    with patch('app.services.ai_extractor._get_openai_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        result = await extract_skills_with_ai(raw_text)

        assert "Python" in result["technical"]
        assert "Leadership" in result["soft_skills"]


@pytest.mark.asyncio
async def test_get_openai_client_returns_none_without_api_key():
    """Test that _get_openai_client returns None when no API key is set."""
    from app.services.ai_extractor import _get_openai_client
    from app.core.config import settings

    # Ensure no API key in both env and settings
    original_key = os.environ.get("OPENAI_API_KEY")
    os.environ.pop("OPENAI_API_KEY", None)

    # Mock settings to return empty API key
    with patch('app.services.ai_extractor.settings') as mock_settings:
        mock_settings.OPENAI_API_KEY = ""

        client = _get_openai_client()
        assert client is None

    # Restore original key
    if original_key:
        os.environ["OPENAI_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_merge_data_merges_dictionaries():
    """Test _merge_data function correctly merges dictionaries."""
    from app.services.ai_extractor import _merge_data

    initial = {
        "personal_info": {"full_name": "John", "email": "john@example.com"},
        "work_experience": [],
        "skills": {"technical": ["Python"]}
    }

    enhanced = {
        "personal_info": {"full_name": "John Doe", "phone": "+1-555-0123"},
        "work_experience": [{"company": "Tech Corp"}],
        "skills": {"technical": ["Python", "JavaScript"], "soft_skills": ["Leadership"]}
    }

    result = _merge_data(initial, enhanced)

    # Enhanced values should be preferred
    assert result["personal_info"]["full_name"] == "John Doe"
    assert result["personal_info"]["email"] == "john@example.com"  # Kept from initial
    assert result["personal_info"]["phone"] == "+1-555-0123"
    assert len(result["work_experience"]) == 1
    assert result["work_experience"][0]["company"] == "Tech Corp"
    assert "JavaScript" in result["skills"]["technical"]
    assert "Leadership" in result["skills"]["soft_skills"]
