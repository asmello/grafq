import os
from unittest import TestCase, main, skipIf

from grafq import Field
from grafq.client import Client
from grafq.language import ID, Null, ScalarExtension, VarRef


@skipIf(
    os.environ.get("GITHUB_TOKEN") is None
    or os.environ.get("GITHUB_REPOSITORY") is None,
    "Must set GITHUB_TOKEN and GITHUB_REPOSITORY environment variables to be able to run these tests.",
)
class TestSchema(TestCase):
    client = None

    @classmethod
    def setUpClass(cls) -> None:
        token = os.environ.get("GITHUB_TOKEN")
        url = os.environ.get("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql")
        repo_parts = os.environ.get("GITHUB_REPOSITORY").split("/")
        cls.repo_owner = repo_parts[0]
        cls.repo_name = repo_parts[1]
        cls.client = Client(url, token)
        cls.schema = cls.client.schema()
        cls.strict_schema = cls.client.schema(strict=True)

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

    def test_id_type(self):
        selection = self.schema.node(id=ID("R_kgDOGQovbg")).id
        self.assertEqual(
            'node(id:"R_kgDOGQovbg"){id}',
            str(selection.root().build()),
        )

    def test_strict_id_type(self):
        with self.assertRaises(TypeError):
            _ = self.strict_schema.node(id="R_kgDOGQovbg").id

    def test_id_type_coercion(self):
        selection = self.schema.node(id="R_kgDOGQovbg").id
        self.assertEqual(
            'node(id:"R_kgDOGQovbg"){id}',
            str(selection.root().build()),
        )

    def test_int_type(self):
        selection = self.schema.viewer.avatarUrl(size=200)
        self.assertEqual(
            "viewer{avatarUrl(size:200)}",
            str(selection.root().build()),
        )

    def test_boolean_type(self):
        selection = self.schema.rateLimit(dryRun=True)
        self.assertEqual(
            "rateLimit(dryRun:true)",
            str(selection.root().build()),
        )

    def test_list_type(self):
        selection = self.schema.nodes(ids=[ID("R_kgDOGQovbg")]).id
        self.assertEqual(
            'nodes(ids:["R_kgDOGQovbg"]){id}',
            str(selection.root().build()),
        )

    def test_null_check(self):
        with self.assertRaises(TypeError):
            _ = self.schema.node(id=None).id
        with self.assertRaises(TypeError):
            _ = self.schema.node(id=Null).id

    def test_complex_arguments(self):
        selection = self.schema.viewer.pullRequests(
            states=["OPEN"], after="foobar", first=10, labels=["test"]
        ).totalCount
        self.assertEqual(
            'viewer{pullRequests(states:["OPEN"],after:"foobar",first:10,labels:["test"]){totalCount}}',
            str(selection.root().build()),
        )

    def test_extension_type(self):
        selection = self.schema.resource(url="https://github.com/").url
        self.assertEqual(
            'resource(url:"https://github.com/"){url}',
            str(selection.root().build()),
        )

    def test_strict_extension_type(self):
        class URI(ScalarExtension):
            pass

        selection = self.strict_schema.resource(url=URI("https://github.com/")).url
        self.assertEqual(
            'resource(url:"https://github.com/"){url}',
            str(selection.root().build()),
        )

    def test_strict_extension_type_validation(self):
        with self.assertRaises(TypeError):
            _ = self.strict_schema.resource(url="https://github.com/").url

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
            .select(
                self.schema.repository(name=self.repo_name, owner=self.repo_owner).name
            )
            .build_and_run()
        )
        self.assertDictEqual({"repository": {"name": self.repo_name}}, result)

    def test_reuse_query(self):
        repository = self.schema.repository(name=self.repo_name, owner=self.repo_owner)
        result = (
            self.client.new_query()
            .select(repository.name, repository.owner.login)
            .build_and_run()
        )
        self.assertDictEqual(
            {
                "repository": {
                    "name": self.repo_name,
                    "owner": {"login": self.repo_owner},
                }
            },
            result,
        )

    def test_mixed_query(self):
        result = (
            self.client.new_query()
            .select(
                self.schema.repository(name=self.repo_name, owner=self.repo_owner).name,
                Field("repository", name=self.repo_name, owner=self.repo_owner).select(
                    Field("owner").select("login")
                ),
            )
            .build_and_run()
        )
        self.assertDictEqual(
            {
                "repository": {
                    "name": self.repo_name,
                    "owner": {"login": self.repo_owner},
                }
            },
            result,
        )

    def test_select_query(self):
        result = (
            self.client.new_query()
            .select(
                self.schema.repository(
                    name=self.repo_name, owner=self.repo_owner
                ).select("name", Field("owner").select("login"))
            )
            .build_and_run()
        )
        self.assertDictEqual(
            {
                "repository": {
                    "name": self.repo_name,
                    "owner": {"login": self.repo_owner},
                }
            },
            result,
        )

    def test_variables_query(self):
        query = (
            self.client.new_query()
            .var("dry_run_var", "Boolean")
            .select(self.schema.rateLimit(dryRun=VarRef("dry_run_var")).used)
            .build()
        )
        self.assertEqual(
            "query($dry_run_var:Boolean){rateLimit(dryRun:$dry_run_var){used}}",
            str(query),
        )

    def test_variables_query_run(self):
        result = (
            self.client.new_query()
            .var("name", "String!")
            .var("owner", "String!")
            .select(
                self.schema.repository(
                    name=VarRef("name"), owner=VarRef("owner")
                ).select("name", Field("owner").select("login"))
            )
            .build_and_run(variables={"name": self.repo_name, "owner": self.repo_owner})
        )
        self.assertDictEqual(
            {
                "repository": {
                    "name": self.repo_name,
                    "owner": {"login": self.repo_owner},
                }
            },
            result,
        )


if __name__ == "__main__":
    main()
