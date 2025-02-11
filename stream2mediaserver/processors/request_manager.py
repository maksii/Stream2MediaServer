"""HTTP request management module."""

import requests
from ..utils.logger import logger

class RequestManager:
    """Handles HTTP requests with proper error handling and logging."""

    # Default headers defined at the class level
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    @classmethod
    def get(cls, url: str, params=None, headers=None) -> requests.Response:
        """Perform a GET request.
        
        Args:
            url: Target URL
            params: Optional query parameters
            headers: Optional custom headers
            
        Returns:
            Response object if successful, None otherwise
        """
        if headers is None:
            headers = cls.DEFAULT_HEADERS
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"GET request failed for {url}: {str(e)}")
            return None

    @classmethod
    def post(cls, url: str, data=None, headers=None) -> requests.Response:
        """Perform a POST request.
        
        Args:
            url: Target URL
            data: Optional POST data
            headers: Optional custom headers
            
        Returns:
            Response object if successful, None otherwise
        """
        if headers is None:
            headers = cls.DEFAULT_HEADERS
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"POST request failed for {url}: {str(e)}")
            return None