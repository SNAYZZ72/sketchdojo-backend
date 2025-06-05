# app/websocket/events.py
"""
WebSocket event definitions
"""
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass
class WebSocketEvent:
    """Base WebSocket event"""

    event_type: str
    timestamp: datetime
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        return {
            "type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            **self.data,
        }


@dataclass
class TaskProgressEvent(WebSocketEvent):
    """Task progress update event"""

    task_id: UUID
    progress_percentage: float
    current_operation: str

    @classmethod
    def create(
        cls,
        task_id: UUID,
        progress_percentage: float,
        current_operation: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        data = {
            "task_id": str(task_id),
            "progress_percentage": progress_percentage,
            "current_operation": current_operation,
        }
        if additional_data:
            data.update(additional_data)

        return cls(
            event_type="task_progress",
            timestamp=datetime.now(UTC),
            data=data,
            task_id=task_id,
            progress_percentage=progress_percentage,
            current_operation=current_operation,
        )


@dataclass
class TaskCompletedEvent(WebSocketEvent):
    """Task completion event"""

    task_id: UUID
    result_data: Dict[str, Any]

    @classmethod
    def create(cls, task_id: UUID, result_data: Dict[str, Any]):
        return cls(
            event_type="task_completed",
            timestamp=datetime.now(UTC),
            data={
                "task_id": str(task_id),
                "status": "completed",
                "result_data": result_data,
            },
            task_id=task_id,
            result_data=result_data,
        )


@dataclass
class TaskFailedEvent(WebSocketEvent):
    """Task failure event"""

    task_id: UUID
    error_message: str

    @classmethod
    def create(cls, task_id: UUID, error_message: str):
        return cls(
            event_type="task_failed",
            timestamp=datetime.now(UTC),
            data={
                "task_id": str(task_id),
                "status": "failed",
                "error_message": error_message,
            },
            task_id=task_id,
            error_message=error_message,
        )


@dataclass
class PanelGeneratedEvent(WebSocketEvent):
    """Panel generation event"""

    task_id: UUID
    panel_id: UUID
    image_url: str
    sequence_number: int

    @classmethod
    def create(
        cls,
        task_id: UUID,
        panel_id: UUID,
        image_url: str,
        sequence_number: int,
    ):
        return cls(
            event_type="panel_generated",
            timestamp=datetime.now(UTC),
            data={
                "task_id": str(task_id),
                "panel_id": str(panel_id),
                "image_url": image_url,
                "sequence_number": sequence_number,
            },
            task_id=task_id,
            panel_id=panel_id,
            image_url=image_url,
            sequence_number=sequence_number,
        )


@dataclass
class ToolDiscoveryEvent(WebSocketEvent):
    """Tool discovery event with available tools"""

    client_id: str
    tools: list

    @classmethod
    def create(cls, client_id: str, tools: list):
        return cls(
            event_type="tool_discovery",
            timestamp=datetime.now(UTC),
            data={
                "client_id": client_id,
                "tools": tools,
            },
            client_id=client_id,
            tools=tools,
        )


@dataclass
class ToolCallEvent(WebSocketEvent):
    """Tool call event for executing a tool"""

    client_id: str
    tool_id: str
    call_id: str
    message_id: Optional[str]
    parameters: Dict[str, Any]

    @classmethod
    def create(
        cls,
        client_id: str,
        tool_id: str,
        call_id: str,
        parameters: Dict[str, Any],
        message_id: Optional[str] = None,
    ):
        return cls(
            event_type="tool_call",
            timestamp=datetime.now(UTC),
            data={
                "client_id": client_id,
                "tool_id": tool_id,
                "call_id": call_id,
                "message_id": message_id,
                "parameters": parameters,
            },
            client_id=client_id,
            tool_id=tool_id,
            call_id=call_id,
            message_id=message_id,
            parameters=parameters,
        )


@dataclass
class ToolCallResultEvent(WebSocketEvent):
    """Tool call result event with execution results"""

    client_id: str
    tool_id: str
    call_id: str
    message_id: Optional[str]
    result: Any

    @classmethod
    def create(
        cls,
        client_id: str,
        tool_id: str,
        call_id: str,
        result: Any,
        message_id: Optional[str] = None,
    ):
        return cls(
            event_type="tool_call_result",
            timestamp=datetime.now(UTC),
            data={
                "client_id": client_id,
                "tool_id": tool_id,
                "call_id": call_id,
                "message_id": message_id,
                "result": result,
            },
            client_id=client_id,
            tool_id=tool_id,
            call_id=call_id,
            message_id=message_id,
            result=result,
        )


@dataclass
class ToolCallErrorEvent(WebSocketEvent):
    """Tool call error event"""

    client_id: str
    message_id: Optional[str]
    call_index: Optional[int]
    error_code: str
    error_message: str

    @classmethod
    def create(
        cls,
        client_id: str,
        error_code: str,
        error_message: str,
        message_id: Optional[str] = None,
        call_index: Optional[int] = None,
    ):
        return cls(
            event_type="tool_call_error",
            timestamp=datetime.now(UTC),
            data={
                "client_id": client_id,
                "message_id": message_id,
                "call_index": call_index,
                "error_code": error_code,
                "error_message": error_message,
            },
            client_id=client_id,
            message_id=message_id,
            call_index=call_index,
            error_code=error_code,
            error_message=error_message,
        )
