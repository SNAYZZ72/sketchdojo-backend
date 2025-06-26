"""
Tests for WebSocket logging middleware.
"""
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket

from app.websocket.middleware.logging_middleware import LoggingMiddleware


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock(spec=WebSocket)
    ws.client = MagicMock()
    ws.client.host = "127.0.0.1"
    return ws


@pytest.fixture
def mock_call_next():
    """Create a mock call_next function."""
    async def call_next(websocket, client_id, message):
        return {"type": "test_response", "status": "success"}
    return call_next


@pytest.mark.asyncio
async def test_logging_middleware_logs_incoming_message(
    mock_websocket, mock_call_next, caplog
):
    """Test that the logging middleware logs incoming messages."""
    # Setup
    middleware = LoggingMiddleware()
    client_id = "test-client-123"
    message = {"type": "test_message", "data": "test"}
    
    # Execute
    with caplog.at_level(logging.INFO):
        await middleware(
            websocket=mock_websocket,
            client_id=client_id,
            message=message,
            call_next=mock_call_next
        )
    
    # Verify
    assert len(caplog.records) >= 1
    assert any("Received message from client" in record.message for record in caplog.records)
    
    # Check that the message was properly formatted
    log_record = next(
        record for record in caplog.records 
        if "Received message from client" in record.message
    )
    assert client_id in log_record.message
    assert "test_message" in log_record.message


@pytest.mark.asyncio
async def test_logging_middleware_logs_response(
    mock_websocket, mock_call_next, caplog
):
    """Test that the logging middleware logs responses."""
    # Setup
    middleware = LoggingMiddleware()
    client_id = "test-client-123"
    message = {"type": "test_message", "data": "test"}
    
    # Execute
    with caplog.at_level(logging.INFO):
        await middleware(
            websocket=mock_websocket,
            client_id=client_id,
            message=message,
            call_next=mock_call_next
        )
    
    # Verify response was logged
    assert any("Sending response to client" in record.message for record in caplog.records)
    
    # Check that the response was properly formatted
    log_record = next(
        record for record in caplog.records 
        if "Sending response to client" in record.message
    )
    assert client_id in log_record.message
    assert "test_response" in log_record.message


@pytest.mark.asyncio
async def test_logging_middleware_handles_errors(
    mock_websocket, caplog
):
    """Test that the logging middleware logs errors during message processing."""
    # Setup
    async def failing_call_next(websocket, client_id, message):
        raise ValueError("Test error")
    
    middleware = LoggingMiddleware()
    client_id = "test-client-123"
    message = {"type": "test_message", "data": "test"}
    
    # Execute & Verify that the error is propagated
    with pytest.raises(ValueError, match="Test error"):
        with caplog.at_level(logging.ERROR):
            await middleware(
                websocket=mock_websocket,
                client_id=client_id,
                message=message,
                call_next=failing_call_next
            )
    
    # Verify error was logged
    assert any("Error processing message" in record.message for record in caplog.records)
    assert any("Test error" in record.message for record in caplog.records)
