"""HTTP request management module."""

import threading
import time
from typing import Dict, Optional
from urllib.parse import urlparse

# curl_cffi replicates a real Chrome TLS/JA3 fingerprint. Plain `requests` is
# fingerprinted and served a Cloudflare "Just a moment..." challenge (403) by
# uakino.best regardless of headers.
from curl_cffi import requests

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
    # Statuses worth another attempt: rate limits, and transient origin/CDN faults.
    RETRY_STATUSES = frozenset({429, 500, 502, 503, 504, 520, 521, 522, 524})
    MAX_RETRY_WAIT = 30.0
    _session = requests.Session(impersonate="chrome")
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
    def _retry_wait(cls, response, attempt: int) -> float:
        """Seconds to wait before retrying: server's Retry-After, else exponential backoff."""
        retry_after = response.headers.get("Retry-After") if response is not None else None
        if retry_after:
            try:
                # Retry-After is either delta-seconds or an HTTP-date; only the
                # former is worth honouring precisely, dates fall back to backoff.
                return min(float(retry_after), cls.MAX_RETRY_WAIT)
            except ValueError:
                pass
        return min(2.0**attempt, cls.MAX_RETRY_WAIT)

    @classmethod
    def _request(
        cls, method: str, url: str, headers: Optional[dict] = None, **kwargs
    ) -> Optional["requests.Response"]:
        """Perform an HTTP request, retrying rate limits and transient failures.

        Args:
            method: HTTP verb
            url: Target URL
            headers: Optional custom headers, merged over the browser defaults
            **kwargs: Passed through to the session (params, data)

        Returns:
            Response object if successful, None otherwise
        """
        merged_headers = cls._merge_headers(headers)
        attempts = max(1, config.provider_config.max_retries)
        for attempt in range(attempts):
            cls._throttle_host(url)
            last = attempt == attempts - 1
            try:
                response = cls._session.request(
                    method,
                    url,
                    headers=merged_headers,
                    timeout=config.provider_config.timeout,
                    **kwargs,
                )
                if not response.ok:
                    # Only rate limits and transient faults are worth a retry;
                    # a 404 or 403 will not become a 200 on the next attempt.
                    if response.status_code in cls.RETRY_STATUSES and not last:
                        wait = cls._retry_wait(response, attempt)
                        logger.warning(
                            f"{method} {url} returned {response.status_code}, "
                            f"retrying in {wait:.1f}s ({attempt + 1}/{attempts})"
                        )
                        time.sleep(wait)
                        continue
                    error = f"HTTP {response.status_code}"
                    TestDataLogger.log_response(response, error=error)
                    logger.error(f"{method} request failed for {url}: {error}")
                    return None
                TestDataLogger.log_response(response)
                return response
            except requests.exceptions.RequestException as e:
                if not last:
                    wait = cls._retry_wait(getattr(e, "response", None), attempt)
                    logger.warning(
                        f"{method} {url} failed ({e}), "
                        f"retrying in {wait:.1f}s ({attempt + 1}/{attempts})"
                    )
                    time.sleep(wait)
                    continue
                TestDataLogger.log_response(getattr(e, "response", None), error=str(e))
                logger.error(f"{method} request failed for {url}: {str(e)}")
        return None

    @classmethod
    def get(
        cls, url: str, params: Optional[dict] = None, headers: Optional[dict] = None
    ) -> Optional["requests.Response"]:
        """Perform a GET request. See _request."""
        return cls._request("GET", url, headers=headers, params=params)

    @classmethod
    def post(
        cls, url: str, data: Optional[dict] = None, headers: Optional[dict] = None
    ) -> Optional["requests.Response"]:
        """Perform a POST request. See _request."""
        return cls._request("POST", url, headers=headers, data=data)
