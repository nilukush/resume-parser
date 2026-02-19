"""
Tests for GET and PUT resume endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.storage import save_parsed_resume, clear_all_resumes

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage_before_each_test():
    """Clear storage before each test"""
    clear_all_resumes()
    yield
    clear_all_resumes()


def test_get_resume_returns_data():
    """Test that GET /resumes/{id} returns parsed data"""
    # Setup: Save test data
    test_resume_id = "test-resume-123"
    test_data = {
        "personal_info": {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-0123"
        },
        "work_experience": [],
        "education": [],
        "skills": {"technical": [], "soft_skills": []},
        "confidence_scores": {}
    }
    save_parsed_resume(test_resume_id, test_data)

    # Act
    response = client.get(f"/v1/resumes/{test_resume_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["resume_id"] == test_resume_id
    assert data["status"] == "complete"
    assert data["data"]["personal_info"]["full_name"] == "John Doe"


def test_get_resume_not_found_returns_404():
    """Test that GET /resumes/{id} returns 404 for non-existent resume"""
    response = client.get("/v1/resumes/non-existent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_resume_modifies_data():
    """Test that PUT /resumes/{id} updates resume data"""
    # Setup
    test_resume_id = "test-resume-456"
    test_data = {
        "personal_info": {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+1-555-9999"
        },
        "work_experience": [],
        "education": [],
        "skills": {"technical": [], "soft_skills": []},
        "confidence_scores": {}
    }
    save_parsed_resume(test_resume_id, test_data)

    # Act: Update personal info
    update_payload = {
        "personal_info": {
            "full_name": "Jane Smith"
        }
    }
    response = client.put(
        f"/v1/resumes/{test_resume_id}",
        json=update_payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert data["data"]["personal_info"]["full_name"] == "Jane Smith"
    # Other fields should remain unchanged
    assert data["data"]["personal_info"]["email"] == "jane@example.com"


def test_update_resume_not_found_returns_404():
    """Test that PUT /resumes/{id} returns 404 for non-existent resume"""
    response = client.put(
        "/v1/resumes/non-existent-id",
        json={"personal_info": {"full_name": "Test"}}
    )
    assert response.status_code == 404


def test_update_work_experience():
    """Test updating work experience array"""
    # Setup
    test_resume_id = "test-resume-789"
    test_data = {
        "personal_info": {},
        "work_experience": [
            {
                "company": "Old Company",
                "title": "Developer",
                "location": "",
                "start_date": "2020",
                "end_date": "2022",
                "description": "Old job"
            }
        ],
        "education": [],
        "skills": {"technical": [], "soft_skills": []},
        "confidence_scores": {}
    }
    save_parsed_resume(test_resume_id, test_data)

    # Act: Replace work experience
    new_experience = [
        {
            "company": "New Company",
            "title": "Senior Developer",
            "location": "Remote",
            "start_date": "2022",
            "end_date": "present",
            "description": "New role"
        }
    ]
    response = client.put(
        f"/v1/resumes/{test_resume_id}",
        json={"work_experience": new_experience}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["work_experience"]) == 1
    assert data["data"]["work_experience"][0]["company"] == "New Company"
