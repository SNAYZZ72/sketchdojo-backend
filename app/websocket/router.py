"""
WebSocket router for message handling

This module provides WebSocket routing functionality, connecting WebSocket connections
to the appropriate message handlers based on message types.
"""
import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status
from starlette.websockets import WebSocketState
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union

# Define custom WebSocket errors
class WebSocketInternalError(Exception):
    """Raised when an internal WebSocket error occurs"""
    pass

class WebSocketInvalidMessageError(Exception):
    """Raised when an invalid WebSocket message is received"""
    pass

from app.dependencies import get_chat_handler_for_websocket
from app.websocket.connection_manager import get_connection_manager
from app.websocket.error_handler import get_error_handler
from app.websocket.exceptions import WebSocketError, WebSocketValidationError
from app.websocket.handlers.tool_handler import get_tool_handler
from app.websocket.middleware import WebSocketMiddleware
from app.websocket.middleware.logging_middleware import LoggingMiddleware

logger = logging.getLogger(__name__)

# Default middleware stack
DEFAULT_MIDDLEWARE = [
    LoggingMiddleware(),
]

async def _apply_middleware(
    websocket: WebSocket,
    client_id: str,
    message: Dict[str, Any],
    call_next: Callable,
    middleware: List[WebSocketMiddleware],
    index: int = 0
) -> Any:
    """Apply middleware to a WebSocket message.
    
    This function creates a chain of middleware calls, where each middleware
    can process the request and response, and decide whether to continue the chain.
    """
    if index >= len(middleware):
        return await call_next(websocket, client_id, message)
    
    current_middleware = middleware[index]
    
    async def next_in_chain(ws: WebSocket, cid: str, msg: Dict[str, Any]) -> Any:
        return await _apply_middleware(
            websocket=ws,
            client_id=cid,
            message=msg,
            call_next=call_next,
            middleware=middleware,
            index=index + 1
        )
    
    return await current_middleware(
        websocket=websocket,
        client_id=client_id,
        message=message,
        call_next=next_in_chain
    )

async def _handle_message(
    websocket: WebSocket,
    client_id: str,
    message: Dict[str, Any],
    chat_handler: Any,
    tool_handler: Any,
    middleware: List[WebSocketMiddleware]
) -> None:
    """Handle a WebSocket message with middleware support."""
    error_handler = get_error_handler()
    
    @error_handler(include_details=False)
    async def call_handler(ws: WebSocket, cid: str, msg: Dict[str, Any]) -> None:
        message_type = msg.get('type')
        if not message_type:
            raise WebSocketValidationError("Message type is required")
        
        # Handle ping messages (WebSocket protocol level)
        if message_type == 'ping':
            logger.debug(f"Received ping from client {cid}")
            await ws.send_json({"type": "pong"})
            return
            
        # Route message to the appropriate handler based on message type
        if message_type in ('discover_tools', 'tool_call'):
            await tool_handler.handle_message(cid, msg, ws)
        else:
            await chat_handler.handle_message(cid, msg, ws)
    
    # Apply middleware chain with error handling
    try:
        await _apply_middleware(
            websocket=websocket,
            client_id=client_id,
            message=message,
            call_next=call_handler,
            middleware=middleware
        )
    except Exception as e:
        # This will catch any errors that escape the middleware chain
        await error_handler.handle_error(
            error=e,
            websocket=websocket,
            client_id=client_id,
            message=message,
            include_details=False
        )


async def websocket_endpoint(
    websocket: WebSocket,
    middleware: Optional[List[WebSocketMiddleware]] = None
) -> None:
    """Main WebSocket endpoint handling all message types.
    
    This function is the main entry point for WebSocket connections. It handles:
    - Connection setup and teardown
    - Message routing to appropriate handlers
    - Error handling and logging
    - Client lifecycle management
    
    Args:
        websocket: The WebSocket connection object
    """
    # Use client_id from query parameters if provided, otherwise generate new
    client_id = websocket.query_params.get("client_id", str(uuid4()))
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    logger.info(
        f"New WebSocket connection from {client_ip} with client_id: {client_id} "
        f"(from query params: {websocket.query_params.get('client_id') is not None})"
    )
    
    # Get dependencies
    connection_manager = get_connection_manager()
    chat_handler = await get_chat_handler_for_websocket()
    tool_handler = get_tool_handler()
    error_handler = get_error_handler()
    
    # Check for existing connection with same client_id
    existing_connection = None
    if client_id in connection_manager.active_connections:
        existing_connection = connection_manager.active_connections[client_id]
        logger.warning(f"Found existing connection for client {client_id}, will replace it")
    
    # Set up tool permissions
    try:
        await _setup_tool_permissions(client_id, tool_handler)
    except Exception as e:
        logger.error(f"Failed to set up tool permissions for {client_id}: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Failed to initialize connection")
        except Exception:
            pass  # Connection might already be closed
        return

    connection_established = False
    
    try:
        # Accept the WebSocket connection first
        await websocket.accept()
        connection_established = True
        logger.debug(f"WebSocket connection accepted for client {client_id}")
        
        # Close existing connection if it exists
        if existing_connection:
            try:
                await existing_connection.close(code=status.WS_1001_GOING_AWAY)
                logger.info(f"Closed existing connection for client {client_id}")
            except Exception as e:
                logger.warning(f"Error closing existing connection for {client_id}: {str(e)}")
        
        # Register the connection with the connection manager
        await connection_manager.connect(websocket, client_id)
        logger.info(f"Successfully registered WebSocket connection for client {client_id}")

        # Send initial ping to verify connection
        try:
            await asyncio.wait_for(
                websocket.send_text(json.dumps({"type": "ping", "message": "Connection test"})),
                timeout=5.0  # 5 second timeout for initial ping
            )
            logger.debug(f"Sent initial ping to client {client_id}")
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Initial ping failed for client {client_id}: {str(e)}")
            # Don't fail the connection just because ping failed
            # The client might still be able to receive messages
            pass
            
    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection for {client_id}: {str(e)}", exc_info=True)
        if connection_established or (hasattr(websocket, 'client_state') and websocket.client_state != WebSocketState.DISCONNECTED):
            try:
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Failed to establish connection")
            except Exception as close_error:
                logger.error(f"Failed to close WebSocket during error handling: {str(close_error)}")
        return  # Don't re-raise, we've already logged the error

    # Main message loop
    try:
        while True:
            try:
                # Use a timeout to periodically check connection health
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Send a ping to check if client is still connected
                    try:
                        await websocket.send_text(json.dumps({"type": "ping"}))
                        continue  # Go back to waiting for messages
                    except Exception as e:
                        logger.info(f"Ping failed for client {client_id}, disconnecting: {str(e)}")
                        raise WebSocketDisconnect("Ping timeout")
                
                logger.debug(f"Received raw WebSocket message: {data[:200]}...")

                try:
                    message = json.loads(data)
                    message_type = message.get('type', 'unknown')
                    logger.debug(f"Routing message of type: {message_type}")
                    
                    # Handle ping/pong messages at the protocol level
                    if message_type == 'pong':
                        logger.debug(f"Received pong from client {client_id}")
                        continue
                    
                    # Use provided middleware or default to DEFAULT_MIDDLEWARE
                    active_middleware = middleware or DEFAULT_MIDDLEWARE
                    
                    # Handle the message with middleware support
                    await _handle_message(
                        websocket=websocket,
                        client_id=client_id,
                        message=message,
                        chat_handler=chat_handler,
                        tool_handler=tool_handler,
                        middleware=active_middleware
                    )
                    
                except json.JSONDecodeError as e:
                    error = WebSocketValidationError("Invalid JSON format")
                    await error_handler.handle_error(
                        error=error,
                        websocket=websocket,
                        client_id=client_id,
                        message={"raw": data},
                        include_details=False
                    )
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {str(e)}", exc_info=True)
                    await error_handler.handle_error(
                        error=e,
                        websocket=websocket,
                        client_id=client_id,
                        message={"raw": data},
                        include_details=False
                    )
                    
            except WebSocketDisconnect as e:
                logger.info(f"Client {client_id} disconnected: {str(e) or 'client disconnected'}")
                break  # Exit the message loop on normal disconnect
            except Exception as e:
                logger.error(f"Unexpected error in WebSocket handler for {client_id}: {str(e)}", exc_info=True)
                try:
                    await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
                except Exception as close_error:
                    logger.error(f"Error closing WebSocket after error: {str(close_error)}")
                raise WebSocketInternalError("Internal server error") from e
    except Exception as e:
        logger.error(f"WebSocket connection error for {client_id}: {str(e)}", exc_info=True)
        # Try to send a final error message before disconnecting if possible
        try:
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await error_handler.handle_error(
                    error=e,
                    websocket=websocket,
                    client_id=client_id,
                    message={"type": "error", "message": "Connection error occurred"},
                    include_details=False
                )
        except Exception as send_error:
            logger.error(f"Failed to send final error message to {client_id}: {str(send_error)}")
        raise
    except asyncio.CancelledError:
        logger.info(f"WebSocket connection for client {client_id} was cancelled")
        raise
    except WebSocketDisconnect as e:
        logger.info(f"WebSocket connection closed by client {client_id}: {str(e) or 'normal closure'}")
    except WebSocketException as e:
        logger.warning(f"WebSocket protocol error for client {client_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection for {client_id}: {str(e)}", exc_info=True)
        # Convert to WebSocketInternalError to ensure proper error handling
        if not isinstance(e, WebSocketInternalError):
            raise WebSocketInternalError("An unexpected error occurred") from e
        raise
    finally:
        logger.info(f"Starting cleanup for WebSocket connection {client_id}")
        cleanup_errors = []
        
        try:
            # Only try to clean up if we successfully established the connection
            if connection_established:
                # Notify handlers of disconnection
                for handler in [chat_handler, tool_handler]:
                    try:
                        if hasattr(handler, 'handle_client_disconnect'):
                            logger.debug(f"Notifying {handler.__class__.__name__} of client {client_id} disconnection")
                            await handler.handle_client_disconnect(client_id)
                    except Exception as e:
                        error_msg = f"Error in {handler.__class__.__name__}.handle_client_disconnect: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        cleanup_errors.append(error_msg)
                
                # Disconnect from connection manager
                try:
                    logger.debug(f"Removing client {client_id} from connection manager")
                    await connection_manager.disconnect(client_id)
                except Exception as e:
                    error_msg = f"Error disconnecting from connection manager: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    cleanup_errors.append(error_msg)
                    
                # Close the WebSocket connection if it's still open
                try:
                    if websocket.client_state != WebSocketState.DISCONNECTED:
                        logger.debug(f"Closing WebSocket connection for client {client_id}")
                        await websocket.close()
                except Exception as e:
                    error_msg = f"Error closing WebSocket: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    cleanup_errors.append(error_msg)
            
            if cleanup_errors:
                logger.warning(f"Encountered {len(cleanup_errors)} errors during cleanup for client {client_id}")
            else:
                logger.info(f"Successfully cleaned up WebSocket connection for client {client_id}")
                
        except Exception as e:
            logger.critical(f"Critical error during WebSocket cleanup for {client_id}: {str(e)}", exc_info=True)
            # At this point, we've done our best to clean up, so we just log the error
            logger.exception("Cleanup error details:")


async def _setup_tool_permissions(client_id: str, tool_handler) -> None:
    """Set up tool permissions for a client.
    
    Args:
        client_id: The client ID to grant permissions to
        tool_handler: The tool handler instance
    """
    from app.config import get_settings
    settings = get_settings()
    
    try:
        # Get all available tools as dictionaries
        available_tools = tool_handler.tool_registry.list_tools()
        tool_ids = [tool["tool_id"] for tool in available_tools]
        
        # Define tool categories
        tool_categories = {
            "basic": ["echo", "weather"],
            "webtoon": [
                tool_id for tool_id in tool_ids 
                if tool_id not in ["echo", "weather"]
            ]
        }
        
        # Get the categories to grant from settings
        categories_to_grant = getattr(settings, "default_tool_categories", ["basic", "webtoon"])
        
        # Build the list of tools to grant
        granted_tools = []
        for category in categories_to_grant:
            if category in tool_categories:
                granted_tools.extend(tool_categories[category])
        
        # Grant the permissions
        if granted_tools:
            tool_handler.grant_permissions(client_id, granted_tools)
            logger.info(f"Granted tool permissions for client {client_id}: {', '.join(granted_tools)}")
        else:
            logger.warning(f"No tool permissions granted for client {client_id}")
            
    except Exception as e:
        logger.error(f"Error setting up tool permissions: {str(e)}", exc_info=True)
        # Don't fail the connection, just log the error and continue with no permissions
        logger.warning("Continuing with no tool permissions due to error")


# Message handler implementations would go here if needed
# These have been moved to their respective handler classes (e.g., ChatHandler)

async def handle_websocket_message(
    client_id: str, 
    message: Dict[str, Any], 
    connection_manager,
    chat_handler
) -> None:
    """Handle incoming WebSocket messages by delegating to the appropriate handler.
    
    This is a compatibility layer that can be used to gradually migrate from the old
    message handling system to the new handler-based approach.
    
    Args:
        client_id: Unique identifier for the client
        message: The decoded message from the client
        connection_manager: WebSocket connection manager instance
        chat_handler: ChatHandler instance for chat-related operations
    """
    logger.warning(
        "handle_websocket_message is deprecated. Use handler.handle_message() directly."
    )
    await chat_handler.handle_message(client_id, message)
