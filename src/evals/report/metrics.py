import math
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from evals.gate import PassK
from evals.graders.verdict import GraderName
from evals.judge.verdicts import ItemVerdict
from evals.records import ExecutionRecord

WILSON_Z = 1.96


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

    @property
    def interval(self) -> tuple[float, float]:
        if not self.total:
            return 0.0, 0.0
        weight = WILSON_Z**2 / self.total
        center = (self.share + weight / 2) / (1 + weight)
        variance = self.share * (1 - self.share) / self.total
        spread = variance + weight / (4 * self.total)
        half = WILSON_Z * math.sqrt(spread) / (1 + weight)
        return max(center - half, 0.0), min(center + half, 1.0)


class Percentile:
    @staticmethod
    def of(values: Sequence[float], share: float) -> float | None:
        if not values:
            return None
        rank = math.ceil(share * len(values))
        return sorted(values)[max(rank - 1, 0)]


class JudgedResult:
    def __init__(self, verdicts: Mapping[str, ItemVerdict]) -> None:
        self._verdicts = verdicts

    def judged_of(self, records: Iterable[ExecutionRecord]) -> list[ExecutionRecord]:
        return [record for record in records if record.key in self._verdicts]

    def accuracy(self, records: Iterable[ExecutionRecord]) -> Accuracy:
        judged = self.judged_of(records)
        results = [self._verdicts[record.key].passed for record in judged]
        return Accuracy.of(GraderName.JUDGE.value, results)


class Consistency:
    @classmethod
    def of(cls, records: Iterable[ExecutionRecord]) -> PassK:
        runs = list(records)
        epochs = Counter(record.item_id for record in runs)
        approved = Counter(record.item_id for record in runs if record.passed)
        return PassK.of(cls._repeated(epochs), approved)

    @staticmethod
    def _repeated(epochs: Counter[str]) -> Counter[str]:
        repeated = {item: total for item, total in epochs.items() if total > 1}
        return Counter(repeated)


class RunCost:
    @staticmethod
    def total(records: Iterable[ExecutionRecord]) -> Decimal | None:
        costs = [record.cost_usd for record in records]
        known = [cost for cost in costs if cost is not None]
        if len(known) != len(costs):
            return None
        return sum(known, Decimal(0))
