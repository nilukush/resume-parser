"""
Integration tests for WebSocket connections.

Tests the WebSocket endpoint for real-time resume parsing updates.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_websocket_connection():
    """Test that WebSocket endpoint accepts connections"""
    with client.websocket_connect("/ws/resumes/test-resume-id") as websocket:
        data = websocket.receive_json()
        assert "type" in data
        assert data["type"] == "connection_established"


def test_websocket_ping_pong():
    """Test WebSocket ping/pong functionality"""
    with client.websocket_connect("/ws/resumes/test-resume-id-2") as websocket:
        # Receive connection confirmation
        data = websocket.receive_json()
        assert data["type"] == "connection_established"

        # Send ping
        websocket.send_text("ping")

        # Receive pong response
        response = websocket.receive_json()
        assert response["type"] == "pong"
        assert response["message"] == "alive"


def test_websocket_disconnect():
    """Test WebSocket disconnection handling"""
    with client.websocket_connect("/ws/resumes/test-resume-id-3") as websocket:
        # Receive connection confirmation
        data = websocket.receive_json()
        assert data["type"] == "connection_established"

    # Connection is closed after context manager exits
    # If we reach here, disconnection was handled gracefully
    assert True
