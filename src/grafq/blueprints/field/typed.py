from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from grafq.language import ValueRawType, ID, NullType, ScalarExtension, VarRef
from .base import FieldBlueprint

if TYPE_CHECKING:
    from grafq.schema import Schema, SchemaType, FieldMeta


def _validate_arg_value(value_type: SchemaType, value: ValueRawType, strict) -> bool:
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
            if strict:
                return isinstance(value, ID)
            else:
                return isinstance(value, (ID, str))
        if strict:
            # the user must define a subtype by deriving from ScalarExtension
            return (
                isinstance(value, ScalarExtension)
                and value_type.name == type(value).__name__
            )
        # in non-strict mode, any scalar value is allowed
        return isinstance(value, (str, int, float, bool))
    elif value_type.kind == "NON_NULL":
        if isinstance(value, NullType) or value is None:
            return False
        return _validate_arg_value(value_type.of_type, value, strict)
    elif value_type.kind == "LIST":
        if not isinstance(value, list):
            return False
        return _validate_arg_value(value_type.of_type, value[0], strict)
    elif value_type.kind == "ENUM":
        if value in (value.name for value in value_type.enum_values):
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
            _validate_arg_value(field_types[name], value, strict)
            for name, value in value.items()
        )
    return False


class TypedFieldBlueprint(FieldBlueprint):
    def __init__(
        self,
        schema: Schema,
        meta: FieldMeta,
        parent: Optional[TypedFieldBlueprint] = None,
        strict: bool = False,
    ):
        super().__init__(meta.name, parent=parent)
        self._schema = schema
        self._meta = meta
        self._strict = strict
        self._core_type = self._resolve_type(meta.type)
        self._var_types: dict[VarRef, tuple[str, SchemaType]] = {}

    @staticmethod
    def _resolve_type(typespec: SchemaType) -> str:
        if typespec.name is None:
            return TypedFieldBlueprint._resolve_type(typespec.of_type)
        return typespec.name

    def get_name(self):
        return self._meta.name

    def get_variable_types(self) -> dict[VarRef, tuple[str, SchemaType]]:
        return self._var_types

    def __call__(self, **kwargs: ValueRawType) -> TypedFieldBlueprint:
        if not self._meta.args:
            raise TypeError(f"Field {self._meta.name} does not support arguments")
        supported_args: dict[str, SchemaType] = {
            arg.name: arg.type for arg in self._meta.args
        }
        for name, value in kwargs.items():
            if name not in supported_args:
                raise TypeError(f"Invalid argument {name} for field {self._meta.name}")
            if isinstance(value, VarRef):
                # we delegate validation to QueryBlueprint class, which has context about variable types
                self._var_types[value] = (name, supported_args[name])
                self._arguments[name] = value
            elif _validate_arg_value(supported_args[name], value, self._strict):
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
        new = TypedFieldBlueprint(
            self._schema, fields[name], parent=self, strict=self._strict
        )
        self._children[name] = new
        return new

    def __getitem__(self, name: str) -> FieldBlueprint:
        if not isinstance(name, str):
            raise TypeError("key must be a string")
        if name in self._children:
            return self._children[name]
        fields = self._schema.get_type_fields(self._core_type)
        if name not in fields:
            raise KeyError(name)
        new = TypedFieldBlueprint(
            self._schema, fields[name], parent=self, strict=self._strict
        )
        self._children[name] = new
        return new
