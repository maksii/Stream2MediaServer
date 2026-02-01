"""Animeon provider implementation.

API: search /api/anime/search?text= ; anime /api/anime/{id} ;
details /api/player/{id}/translations + /api/player/{id}/episodes ;
player https://animeon.club/anime/{id}
"""

from ..models.series import Series, group_series_by_studio
from ..processors.covertor_manager import ConvertorManager
from ..processors.m3u8_manager import M3U8Manager
from ..processors.request_manager import RequestManager
from ..processors.search_manager import SearchManager
from ..providers.provider_base import ProviderBase
from ..utils.logger import logger


def _animeon_extract_id(url: str) -> str | None:
    """Extract anime id from API URL (api/anime/7326) or player URL (anime/7326)."""
    url = url.rstrip("/")
    parts = url.split("/")
    if not parts:
        return None
    candidate = parts[-1]
    return candidate if candidate.isdigit() else None


class AnimeonProvider(ProviderBase):
    def __init__(self, config):
        super().__init__(config)
        self.provider = "animeon"
        self.provider_type = "api"
        self.base_url = "https://animeon.club"
        self.search_url = f"{self.base_url}/api/anime/search"
        self.headers = {
            "User-Agent": self.config.provider_config.user_agent,
            "Accept": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
        }

    def search_title(self, query):
        try:
            # Add required headers for the API
            search_headers = self.headers.copy()
            search_headers.update(
                {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}
            )

            # Pass the base search URL and let SearchManager handle the query
            results = SearchManager.search_movies(
                self.provider,
                query,
                self.base_url,
                self.search_url,  # Pass base search URL without query
                headers=search_headers,
            )

            logger.info(f"Found {len(results)} results for query: {query}")
            return results

        except Exception as e:
            logger.error(
                f"Search error for {self.provider} with query '{query}': {str(e)}"
            )
            return []

    def load_details_page(self, query):
        """Load details: GET /api/player/{id}/translations then /api/player/{id}/episodes. Episodes have direct videoUrl/fileUrl."""
        try:
            anime_id = _animeon_extract_id(query)
            if not anime_id:
                logger.error(f"Failed to extract anime ID from URL: {query}")
                return []

            translations_url = f"{self.base_url}/api/player/{anime_id}/translations"
            tr_response = RequestManager.get(translations_url, headers=self.headers)
            if not tr_response or not tr_response.ok:
                logger.error(f"Failed to fetch translations: {translations_url}")
                return []

            flat = []
            tr_data = tr_response.json()
            fallback_url = f"{self.base_url}/anime/{anime_id}"  # only for synthetic episodes when /episodes fails
            for item in tr_data.get("translations") or []:
                trans = item.get("translation") or {}
                trans_id = trans.get("id")
                trans_name = trans.get("name") or f"Translation {trans_id}"
                players = item.get("player") or []
                if not players:
                    continue
                first_player_id = players[0].get("id")
                episodes_url = (
                    f"{self.base_url}/api/player/{anime_id}/episodes"
                    f"?take=100&skip=-1&playerId={first_player_id}&translationId={trans_id}"
                )
                ep_response = RequestManager.get(episodes_url, headers=self.headers)
                if ep_response and ep_response.ok:
                    ep_data = ep_response.json()
                    for ep in ep_data.get("episodes") or []:
                        ep_num = ep.get("episode")
                        series_label = (
                            f"Серія {ep_num}"
                            if ep_num is not None
                            else f"Episode {ep.get('id', '')}"
                        )
                        ep_url = ep.get("videoUrl") or ep.get("fileUrl") or ""
                        if not ep_url:
                            continue
                        flat.append(
                            Series(
                                studio_id=str(trans_id),
                                studio_name=trans_name,
                                series=series_label,
                                url=ep_url,
                                provider=self.provider,
                            )
                        )
                else:
                    episodes_count = max((p.get("episodesCount") or 0) for p in players)
                    if episodes_count <= 0:
                        continue
                    for n in range(1, episodes_count + 1):
                        flat.append(
                            Series(
                                studio_id=str(trans_id),
                                studio_name=trans_name,
                                series=f"Серія {n}",
                                url=fallback_url,
                                provider=self.provider,
                            )
                        )
            return group_series_by_studio(flat)
        except Exception as e:
            logger.error(f"Error loading details for {query}: {str(e)}")
            return []

    def load_player_page(self, query):
        """Resolve to animeon.club/anime/{id} then fetch m3u8 from page."""
        try:
            aid = _animeon_extract_id(query)
            player_url = f"{self.base_url}/anime/{aid}" if aid else query
            m3u8_url = M3U8Manager.get_master_playlist(player_url, headers=self.headers)
            if m3u8_url:
                segment_files = M3U8Manager.download_series_content(m3u8_url)
                return segment_files
            logger.warning(f"No m3u8 URL found for {player_url}")
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

            logger.warning(
                f"Failed to retrieve or process the M3U8 URL for {series_url}"
            )
            return None

        except Exception as e:
            logger.error(f"Error finding segments for {series_url}: {str(e)}")
            return None

    def download_and_concatenate_series(
        self, segment_files, type, media_dir="media", filename="final_output"
    ):
        try:
            if not segment_files:
                logger.error("No segment files provided for concatenation")
                return None

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
                logger.error(f"Unsupported output type: {type}")
                return None

        except Exception as e:
            logger.error(f"Error concatenating segments: {str(e)}")
            return None
