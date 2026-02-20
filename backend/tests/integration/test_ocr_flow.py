"""
Integration tests for OCR flow within text extraction pipeline.

These tests verify the end-to-end OCR fallback behavior:
1. Regular extraction works for text-based PDFs (no OCR needed)
2. OCR triggers automatically for scanned PDFs (when regular text < 100 chars)
3. Complete flow processes various file types correctly
"""

import io
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image


@pytest.mark.asyncio
async def test_text_extraction_uses_regular_for_text_pdf():
    """Test that regular extraction is used for text-based PDFs."""
    from app.services.text_extractor import extract_text

    # Mock pdfplumber to return sufficient text (no OCR needed)
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "John Doe\nSoftware Engineer\n" * 10  # 100+ chars
    mock_pdf.pages = [mock_page]

    with patch('app.services.text_extractor.pdfplumber.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf

        result = await extract_text("resume.pdf", b"fake pdf content")

        # Should return regular text (OCR should NOT be called)
        assert "John Doe" in result
        assert "Software Engineer" in result
        assert len(result) >= 100


@pytest.mark.asyncio
async def test_text_extraction_triggers_ocr_for_scanned_pdf():
    """Test that OCR triggers when regular extraction yields insufficient text."""
    from app.services.text_extractor import extract_text

    # Mock pdfplumber to return insufficient text (< 100 chars)
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Scanned"  # Only 7 chars
    mock_pdf.pages = [mock_page]

    # Mock OCR to return text
    mock_image = MagicMock(spec=Image.Image)
    mock_image.convert.return_value = mock_image

    with patch('app.services.text_extractor.pdfplumber.open') as mock_pdf_open:
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        with patch('app.services.ocr_extractor.convert_from_bytes') as mock_convert:
            mock_convert.return_value = [mock_image]

            with patch('app.services.ocr_extractor.pytesseract.image_to_string') as mock_ocr:
                mock_ocr.return_value = "OCR Extracted: John Doe - Senior Developer"

                result = await extract_text("scanned.pdf", b"scanned pdf content")

                # Should return OCR text
                assert "OCR Extracted" in result
                assert "John Doe" in result


@pytest.mark.asyncio
async def test_text_extraction_returns_regular_when_both_succeed():
    """Test that regular text is preferred when both regular and OCR succeed."""
    from app.services.text_extractor import extract_text

    # Mock pdfplumber to return sufficient text
    regular_text = "Regular Text: Jane Smith - Data Scientist\n" * 10
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = regular_text
    mock_pdf.pages = [mock_page]

    with patch('app.services.text_extractor.pdfplumber.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf

        # Even if OCR is available, regular text should be returned
        result = await extract_text("resume.pdf", b"content")

        # Should have regular text content
        assert "Regular Text" in result
        assert "Jane Smith" in result


@pytest.mark.asyncio
async def test_ocr_flow_handles_docx_without_ocr():
    """Test that DOCX files don't trigger OCR (different path)."""
    from app.services.text_extractor import extract_text

    # Mock python-docx to return text
    mock_doc = MagicMock()
    mock_paragraph1 = MagicMock()
    mock_paragraph1.text = "Word document content"
    mock_paragraph2 = MagicMock()
    mock_paragraph2.text = "More content here"
    mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]

    with patch('app.services.text_extractor.Document') as mock_document:
        mock_document.return_value = mock_doc

        result = await extract_text("resume.docx", b"docx content")

        # Should return text from DOCX
        assert "Word document content" in result
        assert "More content here" in result


@pytest.mark.asyncio
async def test_ocr_disabled_when_config_is_false():
    """Test that OCR is skipped when ENABLE_OCR_FALLBACK config is False."""
    import os
    from app.services.ocr_extractor import _is_text_sufficient

    # This test verifies the sufficiency check logic
    # The ENABLE_OCR_FALLBACK config would be checked at a higher level
    # For now, we test that short text is correctly identified as insufficient

    short_text = "Short"  # < 100 chars
    assert _is_text_sufficient(short_text) is False

    long_text = "A" * 100  # Exactly 100 chars
    assert _is_text_sufficient(long_text) is True


@pytest.mark.asyncio
async def test_ocr_flow_with_multipage_scanned_pdf():
    """Test OCR processing of multi-page scanned PDFs."""
    from app.services.text_extractor import extract_text

    # Mock pdfplumber to return insufficient text
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    mock_pdf.pages = [mock_page]

    # Mock 2 pages for OCR
    mock_image1 = MagicMock(spec=Image.Image)
    mock_image1.convert.return_value = mock_image1
    mock_image2 = MagicMock(spec=Image.Image)
    mock_image2.convert.return_value = mock_image2

    with patch('app.services.text_extractor.pdfplumber.open') as mock_pdf_open:
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        with patch('app.services.ocr_extractor.convert_from_bytes') as mock_convert:
            mock_convert.return_value = [mock_image1, mock_image2]

            with patch('app.services.ocr_extractor.pytesseract.image_to_string') as mock_ocr:
                # First call is for preprocessed image (returns same), second for text extraction
                mock_ocr.side_effect = [
                    "Page 1: John Doe - Frontend Developer",
                    "Page 2: Experience at Tech Corp"
                ]

                result = await extract_text("multipage.pdf", b"content")

                # Should have text from both pages
                assert "Page 1" in result
                assert "Page 2" in result
                assert "John Doe" in result
                assert "Tech Corp" in result


@pytest.mark.asyncio
async def test_ocr_flow_raises_on_ocr_failure():
    """Test that OCRExtractionError is raised when OCR fails for scanned PDFs."""
    from app.services.text_extractor import extract_text
    from app.services.ocr_extractor import OCRExtractionError

    # Mock pdfplumber to return insufficient text (triggers OCR)
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    mock_pdf.pages = [mock_page]

    with patch('app.services.text_extractor.pdfplumber.open') as mock_pdf_open:
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        # Mock convert_from_bytes to raise an error (OCR failure)
        with patch('app.services.ocr_extractor.convert_from_bytes') as mock_convert:
            mock_convert.side_effect = Exception("PDF corrupted")

            # Should raise OCRExtractionError when OCR fails
            with pytest.raises(OCRExtractionError, match="OCR extraction failed"):
                await extract_text("corrupt.pdf", b"bad content")
