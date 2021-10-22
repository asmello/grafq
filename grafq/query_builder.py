from __future__ import annotations

from typing import Optional, Union

from grafq.client import Client
from grafq.field import Field, coerce_field
from grafq.language import (
    VariableDefinition,
    VariableType,
    Value,
    Selection,
    Query,
    NamedType,
    ValueInnerType,
)


class QueryBuilder:
    def __init__(self, client: Optional[Client] = None):
        self._client = client
        self._name: Optional[str] = None
        self._variable_definitions: list[VariableDefinition] = []
        self._selection_set: set[Selection] = set()

    def name(self, name: str) -> QueryBuilder:
        self._name = name
        return self

    def var(
        self,
        name: str,
        var_type: Union[VariableType, str],
        default: Optional[ValueInnerType] = None,
    ) -> QueryBuilder:
        if isinstance(var_type, str):
            var_type = NamedType(var_type)
        if default is not None:
            default = Value(default)
        self._variable_definitions.append(VariableDefinition(name, var_type, default))
        return self

    def select(self, *fields: Union[str, Field]) -> QueryBuilder:
        fields = (coerce_field(field) for field in fields)
        self._selection_set = set(Field.combine([*self._selection_set, *fields]))
        return self

    def build(self, shorthand: bool = True) -> Query:
        return Query(
            sorted(Selection(field.freeze()) for field in self._selection_set),
            self._name,
            self._variable_definitions,
            shorthand,
        )

    def execute(
        self,
        client: Optional[Client] = None,
        variables: Optional[dict[str, ValueInnerType]] = None,
    ) -> dict:
        client = client or self._client
        if not client:
            raise RuntimeError("Must provide a client to execute query")
        return client.post(self.build(), variables)
