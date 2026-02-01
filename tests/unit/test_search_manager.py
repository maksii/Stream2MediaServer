import unittest
from unittest.mock import patch

from stream2mediaserver.processors.search_manager import SearchManager


class FakeResponse:
    def __init__(self, text=None, json_data=None, ok=True):
        self.text = text or ""
        self._json_data = json_data or {}
        self.ok = ok

    def json(self):
        return self._json_data


class FakeSeries:
    def __init__(self, studio_id, studio_name, series, url, provider=None):
        self.studio_id = studio_id
        self.studio_name = studio_name
        self.series = series
        self.url = url
        self.provider = provider


class SearchManagerUnitTests(unittest.TestCase):
    def test_clean_text_normalizes_whitespace_and_entities(self):
        raw = "  Hello&nbsp;\nWorld\r\n"
        cleaned = SearchManager.clean_text(raw)
        self.assertEqual(cleaned, "Hello World")

    def test_extract_id_from_url_supports_slug_and_html(self):
        self.assertEqual(
            SearchManager.extract_id_from_url("https://site.com/1234-title"), "1234"
        )
        self.assertEqual(
            SearchManager.extract_id_from_url("https://site.com/987.html"), "987"
        )
        self.assertIsNone(SearchManager.extract_id_from_url("https://site.com/no-id"))

    @patch("stream2mediaserver.processors.search_manager.Series", FakeSeries)
    @patch("stream2mediaserver.processors.search_manager.RequestManager.get")
    def test_get_series_page_parses_uakino(self, mock_get):
        html_payload = (
            "<ul>"
            "<li data-id='1' data-file='//video.mp4' data-voice='Studio A'>Episode 1</li>"
            "</ul>"
        )
        mock_get.return_value = FakeResponse(json_data={"response": html_payload})

        series_list = SearchManager.get_series_page(
            "uakino", "https://uakino.me/series"
        )

        self.assertEqual(len(series_list), 1)
        self.assertEqual(series_list[0].studio_id, "1")
        self.assertEqual(series_list[0].studio_name, "Studio A")
        self.assertEqual(series_list[0].series, "Episode 1")
        self.assertEqual(series_list[0].url, "https://video.mp4")

    @patch("stream2mediaserver.processors.search_manager.Series", FakeSeries)
    @patch("stream2mediaserver.processors.search_manager.RequestManager.get")
    def test_get_series_page_parses_anitube(self, mock_get):
        html_payload = (
            "<li data-id='base'>Studio Base</li>"
            "<li data-id='base_1' data-file='http://video.mp4'>Episode 1</li>"
        )
        mock_get.return_value = FakeResponse(json_data={"response": html_payload})

        series_list = SearchManager.get_series_page(
            "anitube", "https://anitube.in.ua/series"
        )

        self.assertEqual(len(series_list), 1)
        self.assertEqual(series_list[0].studio_id, "base_1")
        self.assertEqual(series_list[0].studio_name, "Studio Base")
        self.assertEqual(series_list[0].series, "Episode 1")
        self.assertEqual(series_list[0].url, "http://video.mp4")


if __name__ == "__main__":
    unittest.main()
