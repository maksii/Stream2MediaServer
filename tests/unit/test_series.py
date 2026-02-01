"""Unit tests for Series model and group_series_by_studio (multiple player URLs)."""
import unittest

from stream2mediaserver.models.series import Series, SeriesGroup, group_series_by_studio


class SeriesUnitTests(unittest.TestCase):
    def test_series_single_url_backward_compat(self):
        s = Series("1", "Studio", "1 серія", url="https://ashdi.vip/vod/227417", provider="animeon")
        self.assertEqual(s.urls, ["https://ashdi.vip/vod/227417"])
        self.assertEqual(s.url, "https://ashdi.vip/vod/227417")

    def test_series_multiple_urls(self):
        s = Series(
            "1",
            "РОБОТА ГОЛОСОМ",
            "1 серія",
            urls=[
                "https://ashdi.vip/vod/227417",
                "https://moonanime.art/iframe/rgijmwhdaefyjheee/",
            ],
            provider="animeon",
        )
        self.assertEqual(len(s.urls), 2)
        self.assertEqual(s.url, "https://ashdi.vip/vod/227417")

    def test_group_series_by_studio_merges_same_episode_multiple_players(self):
        flat = [
            Series("t1", "РОБОТА ГОЛОСОМ", "1 серія", url="https://ashdi.vip/vod/227417", provider="animeon"),
            Series("t1", "РОБОТА ГОЛОСОМ", "1 серія", url="https://moonanime.art/iframe/rgijmwhdaefyjheee/", provider="animeon"),
        ]
        groups = group_series_by_studio(flat)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0].episodes), 1)
        ep = groups[0].episodes[0]
        self.assertEqual(ep.series, "1 серія")
        self.assertEqual(len(ep.urls), 2)
        self.assertIn("https://ashdi.vip/vod/227417", ep.urls)
        self.assertIn("https://moonanime.art/iframe/rgijmwhdaefyjheee/", ep.urls)
        self.assertEqual(ep.url, "https://ashdi.vip/vod/227417")


if __name__ == "__main__":
    unittest.main()
