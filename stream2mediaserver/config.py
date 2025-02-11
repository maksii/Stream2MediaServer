"""Configuration management for stream2mediaserver.

This module handles all configuration settings for the application, including
logging and provider settings.
"""

from dataclasses import dataclass
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

@dataclass
class AppConfig:
    """Main application configuration."""
    providers: Dict[str, bool] = None
    log_config: LogConfig = LogConfig()
    provider_config: ProviderConfig = ProviderConfig()

    def __post_init__(self):
        """Initialize default values."""
        if self.providers is None:
            self.providers = {
                "animeon": True,
                "anitube": True,
                "uaflix": True,
                "uakino": True
            }

# Global configuration instance
config = AppConfig() 