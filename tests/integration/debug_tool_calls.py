"""
Debug test for WebSocket Tool Call functionality
"""
import json
import sys
import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.websocket.handlers.tool_handler import get_tool_handler


def test_debug_tool_discovery():
    """Debug test for tool discovery functionality"""
    app = create_app()
    client = TestClient(app)
    
    print("\n=== DEBUG TEST: Tool Discovery ===")
    
    with client.websocket_connect("/ws") as websocket:
        # Skip connection established message
        welcome_msg = websocket.receive_text()
        print(f"Welcome message: {welcome_msg}")
        
        # Send tool discovery request
        print("Sending tool discovery request...")
        websocket.send_text(json.dumps({"type": "tool_discovery"}))
        
        # Should receive tools list
        data = websocket.receive_text()
        print(f"Raw response: {data}")
        
        try:
            response = json.loads(data)
            print(f"Response type: {response.get('type')}")
            print(f"Full response structure: {json.dumps(response, indent=2)}")
        except json.JSONDecodeError:
            print("Failed to parse JSON response")


def test_different_tool_call_formats():
    """Debug test for tool call with different message formats"""
    app = create_app()
    client = TestClient(app)
    
    formats_to_try = [
        # Format 1: direct tool_call
        {
            "type": "tool_call",
            "call_id": "debug_echo_1",
            "tool_id": "echo",
            "parameters": {"message": "Debug echo message"}
        },
        # Format 2: chat_message with tool_calls array
        {
            "type": "chat_message",
            "room_id": "debug_room",
            "message_id": "debug_chat_1",
            "content": "Using echo tool",
            "tool_calls": [{
                "tool_id": "echo",
                "parameters": {"message": "Debug echo from chat"}
            }]
        },
        # Format 3: structured message
        {
            "type": "message",
            "subtype": "tool_call",
            "call_id": "debug_echo_2",
            "tool_id": "echo",
            "parameters": {"message": "Debug echo structured"}
        }
    ]
    
    for i, message_format in enumerate(formats_to_try):
        print(f"\n=== DEBUG TEST: Echo Tool Call Format {i+1} ===")
        
        with client.websocket_connect("/ws") as websocket:
            # Skip connection established message
            welcome_msg = websocket.receive_text()
            print(f"Welcome message: {welcome_msg}")
            
            # Call the echo tool with this format
            print(f"Sending echo tool call with format {i+1}...")
            print(f"Message: {json.dumps(message_format)}")
            websocket.send_text(json.dumps(message_format))
            
            # Receive and parse response
            data = websocket.receive_text()
            print(f"Raw response: {data}")
            
            try:
                response = json.loads(data)
                print(f"Response type: {response.get('type')}")
                print(f"Full response structure: {json.dumps(response, indent=2)}")
            except json.JSONDecodeError:
                print("Failed to parse JSON response")


if __name__ == "__main__":
    test_debug_tool_discovery()
    test_different_tool_call_formats()
