class SearchResult:
    def __init__(
        self,
        title,
        link,
        title_eng=None,
        description=None,
        image_url=None,
        series_info=None,
        year=None,
        rating=None,
        additional_info=None,
        provider=None,
    ):
        self.title = title
        self.title_eng = title_eng
        self.link = link
        self.description = description
        self.image_url = image_url
        self.series_info = series_info
        self.year = year
        self.rating = rating
        self.additional_info = additional_info
        self.provider = provider


class SearchResults:
    def __init__(self):
        self.results = []
        self.advanced_search_link = None
        self.no_results_message = None

    def add_result(self, result):
        self.results.append(result)

    def set_advanced_search_link(self, link):
        self.advanced_search_link = link

    def set_no_results_message(self, message):
        self.no_results_message = message
