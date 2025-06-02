"""
Rate limiting utilities
"""
import logging
import time
from collections import defaultdict, deque
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        # Store requests per client: client_id -> deque of timestamps
        self.clients: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, client_id: str, limit: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        client_requests = self.clients[client_id]

        # Remove expired requests
        while client_requests and client_requests[0] <= now - window_seconds:
            client_requests.popleft()

        # Check if under limit
        if len(client_requests) < limit:
            client_requests.append(now)
            return True

        return False

    def get_reset_time(self, client_id: str, window_seconds: int) -> Optional[float]:
        """Get when the rate limit resets for a client"""
        client_requests = self.clients.get(client_id)
        if not client_requests:
            return None

        return client_requests[0] + window_seconds

    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Clean up old entries to prevent memory leaks"""
        now = time.time()
        cutoff = now - max_age_seconds

        # Remove clients with no recent requests
        clients_to_remove = []
        for client_id, requests in self.clients.items():
            # Remove old requests
            while requests and requests[0] <= cutoff:
                requests.popleft()

            # If no requests left, mark for removal
            if not requests:
                clients_to_remove.append(client_id)

        # Remove empty clients
        for client_id in clients_to_remove:
            del self.clients[client_id]

        logger.debug(f"Rate limiter cleanup: removed {len(clients_to_remove)} clients")


# Global rate limiter instance
_rate_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get global rate limiter instance"""
    return _rate_limiter
