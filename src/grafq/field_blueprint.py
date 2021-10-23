from __future__ import annotations

from collections.abc import Iterable
from typing import Optional, Union

from grafq.language import (
    Argument,
    Value,
    Field,
    Selection,
    ValueRawType,
)


def coerce_to_blueprint(field: Union[str, FieldBlueprint]) -> FieldBlueprint:
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
        return field
    else:
        raise TypeError(f"Illegal type given to select: {type(field)}")


class FieldBlueprint:
    def __init__(self, field_name: str, **kwargs: ValueRawType):
        self._name = field_name
        self._arguments = kwargs
        self._alias: Optional[str] = None
        self._children: list[FieldBlueprint] = []

    @property
    def name(self):
        return self._name

    def arg(self, name: str, value: ValueRawType) -> FieldBlueprint:
        self._arguments[name] = value
        return self

    @staticmethod
    def _combine(blueprints: Iterable[FieldBlueprint]) -> Iterable[FieldBlueprint]:
        found: dict[str, FieldBlueprint] = {}
        for blueprint in blueprints:
            if blueprint._name in found:
                original = found[blueprint._name]
                original._arguments.update(blueprint._arguments)
                # Python 3.6+ ensures dict preserves insertion order, so we can use this trick to dedup stably
                original._children = list(
                    dict.fromkeys((*original._children, *blueprint._children))
                )
                original._alias = blueprint._alias or original._alias
            else:
                found[blueprint._name] = blueprint
        return found.values()

    @staticmethod
    def combine(
        original: Iterable[FieldBlueprint], new: Iterable[FieldBlueprint]
    ) -> Iterable[FieldBlueprint]:
        return FieldBlueprint._combine((*original, *new))

    def select(self, *specs: Union[str, FieldBlueprint]) -> FieldBlueprint:
        self._children = list(
            FieldBlueprint.combine(
                self._children, (coerce_to_blueprint(spec) for spec in specs)
            )
        )
        return self

    def alias(self, alias: str) -> FieldBlueprint:
        self._alias = alias
        return self

    def build(self) -> Field:
        arguments = [
            Argument(name, Value(value)) for name, value in self._arguments.items()
        ]
        arguments.sort()
        return Field(
            self._name,
            self._alias,
            arguments or None,
            [Selection(child.build()) for child in self._children] or None,
        )

    def clone(self) -> FieldBlueprint:
        new = FieldBlueprint(self._name, **self._arguments)
        new._alias = self._alias
        new._children = [child.clone() for child in self._children]
        return new
