"""
Parser Orchestrator Service for ResuMate.

This service orchestrates the resume parsing pipeline:
1. Text Extraction - Extract text from uploaded file
2. NLP Parsing - Extract entities using spaCy NLP
3. Complete - Broadcast final parsed data

Each stage broadcasts progress updates via WebSocket.
"""

import asyncio
from typing import Optional

from app.services.text_extractor import extract_text, TextExtractionError
from app.services.nlp_extractor import extract_entities
from app.models.progress import (
    ProgressUpdate,
    ProgressStage,
    CompleteProgress,
    ErrorProgress
)
from app.core.storage import save_parsed_resume


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
        file_content: bytes
    ) -> dict:
        """
        Parse a resume through the complete pipeline with progress updates.

        Args:
            resume_id: Unique identifier for this resume
            filename: Original filename
            file_content: File bytes content

        Returns:
            Parsed resume data dictionary

        Raises:
            TextExtractionError: If text extraction fails
            Exception: If parsing fails at any stage
        """
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

            # Stage 3: Complete
            # Save to in-memory storage for retrieval later
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
        update = CompleteProgress(resume_id=resume_id, parsed_data=parsed_data)
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
