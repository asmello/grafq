from __future__ import annotations

from typing import Optional, Union, TYPE_CHECKING

from grafq.blueprints import TypedFieldBlueprint
from grafq.blueprints.base import Blueprint
from grafq.blueprints.field.base import coerce, FieldBlueprint

if TYPE_CHECKING:
    from grafq.schema import Schema, SchemaType
    from grafq.client import Client
from grafq.language import (
    VariableDefinition,
    VariableType,
    Value,
    Selection,
    Query,
    NamedType,
    ValueRawType,
    NonNullType,
    ListType,
    ID,
    ScalarExtension,
    NullType,
)


def _decode_variable_type_str(spec: str) -> VariableType:
    if spec.endswith("!"):
        wrapped_type = _decode_variable_type_str(spec[:-1])
        if isinstance(wrapped_type, (ListType, NamedType)):
            return NonNullType(wrapped_type)
        raise RuntimeError("Recursion resulted in illegal type, this is a logic error")
    elif len(spec) > 2 and spec[0] == "[" and spec[-1] == "]":
        return ListType(_decode_variable_type_str(spec[1:-1]))
    return NamedType(spec)


def _type_matches(var_type: VariableType, schema_type: SchemaType):
    if isinstance(var_type, NonNullType) and schema_type.kind == "NON_NULL":
        return _type_matches(var_type.subtype, schema_type.of_type)
    if isinstance(var_type, ListType) and schema_type.kind == "LIST":
        return _type_matches(var_type.subtype, schema_type.of_type)
    if isinstance(var_type, NamedType):
        return var_type.name == schema_type.name
    raise RuntimeError("Invalid variable type passed to function")


class QueryBlueprint(Blueprint):
    def __init__(
        self, client: Optional[Client] = None, schema: Optional[Schema] = None
    ):
        self._client = client
        self._name: Optional[str] = None
        self._variable_definitions: dict[str, VariableDefinition] = {}
        self._fields: dict[str, FieldBlueprint] = {}
        self._schema = schema

    def name(self, name: str) -> QueryBlueprint:
        self._name = name
        return self

    def var(
        self,
        name: str,
        var_type: Union[VariableType, str],
        default: Optional[ValueRawType] = None,
    ) -> QueryBlueprint:
        if isinstance(var_type, str):
            var_type = _decode_variable_type_str(var_type)
        core_type = var_type.core_type_name()
        if self._schema and not self._schema.is_valid_type(core_type):
            raise TypeError(f"Type does not exist: {core_type}")
        if default is not None:
            if self._schema:
                if not self._schema.is_representable(default):
                    raise TypeError(f"Not representable: {default}")
                if not self._variable_accepts(var_type, default):
                    raise TypeError(
                        f"Mismatched type for default value: {default} for {var_type}"
                    )
            default = Value(default)
        self._variable_definitions[name] = VariableDefinition(name, var_type, default)
        return self

    def _variable_accepts(self, value_type: VariableType, value) -> bool:
        if not self._schema:
            # Without schema validation cannot be performed
            return True
        if not self._schema.is_valid_type(value_type.core_type_name()):
            raise TypeError(f"{value_type.core_type_name()} does not exist")
        if isinstance(value_type, NamedType):
            if value_type.name == "Int":
                return isinstance(value, int)
            if value_type.name == "Float":
                return isinstance(value, float)
            if value_type.name == "String":
                return isinstance(value, str)
            if value_type.name == "Boolean":
                return isinstance(value, bool)
            if value_type.name == "ID":
                if self._schema.is_strict:
                    return isinstance(value, ID)
                return isinstance(value, (ID, str))
            return (
                isinstance(value, ScalarExtension)
                and type(value).__name__ == value_type.name
            )
        if isinstance(value_type, ListType):
            if not isinstance(value, list):
                return False
            if not value:
                return True
            return self._variable_accepts(value_type.subtype, value[0])
        if isinstance(value_type, NonNullType):
            if value is None:
                return False
            if isinstance(value, NullType):
                return False
            return self._variable_accepts(value_type.subtype, value)
        if not isinstance(value_type, VariableType):
            raise TypeError(f"{value_type} is not a variable type")
        else:
            raise RuntimeError(f"Received instance of abstract class VariableType!")

    def select(self, *specs: Union[str, FieldBlueprint]) -> QueryBlueprint:
        new_field_blueprints = [coerce(spec) for spec in specs]
        for new_field_blueprint in new_field_blueprints:
            if isinstance(new_field_blueprint, TypedFieldBlueprint):
                var_types = new_field_blueprint.get_variable_types()
                for var_ref, (arg_name, expected_type) in var_types.items():
                    var_def = self._variable_definitions[var_ref.name]
                    if not _type_matches(var_def.type, expected_type):
                        raise TypeError(
                            f"Invalid usage of variable {var_ref.name} "
                            f"as argument {arg_name} of type {expected_type.core_type.name} "
                            f"at field {new_field_blueprint.get_name()}"
                        )
        FieldBlueprint.combine(self._fields, new_field_blueprints)
        return self

    def build(self, shorthand: bool = True) -> Query:
        return Query(
            selection_set=[Selection(field.build()) for field in self._fields.values()],
            name=self._name,
            variable_definitions=list(self._variable_definitions.values()),
            shorthand=shorthand,
            client=self._client,
        )

    def build_and_run(
        self,
        client: Optional[Client] = None,
        variables: Optional[dict[str, ValueRawType]] = None,
    ) -> dict:
        client = client or self._client
        if not client:
            raise RuntimeError("Must provide a client to execute query")
        return client.post(self.build(), variables)
