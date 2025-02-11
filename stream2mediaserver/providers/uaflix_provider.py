"""UAFlix provider implementation."""

import time
from ..processors.covertor_manager import ConvertorManager
from ..processors.m3u8_manager import M3U8Manager
from ..processors.search_manager import SearchManager
from ..providers.provider_base import ProviderBase
from ..utils.logger import logger

class UaflixProvider(ProviderBase):
    def __init__(self, config):
        super().__init__(config)
        self.provider = "uaflix"
        self.provider_type = "dle"
        self.base_url = "https://uafix.net"  # Removed trailing slash
        self.search_url = f"{self.base_url}/index.php?do=search&subaction=search&story="
        self.playlist_url_template = f"{self.base_url}/engine/ajax/playlists.php"
        
        # Define headers for UAFlix
        self.headers = {
            'User-Agent': self.config.provider_config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url
        }

    def search_title(self, query):
        try:
            # UAFlix uses a simple GET request for search
            results = SearchManager.search_movies(
                self.provider,
                query,
                self.base_url,
                f"{self.search_url}{query}",
                headers=self.headers
            )
            
            logger.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Search error for {self.provider} with query '{query}': {str(e)}")
            return []

    def load_details_page(self, query):
        try:
            # Extract ID from URL and fetch series details
            news_id = SearchManager.extract_id_from_url(query)
            if not news_id:
                logger.error(f"Failed to extract ID from URL: {query}")
                return []
                
            timestamp = int(time.time())
            series_url = f"{self.playlist_url_template}?news_id={news_id}&xfield=playlist&time={timestamp}"
            return SearchManager.get_series_page(self.provider, series_url, headers=self.headers)
            
        except Exception as e:
            logger.error(f"Error loading details for {query}: {str(e)}")
            return []

    def load_player_page(self, query):
        try:
            # Load the master playlist for a series
            m3u8_url = M3U8Manager.get_master_playlist(query, headers=self.headers)
            if m3u8_url:
                segment_files = M3U8Manager.download_series_content(m3u8_url)
                return segment_files
            logger.warning(f"No m3u8 URL found for {query}")
            return None
        except Exception as e:
            logger.error(f"Error loading player page for {query}: {str(e)}")
            return None

    def find_segments_series(self, series_url):
        try:
            # Get the master playlist URL for the series
            m3u8_url = self.load_player_page(series_url)

            if m3u8_url:
                # Download the segment files
                segment_files = M3U8Manager.download_series_content(m3u8_url)
                return segment_files
            
            logger.warning(f"Failed to retrieve or process the M3U8 URL for {series_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding segments for {series_url}: {str(e)}")
            return None
        
    def download_and_concatenate_series(self, segment_files, type, media_dir='media', filename='final_output'):
        try:
            if not segment_files:
                logger.error("No segment files provided for concatenation")
                return None
                
            if type == 'ts':
                # Concatenate the segments into a single TS file
                return ConvertorManager.concatenate_segmens_ts(segment_files, media_dir, filename)
            elif type == 'mkv':
                # Optionally, concatenate into an MKV file
                return ConvertorManager.concatenate_segmens_mvk(segment_files, media_dir, filename)
            else:
                logger.error(f"Unsupported output type: {type}")
                return None
                
        except Exception as e:
            logger.error(f"Error concatenating segments: {str(e)}")
            return None