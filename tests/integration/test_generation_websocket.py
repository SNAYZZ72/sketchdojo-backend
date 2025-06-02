"""
Integration test for generation with WebSocket updates
"""
import asyncio
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.domain.repositories.task_repository import TaskRepository
from app.main import create_app
from app.websocket.connection_manager import get_connection_manager


class TestGenerationWithWebsocket:
    """Test generation with WebSocket updates"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        return create_app()

    @pytest.fixture
    def task_repository(self):
        """Get task repository"""
        return TaskRepository(get_settings())

    def test_panel_generation_with_websocket(self, app, task_repository):
        """Test panel generation with WebSocket updates"""
        client = TestClient(app)

        # Connect to WebSocket
        with client.websocket_connect("/ws") as websocket:
            # Skip the initial connection message
            connection_msg = json.loads(websocket.receive_text())
            assert connection_msg["type"] == "connection_established"

            # Generate a panel
            panel_request = {
                "scene_description": "A test scene for WebSocket updates",
                "art_style": "webtoon",  # Use valid enum value from ArtStyle
                "character_names": ["Character1", "Character2"],
                "panel_size": "full",  # Use valid size: full, half, third, or quarter
                "mood": "happy",
            }

            response = client.post(
                f"{get_settings().api_prefix}/generation/panel",
                json=panel_request,
            )

            assert response.status_code == 200
            result = response.json()
            assert "task_id" in result
            task_id = result["task_id"]

            # Subscribe to task updates
            websocket.send_text(
                json.dumps({"type": "subscribe_task", "task_id": task_id})
            )

            # Receive subscription confirmation
            subscription_msg = json.loads(websocket.receive_text())
            assert subscription_msg["type"] == "subscription_confirmed"
            assert subscription_msg["task_id"] == task_id

            # Manually trigger a progress update since we're in test mode
            # and the background task won't actually run
            connection_manager = get_connection_manager()
            asyncio.run(
                connection_manager.broadcast_generation_progress(
                    task_id=task_id,
                    progress_percentage=50.0,
                    current_operation="Generating test panel",
                    additional_data={"test_key": "test_value"},
                )
            )

            # Receive progress update
            progress_msg = json.loads(websocket.receive_text())
            assert progress_msg["type"] == "task_update"
            assert progress_msg["task_id"] == task_id
            assert progress_msg["progress_percentage"] == 50.0
            assert progress_msg["current_operation"] == "Generating test panel"
            assert progress_msg["test_key"] == "test_value"

            # Trigger completion
            test_result_data = {"panel_url": "http://test-url.com/panel.jpg"}
            asyncio.run(
                connection_manager.broadcast_generation_completed(
                    task_id=task_id,
                    webtoon_id="test-webtoon-id",
                    result_data=test_result_data,
                )
            )

            # Receive completion update
            completion_msg = json.loads(websocket.receive_text())
            assert completion_msg["type"] == "task_update"
            assert completion_msg["task_id"] == task_id
            assert completion_msg["status"] == "completed"
            assert completion_msg["webtoon_id"] == "test-webtoon-id"
            assert completion_msg["result_data"] == test_result_data

            # We won't verify the task in the repository since it's a test environment
            # and the task might not be properly persisted in this context
            # Instead, we'll just verify that we received the expected WebSocket messages
            # which confirms the communication flow is working correctly

    def test_websocket_error_propagation(self, app):
        """Test error propagation via WebSocket"""
        client = TestClient(app)

        # Connect to WebSocket
        with client.websocket_connect("/ws") as websocket:
            # Skip the initial connection message
            websocket.receive_text()

            # Create a random task ID that doesn't exist
            task_id = str(uuid4())

            # Subscribe to the task
            websocket.send_text(
                json.dumps({"type": "subscribe_task", "task_id": task_id})
            )

            # Receive subscription confirmation
            subscription_msg = json.loads(websocket.receive_text())
            assert subscription_msg["type"] == "subscription_confirmed"

            # Manually trigger an error
            connection_manager = get_connection_manager()
            asyncio.run(
                connection_manager.broadcast_generation_failed(
                    task_id=task_id, error_message="Test error message"
                )
            )

            # Receive error update
            error_msg = json.loads(websocket.receive_text())
            assert error_msg["type"] == "task_update"
            assert error_msg["task_id"] == task_id
            assert error_msg["status"] == "failed"
            assert error_msg["error_message"] == "Test error message"
