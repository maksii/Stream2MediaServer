from typing import List


class Series:
    def __init__(self, studio_id, studio_name, series, url, provider=None):
        self.studio_id = studio_id
        self.studio_name = studio_name
        self.series = series
        self.url = url
        self.provider = provider  # e.g. "uaflix", "anitube" — so consumer can resolve provider for download

    def __repr__(self):
        return f"Series(studio_id={self.studio_id}, studio_name={self.studio_name}, series={self.series}, url={self.url}, provider={self.provider!r})"


class SeriesGroup:
    """Details for one dubbing/studio: studio id/name and list of episodes (Series)."""

    def __init__(self, studio_id: str, studio_name: str, episodes: List["Series"]):
        self.studio_id = studio_id
        self.studio_name = studio_name
        self.episodes = list(episodes)

    def __repr__(self):
        return f"SeriesGroup(studio_id={self.studio_id!r}, studio_name={self.studio_name!r}, episodes={len(self.episodes)})"


def group_series_by_studio(flat: List[Series]) -> List[SeriesGroup]:
    """Convert flat list of Series into list of SeriesGroup by (studio_id, studio_name). Order of first occurrence is preserved."""
    groups: dict = {}  # (studio_id, studio_name) -> list of Series
    order: List[tuple] = []
    for s in flat:
        key = (s.studio_id, s.studio_name)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(s)
    return [SeriesGroup(sid, sname, groups[(sid, sname)]) for sid, sname in order]
