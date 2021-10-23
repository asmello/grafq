import os
from unittest import TestCase, main

from grafq.client import Client


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
        blueprint = self.schema.viewer.login
        self.assertEqual("login", str(blueprint.build()))
        self.assertEqual("viewer{login}", str(blueprint.root().build()))

    def test_arguments(self):
        query = self.schema.repository(name="grafq", owner="asmello").name
        self.assertEqual(
            'repository(name:"grafq",owner:"asmello"){name}', str(query.root().build())
        )

    def test_get_invalid_field(self):
        with self.assertRaises(AttributeError):
            _ = self.schema.foo

    def test_get_invalid_nested_field(self):
        with self.assertRaises(AttributeError):
            _ = self.schema.viewer.foo


if __name__ == "__main__":
    main()
