"""HTTP request management module."""

from typing import Optional

import requests

from ..config import config
from ..utils.logger import logger


class RequestManager:
    """Handles HTTP requests with proper error handling and logging."""

    # Default headers defined at the class level
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    DEFAULT_TIMEOUT = config.provider_config.timeout
    _session = requests.Session()

    @classmethod
    def _merge_headers(cls, headers: Optional[dict]) -> dict:
        return {**cls.DEFAULT_HEADERS, **(headers or {})}

    @classmethod
    def get(
        cls, url: str, params: Optional[dict] = None, headers: Optional[dict] = None
    ) -> Optional[requests.Response]:
        """Perform a GET request.

        Args:
            url: Target URL
            params: Optional query parameters
            headers: Optional custom headers

        Returns:
            Response object if successful, None otherwise
        """
        merged_headers = cls._merge_headers(headers)
        try:
            response = cls._session.get(
                url,
                headers=merged_headers,
                params=params,
                timeout=cls.DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"GET request failed for {url}: {str(e)}")
            return None

    @classmethod
    def post(
        cls, url: str, data: Optional[dict] = None, headers: Optional[dict] = None
    ) -> Optional[requests.Response]:
        """Perform a POST request.

        Args:
            url: Target URL
            data: Optional POST data
            headers: Optional custom headers

        Returns:
            Response object if successful, None otherwise
        """
        merged_headers = cls._merge_headers(headers)
        try:
            response = cls._session.post(
                url,
                headers=merged_headers,
                data=data,
                timeout=cls.DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"POST request failed for {url}: {str(e)}")
            return None
