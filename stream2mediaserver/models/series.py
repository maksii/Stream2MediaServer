from typing import List


class Series:
    """One episode slot (e.g. '1 серія') under a studio; may have multiple player URLs."""

    def __init__(
        self,
        studio_id,
        studio_name,
        series,
        url=None,
        urls=None,
        provider=None,
    ):
        self.studio_id = studio_id
        self.studio_name = studio_name
        self.series = series
        if urls is not None:
            self.urls = list(urls) if urls else []
        elif url is not None:
            self.urls = [url] if url else []
        else:
            self.urls = []
        self.provider = provider  # e.g. "uaflix", "anitube" — so consumer can resolve provider for download

    @property
    def url(self) -> str:
        """Primary/first player URL; backward compatible."""
        return self.urls[0] if self.urls else ""

    def __repr__(self):
        return f"Series(studio_id={self.studio_id}, studio_name={self.studio_name}, series={self.series}, urls={self.urls!r}, provider={self.provider!r})"


class SeriesGroup:
    """Details for one dubbing/studio: studio id/name and list of episodes (Series)."""

    def __init__(self, studio_id: str, studio_name: str, episodes: List["Series"]):
        self.studio_id = studio_id
        self.studio_name = studio_name
        self.episodes = list(episodes)

    def __repr__(self):
        return f"SeriesGroup(studio_id={self.studio_id!r}, studio_name={self.studio_name!r}, episodes={len(self.episodes)})"


def group_series_by_studio(flat: List[Series]) -> List[SeriesGroup]:
    """Convert flat list of Series into list of SeriesGroup by (studio_id, studio_name).
    Episodes with the same (studio_id, studio_name, series) are merged into one Series
    with combined urls (multiple players for the same episode)."""
    groups: dict = {}  # (studio_id, studio_name) -> list of Series
    order: List[tuple] = []
    for s in flat:
        key = (s.studio_id, s.studio_name)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(s)

    out: List[SeriesGroup] = []
    for sid, sname in order:
        raw_episodes = groups[(sid, sname)]
        # Merge by series label: (series label) -> list of urls
        by_label: dict = {}  # series_label -> (urls, provider)
        for ep in raw_episodes:
            label = ep.series
            ep_urls = getattr(ep, "urls", None)
            if ep_urls is None:
                u = getattr(ep, "url", None) or ""
                ep_urls = [u] if u else []
            if label not in by_label:
                by_label[label] = ([], ep.provider)
            by_label[label][0].extend(ep_urls)
        merged = [
            Series(
                studio_id=sid,
                studio_name=sname,
                series=label,
                urls=urls,
                provider=provider,
            )
            for label, (urls, provider) in by_label.items()
        ]
        # Preserve original order of first occurrence per label
        seen = set()
        ordered_merged = []
        for ep in raw_episodes:
            if ep.series not in seen:
                seen.add(ep.series)
                ordered_merged.append(
                    next(m for m in merged if m.series == ep.series)
                )
        out.append(SeriesGroup(sid, sname, ordered_merged))
    return out
