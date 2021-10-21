from typing import Optional

import requests

from grafq.errors import OperationErrors
from grafq.query import Query, ValueInnerType


class Client:

    def __init__(self, url: str, token: Optional[str] = None):
        self._url = url
        self._session = requests.Session()
        if token:
            self._session.headers['Authorization'] = f"Bearer {token}"

    def get(self, query: Query, variables: Optional[dict[str, ValueInnerType]] = None) -> dict:
        payload = {'query': str(query)}
        if variables:
            payload['variables'] = variables
        resp = self._session.get(self._url, params=payload)
        decoded = resp.json()
        if errors := decoded.get('errors'):
            raise OperationErrors(errors)
        return decoded.get('data')

    def post(self, query: Query, variables: Optional[dict[str, ValueInnerType]] = None) -> dict:
        payload = {'query': str(query)}
        if variables:
            payload['variables'] = variables
        resp = self._session.post(self._url, json=payload)
        decoded = resp.json()
        if errors := decoded.get('errors'):
            raise OperationErrors(errors)
        return decoded.get('data')
