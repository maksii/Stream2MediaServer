import unittest

from stream2mediaserver.config import AppConfig
from stream2mediaserver.processors.request_manager import RequestManager
from stream2mediaserver.processors.search_manager import SearchManager
from stream2mediaserver.providers.animeon_provider import AnimeonProvider
from stream2mediaserver.providers.anitube_provider import AnitubeProvider
from stream2mediaserver.providers.uaflix_provider import UaflixProvider
from stream2mediaserver.providers.uakino_provider import UakinoProvider


class ProviderLiveIntegrationTests(unittest.TestCase):
    def _run_live_search(self, provider_cls, query):
        provider = provider_cls(AppConfig())
        response = RequestManager.get(provider.base_url, headers=provider.headers)
        if not response or not response.ok:
            self.skipTest(
                "Provider base URL not reachable; skipping live integration test."
            )

        results = SearchManager.search_movies(
            provider.provider,
            query,
            provider.base_url,
            provider.search_url,
            headers=provider.headers,
        )
        if not results:
            self.skipTest(
                "No results returned; provider may have changed or blocked the request."
            )

        self.assertTrue(results[0].title)
        self.assertTrue(results[0].link)

    def test_live_animeon_search(self):
        self._run_live_search(AnimeonProvider, "Anime")

    def test_live_anitube_search(self):
        self._run_live_search(AnitubeProvider, "Anime")

    def test_live_uaflix_search(self):
        self._run_live_search(UaflixProvider, "Anime")

    def test_live_uakino_search(self):
        self._run_live_search(UakinoProvider, "Anime")


if __name__ == "__main__":
    unittest.main()
