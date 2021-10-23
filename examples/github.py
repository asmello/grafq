import os

from grafq import Field, Var
from grafq.client import Client


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Must specify token in environment variable GITHUB_TOKEN")

    client = Client("https://api.github.com/graphql", token=token)

    data = (
        client.new_query()
        .var("size", "Int")
        .select(
            Field("viewer").select(
                "login", "name", Field("avatarUrl", size=Var("size"))
            ),
            Field("repository", name="grafq", owner="asmello").select("url"),
        )
        .build_and_run(variables={"size": 200})
    )
    print(data)


if __name__ == "__main__":
    main()
