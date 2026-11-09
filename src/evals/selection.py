from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from evals.golden.items import GoldenItem
from evals.golden.loader import GoldenSet
from evals.golden.vocabulary import Split


class GoldenSource(StrEnum):
    QUESTIONS = "questions"
    REDTEAM = "redteam"
    PROTOCOL_ACTIONS = "protocol_actions"


class SelectionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ItemSelection:
    sources: frozenset[GoldenSource] = frozenset({GoldenSource.QUESTIONS})
    split: Split = Split.DEV
    holdout_from: frozenset[GoldenSource] = frozenset()
    only: frozenset[str] = frozenset()

    def pick(self, golden: GoldenSet) -> tuple[GoldenItem, ...]:
        outside = sorted(self.holdout_from - self.sources)
        if outside:
            raise SelectionError(f"holdout de arquivo fora da seleção: {outside}")
        chosen = tuple(self._chosen(golden))
        unknown = sorted(self.only - {item.id for item in chosen})
        if unknown:
            raise SelectionError(f"itens fora da seleção: {unknown}")
        return chosen

    def _chosen(self, golden: GoldenSet) -> Iterator[GoldenItem]:
        files = {
            GoldenSource.QUESTIONS: golden.questions,
            GoldenSource.REDTEAM: golden.attacks,
            GoldenSource.PROTOCOL_ACTIONS: golden.actions,
        }
        for source, items in files.items():
            if source in self.sources:
                yield from (item for item in items if self._admits(source, item))

    def _admits(self, source: GoldenSource, item: GoldenItem) -> bool:
        if self.only and item.id not in self.only:
            return False
        return item.split is self.split or (
            item.split is Split.HOLDOUT and source in self.holdout_from
        )


@dataclass(frozen=True, slots=True)
class Repetitions:
    default: int = 1
    critical: int | None = None

    def of(self, item: GoldenItem) -> int:
        if item.critical and self.critical is not None:
            return self.critical
        return self.default


@dataclass(frozen=True, slots=True)
class PlannedExecution:
    item: GoldenItem
    repetition: int

    @property
    def key(self) -> str:
        item_id = self.item.id
        return f"{item_id}#{self.repetition}"


class RunPlan:
    @staticmethod
    def of(items: tuple[GoldenItem, ...], repetitions: Repetitions) -> tuple[PlannedExecution, ...]:
        return tuple(
            PlannedExecution(item, repetition)
            for item in items
            for repetition in range(1, repetitions.of(item) + 1)
        )


@dataclass(frozen=True, slots=True)
class RunRequest:
    selection: ItemSelection
    repetitions: Repetitions
    output: Path
    concurrency: int | None = None
    env_file: Path | None = None
