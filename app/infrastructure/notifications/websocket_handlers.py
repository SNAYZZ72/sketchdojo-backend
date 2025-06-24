"""
WebSocket handlers for the notification system.

This module connects the notification system to the WebSocket connection manager.
"""
import logging
from typing import Dict, Any

from app.infrastructure.notifications.notification_types import (
    NotificationType, 
    TaskProgressPayload,
    WebtoonUpdatedPayload,
    TaskCompletedPayload,
    TaskFailedPayload
)
from app.websocket.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class WebSocketNotificationHandler:
    """Handler for mapping notifications to WebSocket broadcasts."""
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize the handler.
        
        Args:
            connection_manager: WebSocket connection manager instance
        """
        self.connection_manager = connection_manager
        logger.info("WebSocket notification handler initialized")
    
    async def handle_task_progress(self, payload: TaskProgressPayload) -> None:
        """
        Handle task progress notification.
        
        Args:
            payload: Task progress notification payload
        """
        task_id = payload["task_id"]
        progress = payload["progress"]
        message = payload["message"]
        
        logger.info(f"Forwarding task progress to WebSocket clients: {task_id}, {progress}%, {message}")
        await self.connection_manager.broadcast_generation_progress(task_id, progress, message)
    
    async def handle_webtoon_updated(self, payload: WebtoonUpdatedPayload) -> None:
        """
        Handle webtoon updated notification.
        
        Args:
            payload: Webtoon updated notification payload
        """
        logger.info(f"WEBTOON_UPDATED handler received payload: {payload}")
        
        # Check if required fields are present
        if "task_id" not in payload:
            logger.error(f"Missing task_id in webtoon update notification: {payload}")
            return
            
        if "webtoon_id" not in payload:
            logger.error(f"Missing webtoon_id in webtoon update notification: {payload}")
            return
            
        if "html_content" not in payload:
            logger.error(f"Missing html_content in webtoon update notification: {payload}")
            return
            
        task_id = payload["task_id"]
        webtoon_id = payload["webtoon_id"]
        html_content = payload["html_content"]
        
        # Check current task subscriptions
        task_subscriptions = self.connection_manager.task_subscriptions
        logger.info(f"Current task subscriptions: {task_subscriptions}")
        
        logger.info(f"Forwarding webtoon update to WebSocket clients: webtoon_id={webtoon_id}, task_id={task_id}, html_content_length={len(html_content)}")
        await self.connection_manager.broadcast_webtoon_updated(webtoon_id, html_content, task_id=task_id)
        
        # Log the success for verification
        client_count = len(self.connection_manager.task_subscriptions.get(task_id, set()))
        logger.info(f"Broadcast webtoon update for {webtoon_id} to {client_count} clients")
    
    async def handle_task_completed(self, payload: TaskCompletedPayload) -> None:
        """
        Handle task completed notification.
        
        Args:
            payload: Task completed notification payload
        """
        task_id = payload["task_id"]
        result = payload["result"]
        webtoon_id = payload.get("webtoon_id")
        
        logger.info(f"Forwarding task completion to WebSocket clients: {task_id}")
        await self.connection_manager.broadcast_generation_completed(task_id, result, webtoon_id=webtoon_id)
    
    async def handle_task_failed(self, payload: TaskFailedPayload) -> None:
        """
        Handle task failed notification.
        
        Args:
            payload: Task failed notification payload
        """
        task_id = payload["task_id"]
        error = payload["error"]
        
        logger.info(f"Forwarding task failure to WebSocket clients: {task_id}")
        await self.connection_manager.broadcast_generation_failed(task_id, error)


async def register_websocket_handlers(subscriber, connection_manager: ConnectionManager) -> None:
    """
    Register WebSocket handlers with the notification subscriber.
    
    Args:
        subscriber: The notification subscriber
        connection_manager: WebSocket connection manager
    """
    logger.info("Registering WebSocket notification handlers")
    handler = WebSocketNotificationHandler(connection_manager)
    
    # Register handlers for each notification type
    await subscriber.register_handler(
        NotificationType.TASK_PROGRESS, 
        handler.handle_task_progress
    )
    
    await subscriber.register_handler(
        NotificationType.WEBTOON_UPDATED, 
        handler.handle_webtoon_updated
    )
    
    await subscriber.register_handler(
        NotificationType.TASK_COMPLETED, 
        handler.handle_task_completed
    )
    
    await subscriber.register_handler(
        NotificationType.TASK_FAILED, 
        handler.handle_task_failed
    )
    
    logger.info("WebSocket notification handlers registered")
