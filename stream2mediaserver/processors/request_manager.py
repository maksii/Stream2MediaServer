import requests

class RequestManager:
    # Default headers defined at the class level
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    @classmethod
    def get(cls, url, params=None, headers=None):
        # Allow custom headers or use default
        if headers is None:
            headers = cls.DEFAULT_HEADERS
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Error during GET request to {url}: {str(e)}")
            return None

    @classmethod
    def post(cls, url, data=None, headers=None):
        # Allow custom headers or use default
        if headers is None:
            headers = cls.DEFAULT_HEADERS
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Error during POST request to {url}: {str(e)}")
            return None