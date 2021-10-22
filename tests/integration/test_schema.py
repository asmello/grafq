import os
from unittest import TestCase, main

from grafq.client import Client


class TestQueryBuilder(TestCase):
    def setUp(self) -> None:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError(
                "Missing Github API token (should be set as GITHUB_TOKEN environment variable)"
            )
        url = os.environ.get("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql")
        self.client = Client(url, token)

    def tearDown(self) -> None:
        self.client._session.close()

    def test_instantiation(self):
        schema = self.client.schema()
        self.assertIsNotNone(schema._types)
        self.assertIsNotNone(schema._root_fields)


if __name__ == "__main__":
    main()
