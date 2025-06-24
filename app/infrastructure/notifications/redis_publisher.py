"""
Redis-based notification publisher implementation.
"""
import json
import logging
from typing import Dict, Any, Optional

import redis

from app.infrastructure.notifications.interfaces import NotificationPublisher
from app.infrastructure.notifications.notification_types import NotificationType, NotificationPayload

logger = logging.getLogger(__name__)


class RedisPublisher(NotificationPublisher):
    """Redis implementation of notification publisher for Celery workers (synchronous)."""
    
    def __init__(self, redis_url: str):
        """
        Initialize Redis publisher.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client = redis.Redis.from_url(redis_url)
        logger.info(f"Redis publisher initialized with URL: {redis_url}")
    
    def publish(self, notification_type: NotificationType, payload: NotificationPayload) -> bool:
        """
        Publish a notification to Redis.
        
        Args:
            notification_type: The type of notification to publish
            payload: The notification payload data
            
        Returns:
            bool: True if the notification was successfully published
        """
        try:
            # Create a message with metadata
            message = {
                "type": notification_type,
                "payload": payload,
            }
            
            # Serialize the message to JSON
            serialized_message = json.dumps(message)
            
            # Publish to the notification-specific channel
            subscriber_count = self.client.publish(notification_type, serialized_message)
            
            if subscriber_count > 0:
                logger.info(f"Published {notification_type} notification to {subscriber_count} subscribers")
            else:
                logger.warning(f"No subscribers for {notification_type} notification")
                
            return True
        except Exception as e:
            logger.error(f"Failed to publish {notification_type} notification: {str(e)}")
            return False


def get_redis_publisher(redis_url: Optional[str] = None) -> RedisPublisher:
    """
    Get a configured Redis publisher.
    
    Args:
        redis_url: Optional Redis URL override
        
    Returns:
        RedisPublisher: Configured publisher instance
    """
    if redis_url is None:
        # Import here to avoid circular imports
        from app.config import get_settings
        settings = get_settings()
        redis_url = getattr(settings, "redis_url", "redis://redis:6379/0")
    
    return RedisPublisher(redis_url)
