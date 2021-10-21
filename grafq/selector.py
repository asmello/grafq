from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from grafq.query import Field, Value, Argument, Selection, ValueInnerType


@dataclass
class MutableField:
    """Used locally to get around immutability of Fields"""

    name: str
    alias: Optional[str] = None
    arguments: Optional[list[Argument]] = None
    children: Optional[list[MutableField]] = None

    def freeze(self) -> Field:
        rendered_children = (
            [Selection(field.freeze()) for field in self.children]
            if self.children
            else None
        )
        return Field(
            self.name,
            alias=self.alias,
            arguments=self.arguments,
            selection_set=rendered_children,
        )

    def pretty(self) -> str:
        return self.freeze().pretty()

    def __str__(self):
        return str(self.freeze())


class Selector:
    def __init__(self):
        self._fields: list[MutableField] = []
        self._parent: Optional[Selector] = None
        self._parent_field: Optional[MutableField] = None

    def add(
        self,
        name,
        alias: Optional[str] = None,
        args: Optional[dict[str, ValueInnerType]] = None,
    ) -> Selector:
        arguments = (
            [Argument(name, Value(inner=value)) for name, value in sorted(args.items())]
            if args
            else None
        )
        self._fields.append(MutableField(name, alias=alias, arguments=arguments))
        return self

    def into(self) -> Selector:
        return Selector()._with(self, self._fields[-1])

    def _with(self, parent: Selector, field: MutableField) -> Selector:
        self._parent = parent
        self._parent_field = field
        return self

    def back(self) -> Selector:
        if not self._parent:
            raise RuntimeError("Tried to back up a root selector")
        self._parent_field.children = self._fields or None
        return self._parent

    def render(self) -> list[Selection]:
        node = self
        while node._parent:
            node = node.back()
        return [Selection(field.freeze()) for field in node._fields]

    def pretty(self) -> str:
        return "\n".join(field.pretty() for field in self._fields)

    def __str__(self):
        return "\n".join(str(field) for field in self._fields)


"""
Selector()
.field("viewer")
.into()
.field("login")
.field("avatarUrl", args={'size': '$size'}, alias='avatar')
.field("name")
.back()
.field("repository", args={'name': 'grafq', 'owner': 'asmello'})
.into()
.field('url')
.
"""
