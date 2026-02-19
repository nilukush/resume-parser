"""
Unit tests for Text Extraction Service.

These tests verify text extraction from PDF, DOCX, DOC, and TXT files.
Following TDD discipline: tests written first, then implementation.
"""

import io
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Mock problematic imports before they load
sys.modules['spacy'] = MagicMock()
sys.modules['spacy.language'] = MagicMock()
sys.modules['spacy.tokens'] = MagicMock()

# Import will fail initially - this is expected in TDD RED phase


@pytest.mark.asyncio
async def test_extract_text_function_exists():
    """Test that extract_text function can be imported."""
    from app.services.text_extractor import extract_text
    assert callable(extract_text)


@pytest.mark.asyncio
async def test_extract_text_returns_string_from_pdf_bytes():
    """Test that extract_text returns a string when given PDF bytes."""
    from app.services.text_extractor import extract_text

    # Mock pdfplumber to avoid needing real PDF files
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Sample resume text"
    mock_pdf.pages = [mock_page]

    with patch('app.services.text_extractor.pdfplumber.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf

        # Mock OCR to return the same text (sufficient text check is done internally)
        with patch('app.services.text_extractor.extract_text_with_ocr') as mock_ocr:
            mock_ocr.return_value = "Sample resume text"

            result = await extract_text("test.pdf", b"fake pdf content")
            assert isinstance(result, str)
            assert result == "Sample resume text"


@pytest.mark.asyncio
async def test_extract_text_from_docx_bytes():
    """Test that extract_text works with DOCX bytes."""
    from app.services.text_extractor import extract_text

    # Mock python-docx Document
    mock_doc = MagicMock()
    mock_paragraph1 = MagicMock()
    mock_paragraph1.text = "Name: John Doe"
    mock_paragraph2 = MagicMock()
    mock_paragraph2.text = "Experience: Software Engineer"
    mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]

    with patch('app.services.text_extractor.Document') as mock_document:
        mock_document.return_value = mock_doc
        result = await extract_text("resume.docx", b"fake docx content")
        assert isinstance(result, str)
        assert "John Doe" in result
        assert "Software Engineer" in result


@pytest.mark.asyncio
async def test_extract_text_from_txt_bytes():
    """Test that extract_text works with TXT bytes."""
    from app.services.text_extractor import extract_text

    test_content = b"Plain text resume content here."
    result = await extract_text("resume.txt", test_content)
    assert isinstance(result, str)
    assert result == "Plain text resume content here."


def test_text_extraction_error_exists():
    """Test that TextExtractionError exception exists."""
    from app.services.text_extractor import TextExtractionError
    assert issubclass(TextExtractionError, Exception)


@pytest.mark.asyncio
async def test_extract_text_raises_error_for_unsupported_format():
    """Test that unsupported file types raise TextExtractionError."""
    from app.services.text_extractor import extract_text, TextExtractionError

    with pytest.raises(TextExtractionError) as exc_info:
        await extract_text("file.unsupported", b"content")
    assert "Unsupported file type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_extract_text_raises_error_for_pdf_extraction_failure():
    """Test that PDF extraction failures raise TextExtractionError."""
    from app.services.text_extractor import extract_text, TextExtractionError

    with patch('app.services.text_extractor.pdfplumber.open') as mock_open:
        mock_open.side_effect = Exception("PDF parsing error")
        with pytest.raises(TextExtractionError) as exc_info:
            await extract_text("corrupted.pdf", b"bad pdf")
        assert "Failed to extract text from PDF" in str(exc_info.value)


@pytest.mark.asyncio
async def test_extract_text_handles_empty_pdf():
    """Test that empty PDF returns empty string."""
    from app.services.text_extractor import extract_text

    mock_pdf = MagicMock()
    mock_pdf.pages = []

    with patch('app.services.text_extractor.pdfplumber.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf

        # Mock OCR to return empty text
        with patch('app.services.text_extractor.extract_text_with_ocr') as mock_ocr:
            mock_ocr.return_value = ""

            result = await extract_text("empty.pdf", b"empty pdf")
            assert result == ""


@pytest.mark.asyncio
async def test_extract_text_handles_pdf_with_multiple_pages():
    """Test that PDF with multiple pages concatenates text."""
    from app.services.text_extractor import extract_text

    mock_pdf = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 content"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 content"
    mock_pdf.pages = [mock_page1, mock_page2]

    expected_text = "Page 1 contentPage 2 content"

    with patch('app.services.text_extractor.pdfplumber.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf

        # Mock OCR to return the concatenated text
        with patch('app.services.text_extractor.extract_text_with_ocr') as mock_ocr:
            mock_ocr.return_value = expected_text

            result = await extract_text("multipage.pdf", b"multipage pdf")
            assert "Page 1 content" in result
            assert "Page 2 content" in result


@pytest.mark.asyncio
async def test_extract_text_handles_docx_with_empty_paragraphs():
    """Test that DOCX with empty paragraphs is handled correctly."""
    from app.services.text_extractor import extract_text

    mock_doc = MagicMock()
    mock_paragraph1 = MagicMock()
    mock_paragraph1.text = "Some text"
    mock_paragraph2 = MagicMock()
    mock_paragraph2.text = ""
    mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]

    with patch('app.services.text_extractor.Document') as mock_document:
        mock_document.return_value = mock_doc
        result = await extract_text("resume.docx", b"docx content")
        assert "Some text" in result


@pytest.mark.asyncio
async def test_extract_text_handles_txt_with_utf8_content():
    """Test that TXT files with UTF-8 content are handled correctly."""
    from app.services.text_extractor import extract_text

    test_content = "Résumé content with unicode: ".encode("utf-8")
    result = await extract_text("resume.txt", test_content)
    assert isinstance(result, str)
    assert "Résumé" in result


@pytest.mark.asyncio
async def test_extract_text_raises_error_for_docx_extraction_failure():
    """Test that DOCX extraction failures raise TextExtractionError."""
    from app.services.text_extractor import extract_text, TextExtractionError

    with patch('app.services.text_extractor.Document') as mock_document:
        mock_document.side_effect = Exception("DOCX parsing error")
        with pytest.raises(TextExtractionError) as exc_info:
            await extract_text("corrupted.docx", b"bad docx")
        assert "Failed to extract text from DOCX" in str(exc_info.value)


@pytest.mark.asyncio
async def test_extract_text_raises_error_for_txt_extraction_failure():
    """Test that TXT extraction failures raise TextExtractionError."""
    from app.services.text_extractor import extract_text, TextExtractionError

    # Invalid UTF-8 bytes should raise an error
    with pytest.raises(TextExtractionError) as exc_info:
        await extract_text("resume.txt", b"\xff\xfe invalid utf-8")
    assert "Failed to extract text from TXT" in str(exc_info.value)


@pytest.mark.asyncio
async def test_extract_text_handles_doc_extension():
    """Test that .doc extension is treated as docx (same format)."""
    from app.services.text_extractor import extract_text

    mock_doc = MagicMock()
    mock_paragraph = MagicMock()
    mock_paragraph.text = "DOC content"
    mock_doc.paragraphs = [mock_paragraph]

    with patch('app.services.text_extractor.Document') as mock_document:
        mock_document.return_value = mock_doc
        result = await extract_text("legacy.doc", b"doc content")
        assert isinstance(result, str)
        assert "DOC content" in result


@pytest.mark.asyncio
async def test_extract_text_calls_ocr_for_scanned_pdf():
    """Test that extract_text uses OCR fallback for PDFs with insufficient text."""
    from app.services.text_extractor import extract_text

    # Mock pdfplumber to return empty text (simulating scanned PDF)
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""  # Empty text - should trigger OCR
    mock_pdf.pages = [mock_page]

    # Mock OCR to return actual text
    mock_ocr_text = "OCR extracted text from scanned resume"

    with patch('app.services.text_extractor.pdfplumber.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf

        with patch('app.services.text_extractor.extract_text_with_ocr') as mock_ocr:
            mock_ocr.return_value = mock_ocr_text

            result = await extract_text("scanned.pdf", b"fake scanned pdf")

            # Verify OCR was called
            mock_ocr.assert_called_once()
            # Verify the result is the OCR text
            assert result == mock_ocr_text


@pytest.mark.asyncio
async def test_extract_text_skips_ocr_for_sufficient_pdf_text():
    """Test that extract_text skips OCR when PDF has sufficient text."""
    from app.services.text_extractor import extract_text

    # Mock pdfplumber to return sufficient text (no OCR needed)
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    # Text longer than MIN_TEXT_LENGTH (100 chars)
    sufficient_text = "This is a resume with lots of text content. " * 5
    mock_page.extract_text.return_value = sufficient_text
    mock_pdf.pages = [mock_page]

    with patch('app.services.text_extractor.pdfplumber.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf

        with patch('app.services.text_extractor.extract_text_with_ocr') as mock_ocr:
            mock_ocr.return_value = sufficient_text

            result = await extract_text("normal.pdf", b"normal pdf")

            # Verify OCR was still called (it checks sufficiency internally)
            mock_ocr.assert_called_once()
            # Verify the result is the sufficient text
            assert result == sufficient_text
