from json import JSONDecodeError
from typing import Optional

import requests

from grafq.blueprints.query import QueryBlueprint
from grafq.errors import OperationErrors, RemoteError
from grafq.language import Query, ValueRawType
from grafq.schema import Schema


class Client:
    def __init__(self, url: str, token: Optional[str] = None):
        self._url = url
        self._session = requests.Session()
        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"
        self._schema: Optional[Schema] = None

    def get(
        self, query: Query, variables: Optional[dict[str, ValueRawType]] = None
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
        self, query: Query, variables: Optional[dict[str, ValueRawType]] = None
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

    def new_query(self) -> QueryBlueprint:
        return QueryBlueprint(client=self)

    @property
    def schema(self) -> Schema:
        if self._schema is None:
            self._schema = Schema(client=self)
        return self._schema
