from collections import Counter
from dataclasses import dataclass

from evals.critical_rule import CRITICAL_GRADERS, KEY_SEPARATOR
from evals.records import ExecutionRecord, RunManifest

CONSISTENCY_LIMIT = "Limite: 5 em 5 não prova ausência de bug."


@dataclass(frozen=True, slots=True)
class CriticalItemRuns:
    item: str
    approved: int
    planned: int

    @property
    def passed_all(self) -> bool:
        return self.approved == self.planned


@dataclass(frozen=True, slots=True)
class ConsistencySummary:
    items: tuple[CriticalItemRuns, ...]

    @property
    def label(self) -> str:
        repeats = sorted({item.planned for item in self.items})
        if len(repeats) == 1:
            return f"pass^{repeats[0]}"
        return "pass^k"

    @property
    def declared_k(self) -> str:
        repeats = sorted({item.planned for item in self.items})
        return ", ".join(map(str, repeats)) if repeats else "nenhum"

    @property
    def passing_items(self) -> int:
        return sum(item.passed_all for item in self.items)

    @property
    def attempts_approved(self) -> int:
        return sum(item.approved for item in self.items)

    @property
    def attempts_planned(self) -> int:
        return sum(item.planned for item in self.items)

    @property
    def attempt_rate(self) -> float:
        planned = self.attempts_planned
        return self.attempts_approved / planned if planned else 0.0

    @property
    def note(self) -> str:
        return (
            f"{self.label} é a medida de consistência: o item só conta se passou nas k repetições "
            f"nos graders críticos (k = {self.declared_k}). {CONSISTENCY_LIMIT}"
        )


class CriticalConsistency:
    @classmethod
    def of(cls, manifest: RunManifest, records: tuple[ExecutionRecord, ...]) -> ConsistencySummary:
        planned = Counter(key.split(KEY_SEPARATOR)[0] for key in manifest.critical_keys)
        approved = Counter(record.item_id for record in records if cls._approved(record))
        items = sorted(planned)
        counts = ((item, approved[item], planned[item]) for item in items)
        runs = [CriticalItemRuns(*count) for count in counts]
        return ConsistencySummary(tuple(runs))

    @staticmethod
    def _approved(record: ExecutionRecord) -> bool:
        if not record.critical or record.error is not None:
            return False
        checks = [v.passed for v in record.verdicts if v.grader in CRITICAL_GRADERS]
        return all(checks)
