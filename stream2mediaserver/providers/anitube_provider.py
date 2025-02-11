"""Anitube provider implementation."""

import time
from ..processors.covertor_manager import ConvertorManager
from ..processors.m3u8_manager import M3U8Manager
from ..processors.search_manager import SearchManager
from ..providers.provider_base import ProviderBase
from ..utils.logger import logger

class AnitubeProvider(ProviderBase):
    def __init__(self, config):
        super().__init__(config)
        self.provider = "anitube"
        self.provider_type = "dle"
        self.base_url = "https://anitube.in.ua"
        self.search_url = f"{self.base_url}/engine/ajax/controller.php?mod=search"
        self.playlist_url_template = f"{self.base_url}/engine/ajax/playlists.php"
        
        # Define headers for Anitube
        self.headers = {
            'User-Agent': self.config.provider_config.user_agent,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': self.base_url,
            'Origin': self.base_url,
            'Connection': 'keep-alive'
        }

    def search_title(self, query):
        try:
            # Get dle_hash for search
            dle_hash = SearchManager.get_dle_login_hash(self.provider, self.base_url, self.headers)
            if not dle_hash:
                logger.warning(f"Failed to retrieve dle_login_hash for query: {query}")
                return []
                
            # Pass both dle_hash and headers with updated Content-Type
            search_headers = self.headers.copy()
            search_headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            
            # Anitube expects 'query' parameter instead of 'story'
            results = SearchManager.search_movies(
                self.provider,
                query,
                self.base_url,
                self.search_url,
                dle_hash,
                search_headers,
                form_data={'query': query, 'user_hash': dle_hash}  # Specific form data for Anitube
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
                
            # Get dle_hash for details page
            dle_hash = SearchManager.get_dle_login_hash(self.provider, self.base_url, self.headers)
            if not dle_hash:
                logger.error(f"Failed to get dle_hash for details page: {query}")
                return []
                
            series_url = f"{self.playlist_url_template}?news_id={news_id}&xfield=playlist&user_hash={dle_hash}"
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
                return ConvertorManager.concatenate_segments_ts(segment_files, media_dir, filename)
            elif type == 'mkv':
                # Optionally, concatenate into an MKV file
                return ConvertorManager.concatenate_segments_mvk(segment_files, media_dir, filename)
            else:
                logger.error(f"Unsupported output type: {type}")
                return None
                
        except Exception as e:
            logger.error(f"Error concatenating segments: {str(e)}")
            return None