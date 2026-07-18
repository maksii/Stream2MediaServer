"""Parsing rules derived from real provider markup (see anitube/uaflix structures)."""

import unittest
from unittest.mock import patch

from stream2mediaserver.models.series import group_series_by_studio
from stream2mediaserver.processors.request_manager import RequestManager
from stream2mediaserver.processors.search_manager import SearchManager


class FakeResponse:
    def __init__(self, payload=None, text=""):
        self._payload = payload
        self.text = text
        self.ok = True
        self.status_code = 200

    def json(self):
        return self._payload


class NormalizeMediaUrlTests(unittest.TestCase):
    def test_passes_through_absolute(self):
        self.assertEqual(
            SearchManager.normalize_media_url("https://ashdi.vip/vod/1"),
            "https://ashdi.vip/vod/1",
        )

    def test_upgrades_protocol_relative(self):
        self.assertEqual(
            SearchManager.normalize_media_url("//ashdi.vip/vod/1"),
            "https://ashdi.vip/vod/1",
        )

    def test_adds_scheme_to_bare_host(self):
        self.assertEqual(
            SearchManager.normalize_media_url("tortuga.wtf/vod/38785"),
            "https://tortuga.wtf/vod/38785",
        )

    def test_recovers_embedded_url_from_corrupt_value(self):
        # Real values seen on anitube's One Piece playlist.
        self.assertEqual(
            SearchManager.normalize_media_url("hhttps://moonanime.art/iframe/abc"),
            "https://moonanime.art/iframe/abc",
        )
        self.assertEqual(
            SearchManager.normalize_media_url(
                "honline/embed/604144https://moonanime.art/iframe/xyz"
            ),
            "https://moonanime.art/iframe/xyz",
        )

    def test_rejects_unusable(self):
        for bad in ("", None, "   ", "not a url"):
            self.assertIsNone(SearchManager.normalize_media_url(bad))


class AnitubeStudioResolutionTests(unittest.TestCase):
    # Deep nesting: dub type > studio > player > range > episodes
    DEEP_LABELS = {
        "0_0": "ОЗВУЧЕННЯ",
        "0_1": "СУБТИТРИ",
        "0_0_0": "TOGARASHI",
        "0_0_0_0": "ПЛЕЄР ASHDI",
        "0_0_0_1": "ПЛЕЄР MOON",
        "0_0_0_0_0": "1-200 серія",
        "0_1_0": "SaloVpalo",
        "0_1_0_0": "ПЛЕЄР ASHDI+МОНСТР",
    }

    def test_deep_nesting_picks_studio_not_player(self):
        sid, name = SearchManager._anitube_studio("0_0_0_0_0", self.DEEP_LABELS)
        self.assertEqual(name, "TOGARASHI")
        self.assertEqual(sid, "0_0_0")

    def test_players_of_same_studio_share_group_id(self):
        ashdi = SearchManager._anitube_studio("0_0_0_0_0", self.DEEP_LABELS)
        moon = SearchManager._anitube_studio("0_0_0_1_4", self.DEEP_LABELS)
        self.assertEqual(ashdi, moon)

    def test_subtitle_branch_is_distinguished(self):
        _, name = SearchManager._anitube_studio("0_1_0_0_0", self.DEEP_LABELS)
        self.assertEqual(name, "SaloVpalo (Субтитри)")

    def test_shallow_nesting_uses_direct_parent(self):
        sid, name = SearchManager._anitube_studio("0_0_0", {"0_0": "DniproFilm"})
        self.assertEqual((sid, name), ("0_0", "DniproFilm"))

    def test_unknown_when_no_labels(self):
        _, name = SearchManager._anitube_studio("0_0_0", {})
        self.assertEqual(name, "Unknown")

    def test_parse_skips_unusable_urls_and_groups_by_studio(self):
        html = """
        <ul>
          <li data-id="0_0">ОЗВУЧЕННЯ</li>
          <li data-id="0_0_0">TOGARASHI</li>
          <li data-id="0_0_0_0">ПЛЕЄР ASHDI</li>
          <li data-id="0_0_0_0" data-file="https://ashdi.vip/vod/1">1 серія</li>
          <li data-id="0_0_0_0" data-file="not a url">2 серія</li>
          <li data-id="0_0_0_1">ПЛЕЄР MOON</li>
          <li data-id="0_0_0_1" data-file="//moonanime.art/iframe/a">1 серія</li>
        </ul>
        """
        series = SearchManager._parse_anitube_series(FakeResponse({"response": html}))
        self.assertEqual(len(series), 2)  # the unusable one is skipped
        self.assertEqual({s.studio_name for s in series}, {"TOGARASHI"})
        # Same episode under two players merges into one entry with both URLs.
        merged = group_series_by_studio(series)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].episodes[0].urls,
                         ["https://ashdi.vip/vod/1", "https://moonanime.art/iframe/a"])


class TitleRelevanceTests(unittest.TestCase):
    """Animeon ORs query tokens, so results must be judged against their titles."""

    def score(self, query, *titles):
        return SearchManager.title_match_score(query, list(titles))

    def test_full_match_scores_one(self):
        self.assertEqual(
            self.score("Attack on Titan", "Атака титанів", "Attack on Titan"), 1.0)
        # 'Season 3' suffix must not dilute the score.
        self.assertEqual(
            self.score("Attack on Titan", "Атака титанів - 3 сезон",
                       "Attack on Titan Season 3"), 1.0)

    def test_matches_across_languages(self):
        self.assertEqual(self.score("Наруто", "Наруто", "Naruto"), 1.0)
        self.assertEqual(self.score("Naruto", "Наруто", "Naruto"), 1.0)

    def test_partial_match_is_rejected(self):
        # 'Stranger Things' vs an anime that only shares 'stranger'.
        self.assertEqual(self.score("Stranger Things", "", "Amazing Stranger"), 0.5)
        self.assertEqual(self.score("Breaking Bad", "Погана дівчинка", "Bad Girl"), 0.5)

    def test_unrelated_scores_zero(self):
        self.assertEqual(
            self.score("Rick and Morty", "Небо на березі Червоної річки", "Red River"),
            0.0)

    def test_fuzzy_matches_long_token_spelling_variants(self):
        self.assertEqual(
            self.score("Naruto Shippuden", "Наруто", "Naruto Shippuuden"), 1.0)

    def test_short_tokens_do_not_fuzzy_collide(self):
        # 'dan' vs 'data' scores 0.86 — close enough to match if fuzz were allowed.
        self.assertEqual(self.score("Dan Da Dan", "Red Data Girl", "Red Data Girl"), 0.0)

    def test_stopword_only_query_is_not_filtered(self):
        # Nothing significant to judge on; better to pass results through than
        # silently return nothing.
        self.assertEqual(self.score("and", "Kicks and Punk", "Kicks and Punk"), 1.0)

    def test_no_titles_scores_zero(self):
        self.assertEqual(self.score("Naruto", None, ""), 0.0)


class AnimeonSearchFilterTests(unittest.TestCase):
    @staticmethod
    def _payload(*titles):
        return {"result": [{"id": i, "titleUa": ua, "titleEn": en}
                           for i, (ua, en) in enumerate(titles, 1)]}

    def _search(self, query, payload):
        with patch.object(RequestManager, "get",
                          return_value=FakeResponse(payload)):
            return SearchManager._search_animeon(
                query, "https://animeon.club/api/anime/search", None,
                "https://animeon.club")

    def test_drops_unrelated_filler(self):
        results = self._search("Rick and Morty", self._payload(
            ("Мої мачуха та сестри зовсім не лихі", "My Stepmother and Stepsisters"),
            ("Небо на березі Червоної річки", "Red River"),
        ))
        self.assertEqual(results, [])

    def test_keeps_genuine_hits(self):
        results = self._search("Dan Da Dan", self._payload(
            ("Дандадан", "Dan Da Dan"),
            ("Дандадан - 2 сезон", "Dan Da Dan Season 2"),
            ("Замальовки Хідамарі", "Hidamari Sketch"),
        ))
        self.assertEqual([r.title for r in results], ["Дандадан", "Дандадан - 2 сезон"])
        self.assertEqual(results[0].provider, "animeon")

    def test_url_encoded_query_is_decoded_before_matching(self):
        # search_movies passes a %-encoded query through to the parser.
        results = self._search("Attack%20on%20Titan", self._payload(
            ("Атака титанів", "Attack on Titan"),
            ("Замальовки Хідамарі", "Hidamari Sketch"),
        ))
        self.assertEqual([r.title for r in results], ["Атака титанів"])


class UakinoSeriesParsingTests(unittest.TestCase):
    def test_protocol_relative_urls_are_normalized(self):
        html = """
        <ul><li data-id="1" data-voice="Струґачка" data-file="//ashdi.vip/vod/9">
        Серія 1</li></ul>
        """
        series = SearchManager._parse_uakino_series(FakeResponse({"response": html}))
        self.assertEqual(series[0].url, "https://ashdi.vip/vod/9")
        self.assertEqual(series[0].studio_name, "Струґачка")


class UaflixSeasonGroupingTests(unittest.TestCase):
    @staticmethod
    def _page(titles):
        items = "".join(
            f'<div class="video-item"><a class="vi-img" '
            f'href="/serials/x/season-09-episode-0{i}/"></a>'
            f'<div class="vi-title">{t}</div></div>'
            for i, t in enumerate(titles, 1)
        )
        return FakeResponse(text=f'<div id="sers-wr">{items}</div>')

    def test_premiere_prefixed_episode_stays_in_its_season(self):
        series = SearchManager.parse_uaflix_series_page_html(
            self._page([
                "Сезон 9 Серія 1 Щось є в Морті",
                "Прем'єра. 20.07.2026 Сезон 9 Серія 9 Вітайте своїх смертних",
            ])
        )
        self.assertEqual(len(series), 2)
        self.assertEqual({s.studio_id for s in series}, {"season_9"})
        # The premiere marker is preserved in the episode label, not dropped.
        self.assertIn("Прем'єра", series[1].series)
        self.assertIn("Серія 9", series[1].series)

    def test_plain_season_episode_label_is_unchanged(self):
        series = SearchManager.parse_uaflix_series_page_html(
            self._page(["Сезон 9 Серія 1 Щось є в Морті"])
        )
        self.assertEqual(series[0].series, "Серія 1 Щось є в Морті")
        self.assertEqual(series[0].studio_name, "UAFlix Сезон 9")


class AnitubeSearchFieldTests(unittest.TestCase):
    HTML = """
    <a style="display: block;" href="https://anitube.in.ua/94-van-pis.html"
       year="1999" rating="9.1">
      <span class="searchheading"><b class="searchheading_title">Ван Піс</b></span>
      <div class="img_fast_search"><img src="https://anitube.in.ua/p.jpg"/><span>
        <b>Серій:</b> 1169 з ХХ (24 хв.)<br/>
        <b>Рік:</b> 1999<br/>
        <b>Опис:</b> Перед смертю король піратів..
      </span></div>
    </a>
    """

    def test_search_fields_are_extracted(self):
        with patch.object(
            RequestManager, "post", return_value=FakeResponse(text=self.HTML)
        ):
            results = SearchManager._search_anitube("Ван Піс", "hash", "url", None, None)
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r.title, "Ван Піс")
        self.assertEqual(r.year, "1999")
        self.assertEqual(r.rating, "9.1")
        self.assertEqual(r.series_info, "1169 з ХХ (24 хв.)")
        self.assertIn("король піратів", r.description)


if __name__ == "__main__":
    unittest.main()
