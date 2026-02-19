"""
Unit tests for OCR Extractor Service.

These tests verify OCR text extraction from scanned PDFs using Tesseract.
Following TDD discipline: tests written first, then implementation.
"""

import io
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from PIL import Image


@pytest.mark.asyncio
async def test_extract_text_with_ocr_returns_string():
    """Test that extract_text_with_ocr returns a string."""
    from app.services.ocr_extractor import extract_text_with_ocr

    # Mock pdf2image convert_from_bytes to return mock PIL Images
    mock_image = MagicMock(spec=Image.Image)
    mock_image.convert.return_value = mock_image

    with patch('app.services.ocr_extractor.convert_from_bytes') as mock_convert:
        mock_convert.return_value = [mock_image]

        # Mock pytesseract image_to_string to return text
        with patch('app.services.ocr_extractor.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Extracted OCR text from resume"

            result = await extract_text_with_ocr("resume.pdf", b"fake pdf content")

            assert isinstance(result, str)
            assert result == "Extracted OCR text from resume"


@pytest.mark.asyncio
async def test_is_text_sufficient_with_long_text():
    """Test that _is_text_sufficient returns True for 100+ character text."""
    from app.services.ocr_extractor import _is_text_sufficient, MIN_TEXT_LENGTH

    # Create text with exactly MIN_TEXT_LENGTH characters
    long_text = "a" * MIN_TEXT_LENGTH
    assert _is_text_sufficient(long_text) is True

    # Create text with more than MIN_TEXT_LENGTH characters
    longer_text = "b" * 150
    assert _is_text_sufficient(longer_text) is True


@pytest.mark.asyncio
async def test_is_text_sufficient_with_short_text():
    """Test that _is_text_sufficient returns False for short text."""
    from app.services.ocr_extractor import _is_text_sufficient, MIN_TEXT_LENGTH

    # Create text with less than MIN_TEXT_LENGTH characters
    short_text = "a" * (MIN_TEXT_LENGTH - 1)
    assert _is_text_sufficient(short_text) is False

    # Empty text should also return False
    assert _is_text_sufficient("") is False


@pytest.mark.asyncio
async def test_ocr_fallback_when_regular_extraction_fails():
    """Test OCR fallback when regular extraction produces insufficient text."""
    from app.services.ocr_extractor import extract_text_with_ocr, OCRExtractionError

    # Mock pdf2image convert_from_bytes
    mock_image = MagicMock(spec=Image.Image)
    mock_image.convert.return_value = mock_image

    with patch('app.services.ocr_extractor.convert_from_bytes') as mock_convert:
        mock_convert.return_value = [mock_image]

        # Mock pytesseract to return sufficient text
        with patch('app.services.ocr_extractor.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "John Doe\nSoftware Engineer\nExperience: 5 years\n" * 5

            # Provide insufficient regular text (should trigger OCR fallback)
            short_regular_text = "Insufficient"
            result = await extract_text_with_ocr(
                "resume.pdf",
                b"fake pdf content",
                regular_text=short_regular_text
            )

            # Should return OCR text since regular text was insufficient
            assert isinstance(result, str)
            assert len(result) > len(short_regular_text)


@pytest.mark.asyncio
async def test_extract_text_with_ocr_raises_error_on_failure():
    """Test that extract_text_with_ocr raises OCRExtractionError on failure."""
    from app.services.ocr_extractor import extract_text_with_ocr, OCRExtractionError

    # Mock convert_from_bytes to raise an exception
    with patch('app.services.ocr_extractor.convert_from_bytes') as mock_convert:
        mock_convert.side_effect = Exception("PDF conversion failed")

        with pytest.raises(OCRExtractionError) as exc_info:
            await extract_text_with_ocr("resume.pdf", b"bad pdf content")

        assert "OCR extraction failed" in str(exc_info.value)


def test_ocr_extraction_error_exists():
    """Test that OCRExtractionError exception exists."""
    from app.services.ocr_extractor import OCRExtractionError
    assert issubclass(OCRExtractionError, Exception)


@pytest.mark.asyncio
async def test_preprocess_image_converts_to_grayscale():
    """Test that _preprocess_image converts image to grayscale."""
    from app.services.ocr_extractor import _preprocess_image

    mock_image = MagicMock(spec=Image.Image)
    mock_grayscale = MagicMock(spec=Image.Image)
    mock_image.convert.return_value = mock_grayscale

    result = _preprocess_image(mock_image)

    # Verify convert was called with 'L' (grayscale mode)
    mock_image.convert.assert_called_once_with('L')
    assert result == mock_grayscale


@pytest.mark.asyncio
async def test_extract_with_ocr_handles_multiple_pages():
    """Test that _extract_with_ocr handles PDFs with multiple pages."""
    from app.services.ocr_extractor import _extract_with_ocr

    # Create mock images for 2 pages
    mock_image1 = MagicMock(spec=Image.Image)
    mock_image2 = MagicMock(spec=Image.Image)
    mock_image1.convert.return_value = mock_image1
    mock_image2.convert.return_value = mock_image2

    with patch('app.services.ocr_extractor.convert_from_bytes') as mock_convert:
        mock_convert.return_value = [mock_image1, mock_image2]

        with patch('app.services.ocr_extractor.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.side_effect = ["Page 1 text", "Page 2 text"]

            result = await _extract_with_ocr("resume.pdf", b"multipage pdf")

            # Both pages should be processed
            assert isinstance(result, str)
            assert "Page 1 text" in result
            assert "Page 2 text" in result
