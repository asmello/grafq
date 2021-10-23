from __future__ import annotations

from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from grafq.schema import Schema
    from grafq.client import Client
from grafq.field_blueprint import FieldBlueprint, coerce_to_blueprint
from grafq.language import (
    VariableDefinition,
    VariableType,
    Value,
    Selection,
    Query,
    NamedType,
    ValueRawType,
)


class QueryBlueprint:
    def __init__(
        self, client: Optional[Client] = None, schema: Optional[Schema] = None
    ):
        self._client = client
        self._name: Optional[str] = None
        self._variable_definitions: list[VariableDefinition] = []
        self._fields: dict[str, FieldBlueprint] = {}

    def name(self, name: str) -> QueryBlueprint:
        self._name = name
        return self

    def var(
        self,
        name: str,
        var_type: Union[VariableType, str],
        default: Optional[ValueRawType] = None,
    ) -> QueryBlueprint:
        if isinstance(var_type, str):
            var_type = NamedType(var_type)
        if default is not None:
            default = Value(default)
        self._variable_definitions.append(VariableDefinition(name, var_type, default))
        return self

    def select(self, *specs: Union[str, FieldBlueprint]) -> QueryBlueprint:
        FieldBlueprint.combine(
            self._fields, (coerce_to_blueprint(spec) for spec in specs)
        )
        return self

    def build(self, shorthand: bool = True) -> Query:
        return Query(
            selection_set=[Selection(field.build()) for field in self._fields.values()],
            name=self._name,
            variable_definitions=self._variable_definitions,
            shorthand=shorthand,
            client=self._client,
        )

    def build_and_run(
        self,
        client: Optional[Client] = None,
        variables: Optional[dict[str, ValueRawType]] = None,
    ) -> dict:
        client = client or self._client
        if not client:
            raise RuntimeError("Must provide a client to execute query")
        return client.post(self.build(), variables)
