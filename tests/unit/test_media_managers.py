import unittest
from types import SimpleNamespace

from stream2mediaserver.processors.m3u8_manager import M3U8Manager
from stream2mediaserver.processors.mp4_manager import MP4Manager


class MediaManagerUnitTests(unittest.TestCase):
    def test_get_best_quality_playlist_selects_highest_bandwidth(self):
        playlists = [
            SimpleNamespace(stream_info=SimpleNamespace(bandwidth=500), uri="low.m3u8"),
            SimpleNamespace(stream_info=SimpleNamespace(bandwidth=1500), uri="high.m3u8"),
            SimpleNamespace(stream_info=SimpleNamespace(bandwidth=1000), uri="mid.m3u8"),
        ]
        master = SimpleNamespace(playlists=playlists)

        best = M3U8Manager.get_best_quality_playlist(master)

        self.assertEqual(best.uri, "high.m3u8")

    def test_identify_best_quality_returns_highest_resolution_url(self):
        urls = [
            "[360p]http://example.com/360.mp4",
            "[720p]http://example.com/720.mp4",
            "[480p]http://example.com/480.mp4",
        ]

        best = MP4Manager.identify_best_quality(urls)

        self.assertEqual(best, "http://example.com/720.mp4")


if __name__ == "__main__":
    unittest.main()
