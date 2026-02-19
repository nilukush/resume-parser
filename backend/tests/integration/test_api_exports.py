"""
Integration tests for export API endpoints.

This module tests the export functionality for resumes, including:
- PDF export (binary file)
- WhatsApp share link generation
- Telegram share link generation
- Email mailto link generation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_export_pdf_returns_binary_pdf():
    """Test that PDF export returns binary PDF file"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares
    clear_all_shares()
    resume_id = "test-resume-pdf"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "PDF Test", "email": "pdf@test.com", "phone": "+1-555-0000", "location": "Test City"},
        "work_experience": [],
        "education": [],
        "skills": {"technical": ["Python"]},
        "confidence_scores": {}
    })
    response = client.get(f"/v1/resumes/{resume_id}/export/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_export_whatsapp_generates_url():
    """Test that WhatsApp export generates valid URL"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares
    clear_all_shares()
    resume_id = "test-resume-whatsapp"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "WhatsApp Test"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })
    response = client.get(f"/v1/resumes/{resume_id}/export/whatsapp")
    assert response.status_code == 200
    data = response.json()
    assert "whatsapp_url" in data
    assert data["whatsapp_url"].startswith("https://wa.me/")


def test_export_telegram_generates_url():
    """Test that Telegram export generates valid URL"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares
    clear_all_shares()
    resume_id = "test-resume-telegram"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "Telegram Test"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })
    response = client.get(f"/v1/resumes/{resume_id}/export/telegram")
    assert response.status_code == 200
    data = response.json()
    assert "telegram_url" in data
    assert data["telegram_url"].startswith("https://t.me/share/url")


def test_export_email_returns_mailto_link():
    """Test that email export returns mailto link"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares
    clear_all_shares()
    resume_id = "test-resume-email"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "Email Test"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })
    response = client.get(f"/v1/resumes/{resume_id}/export/email")
    assert response.status_code == 200
    data = response.json()
    assert "mailto_url" in data
    assert data["mailto_url"].startswith("mailto:")


def test_export_pdf_resume_not_found():
    """Test PDF export with non-existent resume returns 404"""
    from app.core.share_storage import clear_all_shares
    clear_all_shares()
    response = client.get("/v1/resumes/non-existent/export/pdf")
    assert response.status_code == 404


def test_export_whatsapp_resume_not_found():
    """Test WhatsApp export with non-existent resume returns 404"""
    from app.core.share_storage import clear_all_shares
    clear_all_shares()
    response = client.get("/v1/resumes/non-existent/export/whatsapp")
    assert response.status_code == 404


def test_export_telegram_resume_not_found():
    """Test Telegram export with non-existent resume returns 404"""
    from app.core.share_storage import clear_all_shares
    clear_all_shares()
    response = client.get("/v1/resumes/non-existent/export/telegram")
    assert response.status_code == 404


def test_export_email_resume_not_found():
    """Test email export with non-existent resume returns 404"""
    from app.core.share_storage import clear_all_shares
    clear_all_shares()
    response = client.get("/v1/resumes/non-existent/export/email")
    assert response.status_code == 404


def test_export_pdf_with_complete_resume():
    """Test PDF export with a complete resume including all sections"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares
    clear_all_shares()
    resume_id = "test-resume-complete"
    save_parsed_resume(resume_id, {
        "personal_info": {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-1234",
            "location": "San Francisco, CA"
        },
        "work_experience": [
            {
                "company": "Tech Corp",
                "title": "Senior Engineer",
                "start_date": "2020-01",
                "end_date": "Present",
                "description": "Led development of cloud infrastructure"
            }
        ],
        "education": [
            {
                "institution": "University of California",
                "degree": "BS Computer Science",
                "start_date": "2015-09",
                "end_date": "2019-05",
                "gpa": "3.8"
            }
        ],
        "skills": {
            "technical": ["Python", "JavaScript", "AWS", "Docker"],
            "soft": ["Leadership", "Communication"]
        },
        "confidence_scores": {}
    })
    response = client.get(f"/v1/resumes/{resume_id}/export/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"
    # Verify the PDF has reasonable content length
    assert len(response.content) > 1000
