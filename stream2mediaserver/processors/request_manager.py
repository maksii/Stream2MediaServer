"""HTTP request management module."""

import threading
import time
from typing import Dict, Optional
from urllib.parse import urlparse

import requests

from ..config import config
from ..utils.logger import logger
from ..utils.test_data_logger import TestDataLogger


class RequestManager:
    """Handles HTTP requests with proper error handling and logging."""

    # Browser-simulation headers (Chrome-like) to reduce Cloudflare blocks
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    DEFAULT_TIMEOUT = config.provider_config.timeout
    _session = requests.Session()
    _last_request_by_host: Dict[str, float] = {}
    _host_lock = threading.Lock()

    @classmethod
    def _throttle_host(cls, url: str) -> None:
        """Wait if needed to respect minimum delay between requests to same host."""
        delay = config.provider_config.request_delay_seconds
        if delay <= 0:
            return
        try:
            parsed = urlparse(url)
            host = parsed.netloc or parsed.path
        except Exception:
            return
        with cls._host_lock:
            last = cls._last_request_by_host.get(host, 0)
            elapsed = time.monotonic() - last
            if elapsed < delay:
                sleep_time = delay - elapsed
                time.sleep(sleep_time)
            cls._last_request_by_host[host] = time.monotonic()

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
        cls._throttle_host(url)
        merged_headers = cls._merge_headers(headers)
        try:
            response = cls._session.get(
                url,
                headers=merged_headers,
                params=params,
                timeout=cls.DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            TestDataLogger.log_response(response)
            return response
        except requests.RequestException as e:
            TestDataLogger.log_response(getattr(e, "response", None), error=str(e))
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
        cls._throttle_host(url)
        merged_headers = cls._merge_headers(headers)
        try:
            response = cls._session.post(
                url,
                headers=merged_headers,
                data=data,
                timeout=cls.DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            TestDataLogger.log_response(response)
            return response
        except requests.RequestException as e:
            TestDataLogger.log_response(getattr(e, "response", None), error=str(e))
            logger.error(f"POST request failed for {url}: {str(e)}")
            return None
