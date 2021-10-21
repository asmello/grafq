from __future__ import annotations

from typing import Optional

from grafq.query import VariableDefinition, VariableType, Value, Selection, Field, Query, Argument


class QueryBuilder:

    def __init__(self):
        self._name: Optional[str] = None
        self._variable_definitions: list[VariableDefinition] = []
        self._selection_set: list[Selection] = []

    def name(self, name: str) -> QueryBuilder:
        self._name = name
        return self

    def var(self, name: str, var_type: VariableType, default: Optional[Value] = None) -> QueryBuilder:
        self._variable_definitions.append(VariableDefinition(name, var_type, default))
        return self

    def select(self, name: str, alias: Optional[str] = None,
               args: Optional[dict[str, Value]] = None, fields: Optional[list[Field]] = None) -> QueryBuilder:
        arguments = [Argument(name, value) for name, value in sorted(args.items())] if args else None
        inner_selections = [Selection(field) for field in fields] if fields else None
        self._selection_set.append(
            Selection(Field(name, alias, arguments, inner_selections)))
        return self

    def build(self) -> Query:
        return Query(self._selection_set, self._name, self._variable_definitions)
