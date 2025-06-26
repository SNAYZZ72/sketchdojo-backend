"""
Tests for WebSocket exceptions and error handling.
"""
import pytest
from fastapi import WebSocket
from unittest.mock import AsyncMock

from app.websocket.exceptions import (
    WebSocketError,
    WebSocketValidationError,
    WebSocketAuthenticationError,
    WebSocketAuthorizationError,
    WebSocketRateLimitError,
    WebSocketInternalError,
    format_error,
    send_error
)


def test_websocket_error():
    """Test basic WebSocketError functionality."""
    error = WebSocketError("Test error", code="test_error", status_code=400)
    assert str(error) == "Test error"
    assert error.code == "test_error"
    assert error.status_code == 400
    assert error.details == {}


def test_websocket_validation_error():
    """Test WebSocketValidationError."""
    error = WebSocketValidationError("Invalid input", {"field": "value"})
    assert str(error) == "Invalid input"
    assert error.code == "validation_error"
    assert error.status_code == 400
    assert error.details == {"field": "value"}


def test_websocket_authentication_error():
    """Test WebSocketAuthenticationError."""
    error = WebSocketAuthenticationError("Invalid token")
    assert str(error) == "Invalid token"
    assert error.code == "authentication_error"
    assert error.status_code == 401


def test_websocket_authorization_error():
    """Test WebSocketAuthorizationError."""
    error = WebSocketAuthorizationError("Insufficient permissions")
    assert str(error) == "Insufficient permissions"
    assert error.code == "authorization_error"
    assert error.status_code == 403


def test_websocket_rate_limit_error():
    """Test WebSocketRateLimitError."""
    error = WebSocketRateLimitError(retry_after=30)
    assert str(error) == "Rate limit exceeded"
    assert error.code == "rate_limit_exceeded"
    assert error.status_code == 429
    assert error.details == {"retry_after": 30}


def test_format_error_custom():
    """Test formatting of custom WebSocket errors."""
    error = WebSocketValidationError("Invalid input", {"field": "value"})
    result = format_error(error)
    assert result == {
        "type": "error",
        "code": "validation_error",
        "message": "Invalid input",
        "details": {"field": "value"}
    }


def test_format_error_generic():
    """Test formatting of generic exceptions."""
    error = ValueError("Something went wrong")
    result = format_error(error, include_details=True)
    assert result == {
        "type": "error",
        "code": "internal_error",
        "message": "Something went wrong",
        "details": {
            "exception_type": "ValueError"
        }
    }


@pytest.mark.asyncio
async def test_send_error():
    """Test sending an error through a WebSocket."""
    mock_websocket = AsyncMock(spec=WebSocket)
    error = WebSocketValidationError("Invalid input")
    
    await send_error(mock_websocket, error)
    
    mock_websocket.send_json.assert_awaited_once_with({
        "type": "error",
        "code": "validation_error",
        "message": "Invalid input"
    })


@pytest.mark.asyncio
async def test_send_error_send_failure(caplog):
    """Test handling of WebSocket send failures."""
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.send_json.side_effect = Exception("Send failed")
    error = WebSocketValidationError("Invalid input")
    
    with caplog.at_level("ERROR"):
        await send_error(mock_websocket, error)
    
    assert "Failed to send error message: Send failed" in caplog.text
    assert "Original error was: Invalid input" in caplog.text
