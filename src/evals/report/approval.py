from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum

from evals.gate import RoundResult, RoundState
from evals.report.metrics import Accuracy

APPROVAL_SHARE = 0.85


class Approval(StrEnum):
    APPROVED = "APROVADA"
    FAILED = "REPROVADA"
    PENDING = "PENDENTE"


@dataclass(frozen=True, slots=True)
class RoundApproval:
    state: Approval
    reasons: tuple[str, ...]

    @classmethod
    def of(cls, result: RoundResult, graders: Accuracy, judge: Accuracy) -> RoundApproval:
        reasons = tuple(cls._blockers(result, graders, judge))
        if reasons:
            return cls(Approval.FAILED, reasons)
        if not judge.total:
            return cls(Approval.PENDING, ("o juiz ainda não julgou a rodada",))
        return cls(Approval.APPROVED, ())

    @staticmethod
    def _blockers(result: RoundResult, graders: Accuracy, judge: Accuracy) -> Iterator[str]:
        if result.failures:
            total = len({failure.key for failure in result.failures})
            yield (
                "1 execução de gate falhou" if total == 1 else f"{total} execuções de gate falharam"
            )
        if result.state is RoundState.INCOMPLETE:
            yield f"{len(result.missing_executions)} execuções planejadas não rodaram"
        if graders.share < APPROVAL_SHARE:
            yield "graders abaixo de 85%"
        if judge.total and judge.share < APPROVAL_SHARE:
            yield "juiz abaixo de 85%"
