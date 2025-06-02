# app/infrastructure/external/http_client.py
"""
HTTP client utilities for external API calls
"""
import logging
from typing import Any, Dict, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class HTTPClient:
    """Async HTTP client with retry logic"""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def post(
        self,
        url: str,
        json_data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a POST request with retry logic"""
        if not self._client:
            raise RuntimeError(
                "HTTP client not initialized. Use within async context manager."
            )

        try:
            response = await self._client.post(url, json=json_data, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HTTP POST error for {url}: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a GET request with retry logic"""
        if not self._client:
            raise RuntimeError(
                "HTTP client not initialized. Use within async context manager."
            )

        try:
            response = await self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HTTP GET error for {url}: {str(e)}")
            raise
