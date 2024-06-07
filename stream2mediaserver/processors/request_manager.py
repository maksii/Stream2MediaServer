import requests

class RequestManager:
    def __init__(self, headers):
        self.headers = headers

    def get(self, url, params=None):
        return requests.get(url, headers=self.headers, params=params)

    def post(self, url, data=None):
        return requests.post(url, headers=self.headers, data=data)