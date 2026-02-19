"""
Resume database model.

This module defines the Resume ORM model which represents
a parsed resume document in the database.
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import String, Integer, Text, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProcessingStatus(str, Enum):
    """
    Enum for resume processing status.

    Attributes:
        PENDING: Resume is queued for processing
        PROCESSING: Resume is currently being processed
        COMPLETED: Resume has been successfully processed
        FAILED: Resume processing failed
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Resume(Base):
    """
    Resume model representing a parsed resume document.

    This model stores the uploaded file metadata, extracted text,
    and structured parsed data from resume parsing.

    Attributes:
        id: Primary key
        file_name: Original filename of the uploaded resume
        file_type: MIME type of the uploaded file
        file_size: Size of the uploaded file in bytes
        raw_text: Extracted raw text from the document
        extracted_data: Raw extracted data (contact info, skills, etc.)
        parsed_data: Fully parsed and structured resume data
        processing_status: Current status of processing
        error_message: Error message if processing failed
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
    """

    __tablename__ = "resumes"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # File metadata
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Original filename of the uploaded resume"
    )

    file_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="MIME type of the uploaded file (e.g., application/pdf)"
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Size of the uploaded file in bytes"
    )

    # Extracted content
    raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Raw text extracted from the document"
    )

    extracted_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Raw extracted data (contact info, skills, experience, etc.)"
    )

    parsed_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Fully parsed and structured resume data"
    )

    # Processing status
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False,
        index=True,
        comment="Current status of resume processing"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if processing failed"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when the record was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Timestamp when the record was last updated"
    )

    def __repr__(self) -> str:
        """String representation of the Resume model."""
        return (
            f"<Resume(id={self.id}, file_name='{self.file_name}', "
            f"status='{self.processing_status}')>"
        )

    def to_dict(self) -> dict:
        """
        Convert the Resume model to a dictionary.

        Returns:
            dict: Dictionary representation of the resume.
        """
        return {
            "id": self.id,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "raw_text": self.raw_text,
            "extracted_data": self.extracted_data,
            "parsed_data": self.parsed_data,
            "processing_status": self.processing_status.value if isinstance(
                self.processing_status, ProcessingStatus
            ) else self.processing_status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_completed(self) -> bool:
        """Check if the resume processing is completed."""
        return self.processing_status == ProcessingStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if the resume processing has failed."""
        return self.processing_status == ProcessingStatus.FAILED

    @property
    def is_processing(self) -> bool:
        """Check if the resume is currently being processed."""
        return self.processing_status == ProcessingStatus.PROCESSING

    @property
    def is_pending(self) -> bool:
        """Check if the resume is pending processing."""
        return self.processing_status == ProcessingStatus.PENDING

    def mark_as_processing(self) -> None:
        """Mark the resume as currently being processed."""
        self.processing_status = ProcessingStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_as_completed(self, parsed_data: Optional[dict] = None) -> None:
        """
        Mark the resume as successfully processed.

        Args:
            parsed_data: Optional parsed data to set.
        """
        self.processing_status = ProcessingStatus.COMPLETED
        self.updated_at = datetime.utcnow()
        if parsed_data is not None:
            self.parsed_data = parsed_data

    def mark_as_failed(self, error_message: str) -> None:
        """
        Mark the resume as failed with an error message.

        Args:
            error_message: The error message describing the failure.
        """
        self.processing_status = ProcessingStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
