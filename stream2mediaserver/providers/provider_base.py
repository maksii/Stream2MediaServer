"""Base provider module for stream2mediaserver.

This module defines the abstract base class for all content providers.
Each provider must implement the abstract methods defined here.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from urllib.parse import urljoin

from ..config import AppConfig
from ..models.search_result import SearchResult
from ..models.series import Series
from ..utils.logger import logger

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
        self._base_url = value.rstrip('/')

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
        return urljoin(self.base_url, path.lstrip('/'))

    @abstractmethod
    async def search_title(self, query: str) -> List[SearchResult]:
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
    async def load_details_page(self, url: str) -> Optional[Series]:
        """Load detailed information about a series.
        
        Args:
            url: URL of the series details page
            
        Returns:
            Series object if successful, None otherwise
            
        Raises:
            NotImplementedError: If the provider hasn't implemented this method
        """
        raise NotImplementedError("Providers must implement load_details_page")

    @abstractmethod
    async def load_player_page(self, url: str) -> Optional[str]:
        """Load the video player page and extract the video URL.
        
        Args:
            url: URL of the player page
            
        Returns:
            Video URL if successful, None otherwise
            
        Raises:
            NotImplementedError: If the provider hasn't implemented this method
        """
        raise NotImplementedError("Providers must implement load_player_page")

    async def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[str]:
        """Make an HTTP request with error handling.
        
        Args:
            url: The URL to request
            method: HTTP method to use
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response text if successful, None otherwise
        """
        import aiohttp
        import async_timeout

        try:
            timeout = self.config.provider_config.timeout
            async with async_timeout.timeout(timeout):
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, **kwargs) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            logger.error(f"Request failed: {response.status} - {url}")
                            return None
        except Exception as e:
            logger.error(f"Request error: {e} - {url}")
            return None     