"""
AI Enhancement Service for ResuMate.

This service uses OpenAI GPT-4 to enhance resume parsing with:
1. Better entity extraction and validation
2. Filling missing data gaps
3. Improving confidence scores
4. Categorizing skills intelligently
"""

import json
import os
from typing import Dict, Any, Optional

import openai
from app.core.config import settings


class AIEnhancementError(Exception):
    """Raised when AI enhancement fails."""

    pass


# System prompt for resume parsing
_RESUME_PARSING_PROMPT = """You are an expert resume parser. Your task is to extract structured information from resume text.

Extract the following fields:
- personal_info: full_name, email, phone, location, linkedin_url, github_url, portfolio_url, summary
- work_experience: array of objects with company, title, location, start_date, end_date, description
- education: array of objects with institution, degree, field_of_study, location, start_date, end_date, gpa
- skills: object with technical (array), soft_skills (array), languages (array), certifications (array)
- confidence_scores: object with personal_info (0-100), work_experience (0-100), education (0-100), skills (0-100), overall (0-100)

Return ONLY valid JSON. If a field cannot be found, use empty string or empty array.
Be thorough and extract ALL information present in the resume."""


_SKILL_EXTRACTION_PROMPT = """You are an expert at identifying and categorizing skills from resumes.

Extract skills from the text and categorize them into:
- technical: Programming languages, frameworks, tools, technologies
- soft_skills: Interpersonal and communication skills
- languages: Human languages spoken
- certifications: Professional certifications

Return ONLY valid JSON with these four arrays."""


def _get_openai_client() -> Optional[openai.OpenAI]:
    """
    Get OpenAI client instance.

    Returns None if API key is not configured.

    Returns:
        OpenAI client instance or None
    """
    api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "":
        return None
    return openai.OpenAI(api_key=api_key)


async def _call_openai(prompt: str, text: str, model: str = "gpt-4o-mini") -> str:
    """
    Call OpenAI API with given prompt and text.

    Args:
        prompt: System prompt for the model
        text: User text to process
        model: Model to use (default: gpt-4o-mini for cost efficiency)

    Returns:
        Model response as string

    Raises:
        AIEnhancementError: If API call fails
    """
    client = _get_openai_client()
    if client is None:
        raise AIEnhancementError("OpenAI API key not configured")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text[:15000]}  # Limit text length
            ],
            temperature=0.1,  # Low temperature for consistent results
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        raise AIEnhancementError(f"OpenAI API call failed: {str(e)}") from e


async def enhance_with_ai(raw_text: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance parsed resume data using GPT-4 AI.

    This function takes initial NLP-extracted data and enhances it by:
    1. Validating and correcting existing data
    2. Filling in missing information
    3. Improving confidence scores
    4. Better structuring of complex data

    Args:
        raw_text: Original resume text content
        initial_data: Initially parsed data from NLP extractor

    Returns:
        Enhanced resume data dictionary

    Raises:
        AIEnhancementError: If AI enhancement fails
    """
    # Check if OpenAI is configured
    if not settings.OPENAI_API_KEY and not os.environ.get("OPENAI_API_KEY"):
        # Return original data if AI is not configured
        return initial_data

    try:
        # Call OpenAI to enhance the data
        response_text = await _call_openai(_RESUME_PARSING_PROMPT, raw_text)

        # Parse JSON response
        try:
            enhanced_data = json.loads(response_text)
        except json.JSONDecodeError:
            # If response is not valid JSON, try to extract JSON
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                enhanced_data = json.loads(response_text[start:end])
            else:
                raise AIEnhancementError("Invalid JSON response from OpenAI")

        # Merge with initial data, preferring AI-enhanced data
        result = _merge_data(initial_data, enhanced_data)

        return result

    except AIEnhancementError:
        # If AI fails, return original data
        return initial_data


def _merge_data(initial: Dict[str, Any], enhanced: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge initial and enhanced data, preferring enhanced values.

    Args:
        initial: Initial parsed data
        enhanced: AI-enhanced data

    Returns:
        Merged data dictionary
    """
    result = initial.copy()

    for key, value in enhanced.items():
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            # Recursively merge dictionaries
            result[key] = {**result[key], **value}
        elif isinstance(value, list) and isinstance(result[key], list):
            # For lists, prefer the non-empty one
            result[key] = value if value else result[key]
        else:
            # Prefer enhanced value
            result[key] = value

    return result


async def extract_skills_with_ai(raw_text: str) -> Dict[str, list]:
    """
    Extract and categorize skills using AI.

    Args:
        raw_text: Resume text containing skills

    Returns:
        Dictionary with technical, soft_skills, languages, certifications arrays
    """
    try:
        response_text = await _call_openai(_SKILL_EXTRACTION_PROMPT, raw_text)

        try:
            skills_data = json.loads(response_text)
        except json.JSONDecodeError:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                skills_data = json.loads(response_text[start:end])
            else:
                raise AIEnhancementError("Invalid JSON response from OpenAI")

        # Ensure all required keys exist
        return {
            "technical": skills_data.get("technical", []),
            "soft_skills": skills_data.get("soft_skills", []),
            "languages": skills_data.get("languages", []),
            "certifications": skills_data.get("certifications", [])
        }

    except AIEnhancementError:
        # Return empty skills on failure
        return {
            "technical": [],
            "soft_skills": [],
            "languages": [],
            "certifications": []
        }


async def calculate_confidence_with_ai(
    parsed_data: Dict[str, Any],
    raw_text: str
) -> Dict[str, float]:
    """
    Calculate confidence scores for parsed data using AI.

    Args:
        parsed_data: Currently parsed resume data
        raw_text: Original resume text

    Returns:
        Confidence scores dictionary with per-section and overall scores
    """
    confidence_prompt = """Analyze this parsed resume data and assign confidence scores (0-100) for each section.

Consider:
- Data completeness (all required fields present)
- Data consistency (dates make sense, emails valid)
- Data quality (no obvious errors)

Return JSON with:
{
    "personal_info": score (0-100),
    "work_experience": score (0-100),
    "education": score (0-100),
    "skills": score (0-100),
    "overall": score (0-100, average of above)
}

Parsed data:
"""

    try:
        response_text = await _call_openai(
            confidence_prompt,
            json.dumps(parsed_data, indent=2),
            model="gpt-4o-mini"
        )

        try:
            scores = json.loads(response_text)
        except json.JSONDecodeError:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                scores = json.loads(response_text[start:end])
            else:
                raise AIEnhancementError("Invalid JSON response from OpenAI")

        return scores

    except AIEnhancementError:
        # Return default scores on failure
        return {
            "personal_info": 75.0,
            "work_experience": 70.0,
            "education": 70.0,
            "skills": 75.0,
            "overall": 72.5
        }
