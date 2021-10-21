from __future__ import annotations

from typing import Optional, Union

from grafq.query import (
    VariableDefinition,
    VariableType,
    Value,
    Selection,
    Field,
    Query,
    Argument,
    NamedType,
    ValueInnerType,
)


class QueryBuilder:
    def __init__(self):
        self._name: Optional[str] = None
        self._variable_definitions: list[VariableDefinition] = []
        self._selection_set: list[Selection] = []

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

    def select_field(
        self,
        name: str,
        alias: Optional[str] = None,
        args: Optional[dict[str, ValueInnerType]] = None,
        subfields: Optional[list[Union[Field, str]]] = None,
    ) -> QueryBuilder:
        arguments = (
            [Argument(name, Value(value)) for name, value in sorted(args.items())]
            if args
            else None
        )
        inner_selections = []
        for field in subfields or ():
            if isinstance(field, str):
                field = Field(field)
            inner_selections.append(Selection(field))
        self._selection_set.append(
            Selection(Field(name, alias, arguments, inner_selections))
        )
        return self

    def select(self, selection: Union[list[Selection], Selection]) -> QueryBuilder:
        if isinstance(selection, Selection):
            selection = [selection]
        self._selection_set.extend(selection)
        return self

    def build(self) -> Query:
        return Query(self._selection_set, self._name, self._variable_definitions)
