from abc import ABC, abstractmethod
import requests
import time


class WebsiteParser(ABC):
    def get_response(self, url: str, max_retries: int = 1, backoff_factor: float = 1, **kwargs):
        for retry in range(max_retries):
            response = requests.get(url, **kwargs)
            if response.ok:
                return response
            time.sleep(backoff_factor * (2 ** (retry - 1)))
        raise Exception(f'Status: {response.status_code}')

    @abstractmethod
    def parse_data(self, *args, **kwargs): ...
