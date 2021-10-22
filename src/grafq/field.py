from __future__ import annotations

from collections.abc import Iterable
from typing import Optional, Union

from grafq.language import (
    Argument,
    Value,
    Field as FrozenField,
    Selection,
    ValueInnerType,
)


class Field:
    def __init__(self, field_name: str, **kwargs):
        if "." in field_name:
            parts = field_name.split(".")
            node = Field(parts.pop(0))
            while len(parts) > 1:
                child = Field(parts.pop(0))
                node._fields = {child}
                node = child
            node._fields = {self}
            self._parent = node
            field_name = parts[0]
        else:
            self._parent: Optional[Field] = None
        self._name = field_name
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

    @staticmethod
    def coerce_field(field: Union[str, Field]) -> Field:
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
            # When instancing fields by path-like names (e.g. "me.name"), we get back the leaf node,
            # but for our purposes we need the root node, so we traverse up the tree to make sure we have it
            while field._parent is not None:
                field = field._parent
            return field
        else:
            raise TypeError(f"Illegal type given to select: {type(field)}")

    def select(self, *fields: Union[str, Field]) -> Field:
        fields = (Field.coerce_field(field) for field in fields)
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
