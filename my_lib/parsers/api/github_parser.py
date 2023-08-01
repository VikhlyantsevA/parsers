from dotenv import dotenv_values
import requests
from urllib.parse import urljoin


class GithubApiParser:
    """
    A class to get data requests from GitHub API (documentation at https://docs.github.com/en/rest).
    ...

    Attributes
    ----------
    env_file : str
        path to env-file with credentials
    host : str
        API entry-point. Default = 'https://api.github.com'

    Methods
    -------
    get_response(endpoint, **kwargs):
        Get json-response from API.
    """
    def __init__(self, env_file, host='https://api.github.com'):
        self.host = host
        self.__config = dotenv_values(env_file)
        self.__token = self.__config.get('API_TOKEN')

    def get_response(self, endpoint, **kwargs):
        url = urljoin(self.host, endpoint)
        headers = {
            'Authorization': f'Bearer {self.__token}'
        }
        response = requests.get(url, headers=headers, **kwargs)
        print(f'URL: {response.url}.\nTry to get response with given token.')
        if response.ok:
            print(f'Status: {response.status_code}. SUCCESS')
        elif response.status_code == 403:
            raise Exception(f'FAIL. Status: {response.status_code}. Try another token.')
        else:
            raise Exception(f'FAIL. Status: {response.status_code}. {response.text}')
        return response.json()
