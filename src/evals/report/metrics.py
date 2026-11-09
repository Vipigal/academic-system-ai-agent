import math
import statistics
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from evals.graders.verdict import GraderName
from evals.judge.verdicts import CriterionOutcome, ItemVerdict
from evals.records import ExecutionRecord

type ResultsByName = Mapping[str, Sequence[bool]]


@dataclass(frozen=True, slots=True)
class Accuracy:
    name: str
    passed: int
    total: int

    @classmethod
    def of(cls, name: str, results: Sequence[bool]) -> Self:
        return cls(name, sum(results), len(results))

    @property
    def share(self) -> float:
        return self.passed / self.total if self.total else 0.0


class Percentile:
    @staticmethod
    def of(values: Sequence[float], share: float) -> float | None:
        if not values:
            return None
        rank = math.ceil(share * len(values))
        return sorted(values)[max(rank - 1, 0)]


class GroupedAccuracy:
    @classmethod
    def by(
        cls, records: Iterable[ExecutionRecord], key: Callable[[ExecutionRecord], str]
    ) -> tuple[Accuracy, ...]:
        groups: defaultdict[str, list[bool]] = defaultdict(list)
        for record in records:
            groups[key(record)].append(record.passed)
        return cls._accuracies(groups)

    @classmethod
    def by_grader(cls, records: Iterable[ExecutionRecord]) -> tuple[Accuracy, ...]:
        groups: defaultdict[str, list[bool]] = defaultdict(list)
        for record in records:
            for verdict in record.verdicts:
                groups[verdict.grader.value].append(verdict.passed)
        return cls._accuracies(groups)

    @staticmethod
    def _accuracies(groups: ResultsByName) -> tuple[Accuracy, ...]:
        names = sorted(groups)
        return tuple(Accuracy.of(name, groups[name]) for name in names)


class Repeatability:
    @staticmethod
    def results_by_item(
        records: Iterable[ExecutionRecord], passed: Callable[[ExecutionRecord], bool]
    ) -> ResultsByName:
        items: defaultdict[str, list[bool]] = defaultdict(list)
        for record in records:
            items[record.item_id].append(passed(record))
        return items

    @staticmethod
    def pass_at_one(results: ResultsByName) -> float:
        rates = [statistics.fmean(runs) for runs in results.values()]
        return statistics.fmean(rates) if rates else 0.0

    @staticmethod
    def stable(results: ResultsByName) -> Accuracy:
        repeated = [runs for runs in results.values() if len(runs) > 1]
        same = [len(set(runs)) == 1 for runs in repeated]
        return Accuracy.of("estáveis", same)


class JudgedResult:
    def __init__(self, verdicts: Mapping[str, ItemVerdict]) -> None:
        self._verdicts = verdicts

    def judged_of(self, records: Iterable[ExecutionRecord]) -> list[ExecutionRecord]:
        return [record for record in records if record.key in self._verdicts]

    def with_rubric(self, record: ExecutionRecord) -> bool:
        return record.passed and self._verdicts[record.key].passed

    def accuracy(self, records: Iterable[ExecutionRecord]) -> Accuracy:
        judged = self.judged_of(records)
        results = [self._verdicts[record.key].passed for record in judged]
        return Accuracy.of(GraderName.JUDGE.value, results)

    def criteria(self, records: Iterable[ExecutionRecord]) -> Accuracy:
        verdicts = [self._verdicts[record.key] for record in self.judged_of(records)]
        outcomes = [criterion.verdict for verdict in verdicts for criterion in verdict.criteria]
        decided = [outcome for outcome in outcomes if outcome is not CriterionOutcome.UNKNOWN]
        return Accuracy.of(
            "critérios", [outcome is CriterionOutcome.APPROVED for outcome in decided]
        )

    def unknown(self, records: Iterable[ExecutionRecord]) -> int:
        outcomes = [self._verdicts[record.key].outcome for record in self.judged_of(records)]
        return outcomes.count(CriterionOutcome.UNKNOWN)


class RunCost:
    @staticmethod
    def total(records: Iterable[ExecutionRecord]) -> Decimal | None:
        costs = [record.cost_usd for record in records]
        known = [cost for cost in costs if cost is not None]
        if len(known) != len(costs):
            return None
        return sum(known, Decimal(0))
