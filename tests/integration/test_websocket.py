"""
Integration tests for WebSocket functionality
"""
import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class TestWebSocketIntegration:
    """Test WebSocket integration"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        return create_app()

    def test_websocket_connection(self, app):
        """Test WebSocket connection"""
        client = TestClient(app)

        with client.websocket_connect("/ws") as websocket:
            # First, should receive connection established message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "connection_established"

            # Now test ping message
            websocket.send_text(json.dumps({"type": "ping"}))
            data = websocket.receive_text()
            message = json.loads(data)

            # Should receive pong response
            assert message["type"] == "pong"
            assert "timestamp" in message

    def test_websocket_task_subscription(self, app):
        """Test WebSocket task subscription"""
        client = TestClient(app)

        with client.websocket_connect("/ws") as websocket:
            # First, should receive connection established message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "connection_established"

            # Subscribe to a task
            websocket.send_text(
                json.dumps({"type": "subscribe_task", "task_id": "test-task-id"})
            )

            # Should receive subscription confirmation
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "subscription_confirmed"
            assert message["task_id"] == "test-task-id"

    def test_websocket_error_handling(self, app):
        """Test WebSocket error handling"""
        client = TestClient(app)

        with client.websocket_connect("/ws") as websocket:
            # Skip connection message
            websocket.receive_text()

            # Send invalid JSON
            websocket.send_text("invalid json")

            # Should receive error message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"
            assert "Invalid JSON" in message["message"]
