from grafq.query import NamedType, Field
from grafq.query_builder import QueryBuilder


def main():
    query = (QueryBuilder()
             .name("test")
             .var("myVar", NamedType("someType"))
             .select("id")
             .select("friend", args={'id': 4}, fields=[Field("name")])
             .build())
    print(query.pretty())


if __name__ == '__main__':
    main()
