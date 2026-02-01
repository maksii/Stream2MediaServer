import unittest
from unittest.mock import patch

from stream2mediaserver.config import AppConfig
from stream2mediaserver.main_logic import MainLogic
from stream2mediaserver.models.search_result import SearchResult
from stream2mediaserver.models.series import Series


class FakeProvider:
    def __init__(self, config):
        self.config = config
        self.provider = "fake_provider"

    def search_title(self, query):
        result = SearchResult(
            link="http://example.com/item",
            image_url="",
            title=f"Result for {query}",
            title_eng="",
            provider=self.provider,
        )
        result.url = result.link
        return [result]

    async def load_details_page(self, url):
        return Series(studio_id="1", studio_name="Studio", series="Episode 1", url=url)


class FakeConvertor:
    def __init__(self, config):
        self.config = config
        self.processed = []

    async def process(self, item):
        self.processed.append(item)
        return True


class FullFlowMockedIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_and_process_flow(self):
        config = AppConfig(providers={"fake_provider": True})
        logic = MainLogic(config)

        with (
            patch.object(MainLogic, "get_provider_class", return_value=FakeProvider),
            patch(
                "stream2mediaserver.processors.covertor_manager.ConvertorManager",
                FakeConvertor,
            ),
        ):
            results = await logic.search("Sample")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].provider, "fake_provider")

            processed = await logic.process_item(results[0])

        self.assertTrue(processed)


if __name__ == "__main__":
    unittest.main()
