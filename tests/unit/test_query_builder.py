from unittest import TestCase, main

from grafq import Field
from grafq.language import NamedType, VarRef
from grafq.query_builder import QueryBuilder


class TestQueryBuilder(TestCase):
    def test_empty(self):
        query = QueryBuilder().build()
        self.assertEqual("{}", str(query))
        self.assertEqual("{ }", query.pretty())

    def test_short_form_with_name(self):
        query = QueryBuilder().name("foo").build()
        self.assertEqual("{}", str(query))
        self.assertEqual("{ }", query.pretty())

    def test_one_var(self):
        query = QueryBuilder().name("foo").var("myVar", NamedType("myType")).build()
        self.assertEqual("query foo($myVar:myType){}", str(query))
        self.assertEqual("query foo($myVar: myType) { }", query.pretty())

    def test_var_type_by_name(self):
        query = QueryBuilder().name("foo").var("myVar", "myType").build()
        self.assertEqual("query foo($myVar:myType){}", str(query))
        self.assertEqual("query foo($myVar: myType) { }", query.pretty())

    def test_one_var_with_default(self):
        query = (
            QueryBuilder()
            .name("foo")
            .var("myVar", NamedType("myType"), default=42)
            .build()
        )
        self.assertEqual("query foo($myVar:myType=42){}", str(query))
        self.assertEqual("query foo($myVar: myType = 42) { }", query.pretty())

    def test_one_selection(self):
        query = QueryBuilder().select("myAddress").build()
        self.assertEqual("{myAddress}", str(query))
        self.assertEqual("{\n  myAddress\n}", query.pretty())

    def test_alias(self):
        query = QueryBuilder().select(Field("myAddress").alias("myAlias")).build()
        self.assertEqual("{myAlias:myAddress}", str(query))
        self.assertEqual("{\n  myAlias: myAddress\n}", query.pretty())

    def test_arguments(self):
        query = QueryBuilder().select(Field("user", id=4)).build()
        self.assertEqual("{user(id:4)}", str(query))
        self.assertEqual("{\n  user(id: 4)\n}", query.pretty())

    def test_inner_field(self):
        query = QueryBuilder().select(Field("me").select("name")).build()
        self.assertEqual("{me{name}}", str(query))
        self.assertEqual("{\n  me {\n    name\n  }\n}", query.pretty())

    def test_inner_field_by_path(self):
        query = QueryBuilder().select("me.name").build()
        self.assertEqual("{me{name}}", str(query))
        self.assertEqual("{\n  me {\n    name\n  }\n}", query.pretty())

    def test_multiple_fields(self):
        query = QueryBuilder().select("me.name", "me.friends.name").build()
        self.assertEqual("{me{friends{name},name}}", str(query))
        self.assertEqual(
            "{\n  me {\n    friends {\n      name\n    }\n    name\n  }\n}",
            query.pretty(),
        )

    def test_multiple_selects(self):
        query = QueryBuilder().select("other").select("me.name").build()
        self.assertEqual("{me{name},other}", str(query))
        self.assertEqual("{\n  me {\n    name\n  }\n  other\n}", query.pretty())

    def test_composed(self):
        query = (
            QueryBuilder()
            .name("foo")
            .var("myVar", NamedType("myType"), default=42)
            .select("other")
            .select(Field("myAddress", id=4).alias("myAlias"))
            .build()
        )
        self.assertEqual(
            "query foo($myVar:myType=42){myAlias:myAddress(id:4),other}", str(query)
        )
        self.assertEqual(
            "query foo($myVar: myType = 42) {\n  myAlias: myAddress(id: 4)\n  other\n}",
            query.pretty(),
        )

    def test_composed_nested(self):
        query = (
            QueryBuilder()
            .var("size", "Int")
            .select(
                Field("viewer").select(
                    "login", "name", Field("avatarUrl", size=VarRef("size"))
                ),
                Field("repository", owner="asmello").arg("name", "grafq").select("url"),
            )
            .build()
        )
        self.assertEqual(
            'query($size:Int){repository(name:"grafq",owner:"asmello"){url},viewer{avatarUrl(size:$size),login,name}}',
            str(query),
        )


if __name__ == "__main__":
    main()
