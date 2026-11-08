from collections.abc import Mapping

from evals.golden.items import AttackItem, GoldenItem
from evals.golden.oracle import Oracle
from evals.item_context import ForeignIdentifiers, ItemContext
from evals.runner import ContextualizedExecution
from evals.selection import PlannedExecution

FOREIGN_QUERY = "foreign_identifiers"
NO_PARAMETERS: Mapping[str, str] = {}


class ContextError(RuntimeError):
    pass


class ItemContextLoader:
    def __init__(self, oracle: Oracle) -> None:
        self._oracle = oracle
        self._foreign: dict[str, ForeignIdentifiers] = {}

    @classmethod
    async def contextualized(cls, pending: list[PlannedExecution]) -> list[ContextualizedExecution]:
        contexts: dict[str, ItemContext] = {}
        async with Oracle.from_environment() as oracle:
            loader = cls(oracle)
            for planned in pending:
                if planned.item.id not in contexts:
                    contexts[planned.item.id] = await loader.load(planned.item)
        return [
            ContextualizedExecution(contexts[planned.item.id], planned.repetition)
            for planned in pending
        ]

    async def load(self, item: GoldenItem) -> ItemContext:
        return ItemContext(
            item=item,
            question=await self._question(item),
            forbidden_values=tuple(
                [
                    await self._single(item, forbidden.query, forbidden.params)
                    for forbidden in item.forbidden_facts
                ]
            ),
            foreign=await self._foreign_of(item.student),
        )

    async def _question(self, item: GoldenItem) -> str:
        if not isinstance(item, AttackItem):
            return item.question
        values = {
            binding.name: await self._single(item, binding.query, binding.params)
            for binding in item.bindings
        }
        return item.rendered_question(values)

    async def _foreign_of(self, student: str) -> ForeignIdentifiers:
        if student not in self._foreign:
            rows = await self._oracle.rows(FOREIGN_QUERY, student, NO_PARAMETERS)
            identifiers = frozenset(row for row in rows if row)
            self._foreign[student] = ForeignIdentifiers.of(identifiers)
        return self._foreign[student]

    async def _single(self, item: GoldenItem, query: str, params: Mapping[str, str]) -> str:
        rows = await self._oracle.rows(query, item.student, params)
        if len(rows) != 1 or rows[0] is None:
            raise ContextError(f"{item.id}: {query} devolveu {len(rows)} linhas, não um valor")
        return rows[0]
