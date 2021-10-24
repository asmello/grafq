from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from grafq.blueprints import FieldBlueprint, QueryBlueprint, TypedFieldBlueprint

if TYPE_CHECKING:
    from grafq.client import Client

from grafq.language import Query


@dataclass(frozen=True, order=True)
class InputValue:
    name: str
    type: SchemaType
    description: Optional[str] = None
    default_value: Optional[str] = None

    @classmethod
    def from_dict(cls, schema: Schema, d: dict) -> InputValue:
        return cls(
            name=d["name"],
            type=SchemaType.from_dict(schema, d["type"]),
            description=d.get("description"),
            default_value=d.get("defaultValue"),
        )


@dataclass(frozen=True, order=True)
class EnumValue:
    name: str
    description: Optional[str]
    is_deprecated: bool = False
    deprecation_reason: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> EnumValue:
        return cls(
            name=d["name"],
            description=d.get("description"),
            is_deprecated=d.get("isDeprecated"),
            deprecation_reason=d.get("deprecationReason"),
        )


class UnfetchedGuardType:
    pass


Unfetched = UnfetchedGuardType()


class SchemaType:
    def __init__(
        self,
        schema: Schema,
        kind: str,
        name: Optional[str] = None,
        of_type: Optional[dict] = None,
        description: Union[str, None, UnfetchedGuardType] = Unfetched,
        fields: Union[list[FieldMeta], None, UnfetchedGuardType] = Unfetched,
        interfaces: Union[list[SchemaType], None, UnfetchedGuardType] = Unfetched,
        possible_types: Union[list[SchemaType], None, UnfetchedGuardType] = Unfetched,
        enum_values: Union[list[EnumValue], None, UnfetchedGuardType] = Unfetched,
        input_fields: Union[list[InputValue], None, UnfetchedGuardType] = Unfetched,
    ):
        self._schema = schema
        self._kind = kind
        self._name = name  # None for wrapping types (LIST, NON_NULL)
        self._of_type: Optional[SchemaType] = None
        if of_type:
            self._of_type = SchemaType(
                schema, of_type["kind"], of_type.get("name"), of_type.get("ofType")
            )
        self._description = description
        self._fields = fields
        self._interfaces = interfaces
        self._possible_types = possible_types
        self._enum_values = enum_values
        self._input_fields = input_fields

    @classmethod
    def from_dict(cls, schema: Schema, d: dict) -> SchemaType:
        return cls(
            schema=schema,
            kind=d["kind"],
            name=d["name"],  # can be null, but is always required in payload
            description=d["description"] if "description" in d else Unfetched,
            fields=d["fields"] if "fields" in d else Unfetched,
            # assumed to be None if missing (assumption required due to recursion limit)
            of_type=d.get("ofType"),
        )

    @property
    def kind(self) -> str:
        return self._kind

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def description(self) -> Optional[str]:
        if not self._name:
            return None
        if self._description is Unfetched:
            self._description = self._schema.get_type_description(self._name)
        return self._description

    @property
    def fields(self) -> Optional[dict[str, FieldMeta]]:
        if not self._name:
            return None
        if self._fields is Unfetched:
            self._fields = self._schema.get_type_fields(self._name)
        return self._fields

    @property
    def interfaces(self) -> Optional[list[SchemaType]]:
        if not self._name:
            return None
        if self._interfaces is Unfetched:
            self._interfaces = self._schema.get_type_interfaces(self._name)
        return self._interfaces

    @property
    def possible_types(self) -> Optional[list[SchemaType]]:
        if not self._name:
            return None
        if self._possible_types is Unfetched:
            self._possible_types = self._schema.get_type_possible_types(self._name)
        return self._possible_types

    @property
    def enum_values(self) -> Optional[list[EnumValue]]:
        if not self._name:
            return None
        if self._enum_values is Unfetched:
            self._enum_values = self._schema.get_type_enum_values(self._name)
        return self._enum_values

    @property
    def input_fields(self) -> Optional[list[EnumValue]]:
        if not self._name:
            return None
        if self._input_fields is Unfetched:
            self._input_fields = self._schema.get_type_input_fields(self._name)
        return self._input_fields

    @property
    def of_type(self) -> Optional[SchemaType]:
        return self._of_type


class FieldMeta:
    def __init__(
        self,
        schema: Schema,
        name: str,
        args: list[InputValue],
        field_type: SchemaType,
        is_deprecated: bool = False,
        deprecation_reason: Union[str, None, UnfetchedGuardType] = Unfetched,
        description: Union[str, None, UnfetchedGuardType] = Unfetched,
    ):
        self._schema = schema
        self._name = name
        self._description = description
        self._args = args
        self._type = field_type
        self._is_deprecated = is_deprecated
        self._deprecation_reason = deprecation_reason

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def args(self) -> list[InputValue]:
        return self._args

    @property
    def type(self) -> SchemaType:
        return self._type

    @property
    def is_deprecated(self) -> bool:
        return self._is_deprecated

    @property
    def deprecation_reason(self) -> Optional[str]:
        return self._deprecation_reason

    @classmethod
    def from_dict(cls, schema: Schema, d: dict) -> FieldMeta:
        return cls(
            schema=schema,
            name=d["name"],
            args=[
                InputValue(
                    name=value["name"],
                    type=SchemaType.from_dict(schema, value["type"]),
                    description=value["description"],
                    default_value=value["defaultValue"],
                )
                for value in d["args"]
            ],
            field_type=SchemaType.from_dict(schema, d["type"]),
            is_deprecated=d["isDeprecated"],
            deprecation_reason=d["deprecationReason"]
            if "deprecationReason" in d
            else Unfetched,
        )


ROOT_QUERY: Query = (
    QueryBlueprint()
    .select(
        FieldBlueprint("__schema").select(FieldBlueprint("queryType").select("name"))
    )
    .build()
)
# As an odd quirk of GraphQL introspection, we can't incrementally unwrap types as we can only query types by name,
# and wrapped types are anonymous. To get around that, we recurse in the query as many levels as possible, which
# should get us a terminal type from any sensible API.
OF_TYPE_FRAGMENT = FieldBlueprint("ofType").select(
    "name",
    "kind",
    FieldBlueprint("ofType").select(
        "name",
        "kind",
        FieldBlueprint("ofType").select(
            "name",
            "kind",
            FieldBlueprint("ofType").select(
                "name",
                "kind",
                FieldBlueprint("ofType").select(
                    "name",
                    "kind",
                    FieldBlueprint("ofType").select(
                        "name",
                        "kind",
                        FieldBlueprint("ofType").select(
                            "name",
                            "kind",
                        ),
                    ),
                ),
            ),
        ),
    ),
)
TYPE_FRAGMENT = FieldBlueprint("type").select("name", "kind", OF_TYPE_FRAGMENT)


class Schema:
    def __init__(self, client: Client, strict: bool = False):
        self._client = client
        schema = client.get(ROOT_QUERY)["__schema"]
        self._root_fields = self.get_type_fields(schema["queryType"]["name"])
        self._strict = strict

    def get_type(self, name: str) -> SchemaType:
        spec = (
            self._client.new_query()
            .select(
                FieldBlueprint("__type", name=name).select(
                    "kind", "name", OF_TYPE_FRAGMENT
                )
            )
            .build_and_run()
        )
        return SchemaType.from_dict(self, spec["__type"])

    def get_type_description(self, name: str) -> Optional[str]:
        result = (
            self._client.new_query()
            .select(FieldBlueprint("__type", name=name).select("description"))
            .build_and_run()
        )
        return result["__type"]["description"]

    def get_type_fields(self, name: str) -> dict[str, FieldMeta]:
        fields = (
            self._client.new_query()
            .select(
                FieldBlueprint("__type", name=name).select(
                    FieldBlueprint("fields", includeDeprecated=True).select(
                        "name",
                        "description",
                        FieldBlueprint("args").select(
                            "name",
                            "description",
                            TYPE_FRAGMENT,
                            "defaultValue",
                        ),
                        TYPE_FRAGMENT,
                        "isDeprecated",
                        "deprecationReason",
                    )
                )
            )
            .build_and_run()
        )
        fields = fields["__type"].get("fields")
        return (
            {field["name"]: FieldMeta.from_dict(self, field) for field in fields}
            if fields
            else None
        )

    def get_type_interfaces(self, name: str) -> Optional[list[SchemaType]]:
        result = (
            self._client.new_query()
            .select(
                FieldBlueprint("__type", name=name).select(
                    FieldBlueprint("interfaces").select(
                        "name", "kind", OF_TYPE_FRAGMENT
                    )
                )
            )
            .build_and_run()
        )
        interfaces = result["__type"].get("interfaces")
        return (
            [SchemaType.from_dict(self, interface) for interface in interfaces]
            if interfaces
            else None
        )

    def get_type_possible_types(self, name: str) -> Optional[list[SchemaType]]:
        result = (
            self._client.new_query()
            .select(
                FieldBlueprint("__type", name=name).select(
                    FieldBlueprint("possibleTypes").select(
                        "name", "kind", OF_TYPE_FRAGMENT
                    )
                )
            )
            .build_and_run()
        )
        possible_types = result["__type"].get("possibleTypes")
        return (
            [
                SchemaType.from_dict(self, possible_type)
                for possible_type in possible_types
            ]
            if possible_types
            else None
        )

    def get_type_enum_values(self, name: str) -> Optional[list[EnumValue]]:
        result = (
            self._client.new_query()
            .select(
                FieldBlueprint("__type", name=name).select(
                    FieldBlueprint("enumValues", includeDeprecated=True).select(
                        "name", "description", "isDeprecated", "deprecationReason"
                    )
                )
            )
            .build_and_run()
        )
        enum_values = result["__type"].get("enumValues")
        return (
            [EnumValue.from_dict(value) for value in enum_values]
            if enum_values
            else None
        )

    def get_type_input_fields(self, name: str) -> Optional[list[InputValue]]:
        result = (
            self._client.new_query()
            .select(
                FieldBlueprint("__type", name=name).select(
                    FieldBlueprint("inputFields").select(
                        "name", "description", TYPE_FRAGMENT, "defaultValue"
                    )
                )
            )
            .build_and_run()
        )
        input_fields = result["__type"].get("inputFields")
        return (
            [InputValue.from_dict(self, value) for value in input_fields]
            if input_fields
            else None
        )

    def __getattr__(self, name: str) -> TypedFieldBlueprint:
        if name not in self._root_fields:
            raise AttributeError(name)
        return TypedFieldBlueprint(self, self._root_fields[name], strict=self._strict)

    def __getitem__(self, name: str) -> TypedFieldBlueprint:
        if not isinstance(name, str):
            raise TypeError("key must must be a string")
        if name not in self._root_fields:
            raise KeyError(name)
        return TypedFieldBlueprint(self, self._root_fields[name], strict=self._strict)
