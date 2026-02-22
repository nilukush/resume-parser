"""
WebSocket connection manager for real-time progress updates.

This module provides a connection manager that handles WebSocket connections
for broadcasting resume parsing progress to connected clients.
"""

from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio


class ConnectionManager:
    """
    Manage WebSocket connections for real-time progress updates.

    This class maintains a registry of active WebSocket connections
    organized by resume_id, allowing targeted broadcasting of updates
    to clients watching specific resume parsing operations.
    """

    def __init__(self) -> None:
        """Initialize the connection manager with an empty connection registry."""
        # Map resume_id to set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, resume_id: str) -> None:
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept and register
            resume_id: The unique identifier for the resume being watched
        """
        await websocket.accept()
        if resume_id not in self.active_connections:
            self.active_connections[resume_id] = set()
        self.active_connections[resume_id].add(websocket)

        # Send connection confirmation
        await self.send_personal_message(
            {
                "type": "connection_established",
                "resume_id": resume_id,
                "message": "Connected to resume parsing updates",
            },
            websocket,
        )

    def disconnect(self, websocket: WebSocket, resume_id: str) -> None:
        """
        Remove a WebSocket connection from the registry.

        Args:
            websocket: The WebSocket connection to remove
            resume_id: The resume ID associated with the connection
        """
        if resume_id in self.active_connections:
            self.active_connections[resume_id].discard(websocket)
            # Clean up empty connection sets
            if not self.active_connections[resume_id]:
                del self.active_connections[resume_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: The message dictionary to send
            websocket: The target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except RuntimeError as e:
            # Connection may be closed
            import logging
            logging.getLogger(__name__).error(f"WebSocket RuntimeError: {e}", exc_info=True)
            print(f"Error sending personal message: {e}")
        except TypeError as e:
            # JSON serialization error
            import logging
            logging.getLogger(__name__).error(f"WebSocket serialization error: {e}", exc_info=True)
            print(f"Serialization error: {e}")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"WebSocket error: {type(e).__name__}: {e}", exc_info=True)
            print(f"Unexpected error sending message: {type(e).__name__}: {e}")

    async def broadcast_to_resume(self, message: dict, resume_id: str) -> None:
        """
        Broadcast a message to all connections watching a specific resume.

        Args:
            message: The message dictionary to broadcast
            resume_id: The resume ID whose watchers should receive the message
        """
        if resume_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[resume_id]:
                try:
                    # Check WebSocket client state before sending
                    # CLIENT_CLOSED means the connection is no longer valid
                    if getattr(connection, 'client_state', None) != 'DISCONNECTED':
                        await connection.send_json(message)
                    else:
                        # Connection is already closed, mark for cleanup
                        disconnected.add(connection)
                except (RuntimeError, WebSocketDisconnect):
                    # Mark disconnected WebSockets for cleanup
                    disconnected.add(connection)
                except Exception as e:
                    # Log with more context for debugging
                    import logging
                    logging.getLogger(__name__).warning(
                        f"Failed to broadcast to resume {resume_id}: {e}",
                        exc_info=True
                    )
                    disconnected.add(connection)

            # Clean up disconnected WebSockets
            for connection in disconnected:
                self.disconnect(connection, resume_id)


# Global connection manager instance
manager = ConnectionManager()
