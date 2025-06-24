"""
Abstract interfaces for notification system.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Awaitable, Dict, List, Optional, Union

from app.infrastructure.notifications.notification_types import NotificationType, NotificationPayload


class NotificationPublisher(ABC):
    """Abstract base class for notification publishers."""
    
    @abstractmethod
    def publish(self, notification_type: NotificationType, payload: NotificationPayload) -> bool:
        """
        Publish a notification to the messaging system.
        
        Args:
            notification_type: The type of notification to publish
            payload: The notification payload data
            
        Returns:
            bool: True if the notification was successfully published
        """
        pass


class NotificationSubscriber(ABC):
    """Abstract base class for notification subscribers."""
    
    @abstractmethod
    async def subscribe(self, notification_types: List[NotificationType]) -> None:
        """
        Subscribe to specified notification types.
        
        Args:
            notification_types: List of notification types to subscribe to
        """
        pass
    
    @abstractmethod
    async def register_handler(
        self, 
        notification_type: NotificationType,
        handler: Callable[[NotificationPayload], Awaitable[None]]
    ) -> None:
        """
        Register a handler for a specific notification type.
        
        Args:
            notification_type: The notification type to handle
            handler: Async function to handle the notification
        """
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the subscriber."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the subscriber."""
        pass
