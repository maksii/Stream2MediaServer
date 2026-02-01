"""Search management module for content providers."""

import html
import re
from typing import List, Optional
from urllib.parse import quote, unquote, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from ..models.search_result import SearchResult
from ..models.series import Series
from ..utils.logger import logger
from .request_manager import RequestManager


class SearchManager:
    """Manages search operations across different content providers."""

    @staticmethod
    def get_dle_login_hash(
        provider: str, url: str, headers: Optional[dict] = None
    ) -> Optional[str]:
        """Get DLE login hash from the provider's page.

        Args:
            provider: Provider identifier
            url: Base URL of the provider
            headers: Optional request headers

        Returns:
            DLE login hash if found, None otherwise
        """
        response = RequestManager.get(url, headers=headers)
        if response and response.ok:
            soup = BeautifulSoup(response.text, "html.parser")
            script_text = soup.find("script", string=re.compile(r"var dle_login_hash"))
            if script_text:
                match = re.search(r"var dle_login_hash = '(\w+)';", script_text.string)
                if match:
                    return match.group(1)
        logger.warning(f"Failed to get DLE login hash for {provider}")
        return None

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        text = html.unescape(text)
        text = text.replace("\r", "").replace("\n", "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def search_movies(
        provider: str,
        query: str,
        base_url: str,
        search_url: str,
        dle_hash: Optional[str] = None,
        headers: Optional[dict] = None,
        form_data: Optional[dict] = None,
    ) -> List[SearchResult]:
        """Search for movies/series across providers.

        Args:
            provider: Provider identifier
            query: Search query
            base_url: Provider's base URL
            search_url: Search endpoint URL
            dle_hash: Optional DLE login hash
            headers: Optional request headers
            form_data: Optional form data for POST requests

        Returns:
            List of search results
        """
        if not dle_hash and provider != "animeon":
            dle_hash = SearchManager.get_dle_login_hash(provider, base_url, headers)
            if not dle_hash:
                logger.error(f"Failed to get DLE login hash for {provider}")
                return []

        encoded_query = quote(query)
        results = []

        try:
            if provider == "uakino":
                results = SearchManager._search_uakino(
                    encoded_query, dle_hash, search_url, headers, base_url
                )
            elif provider == "anitube":
                results = SearchManager._search_anitube(
                    encoded_query, dle_hash, search_url, headers, form_data
                )
            elif provider == "uaflix":
                results = SearchManager._search_uaflix(
                    encoded_query, search_url, headers
                )
            elif provider == "animeon":
                results = SearchManager._search_animeon(
                    encoded_query, search_url, headers
                )
        except Exception as e:
            logger.error(f"Error searching {provider}: {str(e)}")
            return []

        return results

    @staticmethod
    def _search_uakino(
        query: str,
        dle_hash: str,
        search_url: str,
        headers: Optional[dict],
        base_url: str,
    ) -> List[SearchResult]:
        """Search implementation for UAKino provider.

        Search POSTs to ajax.php with story, dle_hash, thisUrl (referrer path).
        Response is JSON with "content" = HTML fragment; each result is a.search-result-link.
        """
        parsed_base = urlparse(base_url)
        scheme, netloc = parsed_base.scheme or "https", parsed_base.netloc
        # story must be raw query so requests encodes as application/x-www-form-urlencoded (e.g. space -> +)
        form_data = {
            "story": unquote(query),
            "dle_hash": dle_hash,
            "thisUrl": "/index.php",
        }
        response = RequestManager.post(search_url, data=form_data, headers=headers)
        results = []
        if response and response.ok:
            soup = BeautifulSoup(response.json()["content"], "html.parser")
            for link in soup.find_all("a", class_="search-result-link"):
                url = unquote(link.get("href", ""))
                poster = unquote(link.img.get("src", "")) if link.img else ""
                if poster:
                    parsed_url = urlparse(poster)
                    if not parsed_url.netloc:
                        new_url = urlunparse(
                            parsed_url._replace(scheme=scheme, netloc=netloc)
                        )
                        poster = new_url
                name = link.find("span", class_="searchheading")
                name = SearchManager.clean_text(name.get_text()) if name else ""
                name_eng = link.find("span", class_="search-orig-title")
                name_eng = (
                    SearchManager.clean_text(name_eng.get_text()) if name_eng else ""
                )
                results.append(
                    SearchResult(
                        link=url,
                        image_url=poster,
                        title=name,
                        title_eng=name_eng,
                        provider="uakino",
                    )
                )
        return results

    @staticmethod
    def _search_anitube(
        query: str,
        dle_hash: str,
        search_url: str,
        headers: Optional[dict],
        form_data: Optional[dict],
    ) -> List[SearchResult]:
        """Search implementation for Anitube provider."""
        # For Anitube, we need to use the original query (with spaces) and let requests handle the encoding
        original_query = unquote(query)  # Convert back from %20 to spaces

        form_data = {
            "query": original_query,  # Will be properly encoded as + by requests
            "user_hash": dle_hash,
        }

        response = RequestManager.post(search_url, data=form_data, headers=headers)
        results = []
        if response and response.ok:
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", style="display: block;"):
                url = unquote(link.get("href", ""))
                poster = unquote(link.img.get("src", "")) if link.img else ""
                name = link.find("b", class_="searchheading_title")
                name = SearchManager.clean_text(name.get_text()) if name else ""
                results.append(
                    SearchResult(
                        link=url,
                        image_url=poster,
                        title=name,
                        title_eng="Not Specified",
                        provider="anitube",
                    )
                )
        return results

    @staticmethod
    def _search_uaflix(
        query: str, search_url: str, headers: Optional[dict]
    ) -> List[SearchResult]:
        """Search implementation for UAFlix provider."""
        response = RequestManager.get(search_url + quote(query), headers=headers)
        results = []
        if response and response.ok:
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", class_="sres-wrap clearfix"):
                url = unquote(link.get("href", ""))
                poster = unquote(link.find("img").get("src", ""))
                if not poster.startswith("http"):
                    poster = "https://uafix.net" + poster
                name = link.find("h2").get_text().split("/")[0].strip()
                name_eng = (
                    link.find("h2").get_text().split("/")[1].strip()
                    if "/" in link.find("h2").get_text()
                    else "Not Specified"
                )
                results.append(
                    SearchResult(
                        link=url,
                        image_url=poster,
                        title=name,
                        title_eng=name_eng,
                        provider="uaflix",
                    )
                )
        return results

    @staticmethod
    def _search_animeon(
        query: str, search_url: str, headers: Optional[dict]
    ) -> List[SearchResult]:
        """Search implementation for Animeon provider."""
        url = f"{search_url}?text={query}"
        response = RequestManager.get(url, headers=headers)
        results = []
        if response and response.ok:
            try:
                data = response.json()
                for item in data.get("result", []):
                    url = f"https://animeon.club/api/anime/{item['id']}"
                    poster = ""
                    if item.get("poster"):
                        poster = (
                            f"https://animeon.club/api/uploads/images/{item['poster']}"
                        )
                    elif item.get("image") and item["image"].get("original"):
                        poster = f"https://animeon.club/api/uploads/images/{item['image']['original']}"
                    elif item.get("image") and item["image"].get("preview"):
                        poster = f"https://animeon.club/api/uploads/images/{item['image']['preview']}"
                    results.append(
                        SearchResult(
                            link=url,
                            image_url=poster,
                            title=item.get("titleUa", ""),
                            title_eng=item.get("titleEn", ""),
                            provider="animeon",
                        )
                    )
            except ValueError as e:
                logger.error(f"Failed to parse JSON response from Animeon: {str(e)}")
        return results

    @staticmethod
    def get_series_page(
        provider: str, series_url: str, headers: Optional[dict] = None
    ) -> List[Series]:
        """Get series information from a provider's page.

        Args:
            provider: Provider identifier
            series_url: URL of the series page
            headers: Optional request headers

        Returns:
            List of series objects
        """
        response = RequestManager.get(series_url, headers=headers)
        if not response or not response.ok:
            logger.error(f"Failed to get series page from {provider}")
            return []

        try:
            if provider == "uakino":
                return SearchManager._parse_uakino_series(response, provider=provider)
            elif provider == "anitube":
                return SearchManager._parse_anitube_series(response, provider=provider)
            # UAFlix does not use playlists.php; use parse_uaflix_series_page_html on series page HTML
        except Exception as e:
            logger.error(f"Error parsing series page from {provider}: {str(e)}")

        return []

    @staticmethod
    def _parse_uakino_series(response, provider: str = "uakino") -> List[Series]:
        """Parse series information from UAKino response."""
        series_list = []
        soup = BeautifulSoup(response.json()["response"], "html.parser")
        for ul in soup.find_all("ul"):
            for li in ul.find_all("li", attrs={"data-id": True, "data-file": True}):
                series_list.append(
                    Series(
                        studio_id=li["data-id"],
                        studio_name=li["data-voice"],
                        series=li.text.strip(),
                        url=f"https:{li['data-file']}",
                        provider=provider,
                    )
                )
        return series_list

    @staticmethod
    def _parse_anitube_series(response, provider: str = "anitube") -> List[Series]:
        """Parse series information from Anitube response."""
        series_list = []
        soup = BeautifulSoup(response.json()["response"], "html.parser")
        for item in soup.find_all("li", attrs={"data-file": True}):
            studio_id = item["data-id"]
            base_id = "_".join(studio_id.split("_")[:-1])
            studio_name_li = soup.find("li", attrs={"data-id": base_id})
            series_list.append(
                Series(
                    studio_id=studio_id,
                    studio_name=studio_name_li.text if studio_name_li else "Unknown",
                    series=item.text.strip(),
                    url=item["data-file"],
                    provider=provider,
                )
            )
        return series_list

    @staticmethod
    def extract_id_from_url(url: str) -> Optional[str]:
        """Extract content ID from URL.

        Supports DLE-style URLs: /123-title.html or /123-title (numeric prefix).
        Does not match slug-only URLs (e.g. /serials/slug-name/).

        Args:
            url: Content URL

        Returns:
            Content ID if found, None otherwise
        """
        match = re.search(r"/(\d+)-|/(\d+)\.html", url)
        if match:
            return match.group(1) if match.group(1) else match.group(2)
        return None

    @staticmethod
    def parse_uaflix_series_page_html(
        response, base_url: str = "https://uafix.net"
    ) -> List[Series]:
        """Parse UAFlix series page HTML: episodes are listed under frels2 / #sers-wr.

        UAFlix does not embed a player on the series page; each episode link points to
        an episode page where the player is. We return Series with url = episode page URL.

        Args:
            response: requests.Response with HTML body
            base_url: Base URL for resolving relative hrefs

        Returns:
            List of Series (url = episode page, series = episode title)
        """
        series_list: List[Series] = []
        if not response or not response.ok:
            return series_list
        soup = BeautifulSoup(response.text, "html.parser")
        sers_wr = soup.find("div", id="sers-wr")
        if not sers_wr:
            sers_wr = soup.find("div", class_="frels2")
        if not sers_wr:
            return series_list
        for idx, item in enumerate(
            sers_wr.find_all("div", class_="video-item")
        ):
            link = item.find("a", class_=lambda c: c and "vi-img" in c)
            if not link or not link.get("href"):
                continue
            href = unquote(link.get("href", "").strip())
            if not href or "season" not in href.lower() or "episode" not in href.lower():
                continue
            episode_url = href if href.startswith("http") else urljoin(base_url, href)
            vi_title = item.find("div", class_="vi-title")
            vi_rate = item.find("div", class_="vi-rate")
            title_parts = []
            if vi_title:
                title_parts.append(SearchManager.clean_text(vi_title.get_text()))
            if vi_rate:
                title_parts.append(SearchManager.clean_text(vi_rate.get_text()))
            title = " ".join(title_parts) if title_parts else f"Episode {idx + 1}"
            series_list.append(
                Series(
                    studio_id=f"ep_{idx}",
                    studio_name="UAFlix",
                    series=title,
                    url=episode_url,
                    provider="uaflix",
                )
            )
        return series_list

    @staticmethod
    def get_news_id_from_uaflix_slug_page(url: str, headers: Optional[dict] = None) -> Optional[str]:
        """Fetch a UAFlix slug URL (e.g. /serials/rik-i-morti-anime/) and extract news_id.

        DLE pages often embed news_id in scripts or links (playlists.php?news_id=...).

        Args:
            url: Full series page URL (slug-based)
            headers: Optional request headers

        Returns:
            news_id string if found in page, None otherwise
        """
        response = RequestManager.get(url, headers=headers)
        if not response or not response.ok:
            return None
        text = response.text
        # playlists.php?news_id=123 or news_id=123 in scripts/links
        match = re.search(r"playlists\.php\?[^\"'\s]*news_id=(\d+)", text)
        if match:
            return match.group(1)
        match = re.search(r"news_id['\"]?\s*[=:]\s*['\"]?(\d+)", text)
        if match:
            return match.group(1)
        match = re.search(r"newsid['\"]?\s*[=:]\s*['\"]?(\d+)", text, re.I)
        if match:
            return match.group(1)
        return None
