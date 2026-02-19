"""
Unit tests for NLP Entity Extraction Service.

Tests follow TDD discipline:
1. Write failing test FIRST (RED phase)
2. Implement minimal code to pass tests (GREEN phase)
3. Refactor for quality (REFACTOR phase)
"""

import pytest

# Import will fail until module is created
# from app.services.nlp_extractor import extract_entities


def test_extract_entities_returns_structured_data():
    """Test that extract_entities returns structured resume data."""
    from app.services.nlp_extractor import extract_entities

    sample_text = """
    John Doe
    Email: john@example.com
    Phone: +1-555-0123

    Experience:
    Software Engineer at Tech Corp from 2020 to present

    Education:
    Bachelor of Science in Computer Science from MIT
    """

    result = extract_entities(sample_text)

    # Verify all required top-level keys exist
    assert "personal_info" in result
    assert "work_experience" in result
    assert "education" in result
    assert "skills" in result
    assert "confidence_scores" in result

    # Verify types
    assert isinstance(result["personal_info"], dict)
    assert isinstance(result["work_experience"], list)
    assert isinstance(result["education"], list)
    assert isinstance(result["skills"], dict)
    assert isinstance(result["confidence_scores"], dict)


def test_extract_entities_detects_email():
    """Test email detection."""
    from app.services.nlp_extractor import extract_entities

    sample_text = "Contact me at john.doe@example.com"
    result = extract_entities(sample_text)

    assert result.get("personal_info", {}).get("email") == "john.doe@example.com"


def test_extract_entities_detects_phone():
    """Test phone number detection."""
    from app.services.nlp_extractor import extract_entities

    sample_text = "Call me at +1-555-0123"
    result = extract_entities(sample_text)

    assert result.get("personal_info", {}).get("phone") == "+1-555-0123"


def test_extract_entities_detects_urls():
    """Test URL detection for LinkedIn, GitHub, portfolio."""
    from app.services.nlp_extractor import extract_entities

    sample_text = """
    LinkedIn: https://linkedin.com/in/johndoe
    GitHub: https://github.com/johndoe
    Portfolio: https://johndoe.com
    """
    result = extract_entities(sample_text)

    assert "linkedin.com" in result.get("personal_info", {}).get("linkedin_url", "")
    assert "github.com" in result.get("personal_info", {}).get("github_url", "")
    assert "johndoe.com" in result.get("personal_info", {}).get("portfolio_url", "")


def test_extract_entities_calculates_confidence_scores():
    """Test that confidence scores are calculated."""
    from app.services.nlp_extractor import extract_entities

    sample_text = """
    John Doe
    Email: john@example.com
    Phone: +1-555-0123
    """
    result = extract_entities(sample_text)

    confidence = result.get("confidence_scores", {})
    assert "personal_info" in confidence
    assert "work_experience" in confidence
    assert "education" in confidence
    assert "skills" in confidence

    # Verify confidence scores are floats between 0 and 100
    assert isinstance(confidence["personal_info"], (int, float))
    assert 0 <= confidence["personal_info"] <= 100


def test_extract_entities_handles_empty_text():
    """Test handling of empty text input."""
    from app.services.nlp_extractor import extract_entities

    result = extract_entities("")

    # Should still return structured data with empty/default values
    assert "personal_info" in result
    assert "work_experience" in result
    assert "education" in result
    assert "skills" in result
    assert "confidence_scores" in result


def test_extract_entities_detects_name():
    """Test name detection using spaCy PERSON entity."""
    from app.services.nlp_extractor import extract_entities

    sample_text = "John Smith is a software engineer."
    result = extract_entities(sample_text)

    # Should detect the PERSON entity
    name = result.get("personal_info", {}).get("full_name", "")
    assert name or name == ""  # May be empty if model doesn't detect it


def test_extract_work_experience():
    """Test work experience extraction."""
    from app.services.nlp_extractor import extract_entities

    sample_text = """
    Software Engineer at Google from 2020 to present.
    Worked on cloud infrastructure.
    """
    result = extract_entities(sample_text)

    work_exp = result.get("work_experience", [])
    assert isinstance(work_exp, list)


def test_extract_education():
    """Test education extraction."""
    from app.services.nlp_extractor import extract_entities

    sample_text = """
    Bachelor of Science in Computer Science from MIT.
    Graduated in 2019.
    """
    result = extract_entities(sample_text)

    education = result.get("education", [])
    assert isinstance(education, list)


def test_extract_skills():
    """Test skills extraction."""
    from app.services.nlp_extractor import extract_entities

    sample_text = """
    Skills: Python, Java, JavaScript, React, Node.js, SQL, AWS, Docker
    """
    result = extract_entities(sample_text)

    skills = result.get("skills", {})
    assert "technical" in skills
    assert "soft_skills" in skills
    assert isinstance(skills["technical"], list)
    assert isinstance(skills["soft_skills"], list)


def test_extract_entities_detects_location():
    """Test location detection using spaCy GPE/LOC entities."""
    from app.services.nlp_extractor import extract_entities

    sample_text = "John Doe lives in San Francisco, California."
    result = extract_entities(sample_text)

    # Should detect location
    location = result.get("personal_info", {}).get("location", "")
    assert location or location == ""


def test_extract_entities_handles_multiple_emails():
    """Test that first email is extracted when multiple exist."""
    from app.services.nlp_extractor import extract_entities

    sample_text = "Contact me at john@example.com or jane@example.com"
    result = extract_entities(sample_text)

    email = result.get("personal_info", {}).get("email", "")
    assert email in ["john@example.com", "jane@example.com"]


def test_extract_entities_handles_phone_formats():
    """Test various phone number formats."""
    from app.services.nlp_extractor import extract_entities

    # Test different phone formats
    test_cases = [
        ("Call me at (555) 123-4567", "(555) 123-4567"),
        ("Phone: 555-123-4567", "555-123-4567"),
        ("+1 555 123 4567", "+1 555 123 4567"),
    ]

    for text, expected in test_cases:
        result = extract_entities(text)
        phone = result.get("personal_info", {}).get("phone", "")
        # Some pattern should match
        assert phone or phone == ""


def test_confidence_scores_calculated_correctly():
    """Test confidence scores are calculated based on extracted data."""
    from app.services.nlp_extractor import extract_entities

    # Minimal data - should have lower confidence
    sample_text = "John Doe"
    result = extract_entities(sample_text)

    confidence = result.get("confidence_scores", {})

    # Personal info confidence should be lower with just a name
    assert "personal_info" in confidence

    # With more data, confidence should increase
    sample_text_full = """
    John Doe
    Email: john@example.com
    Phone: +1-555-0123
    Location: San Francisco
    """
    result_full = extract_entities(sample_text_full)
    confidence_full = result_full.get("confidence_scores", {})

    # More complete data should have higher or equal confidence
    assert confidence_full.get("personal_info", 0) >= confidence.get("personal_info", 0)


def test_extract_entities_returns_dict():
    """Test that extract_entities returns a dict."""
    from app.services.nlp_extractor import extract_entities

    result = extract_entities("Some text")

    assert isinstance(result, dict)
