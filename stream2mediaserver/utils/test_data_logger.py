"""Utilities for dumping provider response data."""

from __future__ import annotations

import contextlib
import contextvars
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

import requests


_provider_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "test_data_provider", default="unknown"
)
_test_case_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "test_data_case", default="unspecified"
)
_action_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "test_data_action", default="response"
)


class TestDataLogger:
    """Tracks and writes HTTP responses for debug runs."""

    enabled = False
    base_dir = Path("data/test_data")

    @classmethod
    def configure(cls, base_dir: Optional[Path] = None, enabled: bool = True) -> None:
        if base_dir is not None:
            cls.base_dir = base_dir
        cls.enabled = enabled

    @classmethod
    @contextlib.contextmanager
    def context(cls, provider: str, test_case: str, action: str) -> Iterator[None]:
        provider_token = _provider_var.set(cls._sanitize(provider))
        test_case_token = _test_case_var.set(cls._sanitize(test_case))
        action_token = _action_var.set(cls._sanitize(action))
        try:
            yield
        finally:
            _provider_var.reset(provider_token)
            _test_case_var.reset(test_case_token)
            _action_var.reset(action_token)

    @classmethod
    def log_response(
        cls, response: Optional[requests.Response], error: Optional[str] = None
    ) -> None:
        if not cls.enabled or response is None:
            return
        cls.base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%d%m%Y%H%M%S")
        provider = _provider_var.get()
        test_case = _test_case_var.get()
        action = _action_var.get()
        extension = cls._extension_for_response(response)
        filename = f"{provider}_{test_case}_{action}.{timestamp}.{extension}"
        target_path = cls.base_dir / filename
        try:
            target_path.write_bytes(response.content or b"")
        except OSError:
            return
        meta_path = target_path.with_suffix(f"{target_path.suffix}.meta.json")
        metadata = {
            "url": response.url,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "error": error,
        }
        try:
            meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
        except OSError:
            return

    @staticmethod
    def _extension_for_response(response: requests.Response) -> str:
        content_type = response.headers.get("Content-Type", "")
        if "json" in content_type:
            return "json"
        if "html" in content_type:
            return "html"
        if "xml" in content_type:
            return "xml"
        return "txt"

    @staticmethod
    def _sanitize(value: str) -> str:
        cleaned = "".join(char if char.isalnum() else "_" for char in value)
        cleaned = cleaned.strip("_").lower()
        return cleaned or "unknown"
