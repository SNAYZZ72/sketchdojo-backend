"""
Debug script for testing chat message with tool calls
"""
import json
import time
import sys
from fastapi.testclient import TestClient

from app.main import create_app


def test_chat_with_tool_call():
    """Debug test for chat message with tool call"""
    app = create_app()
    client = TestClient(app)
    
    print("\n=== DEBUG TEST: Chat Message with Tool Call ===", file=sys.stderr)
    
    with client.websocket_connect("/ws") as websocket:
        # Skip connection established message
        welcome_text = websocket.receive_text()
        print(f"Raw welcome message: {welcome_text}", file=sys.stderr)
        welcome_msg = json.loads(welcome_text)
        print(f"Welcome message: {welcome_msg}", file=sys.stderr)
        client_id = welcome_msg.get('client_id')
        print(f"Client ID: {client_id}", file=sys.stderr)
        
        # First join a chat room
        room_id = "debug_room_1"
        join_message = {
            "type": "join_chat_room",
            "room_id": room_id
        }
        print(f"Sending join room message: {json.dumps(join_message)}", file=sys.stderr)
        websocket.send_text(json.dumps(join_message))
        
        # Receive room join confirmation
        join_text = websocket.receive_text()
        print(f"Raw join response: {join_text}", file=sys.stderr)
        join_response = json.loads(join_text)
        print(f"Parsed join response: {join_response}", file=sys.stderr)
        
        # Try both formats
        formats = [
            # Format 1: With text field
            {
                "type": "chat_message",
                "room_id": room_id,
                "message_id": "debug_msg_1",
                "text": "Test message with echo tool",
                "tool_calls": [
                    {
                        "tool_id": "echo",
                        "parameters": {
                            "message": "Echo this debug message"
                        }
                    }
                ]
            },
            # Format 2: With content field
            {
                "type": "chat_message",
                "room_id": room_id,
                "message_id": "debug_msg_2",
                "content": "Test message with echo tool",
                "tool_calls": [
                    {
                        "tool_id": "echo",
                        "parameters": {
                            "message": "Echo this debug message 2"
                        }
                    }
                ]
            },
        ]
        
        for i, message in enumerate(formats):
            print(f"\nTrying format {i+1}: {json.dumps(message)}", file=sys.stderr)
            websocket.send_text(json.dumps(message))
            
            try:
                # First response - should be chat broadcast
                response1_text = websocket.receive_text()
                print(f"Raw response 1: {response1_text}", file=sys.stderr)
                response1 = json.loads(response1_text)
                print(f"Parsed response 1: {json.dumps(response1)}", file=sys.stderr)
                
                # Second response - should be tool result
                response2_text = websocket.receive_text()
                print(f"Raw response 2: {response2_text}", file=sys.stderr)
                response2 = json.loads(response2_text)
                print(f"Parsed response 2: {json.dumps(response2)}", file=sys.stderr)
            except Exception as e:
                print(f"Error receiving responses: {str(e)}", file=sys.stderr)


if __name__ == "__main__":
    test_chat_with_tool_call()
