from __future__ import annotations

import copy
from collections.abc import Iterable
from typing import Optional, Union

from grafq.blueprints.base import Blueprint
from grafq.language import (
    Argument,
    Value,
    Field,
    Selection,
    ValueRawType,
)


def coerce(field: Union[str, FieldBlueprint]) -> FieldBlueprint:
    if isinstance(field, str):
        if "." in field:
            parts = field.split(".")
            root = node = FieldBlueprint(parts.pop(0))
            while parts:
                child = FieldBlueprint(parts.pop(0))
                node.select(child)
                node = child
            return root
        else:
            return FieldBlueprint(field)
    elif isinstance(field, FieldBlueprint):
        return field.root()
    else:
        raise TypeError(f"Illegal type given to select: {type(field)}")


class FieldBlueprint(Blueprint):
    def __init__(self, name: str, parent: Optional[FieldBlueprint] = None):
        self._name = name
        self._arguments: dict[str, ValueRawType] = {}
        self._children: dict[str, FieldBlueprint] = {}
        self._alias: Optional[str] = None
        self._parent: Optional[FieldBlueprint] = parent

    def arg(self, name: str, value: ValueRawType) -> FieldBlueprint:
        self._arguments[name] = value
        return self

    @staticmethod
    def combine(original: dict[str, FieldBlueprint], new: Iterable[FieldBlueprint]):
        for blueprint in new:
            if original_blueprint := original.get(blueprint._name):
                original_blueprint._arguments |= blueprint._arguments
                FieldBlueprint.combine(
                    original_blueprint._children, blueprint._children.values()
                )
                original_blueprint._alias = (
                    blueprint._alias or original_blueprint._alias
                )
            else:
                original[blueprint._name] = blueprint

    def select(self, *specs: Union[str, FieldBlueprint]) -> FieldBlueprint:
        FieldBlueprint.combine(self._children, (coerce(spec) for spec in specs))
        return self

    def alias(self, alias: str) -> FieldBlueprint:
        self._alias = alias
        return self

    def build(self) -> Field:
        return Field(
            self._name,
            self._alias,
            [Argument(name, Value(value)) for name, value in self._arguments.items()]
            or None,
            [Selection(child.build()) for child in self._children.values()] or None,
        )

    def clone(self) -> FieldBlueprint:
        return copy.deepcopy(self)

    def root(self) -> FieldBlueprint:
        node = self
        while node._parent:
            node = node._parent
        return node
