from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from pydantic import BaseModel, Field, field_validator

class ProgressStage(str, Enum):
    """Parsing pipeline stages"""
    TEXT_EXTRACTION = "text_extraction"
    NLP_PARSING = "nlp_parsing"
    AI_ENHANCEMENT = "ai_enhancement"
    COMPLETE = "complete"
    ERROR = "error"

class ProgressUpdate:
    """Structured progress update message"""

    def __init__(
        self,
        resume_id: str,
        stage: ProgressStage,
        progress: int,  # 0-100
        status: str,
        estimated_seconds_remaining: Optional[int] = None,
        data: Optional[dict] = None
    ):
        self.resume_id = resume_id
        self.stage = stage
        self.progress = max(0, min(100, progress))  # Clamp to 0-100
        self.status = status
        self.estimated_seconds_remaining = estimated_seconds_remaining
        self.data = data or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": "progress_update",
            "resume_id": self.resume_id,
            "stage": self.stage.value,
            "progress": self.progress,
            "status": self.status,
            "estimated_seconds_remaining": self.estimated_seconds_remaining,
            "data": self.data,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

class CompleteProgress(ProgressUpdate):
    """Progress update for parsing completion"""

    def __init__(self, resume_id: str, parsed_data: dict):
        super().__init__(
            resume_id=resume_id,
            stage=ProgressStage.COMPLETE,
            progress=100,
            status="Parsing complete!",
            data=parsed_data
        )

class ErrorProgress(ProgressUpdate):
    """Progress update for parsing errors"""

    def __init__(self, resume_id: str, error_message: str, error_code: str = "PARSE_ERROR"):
        super().__init__(
            resume_id=resume_id,
            stage=ProgressStage.ERROR,
            progress=0,
            status=f"Error: {error_message}",
            data={"error_code": error_code, "error_message": error_message}
        )


class ParsedData(BaseModel):
    """
    Pydantic model for parsed resume data.

    This is the canonical structure for resume data extracted by NLP/AI.
    Used throughout the application for type safety and validation.
    """

    # Personal Information
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

    # Online Presence
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    # Summary
    summary: Optional[str] = None

    # Skills (list of skill names)
    skills: List[str] = Field(default_factory=list)

    # Work Experience (list of experience objects)
    work_experience: List[Dict[str, Any]] = Field(default_factory=list)

    # Education (list of education objects)
    education: List[Dict[str, Any]] = Field(default_factory=list)

    # Certifications
    certifications: List[str] = Field(default_factory=list)

    # Languages
    languages: List[Dict[str, Any]] = Field(default_factory=list)

    # Projects
    projects: List[Dict[str, Any]] = Field(default_factory=list)

    # Additional Information
    additional_info: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    extraction_confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format"""
        if v is None:
            return None
        # Remove common formatting
        cleaned = v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        if cleaned and len(cleaned) >= 10:
            return v
        return None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format"""
        if v is None:
            return None
        if '@' in v and '.' in v.split('@')[-1]:
            return v.lower()
        return None
