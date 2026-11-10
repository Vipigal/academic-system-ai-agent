from dataclasses import dataclass
from pathlib import Path

from evals.dataset.items import DatasetItem
from evals.dataset.loader import Dataset
from evals.dataset.vocabulary import Split, Suite


class SelectionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ItemSelection:
    suites: frozenset[Suite] = frozenset({Suite.QUALITY})
    splits: frozenset[Split] = frozenset({Split.DEV})
    only: frozenset[str] = frozenset()

    def pick(self, dataset: Dataset) -> tuple[DatasetItem, ...]:
        chosen = tuple(
            item
            for suite in Suite
            if suite in self.suites
            for item in dataset.suites[suite]
            if self._admits(item)
        )
        unknown = sorted(self.only - {item.id for item in chosen})
        if unknown:
            raise SelectionError(f"itens fora da seleção: {unknown}")
        return chosen

    def _admits(self, item: DatasetItem) -> bool:
        in_split = item.split in self.splits or item.gated
        return in_split and (not self.only or item.id in self.only)


@dataclass(frozen=True, slots=True)
class Epochs:
    default: int = 1

    def of(self, item: DatasetItem) -> int:
        return item.pass_k or self.default


@dataclass(frozen=True, slots=True)
class PlannedExecution:
    item: DatasetItem
    epoch: int

    @property
    def key(self) -> str:
        item_id = self.item.id
        return f"{item_id}#{self.epoch}"


class RunPlan:
    @staticmethod
    def of(items: tuple[DatasetItem, ...], epochs: Epochs) -> tuple[PlannedExecution, ...]:
        return tuple(
            PlannedExecution(item, epoch)
            for item in items
            for epoch in range(1, epochs.of(item) + 1)
        )


@dataclass(frozen=True, slots=True)
class RunRequest:
    selection: ItemSelection
    epochs: Epochs
    output: Path
    concurrency: int | None = None
    env_file: Path | None = None
