from pathlib import Path

from evals.dataset.items import DatasetItem
from evals.dataset.oracle import Oracle
from evals.item_context import ForeignIdentifiers, ItemContext
from evals.runner import ContextualizedExecution
from evals.selection import PlannedExecution


class ItemContextLoader:
    def __init__(self, oracle: Oracle) -> None:
        self._oracle = oracle
        self._foreign: dict[str, ForeignIdentifiers] = {}

    @classmethod
    async def contextualized(
        cls, pending: list[PlannedExecution], env_file: Path | None = None
    ) -> list[ContextualizedExecution]:
        contexts: dict[str, ItemContext] = {}
        async with Oracle.from_environment(env_file) as oracle:
            loader = cls(oracle)
            for planned in pending:
                if planned.item.id not in contexts:
                    contexts[planned.item.id] = await loader.load(planned.item)
        return [
            ContextualizedExecution(contexts[planned.item.id], planned.epoch) for planned in pending
        ]

    async def load(self, item: DatasetItem) -> ItemContext:
        return ItemContext(item=item, foreign=await self._foreign_of(item.student))

    async def _foreign_of(self, student: str) -> ForeignIdentifiers:
        if student not in self._foreign:
            identifiers = await self._oracle.foreign_identifiers(student)
            self._foreign[student] = ForeignIdentifiers.of(identifiers)
        return self._foreign[student]
