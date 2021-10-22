# grafq

`grafq` is a library designed to help constructing GraphQL queries with idiomatic Python. It provides a concise and simple API to build such queries incrementally, with strong emphasis on correctness and type safety. Partial queries can be shared, composed and modified trivially, and fully formed queries can be converted to strings and reused infinitely with zero cost.

## Example

```python
from src.grafq import Field, Var, QueryBuilder
from src.grafq.client import Client

client = Client("https://api.github.com/graphql", token=TOKEN)

simple = QueryBuilder().select("viewer.login", "viewer.name").build()
data = client.get(simple)

complex = (
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
data = client.post(complex, variables={"size": 200})
```

# FAQ
## Can't I just type out the query directly?
Yes, but usage of string literals with embedded code have a number of practical disadvantages:
1. **Poor IDE support** - most IDEs aren't smart enough to detect that your string contains some GraphQL code and won't interpret the embedded code specially. This means loss of important productivity features like syntax highlighting, type hinting, validation and autocomplete. This can be sometimes worked around by placing queries in separate files, but that creates a number of overheads and error conditions that are best avoided.
2. **Error proneness** - given lack of tooling support, it's much easier to make mistakes that won't be flagged until the code is executed in an integration test or in production.
3. **Poor integration** - when represented as a string, embedded code has to be manipulated as such. This creates surface area for bugs and vulnerabilities, and makes dynamic queries just a royal pain to implement.
4. **Poor reusability** - it's far too easy to end up just creating static ad-hoc queries everywhere, when often times there are reusable components that could be shared around. Fragments help avoid that, but are hard to use correctly in practice due to (3).

All of these (and other reasons) have led to the development of this library, which makes it possible to construct and manipulate GraphQL queries in a first class manner, using plain old Python objects.

## How is type safety implemented?

Currently, it isn't.

Plan is to use the fact that GraphQL APIs are introspective to give users the option to generate a dynamic Schema object that will mirror the remote schema. By passing this object's fields to the QueryBuilder, it will be possible to validate the query as it's being built, client-side. This won't prevent type errors from popping up at runtime, but they'll arise as early as possible, typically at startup time, as queries are normally only generated once.

Further, there are plans to support generating schema classes staticallly, which can then be used for offline type-checking using Python's native type hinting system. This has the downside that the generated classes need to be kept in sync with the remote API, but it has the upside that IDE features can be leveraged to their full potential.

