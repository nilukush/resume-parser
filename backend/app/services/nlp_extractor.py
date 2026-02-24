"""
NLP Entity Extraction Service for ResuMate.

This service uses spaCy to extract structured resume data from raw text.
Extracts: personal_info, work_experience, education, skills
Calculates confidence scores for each section.

OPTIMIZED FOR SERVERLESS:
- Downloads spaCy models on first use
- Caches models in /tmp for Lambda warm starts
- Uses en_core_web_sm for smaller footprint
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

import spacy
from spacy.cli import download

# Load spaCy model lazily
nlp: Optional[spacy.Language] = None

# Cache spaCy models in /tmp for Lambda (warm starts)
SPACY_MODEL_NAME = "en_core_web_sm"
TMP_DIR = Path("/tmp/spacy")


class NLPEntityExtractionError(Exception):
    """Raised when NLP entity extraction fails."""

    pass


def load_spacy_model() -> spacy.Language:
    """
    Load spaCy model with runtime download and caching.

    For serverless environments (Lambda):
    - Downloads model on first invocation
    - Caches in /tmp for warm starts
    - Falls back to basic parsing if download fails

    Returns:
        Loaded spaCy language model

    Raises:
        NLPEntityExtractionError: If model cannot be loaded
    """
    global nlp
    if nlp is None:
        try:
            # Try loading from standard location first (for local dev)
            nlp = spacy.load(SPACY_MODEL_NAME)
        except OSError:
            try:
                # Model not found, download and cache in /tmp (for Lambda)
                # Create /tmp/spacy directory if it doesn't exist
                TMP_DIR.mkdir(parents=True, exist_ok=True)

                # Download model directly to /tmp
                import subprocess
                subprocess.run(
                    ["python", "-m", "spacy", "download", SPACY_MODEL_NAME, "--target", "/tmp"],
                    capture_output=True,
                    check=True,
                    timeout=60
                )

                # Load from /tmp cache
                model_path = Path(f"/tmp/{SPACY_MODEL_NAME}/{SPACY_MODEL_NAME}")
                if model_path.exists():
                    nlp = spacy.load(model_path)
                else:
                    # Last resort: try loading from default spacy location
                    nlp = spacy.load(SPACY_MODEL_NAME)

            except Exception as e:
                # If all else fails, raise error with helpful message
                raise NLPEntityExtractionError(
                    f"Failed to load spaCy model '{SPACY_MODEL_NAME}'. "
                    f"For local development, run: python -m spacy download {SPACY_MODEL_NAME}. "
                    f"Error: {str(e)}"
                )
    return nlp


def extract_entities(text: str) -> Dict[str, Any]:
    """
    Extract entities from resume text using spaCy NLP.

    Args:
        text: Resume text content

    Returns:
        Dictionary with structured resume data:
        - personal_info: dict with name, email, phone, location, urls
        - work_experience: list of work experience entries
        - education: list of education entries
        - skills: dict with technical, soft_skills, languages, certifications
        - confidence_scores: dict with confidence percentage for each section

    Raises:
        NLPEntityExtractionError: If extraction fails
    """
    if not isinstance(text, str):
        text = str(text) if text else ""

    # Load spaCy model
    try:
        nlp_model = load_spacy_model()
    except NLPEntityExtractionError:
        # If model loading fails, return empty structure
        return _get_empty_structure()

    try:
        doc = nlp_model(text)
    except Exception as e:
        raise NLPEntityExtractionError(f"Failed to process text with spaCy: {str(e)}")

    # Extract all components
    personal_info = _extract_personal_info(doc, text)
    work_experience = _extract_work_experience(doc, text)
    education = _extract_education(doc, text)
    skills = _extract_skills(doc, text)

    # Calculate confidence scores
    confidence_scores = _calculate_confidence(
        personal_info, work_experience, education, skills, text
    )

    return {
        "personal_info": personal_info,
        "work_experience": work_experience,
        "education": education,
        "skills": skills,
        "confidence_scores": confidence_scores
    }


def _get_empty_structure() -> Dict[str, Any]:
    """Return empty structure when model is not available."""
    return {
        "personal_info": {
            "full_name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin_url": "",
            "github_url": "",
            "portfolio_url": "",
            "summary": ""
        },
        "work_experience": [],
        "education": [],
        "skills": {
            "technical": [],
            "soft_skills": [],
            "languages": [],
            "certifications": [],
            "confidence": 0.0
        },
        "confidence_scores": {
            "personal_info": 0.0,
            "work_experience": 0.0,
            "education": 0.0,
            "skills": 0.0
        }
    }


def _extract_personal_info(doc: spacy.tokens.Doc, text: str) -> Dict[str, Any]:
    """
    Extract personal information from resume text.

    Args:
        doc: spaCy Doc object
        text: Original text content

    Returns:
        Dictionary with personal information
    """
    info = {
        "full_name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin_url": "",
        "github_url": "",
        "portfolio_url": "",
        "summary": ""
    }

    # Extract email using regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        info["email"] = emails[0]

    # Extract phone using regex - handles multiple formats
    phone_patterns = [
        r'\+\d{1,3}[-.\s]\d{3}[-.\s]\d{4}',  # +1-555-0123, +1 555 0123
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # International with 10 digits
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',  # (555) 123-4567
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # 555-123-4567
    ]

    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            # Clean up the phone number
            phone = re.sub(r'\s+', ' ', phones[0].strip())
            info["phone"] = phone
            break

    # Extract URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    for url in urls:
        # Remove trailing punctuation
        url = re.sub(r'[.,;:!?]+$', '', url)
        if 'linkedin.com' in url.lower():
            info["linkedin_url"] = url
        elif 'github.com' in url.lower():
            info["github_url"] = url
        else:
            # Last URL that's not LinkedIn/GitHub is considered portfolio
            if not info.get("portfolio_url"):
                info["portfolio_url"] = url

    # Extract name (first PERSON entity)
    for ent in doc.ents:
        if ent.label_ == "PERSON" and not info["full_name"]:
            # Check if it's a proper name (2+ words, or single word with capital letter)
            candidate = ent.text.strip()
            if len(candidate.split()) >= 2 or (len(candidate) > 2 and candidate[0].isupper()):
                info["full_name"] = candidate
                break

    # Extract location (first GPE or LOC entity)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"] and not info["location"]:
            info["location"] = ent.text
            break

    return info


def _extract_work_experience(doc: spacy.tokens.Doc, text: str) -> List[Dict[str, Any]]:
    """
    Extract work experience from resume text.

    Args:
        doc: spaCy Doc object
        text: Original text content

    Returns:
        List of work experience dictionaries
    """
    experiences = []

    # Job title keywords
    job_keywords = [
        "engineer", "developer", "manager", "director", "architect",
        "analyst", "consultant", "specialist", "lead", "senior", "junior",
        "designer", "administrator", "coordinator", "assistant", "chief",
        "officer", "president", "founder", "owner", "partner", "head"
    ]

    # Look for patterns like "Software Engineer at Company"
    for sent in doc.sents:
        sent_text = sent.text.strip()
        sent_lower = sent_text.lower()

        # Check if sentence contains job-related keywords
        if " at " in sent_lower or " @ " in sent_lower or " in " in sent_lower:
            if any(keyword in sent_lower for keyword in job_keywords):
                experiences.append({
                    "title": _extract_job_title(sent_text),
                    "company": _extract_company(sent_text),
                    "location": "",
                    "start_date": "",
                    "end_date": "",
                    "description": sent_text,
                    "confidence": 70.0
                })

    # Limit to reasonable number
    return experiences[:10]


def _extract_job_title(text: str) -> str:
    """Extract job title from a sentence."""
    job_keywords = [
        "engineer", "developer", "manager", "director", "architect",
        "analyst", "consultant", "specialist", "lead", "senior", "junior",
        "designer", "administrator", "coordinator", "assistant",
        "software", "data", "product", "project", "technical"
    ]

    words = text.split()
    for i, word in enumerate(words):
        if word.lower() in job_keywords:
            # Get context around the keyword
            start = max(0, i - 2)
            end = min(len(words), i + 2)
            title = " ".join(words[start:end])
            return title

    return "Unknown"


def _extract_company(text: str) -> str:
    """Extract company name from a sentence."""
    # Look for patterns like "at CompanyName" or "@ CompanyName"
    patterns = [r'(?:at|@)\s+([A-Z][A-Za-z\s&]+?)(?:\s+(?:from|since|in)|[,.]|$)']

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) > 2:
                return company

    return "Unknown"


def _extract_education(doc: spacy.tokens.Doc, text: str) -> List[Dict[str, Any]]:
    """
    Extract education from resume text.

    Args:
        doc: spaCy Doc object
        text: Original text content

    Returns:
        List of education dictionaries
    """
    education = []

    # Degree keywords and patterns
    degree_keywords = [
        "bachelor", "master", "phd", "doctor", "mba", "degree",
        "b.s.", "m.s.", "b.a.", "m.a.", "diploma", "certificate",
        "associate", "graduate", "undergraduate"
    ]

    # Institution patterns (ORG entities)
    for sent in doc.sents:
        sent_text = sent.text.strip()
        sent_lower = sent_text.lower()

        # Check if sentence contains degree-related keywords
        if any(keyword in sent_lower for keyword in degree_keywords):
            # Try to extract institution name (ORG entity)
            institution = "Unknown"
            for ent in sent.ents:
                if ent.label_ == "ORG":
                    institution = ent.text
                    break

            education.append({
                "institution": institution,
                "degree": sent_text,
                "field_of_study": "",
                "location": "",
                "start_date": "",
                "end_date": "",
                "gpa": "",
                "confidence": 70.0
            })

    # Limit to reasonable number
    return education[:10]


def _extract_skills(doc: spacy.tokens.Doc, text: str) -> Dict[str, List[str]]:
    """
    Extract skills from resume text.

    Args:
        doc: spaCy Doc object
        text: Original text content

    Returns:
        Dictionary with categorized skills
    """
    # Common technical skills
    tech_skills = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node", "nodejs", "sql", "nosql", "mysql", "postgresql", "mongodb",
        "aws", "azure", "gcp", "docker", "kubernetes", "git", "github",
        "linux", "html", "css", "json", "xml", "api", "rest", "graphql",
        "django", "flask", "fastapi", "spring", "express", "next.js",
        "tensorflow", "pytorch", "nlp", "machine learning", "ai", "data science",
        "pandas", "numpy", "spark", "hadoop", "scala", "go", "rust", "c++",
        "ci/cd", "devops", "agile", "scrum", "jira", "confluence"
    ]

    # Common soft skills
    soft_skills = [
        "leadership", "communication", "teamwork", "problem solving",
        "project management", "agile", "scrum", "collaboration",
        "analytical", "critical thinking", "creativity", "adaptability",
        "time management", "organization", "presentation", "mentoring"
    ]

    # Common certifications
    certifications = [
        "aws certified", "azure certified", "gcp certified",
        "pmp", "scrum master", "cfa", "cpa", "six sigma"
    ]

    text_lower = text.lower()

    # Find matching skills (case-insensitive)
    found_tech = [
        skill for skill in tech_skills
        if skill.lower() in text_lower or " " + skill.lower() + " " in " " + text_lower + " "
    ]

    found_soft = [
        skill for skill in soft_skills
        if skill.lower() in text_lower or " " + skill.lower() + " " in " " + text_lower + " "
    ]

    found_certs = [
        cert for cert in certifications
        if cert.lower() in text_lower
    ]

    # Extract languages mentioned
    languages = []
    for ent in doc.ents:
        if ent.label_ == "LANGUAGE":
            languages.append(ent.text)

    # Calculate confidence based on number of skills found
    total_skills = len(found_tech) + len(found_soft)
    confidence = min(100.0, 50.0 + (total_skills * 5.0))

    return {
        "technical": found_tech,
        "soft_skills": found_soft,
        "languages": languages,
        "certifications": found_certs,
        "confidence": confidence
    }


def _calculate_confidence(
    personal_info: Dict[str, Any],
    work_experience: List[Dict[str, Any]],
    education: List[Dict[str, Any]],
    skills: Dict[str, List[str]],
    text: str
) -> Dict[str, float]:
    """
    Calculate confidence scores for each section.

    Args:
        personal_info: Extracted personal information
        work_experience: Extracted work experience
        education: Extracted education
        skills: Extracted skills
        text: Original text content

    Returns:
        Dictionary with confidence scores (0-100) for each section
    """
    scores = {
        "personal_info": 0.0,
        "work_experience": 0.0,
        "education": 0.0,
        "skills": 0.0
    }

    # Personal info confidence based on filled critical fields
    personal_fields = ["email", "phone", "full_name"]
    filled_fields = sum(1 for field in personal_fields if personal_info.get(field))
    scores["personal_info"] = round((filled_fields / len(personal_fields)) * 100, 2)

    # Bonus for additional info
    if personal_info.get("location"):
        scores["personal_info"] = min(100.0, scores["personal_info"] + 10)
    if personal_info.get("linkedin_url") or personal_info.get("github_url"):
        scores["personal_info"] = min(100.0, scores["personal_info"] + 5)

    # Work experience confidence
    if work_experience:
        avg_confidence = sum(
            exp.get("confidence", 70.0) for exp in work_experience
        ) / len(work_experience)
        # Reduce confidence if titles/companies are "Unknown"
        unknown_count = sum(
            1 for exp in work_experience
            if exp.get("title") == "Unknown" or exp.get("company") == "Unknown"
        )
        unknown_penalty = (unknown_count / len(work_experience)) * 20
        scores["work_experience"] = max(0.0, min(100.0, avg_confidence - unknown_penalty))
    else:
        # Check if there's any work-related content
        work_keywords = ["experience", "employment", "work", "job", "career"]
        if any(keyword in text.lower() for keyword in work_keywords):
            scores["work_experience"] = 30.0  # Low confidence if section exists but nothing extracted

    # Education confidence
    if education:
        avg_confidence = sum(
            edu.get("confidence", 70.0) for edu in education
        ) / len(education)
        unknown_count = sum(
            1 for edu in education
            if edu.get("institution") == "Unknown"
        )
        unknown_penalty = (unknown_count / len(education)) * 20
        scores["education"] = max(0.0, min(100.0, avg_confidence - unknown_penalty))
    else:
        # Check if there's any education-related content
        edu_keywords = ["education", "university", "college", "school", "degree"]
        if any(keyword in text.lower() for keyword in edu_keywords):
            scores["education"] = 30.0

    # Skills confidence from skills dict
    scores["skills"] = skills.get("confidence", 0.0)

    # Round all scores
    for key in scores:
        scores[key] = round(scores[key], 2)

    return scores
