from sqlalchemy import Column, String, Integer, DateTime, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Resume(Base):
    """
    Resume model representing an uploaded resume file.

    This model stores the metadata and processing status of uploaded resumes.
    """
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    storage_path = Column(String(500), nullable=False)
    processing_status = Column(String(20), default="pending")
    confidence_score = Column(Numeric(5, 2))
    parsing_version = Column(String(20))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ParsedResumeData(Base):
    """
    ParsedResumeData model storing structured data extracted from resumes.

    This model contains the parsed personal information, work experience,
    education, and skills extracted from a resume.
    """
    __tablename__ = "parsed_resume_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), nullable=False)
    personal_info = Column(JSONB, nullable=False)
    work_experience = Column(JSONB, default=list)
    education = Column(JSONB, default=list)
    skills = Column(JSONB, default=dict)
    confidence_scores = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ResumeCorrection(Base):
    """
    ResumeCorrection model storing user corrections to parsed data.

    This model tracks corrections made by users to the parsed resume data.
    """
    __tablename__ = "resume_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), nullable=False)
    field_path = Column(String(100), nullable=False)
    original_value = Column(JSONB, nullable=False)
    corrected_value = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ResumeShare(Base):
    """
    ResumeShare model for sharing resumes via public links.

    This model manages temporary shareable links for resume access.
    """
    __tablename__ = "resume_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), nullable=False)
    share_token = Column(String(64), unique=True, nullable=False)
    access_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
