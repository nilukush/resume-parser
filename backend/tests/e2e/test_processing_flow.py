"""
End-to-end integration tests for the complete resume processing flow.

This module tests the complete happy path from file upload through
WebSocket progress updates to completion.
"""

import pytest
import time
import asyncio
import threading
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.api.websocket import manager
from app.services.parser_orchestrator import ParserOrchestrator


client = TestClient(app)


def test_complete_upload_to_processing_flow():
    """Test complete flow from upload to processing completion"""
    # Step 1: Upload resume
    upload_response = client.post(
        "/v1/resumes/upload",
        files={
            "file": (
                "test_resume.txt",
                b"John Doe\nSoftware Engineer\nEmail: john@example.com\nPhone: +1-555-0123",
                "text/plain"
            )
        }
    )

    assert upload_response.status_code == 202
    data = upload_response.json()
    assert "resume_id" in data
    assert "websocket_url" in data

    resume_id = data["resume_id"]

    # Create a test orchestrator to manually trigger parsing
    # This is needed because TestClient doesn't run asyncio.create_task background tasks
    test_orchestrator = ParserOrchestrator(manager)
    test_content = b"John Doe\nSoftware Engineer\nEmail: john@example.com\nPhone: +1-555-0123"

    def run_parsing():
        """Run parsing in a separate thread with its own event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                test_orchestrator.parse_resume(resume_id, "test_resume.txt", test_content)
            )
        finally:
            loop.close()

    # Start parsing in background thread
    parsing_thread = threading.Thread(target=run_parsing, daemon=True)
    parsing_thread.start()

    # Give the parsing a moment to start
    time.sleep(0.2)

    # Step 2: Connect to WebSocket and receive updates
    with TestClient(app) as test_client:
        with test_client.websocket_connect(f"/ws/resumes/{resume_id}") as websocket:
            # Connection established
            msg = websocket.receive_json()
            assert msg["type"] == "connection_established"

            # Collect all progress messages
            messages = []
            max_messages = 20

            for _ in range(max_messages):
                try:
                    msg = websocket.receive_json()
                    messages.append(msg)

                    if msg.get("stage") == "complete":
                        break
                except Exception:
                    break

    # Wait for parsing thread to complete
    parsing_thread.join(timeout=5)

    # Verify we received meaningful progress
    assert len(messages) >= 2

    # Check for complete message
    complete_msgs = [m for m in messages if m.get("stage") == "complete"]
    assert len(complete_msgs) > 0
