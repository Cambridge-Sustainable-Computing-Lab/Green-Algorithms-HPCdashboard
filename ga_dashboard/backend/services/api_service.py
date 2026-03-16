# ------------------------------------------------------------------
# A generic API Service to perform get and post actions (more can be added)
# ------------------------------------------------------------------

import requests
from requests.exceptions import RequestException

class APIService:
    def __init__(self, base_url: str, api_key: str = None, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        self.session.headers.update({'Content-Type': 'application/json'})

    def close(self):
        self.session.close()

    def __enter__(self): 
        return self

    def __exit__(self, *args):
        self.close()

    def get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"GET request failed: {e}")
            return {}
    
    def post(self, endpoint: str, data: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"POST request failed: {e}")
            return {}