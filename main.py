import os

from grafq.client import Client
from grafq.query import VarRef
from grafq.query_builder import QueryBuilder
from grafq.selector import Selector


def main():
    token = os.environ.get('TOKEN')
    if not token:
        raise RuntimeError("Must specify token in environment variable TOKEN")

    selection = (Selector()
                 .add("viewer")
                 .into()
                 .add("avatarUrl", args={'size': VarRef('size')})
                 .add("login")
                 .add("name")
                 .back()
                 .add("repository", args={'name': 'grafq', 'owner': 'asmello'})
                 .into()
                 .add("url")
                 .render())

    query = (QueryBuilder()
             .var('size', 'Int')
             .select(selection)
             .build())
    client = Client("https://api.github.com/graphql", token=token)
    data = client.post(query, variables={'size': 200})
    print(data)


if __name__ == '__main__':
    main()
