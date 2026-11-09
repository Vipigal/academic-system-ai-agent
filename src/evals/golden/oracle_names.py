from collections.abc import Iterator, Mapping

from evals.golden.items import AttackItem, GoldenItem
from evals.golden.oracle import QueryPreparer
from evals.golden.oracle_queries import ORACLE_QUERIES
from evals.golden.problems import Problem

type QueryParams = Mapping[str, str]
type NamedCall = tuple[str, QueryParams]


class QueryNames:
    @classmethod
    def problems_of(cls, item: GoldenItem) -> Iterator[Problem]:
        calls: list[NamedCall] = [(call.query, call.params) for call in item.queries]
        if isinstance(item, AttackItem):
            calls.extend((binding.query, binding.params) for binding in item.bindings)
        for query, params in calls:
            yield from cls._call_problems(item.id, query, params)

    @staticmethod
    def _call_problems(item_id: str, query: str, params: QueryParams) -> Iterator[Problem]:
        if query not in ORACLE_QUERIES:
            yield Problem(item_id, f"consulta {query} não existe em oracle_queries")
            return
        expected = QueryPreparer.parameters_of(query)
        if set(params) != expected:
            yield Problem(item_id, f"{query} recebe {sorted(expected)}, veio {sorted(params)}")
