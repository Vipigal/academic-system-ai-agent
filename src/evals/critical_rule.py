from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from evals.graders.verdict import GraderName
from evals.records import ExecutionRecord, RunManifest

CRITICAL_GRADERS = frozenset({GraderName.PROPOSAL, GraderName.TRAJECTORY})
KEY_SEPARATOR = "#"
EXIT_FAILED = 1
EXIT_INCOMPLETE = 2


class RoundState(StrEnum):
    APPROVED = "APROVADA"
    FAILED = "REPROVADA"
    INCOMPLETE = "INCOMPLETA"


@dataclass(frozen=True, slots=True)
class CriticalFailure:
    key: str
    grader: GraderName
    problems: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RoundResult:
    failures: tuple[CriticalFailure, ...]
    missing_executions: tuple[str, ...]
    unplanned_critical_items: tuple[str, ...]

    @property
    def state(self) -> RoundState:
        if self.failures:
            return RoundState.FAILED
        if self.missing_executions or self.unplanned_critical_items:
            return RoundState.INCOMPLETE
        return RoundState.APPROVED

    @property
    def exit_code(self) -> int:
        codes = {RoundState.FAILED: EXIT_FAILED, RoundState.INCOMPLETE: EXIT_INCOMPLETE}
        return codes.get(self.state, 0)

    @property
    def reason(self) -> str:
        if self.state is RoundState.FAILED:
            return f"{len(self.failures)} falhas de proposta ou trajetória em itens críticos."
        if self.state is RoundState.INCOMPLETE:
            return self._incomplete_reason()
        return "Todos os itens críticos rodaram e passaram em todas as repetições."

    def _incomplete_reason(self) -> str:
        missing = len(self.missing_executions)
        unplanned = len(self.unplanned_critical_items)
        return (
            f"Sem falha crítica até aqui, mas faltam {missing} execuções planejadas "
            f"e {unplanned} itens críticos ficaram fora da rodada."
        )


class CriticalRule:
    @staticmethod
    def failures(records: Iterable[ExecutionRecord]) -> tuple[CriticalFailure, ...]:
        return tuple(
            CriticalFailure(record.key, verdict.grader, verdict.problems)
            for record in records
            if record.critical
            for verdict in record.verdicts
            if verdict.grader in CRITICAL_GRADERS and not verdict.passed
        )

    @classmethod
    def result(cls, manifest: RunManifest, records: tuple[ExecutionRecord, ...]) -> RoundResult:
        finished = {record.key for record in records}
        planned_items = {key.split(KEY_SEPARATOR)[0] for key in manifest.critical_keys}
        return RoundResult(
            cls.failures(records),
            tuple(key for key in manifest.planned_keys if key not in finished),
            tuple(item for item in manifest.golden_critical_items if item not in planned_items),
        )
