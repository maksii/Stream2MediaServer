import time
import requests
import re
from bs4 import BeautifulSoup
from ..processors.covertor_manager import ConvertorManager
from ..processors.m3u8_manager import M3U8Manager
from ..processors.search_manager import SearchManager
from ..providers.provider_base import ProviderBase
from ..utils.logger import logger


class UakinoProvider(ProviderBase):
    def __init__(self, config):
        super().__init__(config)
        self.provider = "uakino"
        self.provider_type = "dle"
        self.base_url = "https://uakino.me"
        self.search_url = f"{self.base_url}/engine/lazydev/dle_search/ajax.php"
        self.playlist_url_template = f"{self.base_url}/engine/ajax/playlists.php"

        # Define headers for UAKino
        self.headers = {
            "User-Agent": self.config.provider_config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": self.base_url,
        }

    def search_title(self, query):
        try:
            # Initialize session for cookie persistence
            session = requests.Session()
            session.headers.update(self.headers)

            # First, get the main page to establish session and cookies
            main_page = session.get(self.base_url)
            if not main_page.ok:
                logger.error(f"Failed to access main page: {main_page.status_code}")
                return []

            # Extract DLE hash from the main page
            soup = BeautifulSoup(main_page.text, "html.parser")
            script_text = soup.find("script", string=re.compile(r"var dle_login_hash"))
            dle_hash = None

            if script_text:
                match = re.search(r"var dle_login_hash = '(\w+)';", script_text.string)
                if match:
                    dle_hash = match.group(1)

            if not dle_hash:
                logger.warning(f"Failed to retrieve dle_login_hash for query: {query}")
                return []

            # Prepare search request with proper headers and cookies
            search_headers = self.headers.copy()
            search_headers.update(
                {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "Cookie": f"dle_hash={dle_hash}; {'; '.join(f'{k}={v}' for k, v in session.cookies.items())}",
                }
            )

            # Prepare search data
            search_data = {"query": query, "dle_login_hash": dle_hash}

            results = SearchManager.search_movies(
                self.provider,
                query,
                self.base_url,
                self.search_url,
                dle_hash,
                search_headers,
                search_data,
            )

            logger.info(f"Found {len(results)} results for query: {query}")
            return results

        except Exception as e:
            logger.error(
                f"Search error for {self.provider} with query '{query}': {str(e)}"
            )
            return []

    def load_details_page(self, query):
        try:
            # Extract ID from URL and fetch series details
            news_id = SearchManager.extract_id_from_url(query)
            if not news_id:
                logger.error(f"Failed to extract ID from URL: {query}")
                return []

            timestamp = int(time.time())
            series_url = f"{self.base_url}/engine/ajax/playlists.php?news_id={news_id}&xfield=playlist&time={timestamp}"
            return SearchManager.get_series_page(self.provider, series_url)
        except Exception as e:
            logger.error(f"Error loading details for {query}: {str(e)}")
            return []

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

    def download_and_concatenate_series(
        self, segment_files, type, media_dir="media", filename="final_output"
    ):
        if type == "ts":
            # Concatenate the segments into a single TS file
            return ConvertorManager.concatenate_segmens_ts(
                segment_files, media_dir, filename
            )
        elif type == "mkv":
            # Optionally, concatenate into an MKV file
            return ConvertorManager.concatenate_segmens_mvk(
                segment_files, media_dir, filename
            )
        else:
            return None
