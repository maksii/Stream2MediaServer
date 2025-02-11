import time
from stream2mediaserver.processors.covertor_manager import ConvertorManager
from stream2mediaserver.processors.m3u8_manager import M3U8Manager
from stream2mediaserver.processors.search_manager import SearchManager
from stream2mediaserver.providers.provider_base import ProviderBase


class UakinoProvider(ProviderBase):
    def __init__(self, config):
        super().__init__(config)
        self.provider = "uakino"
        self.provider_type = "dle"
        self.base_url = "https://uakino.me"
        self.search_url = f"{self.base_url}/engine/lazydev/dle_search/ajax.php"
        self.playlist_url_template = f"{self.base_url}/engine/ajax/playlists.php"
        
        # Add headers to config
        self.config['headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': self.base_url,
            'X-Requested-With': 'XMLHttpRequest'
        }


    def search_title(self, query):
        try:
            # Get dle_hash with headers
            dle_hash = SearchManager.get_dle_login_hash(self.provider, self.base_url, self.config.get('headers'))
            if not dle_hash:
                print("Failed to retrieve dle_login_hash")
                return []
                
            # Pass both dle_hash and headers
            return SearchManager.search_movies(
                self.provider, 
                query, 
                self.base_url, 
                self.search_url,
                dle_hash,
                self.config.get('headers')
            )
        except Exception as e:
            print(f"Search error for {self.provider}: {str(e)}")
            return []

    def load_details_page(self, query):
        # Extract ID from URL and fetch series details
        news_id = SearchManager.extract_id_from_url(query)
        timestamp = int(time.time())
        series_url = f"{self.base_url}/engine/ajax/playlists.php?news_id={news_id}&xfield=playlist&time={timestamp}"
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
            return ConvertorManager.concatenate_segmens_ts(segment_files, media_dir, filename)
        elif type == 'mkv':
        # Optionally, concatenate into an MKV file
            return ConvertorManager.concatenate_segmens_mvk(segment_files, media_dir, filename)
        else:
            return None