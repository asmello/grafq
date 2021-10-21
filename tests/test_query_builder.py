from unittest import TestCase, main

from grafq.dataclasses import NamedType
from grafq.query_builder import QueryBuilder


class TestQueryBuilder(TestCase):

    def test_empty(self):
        query = QueryBuilder().build()
        self.assertEqual("{ }", str(query))

    def test_short_form_with_name(self):
        query = QueryBuilder().name("foo").build()
        self.assertEqual("{ }", str(query))

    def test_one_var(self):
        query = QueryBuilder().name("foo").var("myVar", NamedType("myType")).build()
        self.assertEqual("query foo($myVar: myType) { }", str(query))

    def test_one_var_with_default(self):
        query = QueryBuilder().name("foo").var("myVar", NamedType("myType"), default=42).build()
        self.assertEqual("query foo($myVar: myType = 42) { }", str(query))

    def test_one_selection(self):
        query = QueryBuilder().select("myAddress").build()
        self.assertEqual("{ myAddress }", str(query))

    def test_alias(self):
        query = QueryBuilder().select("myAddress", alias="myAlias").build()
        self.assertEqual("{ myAlias: myAddress }", str(query))

    def test_arguments(self):
        query = QueryBuilder().select("user", args={'id': 4}).build()
        self.assertEqual("{ user(id: 4) }", str(query))

    def test_all_together(self):
        query = (QueryBuilder()
                 .name("foo")
                 .var("myVar", NamedType("myType"), default=42)
                 .select("myAddress", alias="myAlias", args={'id': 4})
                 .build())
        self.assertEqual("query foo($myVar: myType = 42) { myAlias: myAddress(id: 4) }", str(query))


if __name__ == '__main__':
    main()
