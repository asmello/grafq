from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from grafq.client import Client


def _indent(text: str):
    return "\n".join("  " + line for line in text.splitlines())


# Need to distinguish from None for optional fields
class Null:
    def __str__(self):
        return "null"


@dataclass(frozen=True, order=True)
class Value:
    inner: ValueInnerType

    def __str__(self):
        return _str(self.inner)


@dataclass(frozen=True, order=True)
class VarRef:
    name: str

    def __str__(self):
        return f"${self.name}"


ValueInnerType = Union[
    str, int, float, bool, Null, Enum, list[Value], dict[str, Value], VarRef
]


def _str(value: ValueInnerType) -> str:
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return "[" + ", ".join(_str(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}: {_str(v)}" for k, v in value.items()) + "}"
    return str(value)


@dataclass(frozen=True, order=True)
class VariableType(ABC):
    pass


@dataclass(frozen=True, order=True)
class NamedType(VariableType):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, order=True)
class ListType(VariableType):
    subtype: VariableType

    def __str__(self) -> str:
        return f"[{self.subtype}]"


@dataclass(frozen=True, order=True)
class NonNullType(VariableType):
    subtype: Union[NamedType, ListType]

    def __str__(self) -> str:
        return f"{self.subtype}!"


@dataclass(frozen=True, order=True)
class VariableDefinition:
    name: str
    type: VariableType
    default_value: Optional[Value] = None

    def pretty(self) -> str:
        s = f"${self.name}: {self.type}"
        if self.default_value is not None:
            s += f" = {self.default_value}"
        return s

    def __str__(self) -> str:
        s = f"${self.name}:{self.type}"
        if self.default_value is not None:
            s += f"={self.default_value}"
        return s


@dataclass(frozen=True, order=True)
class Argument:
    name: str
    value: Value

    def pretty(self) -> str:
        return f"{self.name}: {self.value}"

    def __str__(self) -> str:
        return f"{self.name}:{self.value}"


@dataclass(frozen=True, order=True)
class Field:
    name: str
    alias: Optional[str] = None
    arguments: Optional[list[Argument]] = None
    selection_set: Optional[list[Selection]] = None

    def pretty(self) -> str:
        s = ""
        if self.alias:
            s += self.alias + ": "
        s += self.name
        if self.arguments:
            s += "(" + ", ".join(argument.pretty() for argument in self.arguments) + ")"
        if self.selection_set:
            selections = "\n".join(
                _indent(selection.pretty()) for selection in self.selection_set
            )
            s += " {\n" + selections + "\n}"
        return s

    def __str__(self) -> str:
        s = ""
        if self.alias:
            s += self.alias + ":"
        s += self.name
        if self.arguments:
            s += "(" + ",".join(str(argument) for argument in self.arguments) + ")"
        if self.selection_set:
            s += (
                "{" + ",".join(str(selection) for selection in self.selection_set) + "}"
            )
        return s


@dataclass(frozen=True, order=True)
class Selection:
    field: Field

    def pretty(self) -> str:
        return self.field.pretty()

    def __str__(self) -> str:
        return str(self.field)


@dataclass(frozen=True)
class Query:
    selection_set: list[Selection]
    name: Optional[str] = None
    variable_definitions: Optional[list[VariableDefinition]] = None
    shorthand: bool = True
    client: Optional[Client] = None

    def execute(
        self,
        variables: Optional[dict[str, ValueInnerType]] = None,
        client: Optional[Client] = None,
    ) -> dict:
        client = client or self.client
        if not client:
            raise RuntimeError("Must provide a client to execute query")
        return client.post(self, variables)

    def pretty(self) -> str:
        if self.shorthand and not self.variable_definitions:
            s = ""
        else:
            s = "query"
            if self.name:
                s += " " + self.name
            if self.variable_definitions:
                s += (
                    "("
                    + ", ".join(
                        definition.pretty() for definition in self.variable_definitions
                    )
                    + ") "
                )
            else:
                s += " "
        if self.selection_set:
            return (
                s
                + "{\n"
                + "\n".join(
                    _indent(selection.pretty()) for selection in self.selection_set
                )
                + "\n}"
            )
        else:
            return s + "{ }"

    def __str__(self) -> str:
        if self.shorthand and not self.variable_definitions:
            s = ""
        else:
            s = "query"
            if self.name:
                s += " " + self.name
            if self.variable_definitions:
                s += (
                    "("
                    + ",".join(
                        str(definition) for definition in self.variable_definitions
                    )
                    + ")"
                )
        return (
            s + "{" + ",".join(str(selection) for selection in self.selection_set) + "}"
        )
