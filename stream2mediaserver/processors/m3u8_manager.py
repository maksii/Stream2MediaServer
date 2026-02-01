"""M3U8 playlist processing manager."""

import os
import re

import m3u8

from ..utils.logger import logger
from .request_manager import RequestManager


class M3U8Manager:
    def __init__(self):
        self.request_manager = RequestManager()

    @staticmethod
    def load_m3u8(url, headers=None):
        headers = (
            headers
            if headers is not None
            else {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
            }
        )
        return m3u8.load(url, headers=headers)

    @staticmethod
    def get_best_quality_playlist(master_m3u8):
        highest_bandwidth = 0
        highest_quality_playlist = None
        for playlist in master_m3u8.playlists:
            if playlist.stream_info.bandwidth > highest_bandwidth:
                highest_bandwidth = playlist.stream_info.bandwidth
                highest_quality_playlist = playlist
        return highest_quality_playlist

    @staticmethod
    def get_master_playlist(series_url):
        response = RequestManager.get(series_url)
        if response and response.ok:
            match = re.search(r'file:"(https[^"]+\.m3u8)"', response.text)
            if match:
                m3u8_url = match.group(1)
                logger.info("Found m3u8 URL: %s", m3u8_url)
                return m3u8_url
            logger.warning("No m3u8 URL found in the page.")
            return None
        logger.error("Failed to load the series page.")
        return None

    @staticmethod
    def download_series_content(m3u8_url):
        os.makedirs("media", exist_ok=True)

        master_m3u8 = M3U8Manager.load_m3u8(m3u8_url)
        highest_quality_playlist = M3U8Manager.get_best_quality_playlist(master_m3u8)

        if highest_quality_playlist is None:
            raise Exception("No available streams found in the playlist")

        playlist_m3u8 = M3U8Manager.load_m3u8(highest_quality_playlist.uri)
        segment_files = []

        for segment in playlist_m3u8.segments:
            segment_url = segment.absolute_uri
            file_name = os.path.join("media", segment_url.split("/")[-1])
            logger.info("Downloading %s to %s", segment_url, file_name)
            segment_files.append(file_name)
            response = RequestManager.get(segment_url)

            if response and response.ok:
                with open(file_name, "wb") as f:
                    f.write(response.content)
            else:
                logger.warning("Failed to download segment: %s", segment_url)

        logger.info("Download completed.")
        return segment_files
