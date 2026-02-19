"""
OCR Extraction Service for ResuMate.

This service extracts text from scanned PDFs using Tesseract OCR.
It provides a fallback mechanism when regular text extraction fails.
"""

import io
from typing import Optional

from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image

# Minimum character count for text to be considered sufficient
MIN_TEXT_LENGTH = 100


class OCRExtractionError(Exception):
    """Raised when OCR text extraction fails."""

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


def _preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image for better OCR results.

    Converts the image to grayscale which improves OCR accuracy.

    Args:
        image: PIL Image object to preprocess

    Returns:
        Preprocessed PIL Image object
    """
    # Convert to grayscale for better OCR accuracy
    return image.convert('L')


async def _extract_with_ocr(file_path: str, file_content: Optional[bytes] = None) -> str:
    """
    Extract text from PDF using Tesseract OCR.

    Converts PDF pages to images, preprocesses them, and applies OCR.

    Args:
        file_path: Path to the file (used for context)
        file_content: Optional bytes content of the PDF file

    Returns:
        Extracted text as string

    Raises:
        OCRExtractionError: If OCR extraction fails
    """
    try:
        # Convert PDF to images
        if file_content:
            images = convert_from_bytes(file_content)
        else:
            # If no file content provided, read from file path
            with open(file_path, 'rb') as f:
                images = convert_from_bytes(f.read())

        extracted_text = ""

        for image in images:
            # Preprocess image for better OCR
            preprocessed = _preprocess_image(image)

            # Extract text using Tesseract
            page_text = pytesseract.image_to_string(preprocessed)
            extracted_text += page_text + "\n"

        return extracted_text.strip()

    except Exception as e:
        raise OCRExtractionError(f"OCR extraction failed: {str(e)}") from e


async def extract_text_with_ocr(
    file_path: str,
    file_content: Optional[bytes] = None,
    regular_text: Optional[str] = None
) -> str:
    """
    Extract text using OCR, with optional fallback based on regular extraction.

    If regular_text is provided and is sufficient (100+ characters),
    it will be returned directly. Otherwise, OCR extraction is performed.

    Args:
        file_path: Path to the file (used for context and file type detection)
        file_content: Optional bytes content of the PDF file
        regular_text: Optional text from regular extraction to check if OCR is needed

    Returns:
        Extracted text as string

    Raises:
        OCRExtractionError: If OCR extraction fails and no sufficient regular text is available
    """
    # If regular text is provided and sufficient, return it
    if regular_text is not None and _is_text_sufficient(regular_text):
        return regular_text

    # Otherwise, perform OCR extraction
    return await _extract_with_ocr(file_path, file_content)
