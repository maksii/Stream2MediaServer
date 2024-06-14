from abc import ABC, abstractmethod

class ProviderBase(ABC):
    def __init__(self, config):
        self.config = config

    @property
    def base_url(self):
        """Get the url."""
        return self._base_url

    @base_url.setter
    def base_url(self, value):
        """Set the url."""
        self._base_url = value
        
    @property
    def dle_login_hash(self):
        """Get the dle."""
        return self._dle_login_hash

    @dle_login_hash.setter
    def dle_login_hash(self, value):
        """Set the dle."""
        self._dle_login_hash = value

    @abstractmethod
    def search_title(self, query):
        pass

    @abstractmethod
    def load_details_page(self, query):
        pass

    @abstractmethod
    def load_player_page(self, query):
        pass     