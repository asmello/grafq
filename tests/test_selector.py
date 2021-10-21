from unittest import TestCase, main

from grafq.query import VarRef, Selection, Field, Argument, Value
from grafq.selector import Selector


class TestSelector(TestCase):
    def test_simple(self):
        generated = Selector().add("me").render()
        expected = [Selection(Field("me"))]
        self.assertEqual(expected, generated)

    def test_add_multiple(self):
        generated = Selector().add("firstName").add("lastName").render()
        expected = [Selection(Field("firstName")), Selection(Field("lastName"))]
        self.assertEqual(expected, generated)

    def test_into(self):
        generated = Selector().add("me").into().add("id").render()
        expected = [Selection(Field("me", selection_set=[Selection(Field("id"))]))]
        self.assertEqual(expected, generated)

    def test_back(self):
        generated = Selector().add("me").into().back().render()
        expected = [Selection(Field("me"))]
        self.assertEqual(expected, generated)

    def test_into_add_and_back(self):
        generated = Selector().add("me").into().add("id").back().render()
        expected = [Selection(Field("me", selection_set=[Selection(Field("id"))]))]
        self.assertEqual(expected, generated)

    def test_args(self):
        generated = Selector().add("user", args={"id": 1}).render()
        expected = [Selection(Field("user", arguments=[Argument("id", Value(1))]))]
        self.assertEqual(expected, generated)

    def test_alias(self):
        generated = Selector().add("me", alias="myself").render()
        expected = [Selection(Field("me", alias="myself"))]
        self.assertEqual(expected, generated)

    def test_complex(self):
        generated = (
            Selector()
            .add("viewer")
            .into()
            .add("avatarUrl", args={"size": VarRef("size")})
            .add("login")
            .add("name")
            .back()
            .add("repository", args={"name": "grafq", "owner": "asmello"})
            .into()
            .add("url")
            .render()
        )
        expected = [
            Selection(
                Field(
                    "viewer",
                    selection_set=[
                        Selection(
                            Field(
                                "avatarUrl",
                                arguments=[Argument("size", Value(VarRef("size")))],
                            )
                        ),
                        Selection(Field("login")),
                        Selection(Field("name")),
                    ],
                )
            ),
            Selection(
                Field(
                    "repository",
                    arguments=[
                        Argument("name", Value("grafq")),
                        Argument("owner", Value("asmello")),
                    ],
                    selection_set=[Selection(Field("url"))],
                )
            ),
        ]
        self.assertEqual(expected, generated)


if __name__ == "__main__":
    main()
