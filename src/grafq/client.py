from json import JSONDecodeError
from typing import Optional

import requests

from grafq.errors import OperationErrors, RemoteError
from grafq.language import Query, ValueInnerType
from grafq.query_builder import QueryBuilder
from grafq.schema import Schema


class Client:
    def __init__(self, url: str, token: Optional[str] = None):
        self._url = url
        self._session = requests.Session()
        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"

    def get(
        self, query: Query, variables: Optional[dict[str, ValueInnerType]] = None
    ) -> dict:
        payload = {"query": str(query)}
        if variables:
            payload["variables"] = variables
        resp = self._session.get(self._url, params=payload)
        try:
            decoded = resp.json()
        except JSONDecodeError as e:
            raise RemoteError(resp.text) from e
        if errors := decoded.get("errors"):
            raise OperationErrors(errors)
        return decoded.get("data")

    def post(
        self, query: Query, variables: Optional[dict[str, ValueInnerType]] = None
    ) -> dict:
        payload = {"query": str(query)}
        if variables:
            payload["variables"] = variables
        resp = self._session.post(self._url, json=payload)
        try:
            decoded = resp.json()
        except JSONDecodeError as e:
            raise RemoteError(resp.text) from e
        if errors := decoded.get("errors"):
            raise OperationErrors(errors)
        return decoded.get("data")

    def new_query(self) -> QueryBuilder:
        return QueryBuilder(client=self)

    def schema(self) -> Schema:
        return Schema(client=self, fetch=True)
