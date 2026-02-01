"""Main logic module for stream2mediaserver."""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib import import_module
from typing import Dict, Iterable, List, Optional, Type, Union

from .config import AppConfig, config as default_config
from .models.search_result import SearchResult
from .models.series import Series
from .providers.provider_base import ProviderBase
from .utils.logger import logger

# Provider mapping for dynamic loading
PROVIDER_MAPPING: Dict[str, str] = {
    "animeon_provider": "AnimeonProvider",
    "anitube_provider": "AnitubeProvider",
    "uakino_provider": "UakinoProvider",
    "uaflix_provider": "UaflixProvider",
}


class MainLogic:
    """Main logic class for handling media content operations."""

    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize MainLogic with configuration.

        Args:
            config: Optional custom configuration. Uses default if not provided.
        """
        self.config = config or default_config
        self._provider_classes: Dict[str, Type[ProviderBase]] = {}

    def get_provider_class(self, provider_name: str) -> Optional[Type[ProviderBase]]:
        """Get provider class by name.

        Args:
            provider_name: Name of the provider module

        Returns:
            Provider class if found, None otherwise
        """
        if provider_name in self._provider_classes:
            return self._provider_classes[provider_name]

        if provider_name not in PROVIDER_MAPPING:
            logger.error(f"Unknown provider: {provider_name}")
            return None

        class_name = PROVIDER_MAPPING[provider_name]
        try:
            module = import_module(f"stream2mediaserver.providers.{provider_name}")
            provider_class = getattr(module, class_name)
            self._provider_classes[provider_name] = provider_class
            return provider_class
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
        return await self._search_providers(query, self._enabled_providers())

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
            provider_name = getattr(item, "provider", None)
            if not provider_name:
                logger.error("Provider not found on item.")
                return False

            provider_class = self.get_provider_class(provider_name)
            if not provider_class:
                logger.error(f"Provider not found for {provider_name}")
                return False

            provider = provider_class(self.config)
            if isinstance(item, SearchResult):
                url = getattr(item, "url", None) or getattr(item, "link", None)
                if not url:
                    logger.error("Search result missing URL.")
                    return False
                series = await asyncio.to_thread(provider.load_details_page, url)
                if not series:
                    logger.error(f"Failed to load details for {url}")
                    return False
                if isinstance(series, list):
                    if not series:
                        logger.error(f"No series details found for {url}")
                        return False
                    item = series[0]
                else:
                    item = series

            from .processors.covertor_manager import ConvertorManager

            convertor = ConvertorManager(self.config)
            return await asyncio.to_thread(convertor.process, item)

        except Exception as e:
            logger.error(f"Error processing item {item.title}: {e}")
            return False

    def search_titles(self, provider_class, query):
        provider = provider_class(self.config)
        return provider.search_title(query)

    async def search_releases(self, query: str):
        return await self._search_providers(query, self._enabled_providers())

    async def search_releases_for_provider(self, provider_name: str, query: str):
        provider_names = [provider_name]
        return await self._search_providers(query, provider_names)

    def get_release_details(self, provider_name: str, release_url: str):
        provider_class = self.get_provider_class(provider_name)
        if provider_class:
            provider = provider_class(self.config)
            return provider.load_details_page(release_url)
        return None

    def get_details_for_all_releases(self, releases: List[Dict]):
        details = []
        with ThreadPoolExecutor() as executor:
            future_to_details = {
                executor.submit(
                    self.get_release_details, release["provider"], release["url"]
                ): release
                for release in releases
            }
            for future in as_completed(future_to_details):
                release = future_to_details[future]
                try:
                    details.append(future.result())
                except Exception as exc:
                    logger.error(
                        f"Error retrieving details for {release['url']}: {exc}"
                    )
        return details

    def _enabled_providers(self) -> List[str]:
        return [name for name, enabled in self.config.providers.items() if enabled]

    async def _search_providers(
        self, query: str, provider_names: Iterable[str]
    ) -> List[SearchResult]:
        tasks = [
            asyncio.to_thread(self._search_provider, provider_name, query)
            for provider_name in provider_names
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        combined: List[SearchResult] = []
        for provider_name, result in zip(provider_names, results):
            if isinstance(result, Exception):
                logger.error(f"{provider_name} generated an exception: {result}")
                continue
            combined.extend(result)
            logger.info(f"Results from {provider_name} received.")
        return combined

    def _search_provider(self, provider_name: str, query: str) -> List[SearchResult]:
        provider_class = self.get_provider_class(provider_name)
        if not provider_class:
            logger.error(f"Provider {provider_name} could not be loaded.")
            return []
        return self.search_titles(provider_class, query)


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
