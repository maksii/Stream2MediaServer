"""Stream2MediaServer - Content search package.

This package provides functionality to search and retrieve content information
from various streaming providers.
"""

from .config import AppConfig, config
from .main_logic import MainLogic
from .models.search_result import SearchResult
from .models.series import Series

__version__ = "0.2.0"

__all__ = [
    "AppConfig",
    "config",
    "MainLogic",
    "SearchResult",
    "Series",
]
