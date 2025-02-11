"""Main logic module for stream2mediaserver.

This module handles the core functionality of searching and processing media content
from various providers. It implements dynamic provider loading and concurrent operations
for efficient content retrieval.
"""

import concurrent.futures
from importlib import import_module
from typing import Dict, List, Optional, Type, Union

from .config import AppConfig, config as default_config
from .models.search_result import SearchResult
from .models.series import Series
from .providers.provider_base import ProviderBase
from .utils.logger import logger

# Provider mapping for dynamic loading
PROVIDER_MAPPING: Dict[str, str] = {
    "animeon_provider": "AnimeOnProvider",
    "anitube_provider": "AnitubeProvider",
    "uakino_provider": "UakinoProvider",
    "uaflix_provider": "UaflixProvider"
}

class MainLogic:
    """Main logic class for handling media content operations."""

    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize MainLogic with configuration.

        Args:
            config: Optional custom configuration. Uses default if not provided.
        """
        self.config = config or default_config
        self._provider_instances: Dict[str, ProviderBase] = {}

    def get_provider_class(self, provider_name: str) -> Optional[Type[ProviderBase]]:
        """Get provider class by name.

        Args:
            provider_name: Name of the provider module

        Returns:
            Provider class if found, None otherwise
        """
        if not provider_name in PROVIDER_MAPPING:
            logger.error(f"Unknown provider: {provider_name}")
            return None

        class_name = PROVIDER_MAPPING[provider_name]
        try:
            module = import_module(f"stream2mediaserver.providers.{provider_name}")
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load provider {provider_name}: {e}")
            return None

    async def search(self, query: str) -> List[SearchResult]:
        """Search for content across all enabled providers.

        Args:
            query: Search query string

        Returns:
            List of search results from all providers

        Raises:
            Exception: If search operation fails
        """
        results: List[SearchResult] = []
        enabled_providers = [name for name, enabled in self.config.providers.items() if enabled]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_provider = {}
            for provider_name in enabled_providers:
                provider_class = self.get_provider_class(provider_name)
                if provider_class:
                    provider = provider_class(self.config)
                    future = executor.submit(provider.search_title, query)
                    future_to_provider[future] = provider_name

            for future in concurrent.futures.as_completed(future_to_provider):
                provider_name = future_to_provider[future]
                try:
                    provider_results = future.result()
                    results.extend(provider_results)
                    logger.info(f"Received {len(provider_results)} results from {provider_name}")
                except Exception as e:
                    logger.error(f"Error searching {provider_name}: {e}")

        return results

    async def process_item(self, item: Union[SearchResult, Series]) -> bool:
        """Process a search result or series item.

        Args:
            item: SearchResult or Series object to process

        Returns:
            True if processing was successful, False otherwise

        Raises:
            ValueError: If item type is not supported
        """
        if not isinstance(item, (SearchResult, Series)):
            raise ValueError(f"Unsupported item type: {type(item)}")

        try:
            provider_class = self.get_provider_class(item.provider)
            if not provider_class:
                logger.error(f"Provider not found for {item.provider}")
                return False

            provider = provider_class(self.config)
            if isinstance(item, SearchResult):
                series = await provider.load_details_page(item.url)
                if not series:
                    logger.error(f"Failed to load details for {item.url}")
                    return False
                item = series

            from .processors.covertor_manager import ConvertorManager
            convertor = ConvertorManager(self.config)
            return await convertor.process(item)

        except Exception as e:
            logger.error(f"Error processing item {item.title}: {e}")
            return False

    def search_titles(self, provider_class, query):
        provider = provider_class(self.config)
        return provider.search_title(query)

    def search_releases(self, query: str):
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_provider = {}
            for provider_name in [name for name, enabled in self.config.providers.items() if enabled]:
                provider_class = self.get_provider_class(provider_name)
                if provider_class:
                    future = executor.submit(self.search_titles, provider_class, query)
                    future_to_provider[future] = provider_name
                else:
                    logger.error(f"Provider {provider_name} could not be loaded.")

            for future in concurrent.futures.as_completed(future_to_provider):
                provider_name = future_to_provider[future]
                try:
                    provider_results = future.result()
                    results.extend(provider_results)
                    logger.info(f"Results from {provider_name} received.")
                except Exception as exc:
                    logger.error(f"{provider_name} generated an exception: {exc}")
        return results

    def search_releases_for_provider(self, provider_name: str, query: str):
        provider_class = self.get_provider_class(provider_name)
        if provider_class:
            return self.search_titles(provider_class, query)
        return []

    def get_release_details(self, provider_name: str, release_url: str):
        provider_class = self.get_provider_class(provider_name)
        if provider_class:
            provider = provider_class(self.config)
            return provider.load_details_page(release_url)
        return None

    def get_details_for_all_releases(self, releases: List[Dict]):
        details = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_details = {
                executor.submit(self.get_release_details, release['provider'], release['url']): release 
                for release in releases
            }
            for future in concurrent.futures.as_completed(future_to_details):
                release = future_to_details[future]
                try:
                    details.append(future.result())
                except Exception as exc:
                    logger.error(f"Error retrieving details for {release['url']}: {exc}")
        return details

def add_release_by_url(config):
    pass

def add_release_by_name(config):
    pass
    
def update_release_by_name(config):
    pass
    
def update_releases(config):
    pass

def update_release(config):
    pass