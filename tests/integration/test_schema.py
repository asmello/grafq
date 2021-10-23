import os
from unittest import TestCase, main

from grafq import Field
from grafq.client import Client

REPO_NAME = "grafq"
REPO_OWNER = "asmello"


class TestSchema(TestCase):
    client = None

    @classmethod
    def setUpClass(cls) -> None:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError(
                "Missing Github API token (should be set as GITHUB_TOKEN environment variable)"
            )
        url = os.environ.get("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql")
        cls.client = Client(url, token)
        cls.schema = cls.client.schema

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client._session.close()

    def test_get_type(self):
        meta = self.schema.get_type("Repository")
        self.assertEqual("Repository", meta.name)

    def test_get_type_fields(self):
        meta = self.schema.get_type_fields("Label")
        self.assertIn("id", meta)
        self.assertIn("color", meta)

    def test_get_field(self):
        self.assertEqual("viewer", str(self.schema.viewer.build()))

    def test_get_nested_field(self):
        selection = self.schema.viewer.login
        self.assertEqual("login", str(selection.build()))
        self.assertEqual("viewer{login}", str(selection.root().build()))

    def test_get_invalid_field(self):
        with self.assertRaises(AttributeError):
            _ = self.schema.foo

    def test_get_invalid_nested_field(self):
        with self.assertRaises(AttributeError):
            _ = self.schema.viewer.foo

    def test_arguments(self):
        selection = self.schema.repository(name="foo", owner="bar").name
        self.assertEqual(
            'repository(name:"foo",owner:"bar"){name}',
            str(selection.root().build()),
        )

    def test_arguments_alternative(self):
        selection = self.schema.repository(name="foo").arg("owner", "bar").name
        self.assertEqual(
            'repository(name:"foo",owner:"bar"){name}',
            str(selection.root().build()),
        )

    def test_select(self):
        selection = self.schema.repository(name="foo", owner="bar").select(
            "name", Field("owner").select("login")
        )
        self.assertEqual(
            'repository(name:"foo",owner:"bar"){name,owner{login}}',
            str(selection.root().build()),
        )

    def test_alias(self):
        selection = self.schema.repository(name="foo", owner="bar").name.alias(
            "repoName"
        )
        self.assertEqual(
            'repository(name:"foo",owner:"bar"){repoName:name}',
            str(selection.root().build()),
        )

    def test_brackets_notation(self):
        selection = self.schema["repository"](name="foo", owner="bar")["name"]
        self.assertEqual(
            'repository(name:"foo",owner:"bar"){name}',
            str(selection.root().build()),
        )

    def test_brackets_bad_type(self):
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            _ = self.schema[42]
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            _ = self.schema.viewer[42]

    def test_simple_query(self):
        result = (
            self.client.new_query()
            .select(self.schema.repository(name=REPO_NAME, owner=REPO_OWNER).name)
            .build_and_run()
        )
        self.assertDictEqual({"repository": {"name": REPO_NAME}}, result)

    def test_reuse_query(self):
        repository = self.schema.repository(name=REPO_NAME, owner=REPO_OWNER)
        result = (
            self.client.new_query()
            .select(repository.name, repository.owner.login)
            .build_and_run()
        )
        self.assertDictEqual(
            {"repository": {"name": REPO_NAME, "owner": {"login": REPO_OWNER}}}, result
        )

    def test_mixed_query(self):
        result = (
            self.client.new_query()
            .select(
                self.schema.repository(name=REPO_NAME, owner=REPO_OWNER).name,
                Field("repository", name=REPO_NAME, owner=REPO_OWNER).select(
                    Field("owner").select("login")
                ),
            )
            .build_and_run()
        )
        self.assertDictEqual(
            {"repository": {"name": REPO_NAME, "owner": {"login": REPO_OWNER}}}, result
        )

    def test_select_query(self):
        result = (
            self.client.new_query()
            .select(
                self.schema.repository(name=REPO_NAME, owner=REPO_OWNER).select(
                    "name", Field("owner").select("login")
                )
            )
            .build_and_run()
        )
        self.assertDictEqual(
            {"repository": {"name": REPO_NAME, "owner": {"login": REPO_OWNER}}}, result
        )


if __name__ == "__main__":
    main()
