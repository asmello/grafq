from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from grafq import Field, QueryBuilder

if TYPE_CHECKING:
    from grafq.client import Client
    from grafq.language import Query


ScalarType = Union[str, int, float, bool, list["ScalarType"], dict[str, "ScalarType"]]


@dataclass
class SchemaType:
    name: str
    kind: str
    description: str


@dataclass
class FieldArgument:
    name: str
    type: str
    description: Optional[str] = None
    default_value: Optional[str] = None


@dataclass
class SchemaField:
    name: str
    type: str
    args: dict[str, FieldArgument]
    description: Optional[str] = None
    is_deprecated: bool = False
    deprecation_reason: Optional[str] = None


class Schema:

    query: Query = (
        QueryBuilder()
        .select(
            Field("__schema").select(
                Field("types").select("name", "kind", "description"),
                Field("queryType").select("name"),
            )
        )
        .build()
    )

    def __init__(self, client: Client, fetch: bool = False):
        self._client = client
        self._types: Optional[dict[str, SchemaType]] = None
        self._root_fields: Optional[dict[str, SchemaField]] = None
        if fetch:
            self.fetch()

    def fetch(self) -> None:
        schema = self._client.get(Schema.query)["__schema"]
        self._types = {
            t["name"]: SchemaType(t["name"], t["kind"], t["description"])
            for t in schema["types"]
        }
        fields = (
            QueryBuilder(self._client)
            .select(
                Field("__type", name=schema["queryType"]["name"]).select(
                    Field("fields", includeDeprecated=True).select(
                        "name",
                        "description",
                        Field("args").select(
                            "name",
                            "description",
                            Field("type").select("name"),
                            "defaultValue",
                        ),
                        Field("type").select("name"),
                        "isDeprecated",
                        "deprecationReason",
                    )
                )
            )
            .build_and_execute()
        )
        self._root_fields = {
            field["name"]: SchemaField(
                name=field["name"],
                type=field["type"]["name"],
                description=field["description"],
                args={
                    arg["name"]: FieldArgument(
                        name=arg["name"],
                        type=arg["type"]["name"],
                        description=arg.get("description"),
                        default_value=arg.get("defaultValue"),
                    )
                    for arg in field["args"]
                },
                is_deprecated=field["isDeprecated"],
                deprecation_reason=field["deprecationReason"],
            )
            for field in fields["__type"]["fields"]
        }
