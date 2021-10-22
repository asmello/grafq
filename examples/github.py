import os

from src.grafq import Field, Var, QueryBuilder
from src.grafq.client import Client


def main():
    token = os.environ.get("TOKEN")
    if not token:
        raise RuntimeError("Must specify token in environment variable TOKEN")

    query = (
        QueryBuilder()
        .var("size", "Int")
        .select(
            Field("viewer").select(
                "login", "name", Field("avatarUrl", size=Var("size"))
            ),
            Field("repository", owner="asmello").arg("name", "grafq").select("url"),
        )
        .build()
    )
    client = Client("https://api.github.com/graphql", token=token)
    data = client.post(query, variables={"size": 200})
    print(data)


if __name__ == "__main__":
    main()
