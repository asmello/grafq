from grafq.dataclasses import NamedType
from grafq.query_builder import QueryBuilder


def main():
    query = QueryBuilder().name("test").var("myVar", NamedType("someType")).select("address").build()
    print(query)


if __name__ == '__main__':
    main()
