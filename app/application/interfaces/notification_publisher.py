"""
Notification publisher interface for application services.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.infrastructure.notifications.notification_types import NotificationType, NotificationPayload


class INotificationPublisher(ABC):
    """
    Interface for notification publishers in the application layer.
    This provides a clean abstraction over the infrastructure implementation.
    """
    
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


# Re-export the concrete implementation from infrastructure
from app.infrastructure.notifications.redis_publisher import RedisPublisher as RedisPublisher
from app.infrastructure.notifications.notification_types import NotificationType, NotificationPayload

__all__ = [
    'INotificationPublisher',
    'RedisPublisher',
    'NotificationType',
    'NotificationPayload',
]
