from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from grafq.language import ValueRawType, Null
from .base import FieldBlueprint

if TYPE_CHECKING:
    from grafq.schema import Schema, FieldMeta, SchemaType, ID


def _validate_arg_value(value_type: SchemaType, value: ValueRawType) -> bool:
    # todo: handle variable references (VarRef)
    if value_type.kind == "SCALAR":
        if value_type.name == "Int":
            return isinstance(value, int)
        if value_type.name == "Float":
            return isinstance(value, float)
        if value_type.name == "String":
            return isinstance(value, str)
        if value_type.name == "Boolean":
            return isinstance(value, bool)
        if value_type.name == "ID":
            return isinstance(value, ID)
    elif value_type.kind == "NON_NULL":
        if isinstance(value, Null) or value is None:
            return False
        return _validate_arg_value(value_type.of_type, value)
    elif value_type.kind == "LIST":
        if not isinstance(value, list):
            return False
        return _validate_arg_value(value_type.of_type, value[0])
    elif value_type.kind == "ENUM":
        if value in (value["name"] for value in value_type.enum_values):
            return True
    elif value_type.kind == "INPUT_OBJECT":
        if not isinstance(value, dict):
            return False
        field_types: dict[str, SchemaType] = {
            field["name"]: field["type"] for field in value_type.input_fields
        }
        if any(name not in field_types for name in value.keys()):
            return False
        return all(
            _validate_arg_value(field_types[name], value)
            for name, value in value.items()
        )
    return False


class TypedFieldBlueprint(FieldBlueprint):
    def __init__(
        self,
        schema: Schema,
        meta: FieldMeta,
        parent: Optional[TypedFieldBlueprint] = None,
    ):
        super().__init__(meta.name)
        self._schema = schema
        self._meta = meta
        self._core_type = self._resolve_type(meta.type)
        self._parent = parent

    @staticmethod
    def _resolve_type(typespec: SchemaType) -> str:
        if typespec.name is None:
            return TypedFieldBlueprint._resolve_type(typespec.of_type)
        return typespec.name

    def __call__(self, **kwargs: ValueRawType) -> TypedFieldBlueprint:
        if not self._meta.args:
            raise TypeError(f"Field {self._meta.name} does not support arguments")
        supported_args: dict[str, SchemaType] = {
            arg.name: arg.type for arg in self._meta.args
        }
        for name, value in kwargs.items():
            if name not in supported_args:
                raise TypeError(f"Invalid argument {name} for field {self._meta.name}")
            if _validate_arg_value(supported_args[name], value):
                self._arguments[name] = value
            else:
                raise TypeError(
                    f"Invalid argument type for {name} at field {self._meta.name}"
                )
        return self

    def __getattr__(self, name: str) -> FieldBlueprint:
        if name in self._children:
            return self._children[name]
        fields = self._schema.get_type_fields(self._core_type)
        if name not in fields:
            raise AttributeError(name)
        new = TypedFieldBlueprint(self._schema, fields[name], parent=self)
        self._children[name] = new
        return new

    def __getitem__(self, name: str) -> FieldBlueprint:
        if isinstance(name, str):
            raise TypeError("key must be a string")
        if name in self._children:
            return self._children[name]
        fields = self._schema.get_type_fields(self._core_type)
        if name not in fields:
            raise KeyError(name)
        new = TypedFieldBlueprint(self._schema, fields[name], parent=self)
        self._children[name] = new
        return new

    def root(self) -> TypedFieldBlueprint:
        node = self
        while node._parent:
            node = node._parent
        return node
