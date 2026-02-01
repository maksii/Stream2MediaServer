"""Configuration management for stream2mediaserver.

This module handles all configuration settings for the application, including
logging and provider settings.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class LogConfig:
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[Path] = None


@dataclass
class ProviderConfig:
    """Provider-specific configuration settings."""

    timeout: int = 30
    max_retries: int = 3
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def default_providers() -> Dict[str, bool]:
    """Default provider configuration."""
    return {
        "animeon_provider": True,
        "anitube_provider": True,
        "uaflix_provider": True,
        "uakino_provider": True,
    }


@dataclass
class AppConfig:
    """Main application configuration."""

    providers: Dict[str, bool] = field(default_factory=default_providers)
    log_config: LogConfig = field(default_factory=LogConfig)
    provider_config: ProviderConfig = field(default_factory=ProviderConfig)


# Global configuration instance
config = AppConfig()
