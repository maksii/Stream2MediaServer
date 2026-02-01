"""Base provider module for stream2mediaserver."""

from abc import ABC, abstractmethod
from typing import List, Optional
from urllib.parse import urljoin

from ..config import AppConfig
from ..models.search_result import SearchResult
from ..models.series import SeriesGroup


class ProviderBase(ABC):
    """Abstract base class for content providers.

    All content providers must inherit from this class and implement
    its abstract methods.
    """

    def __init__(self, config: AppConfig):
        """Initialize the provider.

        Args:
            config: Application configuration instance
        """
        self.config = config
        self._base_url: str = ""
        self._dle_login_hash: Optional[str] = None

    @property
    def base_url(self) -> str:
        """Get the base URL for the provider.

        Returns:
            The base URL string
        """
        return self._base_url

    @base_url.setter
    def base_url(self, value: str) -> None:
        """Set the base URL for the provider.

        Args:
            value: The base URL string
        """
        self._base_url = value.rstrip("/")

    @property
    def dle_login_hash(self) -> Optional[str]:
        """Get the DLE login hash.

        Returns:
            The DLE login hash if available, None otherwise
        """
        return self._dle_login_hash

    @dle_login_hash.setter
    def dle_login_hash(self, value: Optional[str]) -> None:
        """Set the DLE login hash.

        Args:
            value: The DLE login hash string
        """
        self._dle_login_hash = value

    def build_url(self, path: str) -> str:
        """Build a full URL from a path.

        Args:
            path: The path to append to the base URL

        Returns:
            The complete URL
        """
        return urljoin(self.base_url, path.lstrip("/"))

    @abstractmethod
    def search_title(self, query: str) -> List[SearchResult]:
        """Search for titles matching the query.

        Args:
            query: Search query string

        Returns:
            List of search results

        Raises:
            NotImplementedError: If the provider hasn't implemented this method
        """
        raise NotImplementedError("Providers must implement search_title")

    @abstractmethod
    def load_details_page(self, url: str) -> Optional[List[SeriesGroup]]:
        """Load detailed information about a series, grouped by studio (dubbing).

        Args:
            url: URL of the series details page

        Returns:
            List of SeriesGroup (studio + episodes) if successful, None or empty list otherwise

        Raises:
            NotImplementedError: If the provider hasn't implemented this method
        """
        raise NotImplementedError("Providers must implement load_details_page")

    @abstractmethod
    def load_player_page(self, url: str) -> Optional[str]:
        """Load the video player page and extract the video URL.

        Args:
            url: URL of the player page

        Returns:
            Video URL if successful, None otherwise

        Raises:
            NotImplementedError: If the provider hasn't implemented this method
        """
        raise NotImplementedError("Providers must implement load_player_page")
