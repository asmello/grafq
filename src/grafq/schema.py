from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from grafq.field_blueprint import FieldBlueprint
from grafq.query_blueprint import QueryBlueprint
from grafq.typed_field_blueprint import TypedFieldBlueprint

if TYPE_CHECKING:
    from grafq.client import Client

from grafq.language import Query

ScalarType = Union[str, int, float, bool, list["ScalarType"], dict[str, "ScalarType"]]


@dataclass(frozen=True, order=True)
class ID:
    value: str


@dataclass(frozen=True, order=True)
class InputValue:
    name: str
    type: SchemaType
    description: Optional[str] = None
    default_value: Optional[str] = None


@dataclass(frozen=True, order=True)
class EnumValue:
    name: str
    description: Optional[str]
    is_deprecated: bool = False
    deprecation_reason: Optional[str] = None


@dataclass(frozen=True, order=True)
class SchemaType:
    kind: str
    name: Optional[str] = None
    description: Optional[str] = None
    enum_values: Optional[list[EnumValue]] = None
    input_fields: Optional[list[InputValue]] = None
    of_type: Optional[SchemaType] = None

    @classmethod
    def from_dict(cls, d: dict) -> SchemaType:
        return cls(
            kind=d["kind"],
            name=d.get("name"),
            description=d.get("description"),
            enum_values=[
                EnumValue(
                    name=enum_value["name"],
                    description=enum_value.get("description"),
                    is_deprecated=enum_value.get("isDeprecated"),
                    deprecation_reason=enum_value.get("deprecationReason"),
                )
                for enum_value in d["enumValues"]
            ]
            if d.get("enumValues")
            else None,
            input_fields=[
                InputValue(
                    name=input_value["name"],
                    type=SchemaType.from_dict(input_value["type"]),
                    description=input_value.get("description"),
                    default_value=input_value.get("defaultValue"),
                )
                for input_value in d["inputFields"]
            ]
            if d.get("inputFields")
            else None,
            of_type=SchemaType.from_dict(d["ofType"]) if d.get("ofType") else None,
        )


@dataclass(frozen=True, order=True)
class FieldMeta:
    name: str
    type: SchemaType
    args: list[InputValue]
    description: Optional[str] = None
    is_deprecated: bool = False
    deprecation_reason: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> FieldMeta:
        return cls(
            name=d["name"],
            description=d.get("description"),
            args=[
                InputValue(
                    name=value["name"],
                    description=value["description"],
                    type=value["type"],
                    default_value=value["defaultValue"],
                )
                for value in d["args"]
            ],
            type=SchemaType.from_dict(d["type"]),
            is_deprecated=d["isDeprecated"],
            deprecation_reason=d["deprecationReason"],
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
    def __init__(self, client: Client):
        self._client = client
        schema = client.get(ROOT_QUERY)["__schema"]
        self._root_fields = self.get_type_fields(schema["queryType"]["name"])

    def get_type(self, name: str) -> SchemaType:
        spec = (
            self._client.new_query()
            .select(
                FieldBlueprint("__type", name=name).select(
                    "kind",
                    "name",
                    "description",
                    FieldBlueprint("interfaces").select(
                        "name", "kind", OF_TYPE_FRAGMENT
                    ),
                    FieldBlueprint("possibleTypes").select(
                        "name", "kind", OF_TYPE_FRAGMENT
                    ),
                    FieldBlueprint("enumValues", includeDeprecated=True).select(
                        "name", "description", "isDeprecated", "deprecationReason"
                    ),
                    FieldBlueprint("inputFields").select(
                        "name", "description", TYPE_FRAGMENT, "defaultValue"
                    ),
                    OF_TYPE_FRAGMENT,
                )
            )
            .build_and_run()
        )
        return SchemaType.from_dict(spec["__type"])

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
        return {
            field["name"]: FieldMeta.from_dict(field)
            for field in fields["__type"].get("fields", ())
        }

    def __getattr__(self, name: str) -> TypedFieldBlueprint:
        if name not in self._root_fields:
            raise AttributeError(name)
        return TypedFieldBlueprint(self, self._root_fields[name])

    def __getitem__(self, name: str) -> TypedFieldBlueprint:
        if not isinstance(name, str):
            raise TypeError("key must must be a string")
        if name not in self._root_fields:
            raise KeyError(name)
        return TypedFieldBlueprint(self, self._root_fields[name])
