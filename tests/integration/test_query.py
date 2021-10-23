import os
from unittest import TestCase, main

from grafq.client import Client


class TestQuery(TestCase):
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

    def test_simple(self):
        result = (
            self.client.new_query()
            .select(self.schema.repository(name="grafq", owner="asmello").name)
            .build_and_run()
        )
        self.assertEqual("grafq", result["repository"]["name"])


if __name__ == "__main__":
    main()
