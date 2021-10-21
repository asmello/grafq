from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union


# Need to distinguish from None for optional fields
class Null:
    pass


Value = Union[str, int, float, bool, Null, Enum, list['Value'], dict[str, 'Value']]


@dataclass(frozen=True)
class VariableType:
    pass


@dataclass(frozen=True)
class NamedType(VariableType):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class ListType(VariableType):
    subtype: VariableType

    def __str__(self) -> str:
        return f"[{self.subtype}]"


@dataclass(frozen=True)
class NonNullType(VariableType):
    subtype: Union[NamedType, ListType]

    def __str__(self) -> str:
        return f"{self.subtype}!"


@dataclass(frozen=True)
class VariableDefinition:
    name: str
    type: VariableType
    default_value: Optional[Value]

    def __str__(self) -> str:
        s = f"${self.name}: {self.type}"
        if self.default_value is not None:
            s += f" = {self.default_value}"
        return s


@dataclass(frozen=True)
class Argument:
    name: str
    value: Value

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"


@dataclass(frozen=True)
class Field:
    alias: Optional[str]
    name: str
    arguments: Optional[list[Argument]]
    # todo: directives
    selection_set: Optional[list[Selection]]

    def __str__(self) -> str:
        s = ""
        if self.alias:
            s += self.alias + ': '
        s += self.name
        if self.arguments:
            s += '(' + ', '.join(str(argument) for argument in self.arguments) + ')'
        if self.selection_set:
            s += ' { ' + ' '.join(str(selection) for selection in self.selection_set) + ' }'
        return s


@dataclass(frozen=True)
class Selection:
    field: Field

    # todo: fragment_spread
    # todo: inline_fragment

    def __str__(self) -> str:
        return str(self.field)


@dataclass(frozen=True)
class Query:
    name: Optional[str]
    variable_definitions: Optional[list[VariableDefinition]]
    # todo: directives
    selection_set: list[Selection]

    def __str__(self) -> str:
        if self.variable_definitions:
            s = "query "
            if self.name:
                s += self.name
            s += '(' + ', '.join(str(definition) for definition in self.variable_definitions) + ') '
        else:
            s = ""
        if self.selection_set:
            s += '{ ' + ' '.join(str(selection) for selection in self.selection_set) + ' }'
        else:
            s += '{ }'
        return s
