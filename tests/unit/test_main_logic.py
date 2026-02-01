import unittest
from types import SimpleNamespace
from unittest.mock import patch

from stream2mediaserver.config import AppConfig
from stream2mediaserver.main_logic import MainLogic
from stream2mediaserver.models.search_result import SearchResult
from stream2mediaserver.models.series import Series


class FakeProvider:
    def __init__(self, config):
        self.config = config

    def search_title(self, query):
        result = SearchResult(
            link="http://example.com/item",
            image_url="",
            title="Test",
            title_eng="",
            provider="fake",
        )
        result.url = result.link
        return [result]

    async def load_details_page(self, url):
        return Series(studio_id="1", studio_name="Studio", series="Episode 1", url=url)


class FakeConvertor:
    def __init__(self, config):
        self.config = config

    async def process(self, item):
        return True


class MainLogicUnitTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_aggregates_provider_results(self):
        config = AppConfig(providers={"fake_provider": True})
        logic = MainLogic(config)

        with patch.object(MainLogic, "get_provider_class", return_value=FakeProvider):
            results = await logic.search("query")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Test")

    async def test_process_item_with_search_result_loads_details(self):
        config = AppConfig(providers={"fake_provider": True})
        logic = MainLogic(config)
        item = SearchResult(
            link="http://example.com/item",
            image_url="",
            title="Test",
            title_eng="",
            provider="fake_provider",
        )
        item.url = item.link

        with (
            patch.object(MainLogic, "get_provider_class", return_value=FakeProvider),
            patch(
                "stream2mediaserver.processors.covertor_manager.ConvertorManager",
                FakeConvertor,
            ),
        ):
            result = await logic.process_item(item)

        self.assertTrue(result)

    async def test_process_item_with_series_skips_details_lookup(self):
        config = AppConfig(providers={"fake_provider": True})
        logic = MainLogic(config)
        series = Series(
            studio_id="1",
            studio_name="Studio",
            series="Episode 1",
            url="http://example.com",
        )
        series.provider = "fake_provider"
        series.title = "Episode 1"

        with (
            patch.object(MainLogic, "get_provider_class", return_value=FakeProvider),
            patch(
                "stream2mediaserver.processors.covertor_manager.ConvertorManager",
                FakeConvertor,
            ),
        ):
            result = await logic.process_item(series)

        self.assertTrue(result)

    async def test_process_item_rejects_unknown_type(self):
        logic = MainLogic(AppConfig())

        with self.assertRaises(ValueError):
            await logic.process_item(SimpleNamespace())


if __name__ == "__main__":
    unittest.main()
