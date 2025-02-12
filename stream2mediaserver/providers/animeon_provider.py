"""Animeon provider implementation."""

import time
from urllib.parse import quote
from ..processors.covertor_manager import ConvertorManager
from ..processors.m3u8_manager import M3U8Manager
from ..processors.search_manager import SearchManager
from ..providers.provider_base import ProviderBase
from ..utils.logger import logger


class AnimeonProvider(ProviderBase):
    def __init__(self, config):
        super().__init__(config)
        self.provider = "animeon"
        self.provider_type = "api"  # Changed from "dle" as this is a REST API
        self.base_url = "https://animeon.club"
        self.search_url = f"{self.base_url}/api/anime/search"
        self.details_url = f"{self.base_url}/api/anime"
        
        # Define headers specific to Animeon's API
        self.headers = {
            'User-Agent': self.config.provider_config.user_agent,
            'Accept': 'application/json',
            'Origin': self.base_url,
            'Referer': f"{self.base_url}/"
        }

    def search_title(self, query):
        try:
            # Add required headers for the API
            search_headers = self.headers.copy()
            search_headers.update({
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            # Pass the base search URL and let SearchManager handle the query
            results = SearchManager.search_movies(
                self.provider,
                query,
                self.base_url,
                self.search_url,  # Pass base search URL without query
                headers=search_headers
            )
            
            logger.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Search error for {self.provider} with query '{query}': {str(e)}")
            return []

    def load_details_page(self, query):
        try:
            # Extract anime ID from the API URL
            anime_id = query.split('/')[-1]
            if not anime_id:
                logger.error(f"Failed to extract anime ID from URL: {query}")
                return []
                
            details_url = f"{self.details_url}/{anime_id}"
            return SearchManager.get_series_page(self.provider, details_url, headers=self.headers)
            
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