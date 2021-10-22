from __future__ import annotations

from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from grafq.schema import Schema
    from grafq.client import Client
from grafq.field import Field
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
    def __init__(
        self, client: Optional[Client] = None, schema: Optional[Schema] = None
    ):
        self._client = client
        self._name: Optional[str] = None
        self._variable_definitions: list[VariableDefinition] = []
        self._fields: set[Field] = set()

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
        fields = (Field.coerce_field(field) for field in fields)
        self._fields = set(Field.combine([*self._fields, *fields]))
        return self

    def build(self, shorthand: bool = True) -> Query:
        selection_set = [Selection(field.freeze()) for field in self._fields]
        selection_set.sort()
        return Query(
            selection_set,
            self._name,
            self._variable_definitions,
            shorthand,
            client=self._client,
        )

    def build_and_execute(
        self,
        client: Optional[Client] = None,
        variables: Optional[dict[str, ValueInnerType]] = None,
    ) -> dict:
        client = client or self._client
        if not client:
            raise RuntimeError("Must provide a client to execute query")
        return client.post(self.build(), variables)
