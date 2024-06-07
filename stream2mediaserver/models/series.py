class Series:
    def __init__(self, studio_id, studio_name, series, url):
        self.studio_id = studio_id
        self.studio_name = studio_name
        self.series = series
        self.url = url

    def __repr__(self):
        return f"Series(studio_id={self.studio_id}, studio_name={self.studio_name}, series={self.series}, url={self.url})"
