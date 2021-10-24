import os

from grafq import Var
from grafq.client import Client


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Must specify token in environment variable GITHUB_TOKEN")

    client = Client("https://api.github.com/graphql", token=token)
    schema = client.schema(strict=True)
    viewer = schema.viewer

    data = (
        client.new_query()
        .var("size", "Int")
        .select(
            viewer.login,
            viewer.name,
            viewer.avatarUrl(size=Var("size")),
            schema.repository(name="grafq", owner="asmello").url,
        )
        .build_and_run(variables={"size": 200})
    )
    print(data)


if __name__ == "__main__":
    main()
