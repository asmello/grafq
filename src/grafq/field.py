from __future__ import annotations

from collections.abc import Iterable
from typing import Optional, Union

from src.grafq.language import (
    Argument,
    Value,
    Field as FrozenField,
    Selection,
    ValueInnerType,
)


def _coerce_field(field: Union[str, Field]) -> Field:
    if isinstance(field, str):
        parts = field.split(".")
        original_field = Field(parts.pop(0))
        field = original_field
        while parts:
            inner_field = Field(parts.pop(0))
            field.select(inner_field)
            field = inner_field
        return original_field
    elif isinstance(field, Field):
        return field
    else:
        raise TypeError(f"Illegal type given to select: {type(field)}")


class Field:
    def __init__(self, name: str, **kwargs):
        self._name = name
        self._arguments = kwargs
        self._alias: Optional[str] = None
        self._fields: set[Field] = set()

    def arg(self, name: str, value: ValueInnerType) -> Field:
        self._arguments[name] = value
        return self

    @staticmethod
    def combine(fields: Iterable[Field]) -> Iterable[Field]:
        found: dict[str, Field] = {}
        for field in fields:
            if field._name in found:
                original = found[field._name]
                original._arguments.update(field._arguments)
                original._fields.update(field._fields)
                original._alias = field._alias or original._alias
            else:
                found[field._name] = field
        return found.values()

    def select(self, *fields: Union[str, Field]) -> Field:
        fields = (_coerce_field(field) for field in fields)
        self._fields = set(Field.combine([*self._fields, *fields]))
        return self

    def alias(self, alias: str) -> Field:
        self._alias = alias
        return self

    def freeze(self) -> FrozenField:
        arguments = [
            Argument(name, Value(value)) for name, value in self._arguments.items()
        ]
        arguments.sort()
        selection_set = [Selection(field.freeze()) for field in self._fields]
        selection_set.sort()
        return FrozenField(
            self._name,
            self._alias,
            arguments,
            selection_set,
        )
