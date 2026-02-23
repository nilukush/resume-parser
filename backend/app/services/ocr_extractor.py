"""
OCR Extraction Service for ResuMate.

NOTE: OCR functionality has been DISABLED for Vercel Lambda deployment.

OCR dependencies (pdf2image, pytesseract) require external binaries
that are not available in Vercel's serverless environment:
- pdf2image requires 'poppler' utility
- pytesseract requires 'tesseract' OCR engine

This module now provides graceful degradation for image-based PDFs.
"""

from typing import Optional

# Minimum character count for text to be considered sufficient
MIN_TEXT_LENGTH = 100


class OCRExtractionError(Exception):
    """Raised when OCR text extraction fails."""

    pass


class OCRNotAvailableError(Exception):
    """Raised when OCR is requested but not available in this environment."""

    pass


def _is_text_sufficient(text: str) -> bool:
    """
    Check if extracted text is sufficient.

    Args:
        text: The extracted text to check

    Returns:
        True if text length is >= MIN_TEXT_LENGTH, False otherwise
    """
    return len(text) >= MIN_TEXT_LENGTH if text else False


async def extract_text_with_ocr(
    file_path: str,
    file_content: Optional[bytes] = None,
    regular_text: Optional[str] = None
) -> str:
    """
    Extract text using OCR - DISABLED in serverless environment.

    This function now implements graceful degradation:
    - If regular_text is provided and sufficient, return it
    - If regular_text is insufficient, raise OCRNotAvailableError
    - The calling code should handle this error and inform the user

    Args:
        file_path: Path to the file (used for context)
        file_content: Optional bytes content of the PDF file (unused)
        regular_text: Optional text from regular extraction to check if OCR is needed

    Returns:
        Extracted text as string (only if regular_text is sufficient)

    Raises:
        OCRNotAvailableError: If regular_text is insufficient and OCR is needed
    """
    # If regular text is provided and sufficient, return it
    if regular_text is not None and _is_text_sufficient(regular_text):
        return regular_text

    # Text is insufficient and OCR is not available
    # Raise error to inform user
    if regular_text is not None and len(regular_text) < MIN_TEXT_LENGTH:
        raise OCRNotAvailableError(
            "This PDF appears to be image-based (scanned) and requires OCR. "
            "OCR functionality is not available in this serverless environment. "
            "Please upload a text-based PDF or try another document format. "
            f"Extracted text length: {len(regular_text)} characters (minimum {MIN_TEXT_LENGTH} required)."
        )

    # No text provided at all
    raise OCRNotAvailableError(
        "Unable to extract text from this PDF. It may be image-based or corrupted. "
        "OCR functionality is not available in this serverless environment. "
        "Please upload a text-based PDF, DOCX, or TXT file."
    )
