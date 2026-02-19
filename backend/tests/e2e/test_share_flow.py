"""
End-to-end integration tests for the complete share flow.

This module tests the complete happy path from file upload through
processing to share creation, public access, and export.
"""

import pytest
import time
import asyncio
import threading
from fastapi.testclient import TestClient

from app.main import app
from app.api.websocket import manager
from app.services.parser_orchestrator import ParserOrchestrator


client = TestClient(app)


def test_complete_share_flow():
    """
    Test complete flow: Upload -> Process -> Review -> Share -> Export

    This is a comprehensive end-to-end test that validates:
    1. Resume upload
    2. Background processing completion
    3. Retrieving parsed data
    4. Creating shareable link
    5. Accessing shared resume publicly
    6. Exporting to PDF
    7. Exporting to WhatsApp
    8. Revoking share
    9. Verifying access is denied after revocation
    """
    from app.core.storage import clear_all_resumes, save_parsed_resume
    from app.core.share_storage import clear_all_shares

    # Clear all data before test
    clear_all_resumes()
    clear_all_shares()

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
    upload_data = upload_response.json()
    assert "resume_id" in upload_data
    resume_id = upload_data["resume_id"]

    # Step 2: Simulate background parsing completion
    # In real scenario, the background task would complete. For testing,
    # we manually trigger the parsing in a separate thread
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

    # Wait for parsing to complete
    parsing_thread.join(timeout=5)

    # Give a small buffer for storage to be updated
    time.sleep(0.5)

    # Step 3: Get parsed data
    get_response = client.get(f"/v1/resumes/{resume_id}")
    assert get_response.status_code == 200
    resume_data = get_response.json()
    assert resume_data["status"] == "complete"
    assert "data" in resume_data
    assert resume_data["data"]["personal_info"]["full_name"] == "John Doe"

    # Step 4: Create share
    share_response = client.post(f"/v1/resumes/{resume_id}/share")
    assert share_response.status_code == 202
    share_data = share_response.json()
    assert "share_token" in share_data
    assert "share_url" in share_data
    share_token = share_data["share_token"]

    # Step 5: Access public share
    public_response = client.get(f"/v1/share/{share_token}")
    assert public_response.status_code == 200
    public_data = public_response.json()
    assert public_data["resume_id"] == resume_id
    assert public_data["personal_info"]["full_name"] == "John Doe"

    # Step 6: Export PDF
    pdf_response = client.get(f"/v1/resumes/{resume_id}/export/pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    # Verify it's a valid PDF file
    assert pdf_response.content[:4] == b"%PDF"

    # Step 7: Export WhatsApp
    whatsapp_response = client.get(f"/v1/resumes/{resume_id}/export/whatsapp")
    assert whatsapp_response.status_code == 200
    whatsapp_data = whatsapp_response.json()
    assert "whatsapp_url" in whatsapp_data
    assert whatsapp_data["whatsapp_url"].startswith("https://wa.me/")

    # Step 8: Export Telegram
    telegram_response = client.get(f"/v1/resumes/{resume_id}/export/telegram")
    assert telegram_response.status_code == 200
    telegram_data = telegram_response.json()
    assert "telegram_url" in telegram_data
    assert telegram_data["telegram_url"].startswith("https://t.me/share/url")

    # Step 9: Export Email
    email_response = client.get(f"/v1/resumes/{resume_id}/export/email")
    assert email_response.status_code == 200
    email_data = email_response.json()
    assert "mailto_url" in email_data
    assert email_data["mailto_url"].startswith("mailto:")

    # Step 10: Get share details before revocation
    share_details_response = client.get(f"/v1/resumes/{resume_id}/share")
    assert share_details_response.status_code == 200
    share_details = share_details_response.json()
    assert share_details["share_token"] == share_token
    assert share_details["is_active"] is True

    # Step 11: Revoke share
    revoke_response = client.delete(f"/v1/resumes/{resume_id}/share")
    assert revoke_response.status_code == 200
    revoke_data = revoke_response.json()
    assert "message" in revoke_data

    # Step 12: Verify access denied after revocation
    public_after = client.get(f"/v1/share/{share_token}")
    assert public_after.status_code == 403
    assert "revoked" in public_after.json()["detail"].lower()

    print("Complete share flow test passed!")


def test_share_flow_with_full_resume_data():
    """
    Test share flow with complete resume data including all sections.

    This validates that all resume sections are properly preserved
    through the share and export flow.
    """
    from app.core.storage import clear_all_resumes, save_parsed_resume
    from app.core.share_storage import clear_all_shares

    # Clear all data before test
    clear_all_resumes()
    clear_all_shares()

    # Create a complete resume with all sections
    resume_id = "test-full-resume-123"
    complete_resume_data = {
        "personal_info": {
            "full_name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+1-555-9999",
            "location": "New York, NY"
        },
        "work_experience": [
            {
                "company": "Tech Innovations Inc",
                "title": "Senior Software Engineer",
                "start_date": "2020-06",
                "end_date": "Present",
                "description": "Leading cloud architecture projects"
            },
            {
                "company": "Startup Co",
                "title": "Software Developer",
                "start_date": "2018-01",
                "end_date": "2020-05",
                "description": "Full-stack development"
            }
        ],
        "education": [
            {
                "institution": "MIT",
                "degree": "Master of Science in Computer Science",
                "start_date": "2016-09",
                "end_date": "2018-05",
                "gpa": "3.9"
            }
        ],
        "skills": {
            "technical": ["Python", "JavaScript", "React", "AWS", "Docker"],
            "soft": ["Team Leadership", "Agile Methodology"]
        },
        "confidence_scores": {
            "personal_info": 0.95,
            "work_experience": 0.88,
            "education": 0.92,
            "skills": 0.85
        }
    }

    save_parsed_resume(resume_id, complete_resume_data)

    # Create share
    share_response = client.post(f"/v1/resumes/{resume_id}/share")
    assert share_response.status_code == 202
    share_token = share_response.json()["share_token"]

    # Access via public share
    public_response = client.get(f"/v1/share/{share_token}")
    assert public_response.status_code == 200
    shared_data = public_response.json()

    # Verify all sections are preserved
    assert shared_data["personal_info"]["full_name"] == "Jane Smith"
    assert len(shared_data["work_experience"]) == 2
    assert shared_data["work_experience"][0]["company"] == "Tech Innovations Inc"
    assert len(shared_data["education"]) == 1
    assert shared_data["education"][0]["institution"] == "MIT"
    assert "technical" in shared_data["skills"]
    assert len(shared_data["skills"]["technical"]) == 5

    # Verify confidence scores are included
    assert shared_data["confidence_scores"]["personal_info"] == 0.95

    # Test PDF export with complete data
    pdf_response = client.get(f"/v1/resumes/{resume_id}/export/pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert len(pdf_response.content) > 2000  # Should have more content

    # Test WhatsApp export with complete data
    whatsapp_response = client.get(f"/v1/resumes/{resume_id}/export/whatsapp")
    assert whatsapp_response.status_code == 200
    whatsapp_url = whatsapp_response.json()["whatsapp_url"]
    assert "Jane" in whatsapp_url or "Smith" in whatsapp_url or "resume" in whatsapp_url.lower()

    print("Share flow with full resume data test passed!")


def test_multiple_resumes_shares_independence():
    """
    Test that shares for different resumes are independent.

    Validates that:
    - Multiple resumes can have active shares simultaneously
    - Revoking one share doesn't affect others
    - Each share token correctly maps to its resume
    """
    from app.core.storage import clear_all_resumes, save_parsed_resume
    from app.core.share_storage import clear_all_shares

    # Clear all data before test
    clear_all_resumes()
    clear_all_shares()

    # Create two different resumes
    resume_1_id = "resume-1"
    resume_2_id = "resume-2"

    save_parsed_resume(resume_1_id, {
        "personal_info": {"full_name": "Alice Johnson"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })

    save_parsed_resume(resume_2_id, {
        "personal_info": {"full_name": "Bob Williams"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })

    # Create shares for both
    share_1_response = client.post(f"/v1/resumes/{resume_1_id}/share")
    share_2_response = client.post(f"/v1/resumes/{resume_2_id}/share")

    share_1_token = share_1_response.json()["share_token"]
    share_2_token = share_2_response.json()["share_token"]

    # Verify both shares work
    public_1 = client.get(f"/v1/share/{share_1_token}")
    public_2 = client.get(f"/v1/share/{share_2_token}")

    assert public_1.status_code == 200
    assert public_1.json()["personal_info"]["full_name"] == "Alice Johnson"

    assert public_2.status_code == 200
    assert public_2.json()["personal_info"]["full_name"] == "Bob Williams"

    # Revoke only share 1
    client.delete(f"/v1/resumes/{resume_1_id}/share")

    # Verify share 1 is revoked but share 2 still works
    public_1_after = client.get(f"/v1/share/{share_1_token}")
    public_2_after = client.get(f"/v1/share/{share_2_token}")

    assert public_1_after.status_code == 403
    assert public_2_after.status_code == 200
    assert public_2_after.json()["personal_info"]["full_name"] == "Bob Williams"

    print("Multiple resumes shares independence test passed!")
