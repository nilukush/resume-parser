"""
Integration tests for the resume upload API endpoints.

This module tests the resume upload functionality including:
- Successful upload returns 202 Accepted
- Unsupported file types return 400
- File size validation (> 10MB returns 400)
- Health check endpoint
"""

import pytest

from fastapi.testclient import TestClient


def test_upload_resume_returns_202():
    """
    Test that resume upload returns 202 Accepted.

    GIVEN: A valid PDF resume file
    WHEN: The file is uploaded to /v1/resumes/upload
    THEN: The response should be 202 Accepted with a resume_id
    """
    # Import here to avoid import errors when app doesn't exist yet
    try:
        from app.main import app
    except ImportError:
        pytest.skip("app.main not implemented yet")

    client = TestClient(app)

    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    )

    assert response.status_code == 202
    data = response.json()
    assert "resume_id" in data
    assert "status" in data
    assert data["status"] == "processing"


def test_upload_unsupported_file_type_returns_400():
    """
    Test that unsupported file types return 400 Bad Request.

    GIVEN: An image file (JPEG)
    WHEN: The file is uploaded to /v1/resumes/upload
    THEN: The response should be 400 with appropriate error message
    """
    try:
        from app.main import app
    except ImportError:
        pytest.skip("app.main not implemented yet")

    client = TestClient(app)

    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.jpg", b"fake image", "image/jpeg")}
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_upload_file_too_large_returns_400():
    """
    Test that files larger than 10MB return 400 Bad Request.

    GIVEN: A PDF file larger than 10MB
    WHEN: The file is uploaded to /v1/resumes/upload
    THEN: The response should be 400 with file size error message
    """
    try:
        from app.main import app
    except ImportError:
        pytest.skip("app.main not implemented yet")

    client = TestClient(app)

    # Create content larger than 10MB (11MB)
    large_content = b"x" * (11 * 1024 * 1024)

    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("large.pdf", large_content, "application/pdf")}
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_upload_docx_file_returns_202():
    """
    Test that DOCX files are accepted.

    GIVEN: A valid DOCX resume file
    WHEN: The file is uploaded to /v1/resumes/upload
    THEN: The response should be 202 Accepted
    """
    try:
        from app.main import app
    except ImportError:
        pytest.skip("app.main not implemented yet")

    client = TestClient(app)

    response = client.post(
        "/v1/resumes/upload",
        files={
            "file": (
                "test.docx",
                b"fake docx content",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }
    )

    assert response.status_code == 202
    data = response.json()
    assert "resume_id" in data


def test_upload_txt_file_returns_202():
    """
    Test that TXT files are accepted.

    GIVEN: A valid TXT resume file
    WHEN: The file is uploaded to /v1/resumes/upload
    THEN: The response should be 202 Accepted
    """
    try:
        from app.main import app
    except ImportError:
        pytest.skip("app.main not implemented yet")

    client = TestClient(app)

    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.txt", b"fake text content", "text/plain")}
    )

    assert response.status_code == 202
    data = response.json()
    assert "resume_id" in data


def test_upload_doc_file_returns_202():
    """
    Test that legacy DOC files are accepted.

    GIVEN: A valid legacy DOC resume file
    WHEN: The file is uploaded to /v1/resumes/upload
    THEN: The response should be 202 Accepted
    """
    try:
        from app.main import app
    except ImportError:
        pytest.skip("app.main not implemented yet")

    client = TestClient(app)

    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.doc", b"fake doc content", "application/msword")}
    )

    assert response.status_code == 202
    data = response.json()
    assert "resume_id" in data


def test_health_check():
    """
    Test health check endpoint.

    GIVEN: The API is running
    WHEN: A GET request is made to /health
    THEN: The response should be 200 with status "healthy"
    """
    try:
        from app.main import app
    except ImportError:
        pytest.skip("app.main not implemented yet")

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_upload_returns_file_hash():
    """
    Test that upload endpoint returns a file hash.

    GIVEN: A valid PDF resume file
    WHEN: The file is uploaded to /v1/resumes/upload
    THEN: The response should include a SHA256 file hash
    """
    try:
        from app.main import app
    except ImportError:
        pytest.skip("app.main not implemented yet")

    client = TestClient(app)

    content = b"test pdf content for hashing"

    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.pdf", content, "application/pdf")}
    )

    assert response.status_code == 202
    data = response.json()
    assert "file_hash" in data
    # SHA256 hashes are 64 characters long (hex)
    assert len(data["file_hash"]) == 64


def test_upload_returns_estimated_time():
    """
    Test that upload endpoint returns estimated processing time.

    GIVEN: A valid PDF resume file
    WHEN: The file is uploaded to /v1/resumes/upload
    THEN: The response should include estimated processing time
    """
    try:
        from app.main import app
    except ImportError:
        pytest.skip("app.main not implemented yet")

    client = TestClient(app)

    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    )

    assert response.status_code == 202
    data = response.json()
    assert "estimated_time_seconds" in data
    assert isinstance(data["estimated_time_seconds"], int)
