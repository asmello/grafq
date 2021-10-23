from unittest import TestCase, main

from grafq import Field, QueryBlueprint
from grafq.language import NamedType, VarRef


class TestQueryBuilder(TestCase):
    def test_empty(self):
        query = QueryBlueprint().build()
        self.assertEqual("{}", str(query))
        self.assertEqual("{ }", query.pretty())

    def test_short_form_with_name(self):
        query = QueryBlueprint().name("foo").build()
        self.assertEqual("{}", str(query))
        self.assertEqual("{ }", query.pretty())

    def test_one_var(self):
        query = QueryBlueprint().name("foo").var("myVar", NamedType("myType")).build()
        self.assertEqual("query foo($myVar:myType){}", str(query))
        self.assertEqual("query foo($myVar: myType) { }", query.pretty())

    def test_var_type_by_name(self):
        query = QueryBlueprint().name("foo").var("myVar", "myType").build()
        self.assertEqual("query foo($myVar:myType){}", str(query))
        self.assertEqual("query foo($myVar: myType) { }", query.pretty())

    def test_one_var_with_default(self):
        query = (
            QueryBlueprint()
            .name("foo")
            .var("myVar", NamedType("myType"), default=42)
            .build()
        )
        self.assertEqual("query foo($myVar:myType=42){}", str(query))
        self.assertEqual("query foo($myVar: myType = 42) { }", query.pretty())

    def test_one_selection(self):
        query = QueryBlueprint().select("myAddress").build()
        self.assertEqual("{myAddress}", str(query))
        self.assertEqual("{\n  myAddress\n}", query.pretty())

    def test_alias(self):
        query = QueryBlueprint().select(Field("myAddress").alias("myAlias")).build()
        self.assertEqual("{myAlias:myAddress}", str(query))
        self.assertEqual("{\n  myAlias: myAddress\n}", query.pretty())

    def test_arguments(self):
        query = QueryBlueprint().select(Field("user", id=4)).build()
        self.assertEqual("{user(id:4)}", str(query))
        self.assertEqual("{\n  user(id: 4)\n}", query.pretty())

    def test_inner_field(self):
        query = QueryBlueprint().select(Field("me").select("name")).build()
        self.assertEqual("{me{name}}", str(query))
        self.assertEqual("{\n  me {\n    name\n  }\n}", query.pretty())

    def test_inner_field_by_path(self):
        query = QueryBlueprint().select("me.name").build()
        self.assertEqual("{me{name}}", str(query))
        self.assertEqual("{\n  me {\n    name\n  }\n}", query.pretty())

    def test_multiple_fields(self):
        query = QueryBlueprint().select("me.name", "me.friends.name").build()
        self.assertEqual("{me{name,friends{name}}}", str(query))
        self.assertEqual(
            "{\n  me {\n    name\n    friends {\n      name\n    }\n  }\n}",
            query.pretty(),
        )

    def test_multiple_selects(self):
        query = QueryBlueprint().select("other").select("me.name").build()
        self.assertEqual("{other,me{name}}", str(query))
        self.assertEqual("{\n  other\n  me {\n    name\n  }\n}", query.pretty())

    def test_composed(self):
        query = (
            QueryBlueprint()
            .name("foo")
            .var("myVar", NamedType("myType"), default=42)
            .select("other")
            .select(Field("myAddress", id=4).alias("myAlias"))
            .build()
        )
        self.assertEqual(
            "query foo($myVar:myType=42){other,myAlias:myAddress(id:4)}", str(query)
        )
        self.assertEqual(
            "query foo($myVar: myType = 42) {\n  other\n  myAlias: myAddress(id: 4)\n}",
            query.pretty(),
        )

    def test_composed_nested(self):
        query = (
            QueryBlueprint()
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
            'query($size:Int){viewer{login,name,avatarUrl(size:$size)},repository(name:"grafq",owner:"asmello"){url}}',
            str(query),
        )


if __name__ == "__main__":
    main()
