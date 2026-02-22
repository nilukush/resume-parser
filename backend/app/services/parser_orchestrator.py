"""
Parser Orchestrator Service for ResuMate.

This service orchestrates the resume parsing pipeline:
1. Text Extraction - Extract text from uploaded file
2. NLP Parsing - Extract entities using spaCy NLP
3. AI Enhancement - Improve results using GPT-4 (if configured)
4. Complete - Broadcast final parsed data

Each stage broadcasts progress updates via WebSocket.
"""

import asyncio
from typing import Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.services.text_extractor import extract_text, TextExtractionError
from app.services.nlp_extractor import extract_entities
from app.services.ai_extractor import enhance_with_ai
from app.models.progress import (
    ProgressUpdate,
    ProgressStage,
    CompleteProgress,
    ErrorProgress
)
from app.core.storage import save_parsed_resume
from app.core.config import settings


def _serialize_for_websocket(data: Any) -> Any:
    """
    Recursively convert complex types to JSON-serializable formats.

    This handles:
    - UUID → str
    - datetime → ISO format str
    - Decimal → float
    - Recursive dicts and lists

    Args:
        data: Data to serialize

    Returns:
        JSON-serializable version of data
    """
    if isinstance(data, dict):
        return {k: _serialize_for_websocket(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_serialize_for_websocket(item) for item in data]
    elif isinstance(data, UUID):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data


class ParserOrchestrator:
    """Orchestrates the resume parsing pipeline with progress updates"""

    def __init__(self, websocket_manager):
        """
        Initialize the parser orchestrator.

        Args:
            websocket_manager: WebSocket manager for broadcasting progress updates
        """
        self.websocket_manager = websocket_manager

    async def parse_resume(
        self,
        resume_id: str,
        filename: str,
        file_content: bytes,
        file_hash: str = "",
        file_size: int = 0,
        file_type: str = "unknown",
        enable_ai: bool = True
    ) -> dict:
        """
        Parse a resume through the complete pipeline with progress updates.

        Args:
            resume_id: Unique identifier for this resume
            filename: Original filename
            file_content: File bytes content
            file_hash: SHA256 hash of file content
            file_size: File size in bytes
            file_type: File extension (pdf, docx, doc, txt)
            enable_ai: Whether to use AI enhancement (default: True)

        Returns:
            Parsed resume data dictionary

        Raises:
            TextExtractionError: If text extraction fails
            Exception: If parsing fails at any stage
        """
        raw_text = None  # Store for AI enhancement

        try:
            # Stage 1: Text Extraction
            await self._send_progress(
                resume_id,
                ProgressStage.TEXT_EXTRACTION,
                10,
                "Starting text extraction..."
            )

            raw_text = await self._extract_text_with_progress(
                resume_id, filename, file_content
            )

            # Stage 2: NLP Entity Extraction
            await self._send_progress(
                resume_id,
                ProgressStage.NLP_PARSING,
                40,
                "Extracting entities using NLP..."
            )

            parsed_data = await self._extract_entities_with_progress(
                resume_id, raw_text
            )

            # Stage 3: AI Enhancement (if enabled and configured)
            if enable_ai and raw_text:
                parsed_data = await self._enhance_with_ai_progress(
                    resume_id, raw_text, parsed_data
                )

            # Stage 4: Complete
            # Save to storage (database or in-memory based on feature flag)
            if settings.USE_DATABASE:
                # Import here to avoid circular dependency
                from app.core.database import AsyncSessionLocal
                from app.services.storage_adapter import StorageAdapter

                # Save to database
                async with AsyncSessionLocal() as db:
                    adapter = StorageAdapter(db)
                    await adapter.save_parsed_data(resume_id, parsed_data, ai_enhanced=enable_ai)
            else:
                # Save to in-memory storage
                save_parsed_resume(resume_id, parsed_data)

            await self._send_complete(resume_id, parsed_data)

            return parsed_data

        except TextExtractionError as e:
            await self._send_error(
                resume_id,
                f"Text extraction failed: {str(e)}",
                "TEXT_EXTRACTION_ERROR"
            )
            raise
        except Exception as e:
            await self._send_error(
                resume_id,
                f"Parsing failed: {str(e)}",
                "PARSE_ERROR"
            )
            raise

    async def _extract_text_with_progress(
        self,
        resume_id: str,
        filename: str,
        file_content: bytes
    ) -> str:
        """
        Extract text with progress updates.

        Args:
            resume_id: Unique identifier for this resume
            filename: Original filename
            file_content: File bytes content

        Returns:
            Extracted text content

        Raises:
            TextExtractionError: If extraction fails
        """
        try:
            await self._send_progress(
                resume_id,
                ProgressStage.TEXT_EXTRACTION,
                30,
                "Extracting text from file..."
            )

            text = await extract_text(filename, file_content)

            await self._send_progress(
                resume_id,
                ProgressStage.TEXT_EXTRACTION,
                100,
                "Text extraction complete!"
            )

            return text
        except Exception as e:
            await self._send_progress(
                resume_id,
                ProgressStage.TEXT_EXTRACTION,
                0,
                f"Extraction failed: {str(e)}"
            )
            raise

    async def _extract_entities_with_progress(
        self,
        resume_id: str,
        text: str
    ) -> dict:
        """
        Extract entities with progress updates.

        Args:
            resume_id: Unique identifier for this resume
            text: Extracted text content

        Returns:
            Parsed resume data dictionary

        Raises:
            Exception: If NLP extraction fails
        """
        try:
            await self._send_progress(
                resume_id,
                ProgressStage.NLP_PARSING,
                60,
                "Analyzing resume structure..."
            )

            # Simulate NLP processing time for better UX
            await asyncio.sleep(0.5)

            parsed_data = extract_entities(text)

            await self._send_progress(
                resume_id,
                ProgressStage.NLP_PARSING,
                100,
                "Entity extraction complete!"
            )

            return parsed_data
        except Exception as e:
            await self._send_progress(
                resume_id,
                ProgressStage.NLP_PARSING,
                0,
                f"NLP parsing failed: {str(e)}"
            )
            raise

    async def _enhance_with_ai_progress(
        self,
        resume_id: str,
        raw_text: str,
        parsed_data: dict
    ) -> dict:
        """
        Enhance parsed data using AI with progress updates.

        Args:
            resume_id: Unique identifier for this resume
            raw_text: Original extracted text content
            parsed_data: Initial NLP-parsed data

        Returns:
            Enhanced resume data dictionary
        """
        try:
            await self._send_progress(
                resume_id,
                ProgressStage.AI_ENHANCEMENT,
                70,
                "Enhancing with AI..."
            )

            # Simulate AI processing time for better UX
            await asyncio.sleep(0.3)

            enhanced_data = await enhance_with_ai(raw_text, parsed_data)

            await self._send_progress(
                resume_id,
                ProgressStage.AI_ENHANCEMENT,
                100,
                "AI enhancement complete!"
            )

            return enhanced_data
        except Exception as e:
            # AI enhancement is optional - log and continue with original data
            await self._send_progress(
                resume_id,
                ProgressStage.AI_ENHANCEMENT,
                100,
                f"AI enhancement skipped: {str(e)}"
            )
            return parsed_data

    async def _send_progress(
        self,
        resume_id: str,
        stage: ProgressStage,
        progress: int,
        status: str
    ):
        """
        Send a progress update via WebSocket.

        Args:
            resume_id: Unique identifier for this resume
            stage: Current parsing stage
            progress: Progress percentage (0-100)
            status: Human-readable status message
        """
        update = ProgressUpdate(
            resume_id=resume_id,
            stage=stage,
            progress=progress,
            status=status
        )
        await self.websocket_manager.broadcast_to_resume(
            update.to_dict(), resume_id
        )

    async def _send_complete(self, resume_id: str, parsed_data: dict):
        """
        Send completion message via WebSocket.

        Args:
            resume_id: Unique identifier for this resume
            parsed_data: Final parsed resume data
        """
        # Serialize complex objects to JSON-compatible types
        serializable_data = _serialize_for_websocket(parsed_data)

        update = CompleteProgress(resume_id=resume_id, parsed_data=serializable_data)
        await self.websocket_manager.broadcast_to_resume(
            update.to_dict(), resume_id
        )

    async def _send_error(
        self,
        resume_id: str,
        error_message: str,
        error_code: str
    ):
        """
        Send error message via WebSocket.

        Args:
            resume_id: Unique identifier for this resume
            error_message: Human-readable error message
            error_code: Machine-readable error code
        """
        update = ErrorProgress(
            resume_id=resume_id,
            error_message=error_message,
            error_code=error_code
        )
        await self.websocket_manager.broadcast_to_resume(
            update.to_dict(), resume_id
        )
