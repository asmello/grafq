from unittest import TestCase, main

from grafq.query import NamedType, Field, Selection
from grafq.query_builder import QueryBuilder
from grafq.selector import Selector


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
        query = QueryBuilder().select_field("myAddress").build()
        self.assertEqual("{myAddress}", str(query))
        self.assertEqual("{\n  myAddress\n}", query.pretty())

    def test_alias(self):
        query = QueryBuilder().select_field("myAddress", alias="myAlias").build()
        self.assertEqual("{myAlias:myAddress}", str(query))
        self.assertEqual("{\n  myAlias: myAddress\n}", query.pretty())

    def test_arguments(self):
        query = QueryBuilder().select_field("user", args={"id": 4}).build()
        self.assertEqual("{user(id:4)}", str(query))
        self.assertEqual("{\n  user(id: 4)\n}", query.pretty())

    def test_inner_fields(self):
        query = QueryBuilder().select_field("me", subfields=[Field("name")]).build()
        self.assertEqual("{me{name}}", str(query))
        self.assertEqual("{\n  me {\n    name\n  }\n}", query.pretty())

    def test_field_by_name(self):
        query = QueryBuilder().select_field("me", subfields=["name"]).build()
        self.assertEqual("{me{name}}", str(query))
        self.assertEqual("{\n  me {\n    name\n  }\n}", query.pretty())

    def test_multiple_fields(self):
        query = (
            QueryBuilder()
            .select_field(
                "me",
                subfields=[
                    Field("name"),
                    Field("friends", selection_set=[Selection(Field("name"))]),
                ],
            )
            .build()
        )
        self.assertEqual("{me{name,friends{name}}}", str(query))
        self.assertEqual(
            "{\n  me {\n    name\n    friends {\n      name\n    }\n  }\n}",
            query.pretty(),
        )

    def test_multiple_selects(self):
        query = (
            QueryBuilder()
            .select_field("other")
            .select_field("me", subfields=[Field("name")])
            .build()
        )
        self.assertEqual("{other,me{name}}", str(query))
        self.assertEqual("{\n  other\n  me {\n    name\n  }\n}", query.pretty())

    def test_all_together(self):
        query = (
            QueryBuilder()
            .name("foo")
            .var("myVar", NamedType("myType"), default=42)
            .select_field("other")
            .select_field("myAddress", alias="myAlias", args={"id": 4})
            .build()
        )
        self.assertEqual(
            "query foo($myVar:myType=42){other,myAlias:myAddress(id:4)}", str(query)
        )
        self.assertEqual(
            "query foo($myVar: myType = 42) {\n  other\n  myAlias: myAddress(id: 4)\n}",
            query.pretty(),
        )

    def test_select(self):
        query = (
            QueryBuilder()
            .select(
                Selector()
                .add("myAddress", alias="myAlias", args={"id": 4})
                .add("other")
                .render()
            )
            .build()
        )
        self.assertEqual("{myAlias:myAddress(id:4),other}", str(query))

    def test_select_multiple(self):
        query = (
            QueryBuilder()
            .select(
                Selector().add("myAddress", alias="myAlias", args={"id": 4}).render()
            )
            .select(Selector().add("other").render())
            .build()
        )
        self.assertEqual("{myAlias:myAddress(id:4),other}", str(query))

    def test_select_and_select_field(self):
        query = (
            QueryBuilder()
            .select(
                Selector().add("myAddress", alias="myAlias", args={"id": 4}).render()
            )
            .select_field("other")
            .build()
        )
        self.assertEqual("{myAlias:myAddress(id:4),other}", str(query))


if __name__ == "__main__":
    main()
