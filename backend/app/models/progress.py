from enum import Enum
from typing import Optional
from datetime import datetime
import json

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
