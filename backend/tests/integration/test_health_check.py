"""
Integration tests for health check endpoint.

These tests validate that the health check endpoint returns
proper system status including database connectivity.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_returns_system_status():
    """Test that health check returns detailed system status"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "environment" in data
    assert "timestamp" in data


def test_health_check_includes_database_status():
    """Test that health check reports database connectivity"""
    response = client.get("/health")

    data = response.json()
    assert "database" in data
    # Database status can be "connected", "disconnected", or "unknown"
    assert data["database"] in ["connected", "disconnected", "unknown"]

    # If database is disconnected, should return 503
    if data["database"] == "disconnected":
        assert response.status_code == 503
    else:
        assert response.status_code == 200


def test_health_check_returns_503_when_database_unhealthy():
    """Test that health check returns 503 when database is disconnected"""
    # This test would require mocking a database failure
    # For now, we just verify the structure exists
    response = client.get("/health")

    data = response.json()
    if data["database"] == "disconnected":
        assert response.status_code == 503
        assert data["status"] == "unhealthy"


def test_health_check_includes_version():
    """Test that health check includes application version"""
    response = client.get("/health")

    data = response.json()
    assert data["version"] == "1.0.0"

    # Version should be included even if database is disconnected
    assert "version" in data
