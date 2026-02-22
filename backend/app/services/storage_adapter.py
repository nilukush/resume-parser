"""
Unified Storage Adapter with feature flag support.

This adapter routes storage operations to either:
- DatabaseStorageService (when USE_DATABASE=true)
- In-memory storage (when USE_DATABASE=false)

This provides a clean migration path with feature flag safety.
"""
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.core.config import get_settings
from app.services.database_storage import DatabaseStorageService
from app.core.storage import (
    save_parsed_resume as save_in_memory,
    get_parsed_resume as get_in_memory,
    update_parsed_resume as update_in_memory,
)

logger = logging.getLogger(__name__)


class StorageAdapter:
    """
    Unified storage adapter that routes to database or in-memory storage.

    Usage:
        adapter = StorageAdapter(db_session)
        await adapter.save_parsed_data(resume_id, parsed_data)
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize storage adapter.

        Args:
            db_session: SQLAlchemy async session (used only if USE_DATABASE=true)
        """
        self.db_session = db_session
        # Use get_settings() instead of module-level settings for testability
        settings = get_settings()
        self.use_database = settings.USE_DATABASE

        if self.use_database:
            self.db_service = DatabaseStorageService(db_session)

    def _is_valid_uuid(self, resume_id: str) -> bool:
        """Check if resume_id is a valid UUID format."""
        try:
            UUID(resume_id)
            return True
        except (ValueError, AttributeError, TypeError):
            return False

    def _normalize_nlp_output_to_parsed_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize NLP extractor output to match ParsedData schema.

        The NLP extractor returns:
        - skills: Dict with categories (technical, soft_skills, etc.)
        - personal_info: Dict with all fields (possibly empty strings)
        - confidence_scores: Dict with section scores

        ParsedData expects:
        - skills: List[str] (flat list)
        - personal_info: Fields should be None if empty, not empty string
        - extraction_confidence: float (0-1)

        Args:
            raw_data: Raw data from NLP extractor

        Returns:
            Normalized dict compatible with ParsedData schema
        """
        normalized = {}

        # Normalize personal_info - convert empty strings to None
        personal_info = raw_data.get("personal_info", {})
        normalized["full_name"] = personal_info.get("full_name") or None
        normalized["email"] = personal_info.get("email") or None
        normalized["phone"] = personal_info.get("phone") or None
        normalized["location"] = personal_info.get("location") or None
        normalized["linkedin_url"] = personal_info.get("linkedin_url") or None
        normalized["github_url"] = personal_info.get("github_url") or None
        normalized["portfolio_url"] = personal_info.get("portfolio_url") or None
        normalized["summary"] = personal_info.get("summary") or None

        # Normalize skills from categorized dict to flat list
        skills_data = raw_data.get("skills", {})
        if isinstance(skills_data, dict):
            # Extract all skills from categories
            all_skills = []
            for category, skills in skills_data.items():
                if category == "confidence":
                    continue  # Skip the confidence score
                if isinstance(skills, list):
                    all_skills.extend(skills)
            normalized["skills"] = all_skills
        else:
            # Already a list or unexpected format
            normalized["skills"] = skills_data if isinstance(skills_data, list) else []

        # Normalize work_experience and education (ensure lists)
        normalized["work_experience"] = raw_data.get("work_experience", [])
        normalized["education"] = raw_data.get("education", [])

        # Extract certifications from skills if present
        if isinstance(skills_data, dict) and "certifications" in skills_data:
            normalized["certifications"] = skills_data["certifications"]
        else:
            normalized["certifications"] = []

        # Extract languages from skills if present
        if isinstance(skills_data, dict) and "languages" in skills_data:
            normalized["languages"] = [{"name": lang, "fluency": "unknown"} for lang in skills_data["languages"]]
        else:
            normalized["languages"] = []

        # Projects and additional_info (rarely extracted by NLP)
        normalized["projects"] = raw_data.get("projects", [])
        normalized["additional_info"] = raw_data.get("additional_info", {})

        # Normalize confidence scores (0-100 scale from NLP to 0-1 scale for ParsedData)
        confidence_scores = raw_data.get("confidence_scores", {})
        overall_confidence = confidence_scores.get("overall", 0.0) / 100.0  # Convert to 0-1 scale
        normalized["extraction_confidence"] = round(max(0.0, min(1.0, overall_confidence)), 2)

        return normalized

    async def save_parsed_data(
        self,
        resume_id: str,
        parsed_data: Dict[str, Any],
        ai_enhanced: bool = False
    ) -> None:
        """
        Save parsed resume data.

        Args:
            resume_id: Resume ID (string or UUID)
            parsed_data: Parsed resume data dictionary
            ai_enhanced: Whether data was AI-enhanced
        """
        # Use database only if enabled AND resume_id is a valid UUID
        if self.use_database and self._is_valid_uuid(resume_id):
            # Convert to ParsedData model and save to database
            from app.models.progress import ParsedData
            from app.models.resume import Resume

            # Normalize NLP output to match ParsedData schema
            normalized_data = self._normalize_nlp_output_to_parsed_data(parsed_data)

            # Convert dict to ParsedData with error handling
            resume_uuid = UUID(resume_id) if isinstance(resume_id, str) else resume_id

            try:
                parsed_data_model = ParsedData(**normalized_data)
            except ValidationError as e:
                # Log validation error with details
                logger.error(
                    f"Pydantic validation failed for resume {resume_id}: {e}",
                    extra={
                        "resume_id": str(resume_id),
                        "validation_errors": e.errors(),
                        "normalized_data": normalized_data
                    }
                )

                # Create minimal valid ParsedData as fallback
                parsed_data_model = ParsedData(
                    full_name=normalized_data.get("full_name"),
                    email=normalized_data.get("email"),
                    phone=normalized_data.get("phone"),
                    location=normalized_data.get("location"),
                    skills=normalized_data.get("skills", []),
                    work_experience=normalized_data.get("work_experience", []),
                    education=normalized_data.get("education", []),
                    certifications=normalized_data.get("certifications", []),
                    languages=normalized_data.get("languages", []),
                    projects=normalized_data.get("projects", []),
                    additional_info=normalized_data.get("additional_info", {}),
                    extraction_confidence=normalized_data.get("extraction_confidence", 0.0)
                )

            # Check if resume metadata exists (it should from upload endpoint)
            resume = await self.db_service.get_resume(resume_uuid)
            if not resume:
                # Legacy case: create metadata if it doesn't exist
                # This should NOT happen with the new upload flow
                await self.db_service.save_resume_metadata(
                    resume_id=resume_uuid,
                    original_filename=parsed_data.get("filename", "unknown"),
                    file_type=parsed_data.get("file_type", "unknown"),
                    file_size_bytes=parsed_data.get("file_size", 0),
                    file_hash=parsed_data.get("file_hash", ""),
                    storage_path=parsed_data.get("storage_path", ""),
                    processing_status="complete"
                )

            # Update processing status to complete
            await self.db_service.update_processing_status(
                resume_uuid,
                "complete",
                confidence_score=parsed_data_model.extraction_confidence
            )

            # Save parsed data
            try:
                await self.db_service.save_parsed_data(resume_uuid, parsed_data_model, ai_enhanced)
                logger.info(f"Successfully saved parsed data for resume {resume_id}")
            except Exception as e:
                logger.error(
                    f"Failed to save parsed data to database for resume {resume_id}: {e}",
                    exc_info=True
                )
                raise
        else:
            # Use in-memory storage
            save_in_memory(resume_id, parsed_data)

    def _parsed_data_to_nested_dict(self, parsed_data: 'ParsedData') -> Dict[str, Any]:
        """
        Convert ParsedData (flat Pydantic model) to nested dict format expected by frontend.

        Frontend expects:
        {
            "personal_info": { "full_name": "...", "email": "...", ... },
            "skills": { "technical": [...], "soft_skills": [...], ... },
            "confidence_scores": { "overall": 0.96, ... }
        }

        Args:
            parsed_data: ParsedData Pydantic model (flat structure)

        Returns:
            Nested dictionary matching frontend expectations
        """
        data_dict = parsed_data.model_dump(exclude_none=True)

        # Build personal_info object
        personal_info = {
            "full_name": data_dict.get("full_name"),
            "email": data_dict.get("email"),
            "phone": data_dict.get("phone"),
            "location": data_dict.get("location"),
            "linkedin_url": data_dict.get("linkedin_url"),
            "github_url": data_dict.get("github_url"),
            "portfolio_url": data_dict.get("portfolio_url"),
            "summary": data_dict.get("summary"),
        }

        # Build skills object (categorized format)
        # Note: NLP/AI may return categorized skills, but ParsedData stores as flat list
        # We convert back to categorized format for frontend compatibility
        skills_list = data_dict.get("skills", [])
        skills_obj = {
            "technical": skills_list,  # All skills go to technical by default
            "soft_skills": data_dict.get("soft_skills", []),
            "languages": data_dict.get("languages", []),
            "certifications": data_dict.get("certifications", []),
        }

        # Build confidence scores object (convert 0-1 to 0-100 scale)
        extraction_confidence = data_dict.get("extraction_confidence", 0.0)
        confidence_scores = {
            "overall": round(extraction_confidence * 100, 2),
            "personal_info": round(extraction_confidence * 100, 2),
            "work_experience": round(extraction_confidence * 100, 2),
            "education": round(extraction_confidence * 100, 2),
            "skills": round(extraction_confidence * 100, 2),
        }

        return {
            "personal_info": personal_info,
            "work_experience": data_dict.get("work_experience", []),
            "education": data_dict.get("education", []),
            "skills": skills_obj,
            "confidence_scores": confidence_scores,
        }

    async def get_parsed_data(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve parsed resume data.

        Args:
            resume_id: Resume ID

        Returns:
            Parsed data dictionary or None if not found
        """
        # Use database only if enabled AND resume_id is a valid UUID
        if self.use_database and self._is_valid_uuid(resume_id):
            resume_uuid = UUID(resume_id) if isinstance(resume_id, str) else resume_id
            parsed_data = await self.db_service.get_parsed_data(resume_uuid)

            if parsed_data:
                # Convert ParsedData (flat) to nested format expected by frontend
                return self._parsed_data_to_nested_dict(parsed_data)
            return None
        else:
            return get_in_memory(resume_id)

    async def update_parsed_data(
        self,
        resume_id: str,
        updated_data: Dict[str, Any]
    ) -> bool:
        """
        Update parsed resume data.

        Args:
            resume_id: Resume ID
            updated_data: Updated resume data dictionary

        Returns:
            True if updated successfully, False otherwise
        """
        # Use database only if enabled AND resume_id is a valid UUID
        if self.use_database and self._is_valid_uuid(resume_id):
            resume_uuid = UUID(resume_id) if isinstance(resume_id, str) else resume_id

            # Normalize NLP output to match ParsedData schema
            normalized_data = self._normalize_nlp_output_to_parsed_data(updated_data)

            # Convert dict to ParsedData with error handling
            from app.models.progress import ParsedData

            try:
                parsed_data_model = ParsedData(**normalized_data)
            except ValidationError as e:
                logger.error(
                    f"Pydantic validation failed for resume {resume_id} update: {e}",
                    extra={
                        "resume_id": str(resume_id),
                        "validation_errors": e.errors(),
                        "normalized_data": normalized_data
                    }
                )
                # Create minimal valid ParsedData as fallback
                parsed_data_model = ParsedData(
                    full_name=normalized_data.get("full_name"),
                    email=normalized_data.get("email"),
                    skills=normalized_data.get("skills", []),
                    work_experience=normalized_data.get("work_experience", []),
                    education=normalized_data.get("education", []),
                    extraction_confidence=normalized_data.get("extraction_confidence", 0.0)
                )

            result = await self.db_service.update_parsed_data(resume_uuid, parsed_data_model)
            return result is not None
        else:
            return update_in_memory(resume_id, updated_data)

    async def delete_parsed_data(self, resume_id: str) -> bool:
        """
        Delete parsed resume data.

        Args:
            resume_id: Resume ID

        Returns:
            True if deleted successfully, False otherwise
        """
        if self.use_database:
            # Database doesn't have a delete in ParsedResumeData yet
            # Would cascade delete from Resume table
            return True  # Placeholder
        else:
            from app.core.storage import delete_parsed_resume
            return delete_parsed_resume(resume_id)


# Convenience functions for backward compatibility
async def get_storage_adapter(db_session: AsyncSession) -> StorageAdapter:
    """
    Get storage adapter instance.

    Args:
        db_session: SQLAlchemy async session

    Returns:
        StorageAdapter instance configured with feature flags
    """
    return StorageAdapter(db_session)
