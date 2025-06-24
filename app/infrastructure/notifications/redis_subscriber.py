"""
Redis-based notification subscriber implementation for the FastAPI application.
"""
import asyncio
import json
import logging
from typing import Dict, Callable, Awaitable, List, Optional, Set

from redis.asyncio import Redis

from app.infrastructure.notifications.interfaces import NotificationSubscriber
from app.infrastructure.notifications.notification_types import NotificationType, NotificationPayload

logger = logging.getLogger(__name__)


class RedisSubscriber(NotificationSubscriber):
    """Redis implementation of notification subscriber for FastAPI (asynchronous)."""
    
    def __init__(self, redis_url: str):
        """
        Initialize Redis subscriber.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client = None
        self.pubsub = None
        self.handlers: Dict[NotificationType, List[Callable[[NotificationPayload], Awaitable[None]]]] = {}
        self.subscribed_channels: Set[NotificationType] = set()
        self.running = False
        self.listener_task = None
        logger.info(f"Redis subscriber initialized with URL: {redis_url}")
    
    async def subscribe(self, notification_types: List[NotificationType]) -> None:
        """
        Subscribe to specified notification types.
        
        Args:
            notification_types: List of notification types to subscribe to
        """
        logger.info(f"Attempting to subscribe to: {notification_types}")
        if not self.redis_client:
            logger.info(f"Creating new Redis client with URL: {self.redis_url}")
            self.redis_client = Redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
        
        # Track which channels we're subscribed to
        self.subscribed_channels.update(notification_types)
        
        # Subscribe to each channel
        await asyncio.gather(*[
            self.pubsub.subscribe(channel)
            for channel in notification_types
        ])
        
        logger.info(f"Subscribed to notification types: {', '.join(notification_types)}")
    
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
        if notification_type not in self.handlers:
            self.handlers[notification_type] = []
        
        self.handlers[notification_type].append(handler)
        logger.debug(f"Registered handler for {notification_type}")
        
        # Auto-subscribe if not already subscribed
        if notification_type not in self.subscribed_channels:
            await self.subscribe([notification_type])
    
    async def _message_listener(self) -> None:
        """Listen for messages and dispatch to handlers."""
        logger.info("Message listener started and running")
        logger.info(f"Currently subscribed to channels: {self.subscribed_channels}")
        try:
            while self.running:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                logger.info(f"Redis get_message result: {message is not None}")
                if message is not None:
                    try:
                        # Get channel name and message data
                        channel = message['channel'].decode('utf-8')
                        notification_type = NotificationType(channel)
                        
                        # Parse the message data
                        if message.get('data'):
                            data = json.loads(message['data'].decode('utf-8'))
                            payload = data.get('payload', {})
                            
                            # Log received notification with higher visibility
                            logger.info(f"Received {notification_type} notification: {payload}")
                            
                            # Call all registered handlers
                            if notification_type in self.handlers:
                                for handler in self.handlers[notification_type]:
                                    try:
                                        await handler(payload)
                                    except Exception as handler_error:
                                        logger.error(f"Error in {notification_type} handler: {str(handler_error)}")
                            else:
                                logger.warning(f"No handlers registered for {notification_type}")
                    except Exception as msg_error:
                        logger.error(f"Error processing notification: {str(msg_error)}")
                
                # Small sleep to prevent CPU overuse
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info("Notification listener task cancelled")
        except Exception as e:
            logger.error(f"Error in notification listener: {str(e)}")
            if self.running:
                # Restart the listener if it was unexpectedly terminated
                asyncio.create_task(self._restart_listener())
    
    async def _restart_listener(self) -> None:
        """Restart the message listener after a failure."""
        await asyncio.sleep(1)  # Brief delay before restart
        if self.running:
            logger.info("Restarting notification listener")
            self.listener_task = asyncio.create_task(self._message_listener())
    
    async def start(self) -> None:
        """Start the subscriber."""
        if self.running:
            logger.warning("Subscriber already running")
            return
            
        if not self.redis_client:
            self.redis_client = Redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            
            # Resubscribe to channels if needed
            if self.subscribed_channels:
                await asyncio.gather(*[
                    self.pubsub.subscribe(channel)
                    for channel in self.subscribed_channels
                ])
        
        self.running = True
        self.listener_task = asyncio.create_task(self._message_listener())
        logger.info("Redis notification listener started")
    
    async def stop(self) -> None:
        """Stop the subscriber."""
        if not self.running:
            logger.warning("Subscriber not running")
            return
            
        self.running = False
        
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
            self.listener_task = None
        
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("Redis notification subscriber stopped")


async def create_redis_subscriber(redis_url: Optional[str] = None) -> RedisSubscriber:
    """
    Create and initialize a Redis subscriber.
    
    Args:
        redis_url: Optional Redis URL override
        
    Returns:
        RedisSubscriber: Configured subscriber instance
    """
    if redis_url is None:
        # Import here to avoid circular imports
        from app.config import get_settings
        settings = get_settings()
        redis_url = getattr(settings, "redis_url", "redis://redis:6379/0")
    
    subscriber = RedisSubscriber(redis_url)
    return subscriber
