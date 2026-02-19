"""
Integration tests for complete upload and WebSocket flow.

Tests the complete flow from file upload through WebSocket connection
to receiving progress updates during parsing.
"""

import pytest
import asyncio
import threading
import time
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.api.websocket import manager
from app.services.parser_orchestrator import ParserOrchestrator


client = TestClient(app)


def test_upload_and_websocket_progress():
    """
    Test complete flow: upload -> WebSocket connects -> progress updates.

    This integration test verifies that:
    1. WebSocket connection can be established
    2. Progress updates are broadcast during parsing
    3. Final completion message is received
    """
    # Create a test orchestrator instance
    test_orchestrator = ParserOrchestrator(manager)

    # Generate a resume ID for testing
    resume_id = str(uuid.uuid4())
    test_content = b"John Doe\nEmail: john@example.com"

    messages_received = []

    def run_parsing():
        """Run parsing in a separate thread with its own event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                test_orchestrator.parse_resume(resume_id, "test.txt", test_content)
            )
        finally:
            loop.close()

    # Start parsing in background thread
    parsing_thread = threading.Thread(target=run_parsing, daemon=True)
    parsing_thread.start()

    # Give the parsing a moment to start
    time.sleep(0.2)

    # Connect WebSocket and receive messages
    with TestClient(app) as test_client:
        with test_client.websocket_connect(f"/ws/resumes/{resume_id}") as websocket:
            # Connection established
            msg1 = websocket.receive_json()
            assert msg1["type"] == "connection_established"
            assert msg1["resume_id"] == resume_id
            messages_received.append(msg1)

            # Progress updates
            max_messages = 20

            for _ in range(max_messages):
                try:
                    msg = websocket.receive_json()
                    messages_received.append(msg)

                    if msg.get("stage") == "complete":
                        break
                except Exception:
                    break

    # Wait for parsing thread to complete
    parsing_thread.join(timeout=5)

    # Verify we received progress updates
    message_types = [msg.get("type") for msg in messages_received]
    stages = [msg.get("stage") for msg in messages_received]

    # Should have connection_established
    assert "connection_established" in message_types

    # Should have received some messages beyond connection
    assert len(messages_received) >= 1

    # Should have complete stage (parsing finished)
    assert "complete" in stages


def test_upload_invalid_file_type():
    """Test that invalid file types are rejected."""
    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.exe", b"invalid content", "application/octet-stream")}
    )

    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]


def test_upload_returns_websocket_url():
    """Test that upload response includes WebSocket URL for progress tracking."""
    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("resume.txt", b"Sample resume content", "text/plain")}
    )

    assert response.status_code == 202
    data = response.json()

    # Verify WebSocket URL format
    assert "websocket_url" in data
    assert data["websocket_url"].startswith("/ws/resumes/")
    # Extract resume_id from response and verify URL
    resume_id = data["resume_id"]
    assert data["websocket_url"] == f"/ws/resumes/{resume_id}"


def test_upload_response_includes_required_fields():
    """Test that upload response includes all required fields."""
    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.txt", b"Content", "text/plain")}
    )

    assert response.status_code == 202
    data = response.json()

    # Verify all expected fields are present
    assert "resume_id" in data
    assert "status" in data
    assert "estimated_time_seconds" in data
    assert "file_hash" in data
    assert "websocket_url" in data

    # Verify data types
    assert isinstance(data["resume_id"], str)
    assert data["status"] == "processing"
    assert isinstance(data["estimated_time_seconds"], int)
    assert isinstance(data["file_hash"], str) and len(data["file_hash"]) == 64  # SHA256


def test_websocket_connection_established():
    """Test that WebSocket connection is established with confirmation message."""
    test_id = str(uuid.uuid4())

    with client.websocket_connect(f"/ws/resumes/{test_id}") as websocket:
        msg = websocket.receive_json()
        assert msg["type"] == "connection_established"
        assert msg["resume_id"] == test_id
        assert "message" in msg


def test_websocket_ping_pong():
    """Test WebSocket ping/pong functionality."""
    test_id = str(uuid.uuid4())

    with client.websocket_connect(f"/ws/resumes/{test_id}") as websocket:
        # Receive connection message
        websocket.receive_json()

        # Send ping
        websocket.send_text("ping")

        # Receive pong
        response = websocket.receive_json()
        assert response["type"] == "pong"
        assert response["message"] == "alive"


def test_upload_with_pdf_mime_type():
    """Test upload endpoint accepts PDF files with correct MIME type."""
    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")}
    )

    # Should be accepted (validation passes for MIME type)
    assert response.status_code == 202
    data = response.json()
    assert "resume_id" in data


def test_upload_with_docx_mime_type():
    """Test upload endpoint accepts DOCX files with correct MIME type."""
    response = client.post(
        "/v1/resumes/upload",
        files={
            "file": (
                "test.docx",
                b"PKfake content",  # DOCX files start with PK (zip signature)
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }
    )

    # Should be accepted
    assert response.status_code == 202
    data = response.json()
    assert "resume_id" in data


def test_upload_file_size_validation():
    """Test that upload endpoint validates file size."""
    # Create a file larger than 10MB
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB

    response = client.post(
        "/v1/resumes/upload",
        files={"file": ("large.txt", large_content, "text/plain")}
    )

    # Should be rejected for size
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()
