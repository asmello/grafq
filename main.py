import os

from grafq.client import Client
from grafq.query import Field, Argument
from grafq.query_builder import QueryBuilder


def main():
    token = os.environ.get('TOKEN')
    if not token:
        raise RuntimeError("Must specify token in environment variable TOKEN")

    query = (QueryBuilder()
             .var('size', 'Int')
             .select('viewer', fields=['login', Field('avatarUrl', arguments=[Argument('size', '$size')])])
             .build())
    client = Client("https://api.github.com/graphql", token=token)
    data = client.post(query, variables={'size': 200})
    print(data)


if __name__ == '__main__':
    main()
