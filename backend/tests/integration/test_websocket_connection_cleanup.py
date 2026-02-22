"""
Integration test for WebSocket connection cleanup and management.

This test verifies that:
1. Multiple WebSocket connections to the same resume_id are handled correctly
2. Closed connections are properly cleaned up
3. Broadcasting to disconnected connections doesn't cause errors
4. The connection manager properly tracks active connections
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.websocket import manager


class TestWebSocketConnectionCleanup:
    """Test WebSocket connection lifecycle and cleanup"""

    def test_multiple_connections_same_resume(self, sample_resume_txt: bytes):
        """
        Test that multiple WebSocket connections to the same resume_id are handled.

        Scenario:
        1. Upload a resume
        2. Create multiple WebSocket connections for the same resume_id
        3. Close one connection before parsing completes
        4. Verify that broadcasting doesn't fail and connections are cleaned up
        """
        from app.core.config import settings
        original_use_db = settings.USE_DATABASE
        settings.USE_DATABASE = False  # Use in-memory for this test

        try:
            client = TestClient(app)

            # Step 1: Upload resume
            response = client.post(
                "/v1/resumes/upload",
                files={"file": ("test.txt", sample_resume_txt, "text/plain")}
            )
            assert response.status_code == 202
            resume_id = response.json()["resume_id"]

            # Step 2: Create multiple WebSocket connections
            connections = []
            for i in range(3):
                ws = client.websocket_connect(f"/ws/resumes/{resume_id}")
                ws.__enter__()
                connections.append(ws)

            # Verify all connections are tracked
            assert resume_id in manager.active_connections
            assert len(manager.active_connections[resume_id]) == 3

            # Step 3: Close one connection early
            connections[0].__exit__(None, None, None)

            # Give the system time to process
            # Note: In TestClient, connections are synchronous
            import time
            time.sleep(0.5)

            # Step 4: Trigger a broadcast (simulating parsing progress)
            async def test_broadcast():
                await manager.broadcast_to_resume(
                    {"type": "test", "message": "test message"},
                    resume_id
                )

            # Run the async broadcast
            asyncio.run(test_broadcast())

            # Step 5: Clean up remaining connections
            for ws in connections[1:]:
                ws.__exit__(None, None, None)

            # Verify all connections are eventually cleaned up
            # Note: The connection manager runs in the same process in tests
            time.sleep(0.5)
            assert resume_id not in manager.active_connections or len(manager.active_connections.get(resume_id, set())) == 0

        finally:
            settings.USE_DATABASE = original_use_db

    def test_broadcast_to_disconnected_connection(self, sample_resume_txt: bytes):
        """
        Test that broadcasting to a disconnected connection doesn't cause errors.

        Scenario:
        1. Create a WebSocket connection
        2. Close the connection
        3. Attempt to broadcast to the closed connection
        4. Verify no exception is raised and connection is cleaned up
        """
        from app.core.config import settings
        original_use_db = settings.USE_DATABASE
        settings.USE_DATABASE = False

        try:
            client = TestClient(app)

            # Upload resume
            response = client.post(
                "/v1/resumes/upload",
                files={"file": ("test.txt", sample_resume_txt, "text/plain")}
            )
            assert response.status_code == 202
            resume_id = response.json()["resume_id"]

            # Create and immediately close connection
            with client.websocket_connect(f"/ws/resumes/{resume_id}") as ws:
                # Connection is established
                pass

            # Connection is now closed
            # Attempt to broadcast - should not raise an exception
            async def test_broadcast_to_closed():
                await manager.broadcast_to_resume(
                    {"type": "progress_update", "progress": 100, "status": "Complete"},
                    resume_id
                )

            # This should complete without errors
            asyncio.run(test_broadcast_to_closed())

            # Connection should be cleaned up
            assert resume_id not in manager.active_connections

        finally:
            settings.USE_DATABASE = original_use_db

    def test_connection_state_validation(self, sample_resume_txt: bytes):
        """
        Test that connection manager validates WebSocket state before sending.

        This verifies the fix for checking client_state before broadcasting.
        """
        from app.core.config import settings
        original_use_db = settings.USE_DATABASE
        settings.USE_DATABASE = False

        try:
            client = TestClient(app)

            # Upload resume
            response = client.post(
                "/v1/resumes/upload",
                files={"file": ("test.txt", sample_resume_txt, "text/plain")}
            )
            assert response.status_code == 202
            resume_id = response.json()["resume_id"]

            # Create connection
            with client.websocket_connect(f"/ws/resumes/{resume_id}") as ws:
                # Receive the connection confirmation
                message = ws.receive_json()
                assert message["type"] == "connection_established"
                assert message["resume_id"] == resume_id

            # After exiting context, connection is closed
            # Broadcasting should handle this gracefully
            async def send_test_message():
                await manager.broadcast_to_resume(
                    {"type": "test", "data": "after_close"},
                    resume_id
                )

            # Should not raise an exception
            asyncio.run(send_test_message())

        finally:
            settings.USE_DATABASE = original_use_db


@pytest.fixture
def sample_resume_txt():
    """Sample resume text content for testing"""
    return b"""
John Doe
john.doe@example.com

Experience
-----------
Software Engineer at Tech Corp (2020-Present)
- Developed web applications
- Led team of 5 developers

Education
---------
Bachelor of Science in Computer Science
University of Technology (2016-2020)

Skills
------
Python, JavaScript, React, SQL
"""
