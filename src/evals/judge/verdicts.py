from enum import StrEnum

from pydantic import Field

from evals.dataset.parts import FrozenModel


class CriterionOutcome(StrEnum):
    APPROVED = "pass"
    REJECTED = "fail"
    UNKNOWN = "unknown"


class ToolEvidence(FrozenModel):
    name: str
    arguments: dict[str, object]
    status: str
    output: dict[str, object]


class JudgeRequest(FrozenModel):
    id: str
    question: str
    answer: str
    reference: str
    rubric: tuple[str, ...]
    history: tuple[str, ...] = ()
    tools: tuple[ToolEvidence, ...] = ()


class CriterionVerdict(FrozenModel):
    criterion: int
    reasoning: str = Field(min_length=1)
    verdict: CriterionOutcome


class ItemVerdict(FrozenModel):
    id: str
    criteria: tuple[CriterionVerdict, ...]

    @property
    def outcome(self) -> CriterionOutcome:
        found = {criterion.verdict for criterion in self.criteria}
        if CriterionOutcome.REJECTED in found:
            return CriterionOutcome.REJECTED
        if CriterionOutcome.UNKNOWN in found:
            return CriterionOutcome.UNKNOWN
        return CriterionOutcome.APPROVED

    @property
    def passed(self) -> bool:
        return self.outcome is CriterionOutcome.APPROVED

    def covers(self, request: JudgeRequest) -> bool:
        numbers = [criterion.criterion for criterion in self.criteria]
        return numbers == list(range(1, len(request.rubric) + 1))


class JudgedVerdict(ItemVerdict):
    judge_model: str
