"""
In-memory storage for parsed resume data.

This is a temporary solution for the MVP. In production, this should be
replaced with PostgreSQL database persistence.
"""

from typing import Dict, Optional
from datetime import datetime

# In-memory store: {resume_id: parsed_data}
_resume_store: Dict[str, dict] = {}


def save_parsed_resume(resume_id: str, parsed_data: dict) -> None:
    """
    Save parsed resume data to in-memory storage.

    Args:
        resume_id: Unique identifier for the resume
        parsed_data: Parsed resume data dictionary
    """
    _resume_store[resume_id] = {
        "data": parsed_data,
        "created_at": datetime.utcnow().isoformat()
    }


def get_parsed_resume(resume_id: str) -> Optional[dict]:
    """
    Retrieve parsed resume data from storage.

    Args:
        resume_id: Unique identifier for the resume

    Returns:
        Parsed resume data dictionary, or None if not found
    """
    if resume_id in _resume_store:
        return _resume_store[resume_id]["data"]
    return None


def update_parsed_resume(resume_id: str, updated_data: dict) -> bool:
    """
    Update parsed resume data in storage.

    Args:
        resume_id: Unique identifier for the resume
        updated_data: Updated resume data dictionary

    Returns:
        True if updated successfully, False if resume not found
    """
    if resume_id not in _resume_store:
        return False

    _resume_store[resume_id]["data"] = updated_data
    _resume_store[resume_id]["updated_at"] = datetime.utcnow().isoformat()
    return True


def delete_parsed_resume(resume_id: str) -> bool:
    """
    Delete parsed resume data from storage.

    Args:
        resume_id: Unique identifier for the resume

    Returns:
        True if deleted successfully, False if resume not found
    """
    if resume_id in _resume_store:
        del _resume_store[resume_id]
        return True
    return False


def get_all_resumes() -> Dict[str, dict]:
    """
    Get all stored resumes (for debugging/testing).

    Returns:
        Dictionary of all resume_id -> data pairs
    """
    return _resume_store.copy()


def clear_all_resumes() -> None:
    """
    Clear all stored resumes (for testing).
    """
    global _resume_store
    _resume_store = {}
