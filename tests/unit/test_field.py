from unittest import TestCase, main

from grafq import Field
from grafq.language import Argument, Value, Field as FrozenField


class TestField(TestCase):
    def test_name(self):
        field = Field("test").build()
        self.assertEqual("test", field.name)

    def test_argument(self):
        field = Field("test", foo="bar").build()
        self.assertEqual(Argument("foo", Value("bar")), field.arguments[0])

    def test_multiple_arguments(self):
        field = Field("test", id=42, foo="bar").build()
        self.assertEqual(
            [Argument("foo", Value("bar")), Argument("id", Value(42))], field.arguments
        )
        self.assertEqual('test(foo:"bar",id:42)', str(field))

    def test_select(self):
        field = Field("test").select("inner").build()
        self.assertEqual(FrozenField("inner"), field.selection_set[0].field)
        self.assertEqual("test{inner}", str(field))

    def test_select_multiple(self):
        field = Field("test").select("foo", "bar").build()
        self.assertEqual(FrozenField("foo"), field.selection_set[0].field)
        self.assertEqual(FrozenField("bar"), field.selection_set[1].field)
        self.assertEqual("test{foo,bar}", str(field))

    def test_arg_interface(self):
        field = Field("test").arg("foo", "bar").build()
        self.assertEqual(Argument("foo", Value("bar")), field.arguments[0])
        self.assertEqual('test(foo:"bar")', str(field))

    def test_alias(self):
        field = Field("test").alias("alt").build()
        self.assertEqual("alt", field.alias)
        self.assertEqual("alt:test", str(field))


if __name__ == "__main__":
    main()
