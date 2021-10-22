import os

from grafq.client import Client
from grafq.field import Field
from grafq.language import VarRef
from grafq.query_builder import QueryBuilder


def main():
    token = os.environ.get("TOKEN")
    if not token:
        raise RuntimeError("Must specify token in environment variable TOKEN")

    query = (
        QueryBuilder()
        .var("size", "Int")
        .select(
            Field("viewer").select(
                "login", "name", Field("avatarUrl", size=VarRef("size"))
            ),
            Field("repository", owner="asmello").arg("name", "grafq").select("url"),
        )
        .build()
    )
    print(str(query))
    client = Client("https://api.github.com/graphql", token=token)
    data = client.post(query, variables={"size": 200})
    print(data)


if __name__ == "__main__":
    main()
