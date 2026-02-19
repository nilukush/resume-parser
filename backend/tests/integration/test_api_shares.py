"""
Integration tests for share API endpoints.

These tests verify the share management endpoints including:
- Creating share links
- Retrieving share details
- Revoking shares
- Public access to shared resumes
- Error handling for expired/revoked shares
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_share_returns_202():
    """Test that creating a share returns 202 Accepted"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares

    clear_all_shares()
    resume_id = "test-resume-123"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "John Doe"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })

    response = client.post(f"/v1/resumes/{resume_id}/share")

    assert response.status_code == 202
    data = response.json()
    assert "share_token" in data
    assert "share_url" in data
    assert "expires_at" in data


def test_create_share_returns_404_for_nonexistent_resume():
    """Test that creating a share for non-existent resume returns 404"""
    from app.core.share_storage import clear_all_shares

    clear_all_shares()
    resume_id = "nonexistent-resume"

    response = client.post(f"/v1/resumes/{resume_id}/share")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_share_returns_200():
    """Test that getting share details returns 200"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares

    clear_all_shares()
    resume_id = "test-resume-789"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "Test User"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })

    create_response = client.post(f"/v1/resumes/{resume_id}/share")
    share_token = create_response.json()["share_token"]

    response = client.get(f"/v1/resumes/{resume_id}/share")

    assert response.status_code == 200
    data = response.json()
    assert data["share_token"] == share_token


def test_get_share_returns_404_when_no_share_exists():
    """Test that getting share details returns 404 when no share exists"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares

    clear_all_shares()
    resume_id = "test-resume-no-share"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "No Share User"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })

    response = client.get(f"/v1/resumes/{resume_id}/share")

    assert response.status_code == 404


def test_revoke_share_deactivates_link():
    """Test that revoking a share deactivates it"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares, get_share

    clear_all_shares()
    resume_id = "test-resume-revoke"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "Revoke Test"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })

    create_response = client.post(f"/v1/resumes/{resume_id}/share")
    share_token = create_response.json()["share_token"]

    response = client.delete(f"/v1/resumes/{resume_id}/share")

    assert response.status_code == 200

    share = get_share(share_token)
    assert share["is_active"] is False


def test_revoke_share_returns_404_when_no_share_exists():
    """Test that revoking a share returns 404 when no share exists"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares

    clear_all_shares()
    resume_id = "test-resume-no-share-to-revoke"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "No Share to Revoke"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })

    response = client.delete(f"/v1/resumes/{resume_id}/share")

    assert response.status_code == 404


def test_public_share_access_returns_resume_data():
    """Test that public share endpoint returns resume data"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares

    clear_all_shares()
    resume_id = "test-resume-public"
    resume_data = {
        "personal_info": {"full_name": "Public User", "email": "public@test.com"},
        "work_experience": [],
        "education": [],
        "skills": {"technical": ["Python"]},
        "confidence_scores": {}
    }
    save_parsed_resume(resume_id, resume_data)

    create_response = client.post(f"/v1/resumes/{resume_id}/share")
    share_token = create_response.json()["share_token"]

    response = client.get(f"/v1/share/{share_token}")

    assert response.status_code == 200
    data = response.json()
    assert data["resume_id"] == resume_id
    assert data["personal_info"]["full_name"] == "Public User"


def test_expired_share_returns_410():
    """Test that expired share returns 410 Gone"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares, create_share

    clear_all_shares()
    resume_id = "test-resume-expired"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "Expired Test"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })

    share_data = create_share(resume_id, expires_in_days=-1)
    share_token = share_data["share_token"]

    response = client.get(f"/v1/share/{share_token}")

    assert response.status_code == 410


def test_revoked_share_returns_403():
    """Test that revoked share returns 403 Forbidden"""
    from app.core.storage import save_parsed_resume
    from app.core.share_storage import clear_all_shares

    clear_all_shares()
    resume_id = "test-resume-revoked-access"
    save_parsed_resume(resume_id, {
        "personal_info": {"full_name": "Revoked Access Test"},
        "work_experience": [],
        "education": [],
        "skills": {},
        "confidence_scores": {}
    })

    create_response = client.post(f"/v1/resumes/{resume_id}/share")
    client.delete(f"/v1/resumes/{resume_id}/share")

    response = client.get(f"/v1/share/{create_response.json()['share_token']}")

    assert response.status_code == 403


def test_public_share_returns_404_for_invalid_token():
    """Test that public share returns 404 for invalid token"""
    from app.core.share_storage import clear_all_shares

    clear_all_shares()
    invalid_token = "invalid-token-12345"

    response = client.get(f"/v1/share/{invalid_token}")

    assert response.status_code == 404
