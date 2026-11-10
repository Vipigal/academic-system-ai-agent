from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum

from evals.graders.verdict import GraderName
from evals.records import ExecutionRecord, RunManifest

GATE_GRADERS = frozenset({GraderName.PROPOSAL, GraderName.TRAJECTORY})
KEY_SEPARATOR = "#"
EXIT_FAILED = 1
EXIT_INCOMPLETE = 2


class RoundState(StrEnum):
    APPROVED = "APROVADA"
    FAILED = "REPROVADA"
    INCOMPLETE = "INCOMPLETA"
    PARTIAL = "PARCIAL"
    UNGATED = "SEM GATE"


@dataclass(frozen=True, slots=True)
class GateFailure:
    key: str
    grader: GraderName
    problems: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PassK:
    passing_items: int
    items: int
    k: tuple[int, ...]

    @property
    def label(self) -> str:
        return f"pass^{self.k[0]}" if len(self.k) == 1 else "pass^k"

    @classmethod
    def of(cls, planned: Counter[str], approved: Counter[str]) -> PassK:
        passing = sum(approved[item] == planned[item] for item in planned)
        epochs = tuple(sorted(set(planned.values())))
        return cls(passing, len(planned), epochs)


@dataclass(frozen=True, slots=True)
class RoundResult:
    failures: tuple[GateFailure, ...]
    missing_executions: tuple[str, ...]
    unplanned_gated_items: tuple[str, ...]
    gated_planned: bool = True

    @property
    def state(self) -> RoundState:
        if self.failures:
            return RoundState.FAILED
        if self.missing_executions:
            return RoundState.INCOMPLETE
        if not self.gated_planned:
            return RoundState.UNGATED
        if self.unplanned_gated_items:
            return RoundState.PARTIAL
        return RoundState.APPROVED

    @property
    def exit_code(self) -> int:
        codes = {
            RoundState.FAILED: EXIT_FAILED,
            RoundState.INCOMPLETE: EXIT_INCOMPLETE,
            RoundState.PARTIAL: EXIT_INCOMPLETE,
        }
        return codes.get(self.state, 0)


class GateRule:
    @staticmethod
    def passed(record: ExecutionRecord) -> bool:
        checks = [verdict.passed for verdict in record.verdicts if verdict.grader in GATE_GRADERS]
        return record.error is None and all(checks)

    @staticmethod
    def item_of(key: str) -> str:
        return key.split(KEY_SEPARATOR, maxsplit=1)[0]

    @classmethod
    def _approved(cls, records: Iterable[ExecutionRecord]) -> Iterator[ExecutionRecord]:
        return (record for record in records if record.gated and cls.passed(record))

    @classmethod
    def failures(cls, records: Iterable[ExecutionRecord]) -> tuple[GateFailure, ...]:
        return tuple(
            GateFailure(record.key, verdict.grader, verdict.problems)
            for record in records
            if record.gated
            for verdict in record.verdicts
            if verdict.grader in GATE_GRADERS and not verdict.passed
        )

    @classmethod
    def result(cls, manifest: RunManifest, records: tuple[ExecutionRecord, ...]) -> RoundResult:
        finished = {record.key for record in records}
        planned_items = set(map(cls.item_of, manifest.gated_keys))
        return RoundResult(
            cls.failures(records),
            tuple(key for key in manifest.planned_keys if key not in finished),
            tuple(item for item in manifest.gated_items if item not in planned_items),
            bool(planned_items),
        )

    @classmethod
    def pass_k(cls, manifest: RunManifest, records: tuple[ExecutionRecord, ...]) -> PassK:
        planned = Counter(map(cls.item_of, manifest.gated_keys))
        approved = Counter(record.item_id for record in cls._approved(records))
        return PassK.of(planned, approved)
