
import time
from stream2mediaserver.processors.covertor_manager import ConvertorManager
from stream2mediaserver.processors.m3u8_manager import M3U8Manager
from stream2mediaserver.processors.search_manager import SearchManager
from stream2mediaserver.providers.provider_base import ProviderBase

class AnitubeProvider(ProviderBase):
    def __init__(self, config):
        super().__init__(config)
        self.provider = "anitube"
        self.provider_type = "dle"
        self.base_url = "https://anitube.in.ua"
        self.search_url = f"{self.base_url}/engine/ajax/controller.php?mod=search"
        self.playlist_url_template = f"{self.base_url}/engine/ajax/playlists.php"


    def search_title(self, query):
        # Conduct a search and return search results
        return SearchManager.search_movies(self.provider, query, self.base_url, self.search_url)

    def load_details_page(self, query):
        # Extract ID from URL and fetch series details
        news_id = SearchManager.extract_id_from_url(query)
        dle_hash = SearchManager.get_dle_login_hash(self.provider, self.base_url)
        series_url = f"{self.base_url}/engine/ajax/playlists.php?news_id={news_id}&xfield=playlist&user_hash={dle_hash}"
        return SearchManager.get_series_page(self.provider, series_url)

    def load_player_page(self, query):
        # Load the master playlist for a series
        m3u8_url = M3U8Manager.get_master_playlist(query)
        if m3u8_url:
            segment_files = M3U8Manager.download_series_content(m3u8_url)
            return segment_files
        return None

    def find_segments_series(self, series_url):
        # Get the master playlist URL for the series
        m3u8_url = self.load_player_page(series_url)

        if m3u8_url:
            # Download the segment files
            segment_files = M3U8Manager.download_series_content(m3u8_url)

            return segment_files
        else:
            print("Failed to retrieve or process the M3U8 URL.")
            return None
        
    def download_and_concatenate_series(self, segment_files, type, media_dir='media', filename='final_output'):
        
        if type == 'ts':
            # Concatenate the segments into a single TS file
            return ConvertorManager.concatenate_segments_ts(segment_files, media_dir, filename)
        elif type == 'mkv':
        # Optionally, concatenate into an MKV file
            return ConvertorManager.concatenate_segments_mvk(segment_files, media_dir, filename)
        else:
            return None