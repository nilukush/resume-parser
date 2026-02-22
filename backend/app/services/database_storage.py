"""
Database Storage Service for persistent resume storage.

This service provides CRUD operations for:
- Resume metadata
- Parsed resume data (stored as JSONB)
- Share tokens
- User corrections (for AI learning)

All operations are async and use SQLAlchemy 2.0 with asyncpg.

Architecture:
- ParsedData (Pydantic): Flat, validated model for API layer
- ParsedResumeData (SQLAlchemy): JSONB columns for database storage
- Conversion methods handle transformation between layers
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.resume import Resume, ParsedResumeData, ResumeShare, ResumeCorrection
from app.models.progress import ParsedData


class DatabaseStorageService:
    """
    Async database storage service for resume persistence.

    Replaces in-memory storage with PostgreSQL for production reliability.

    Usage:
        service = DatabaseStorageService(db_session)
        await service.save_resume_metadata(resume_data)
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize database storage service.

        Args:
            db_session: SQLAlchemy async session
        """
        self.db = db_session

    # ========== Helper Methods for ParsedData Conversion ==========

    def _parsed_data_to_jsonb(self, parsed_data: ParsedData) -> Dict[str, Any]:
        """
        Convert ParsedData (Pydantic) to JSONB-compatible structure.

        Args:
            parsed_data: ParsedData Pydantic model

        Returns:
            Dictionary matching ParsedResumeData JSONB schema
        """
        data_dict = parsed_data.model_dump(exclude_none=True)

        # Convert flat structure to nested JSONB structure
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

        # Remove None values
        personal_info = {k: v for k, v in personal_info.items() if v is not None}

        return {
            "personal_info": personal_info,
            "work_experience": data_dict.get("work_experience", []),
            "education": data_dict.get("education", []),
            "skills": data_dict.get("skills", {}),
            "confidence_scores": {
                "overall": data_dict.get("extraction_confidence", 0.0),
                "personal_info": data_dict.get("extraction_confidence", 0.0),
                "work_experience": data_dict.get("extraction_confidence", 0.0),
                "education": data_dict.get("extraction_confidence", 0.0),
                "skills": data_dict.get("extraction_confidence", 0.0),
            },
        }

    def _jsonb_to_parsed_data(self, jsonb_data: Dict[str, Any]) -> ParsedData:
        """
        Convert JSONB structure to ParsedData (Pydantic).

        Args:
            jsonb_data: Dictionary from database JSONB columns

        Returns:
            ParsedData Pydantic model
        """
        personal_info = jsonb_data.get("personal_info", {})
        confidence_scores = jsonb_data.get("confidence_scores", {})
        skills_data = jsonb_data.get("skills", {})

        # Handle skills being either a dict (categorized) or list (flat)
        if isinstance(skills_data, dict):
            # Categorized skills format
            skills_list = skills_data.get("all", [])
            certifications = skills_data.get("certifications", [])
            languages = skills_data.get("languages", [])
            projects = skills_data.get("projects", [])
            publications = skills_data.get("publications", [])
        else:
            # Flat skills format (list)
            skills_list = skills_data if isinstance(skills_data, list) else []
            certifications = []
            languages = []
            projects = []
            publications = []

        return ParsedData(
            full_name=personal_info.get("full_name"),
            email=personal_info.get("email"),
            phone=personal_info.get("phone"),
            location=personal_info.get("location"),
            linkedin_url=personal_info.get("linkedin_url"),
            github_url=personal_info.get("github_url"),
            portfolio_url=personal_info.get("portfolio_url"),
            summary=personal_info.get("summary"),
            skills=skills_list,
            work_experience=jsonb_data.get("work_experience", []),
            education=jsonb_data.get("education", []),
            certifications=certifications,
            languages=languages,
            projects=projects,
            additional_info={
                "publications": publications,
            },
            extraction_confidence=confidence_scores.get("overall", 0.0),
        )

    # ========== Resume Metadata Operations ==========

    async def save_resume_metadata(
        self,
        resume_id: UUID,
        original_filename: str,
        file_type: str,
        file_size_bytes: int,
        file_hash: str,
        storage_path: str,
        processing_status: str = "pending"
    ) -> Resume:
        """
        Save resume metadata to database.

        Args:
            resume_id: Resume UUID
            original_filename: Original filename
            file_type: File type (pdf, docx, doc, txt)
            file_size_bytes: File size in bytes
            file_hash: SHA256 hash of file contents
            storage_path: Path where file is stored
            processing_status: Initial processing status

        Returns:
            Resume model instance
        """
        resume = Resume(
            id=resume_id,
            original_filename=original_filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            file_hash=file_hash,
            storage_path=storage_path,
            processing_status=processing_status,
        )

        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)

        return resume

    async def get_resume(self, resume_id: UUID) -> Optional[Resume]:
        """
        Retrieve resume metadata by ID.

        Args:
            resume_id: Resume UUID

        Returns:
            Resume model or None if not found
        """
        result = await self.db.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        return result.scalar_one_or_none()

    async def update_processing_status(
        self,
        resume_id: UUID,
        status: str,
        confidence_score: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update resume processing status.

        Args:
            resume_id: Resume UUID
            status: New processing status
            confidence_score: Optional confidence score
            error_message: Optional error message if failed
        """
        update_data = {
            "processing_status": status,
            "processed_at": datetime.utcnow() if status in ["complete", "failed"] else None,
        }

        if confidence_score is not None:
            update_data["confidence_score"] = confidence_score

        await self.db.execute(
            update(Resume)
            .where(Resume.id == resume_id)
            .values(**update_data)
        )
        await self.db.commit()

    async def get_recent_resumes(self, limit: int = 10) -> List[Resume]:
        """
        Get recent resumes ordered by upload date.

        Args:
            limit: Maximum number of resumes to return

        Returns:
            List of Resume models
        """
        result = await self.db.execute(
            select(Resume)
            .order_by(Resume.uploaded_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # ========== Parsed Data Operations ==========

    async def save_parsed_data(
        self,
        resume_id: UUID,
        parsed_data: ParsedData,
        ai_enhanced: bool = False
    ) -> ParsedResumeData:
        """
        Save parsed resume data to database.

        Args:
            resume_id: Resume UUID
            parsed_data: ParsedData model with extracted information
            ai_enhanced: Whether data was AI-enhanced

        Returns:
            ParsedResumeData model instance
        """
        # Convert ParsedData (flat) to JSONB structure (nested)
        jsonb_data = self._parsed_data_to_jsonb(parsed_data)

        parsed_resume = ParsedResumeData(
            id=uuid4(),
            resume_id=resume_id,
            personal_info=jsonb_data["personal_info"],
            work_experience=jsonb_data["work_experience"],
            education=jsonb_data["education"],
            skills=jsonb_data["skills"],
            confidence_scores=jsonb_data["confidence_scores"],
            ai_enhanced=ai_enhanced,
        )

        self.db.add(parsed_resume)
        await self.db.commit()
        await self.db.refresh(parsed_resume)

        return parsed_resume

    async def get_parsed_data(self, resume_id: UUID) -> Optional[ParsedData]:
        """
        Retrieve parsed resume data by resume ID.

        Args:
            resume_id: Resume UUID

        Returns:
            ParsedData Pydantic model or None if not found
        """
        result = await self.db.execute(
            select(ParsedResumeData)
            .where(ParsedResumeData.resume_id == resume_id)
        )
        parsed_resume = result.scalar_one_or_none()

        if not parsed_resume:
            return None

        # Convert JSONB structure to ParsedData (flat)
        return self._jsonb_to_parsed_data({
            "personal_info": parsed_resume.personal_info,
            "work_experience": parsed_resume.work_experience,
            "education": parsed_resume.education,
            "skills": parsed_resume.skills,
            "confidence_scores": parsed_resume.confidence_scores,
        })

    async def update_parsed_data(
        self,
        resume_id: UUID,
        parsed_data: ParsedData
    ) -> Optional[ParsedData]:
        """
        Update existing parsed resume data.

        Args:
            resume_id: Resume UUID
            parsed_data: New parsed data

        Returns:
            Updated ParsedData or None if not found
        """
        existing = await self.db.execute(
            select(ParsedResumeData)
            .where(ParsedResumeData.resume_id == resume_id)
        )
        existing_obj = existing.scalar_one_or_none()

        if not existing_obj:
            return None

        # Convert ParsedData to JSONB and update
        jsonb_data = self._parsed_data_to_jsonb(parsed_data)

        existing_obj.personal_info = jsonb_data["personal_info"]
        existing_obj.work_experience = jsonb_data["work_experience"]
        existing_obj.education = jsonb_data["education"]
        existing_obj.skills = jsonb_data["skills"]
        existing_obj.confidence_scores = jsonb_data["confidence_scores"]

        await self.db.commit()
        await self.db.refresh(existing_obj)

        # Convert back to ParsedData
        return self._jsonb_to_parsed_data({
            "personal_info": existing_obj.personal_info,
            "work_experience": existing_obj.work_experience,
            "education": existing_obj.education,
            "skills": existing_obj.skills,
            "confidence_scores": existing_obj.confidence_scores,
        })

    # ========== Share Token Operations ==========

    async def create_share_token(
        self,
        resume_id: UUID,
        expires_in_days: int = 30,
        max_access_count: Optional[int] = None
    ) -> str:
        """
        Create shareable link token for resume.

        Args:
            resume_id: Resume UUID to share
            expires_in_days: Number of days until token expires
            max_access_count: Maximum number of times link can be accessed

        Returns:
            Share token (64-character hex string)
        """
        # Generate unique token
        token_data = f"{resume_id}:{secrets.token_bytes(32).hex()}"
        share_token = hashlib.sha256(token_data.encode()).hexdigest()

        expires_at = datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None

        share = ResumeShare(
            id=uuid4(),
            resume_id=resume_id,
            share_token=share_token,
            expires_at=expires_at,
            max_access_count=max_access_count,
        )

        self.db.add(share)
        await self.db.commit()

        return share_token

    async def get_share_by_token(self, share_token: str) -> Optional[ResumeShare]:
        """
        Retrieve share record by token.

        Args:
            share_token: Share token string

        Returns:
            ResumeShare model or None if not found
        """
        result = await self.db.execute(
            select(ResumeShare)
            .where(ResumeShare.share_token == share_token)
        )
        return result.scalar_one_or_none()

    async def validate_share_token(self, share_token: str) -> bool:
        """
        Check if share token is valid and not expired.

        Args:
            share_token: Share token string

        Returns:
            True if token is valid and active
        """
        share = await self.get_share_by_token(share_token)

        if not share or not share.is_active:
            return False

        # Check expiration
        if share.expires_at and share.expires_at < datetime.utcnow():
            return False

        # Check access count
        if share.max_access_count and share.access_count >= share.max_access_count:
            return False

        return True

    async def increment_share_access(self, share_token: str) -> None:
        """
        Increment access count for share token.

        Args:
            share_token: Share token string
        """
        await self.db.execute(
            update(ResumeShare)
            .where(ResumeShare.share_token == share_token)
            .values(access_count=ResumeShare.access_count + 1)
        )
        await self.db.commit()

    async def deactivate_share(self, share_token: str) -> None:
        """
        Deactivate share token.

        Args:
            share_token: Share token string
        """
        await self.db.execute(
            update(ResumeShare)
            .where(ResumeShare.share_token == share_token)
            .values(is_active=False)
        )
        await self.db.commit()

    # ========== User Corrections (AI Learning) ==========

    async def save_correction(
        self,
        resume_id: UUID,
        field_path: str,
        original_value: Any,
        corrected_value: Any
    ) -> ResumeCorrection:
        """
        Save user correction for AI learning.

        Args:
            resume_id: Resume UUID
            field_path: Field path (e.g., "personal_info.email")
            original_value: Original extracted value
            corrected_value: User-corrected value

        Returns:
            ResumeCorrection model instance
        """
        correction = ResumeCorrection(
            id=uuid4(),
            resume_id=resume_id,
            field_path=field_path,
            original_value=original_value,
            corrected_value=corrected_value,
        )

        self.db.add(correction)
        await self.db.commit()
        await self.db.refresh(correction)

        return correction

    async def get_corrections(self, resume_id: UUID) -> List[ResumeCorrection]:
        """
        Get all corrections for a resume.

        Args:
            resume_id: Resume UUID

        Returns:
            List of ResumeCorrection models
        """
        result = await self.db.execute(
            select(ResumeCorrection)
            .where(ResumeCorrection.resume_id == resume_id)
            .order_by(ResumeCorrection.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_all_corrections(self) -> List[ResumeCorrection]:
        """
        Get all corrections (for AI training export).

        Returns:
            List of all ResumeCorrection models
        """
        result = await self.db.execute(
            select(ResumeCorrection)
            .order_by(ResumeCorrection.created_at.desc())
        )
        return list(result.scalars().all())
