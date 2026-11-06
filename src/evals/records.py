from collections.abc import Sequence
from decimal import Decimal
from typing import Self

from evals.execution import Execution, ToolStep
from evals.golden.items import GoldenItem
from evals.golden.parts import FrozenModel
from evals.golden.vocabulary import Kind, Split
from evals.graders.verdict import GraderName, Verdict


class RunVersions(FrozenModel):
    model: str
    effort: str
    prompt_version: str
    skills_hash: str
    tools_hash: str


class PlannedRound(FrozenModel):
    versions: RunVersions
    planned_keys: tuple[str, ...]
    critical_keys: tuple[str, ...]
    golden_critical_items: tuple[str, ...]
    trace_url_prefix: str | None = None

    def same_round(self, other: PlannedRound) -> bool:
        mine = (self.versions, self.planned_keys)
        return mine == (other.versions, other.planned_keys)


class RunManifest(PlannedRound):
    commit: str
    worktree_clean: bool
    started_at: str


class StepRecord(FrozenModel):
    name: str
    arguments: dict[str, object]
    status: str
    duration_ms: int
    guardrail_problems: tuple[str, ...] = ()

    @classmethod
    def of(cls, step: ToolStep) -> Self:
        return cls(
            name=step.name,
            arguments=dict(step.arguments),
            status=step.status,
            duration_ms=step.duration_ms,
            guardrail_problems=step.guardrail_problems,
        )


class VerdictRecord(FrozenModel):
    grader: GraderName
    passed: bool
    problems: tuple[str, ...] = ()

    @classmethod
    def of(cls, verdict: Verdict) -> Self:
        return cls(grader=verdict.grader, passed=verdict.passed, problems=verdict.problems)


class ExecutionRecord(FrozenModel):
    item_id: str
    repetition: int
    area: str
    kind: Kind
    split: Split
    critical: bool
    history: tuple[str, ...] = ()
    question: str
    answer: str
    steps: tuple[StepRecord, ...]
    stop_reason: str
    total_ms: float
    first_token_ms: float | None
    tokens_in: int
    tokens_out: int
    cost_usd: Decimal | None
    error: str | None
    trace_id: str | None
    verdicts: tuple[VerdictRecord, ...]
    versions: RunVersions

    @property
    def key(self) -> str:
        return f"{self.item_id}#{self.repetition}"

    @property
    def passed(self) -> bool:
        return self.error is None and all(verdict.passed for verdict in self.verdicts)


class ExecutionRecords:
    @staticmethod
    def of(
        item: GoldenItem,
        execution: Execution,
        verdicts: Sequence[Verdict],
        priced: tuple[RunVersions, Decimal | None],
    ) -> ExecutionRecord:
        versions, cost = priced
        return ExecutionRecord(
            item_id=item.id,
            repetition=execution.repetition,
            area=item.area,
            kind=item.kind,
            split=item.split,
            critical=item.critical,
            history=item.history,
            question=execution.question,
            answer=execution.answer,
            steps=tuple(StepRecord.of(step) for step in execution.steps),
            stop_reason=execution.stop_reason,
            total_ms=execution.timing.total_ms,
            first_token_ms=execution.timing.first_token_ms,
            tokens_in=execution.usage.tokens_in,
            tokens_out=execution.usage.tokens_out,
            cost_usd=cost,
            error=execution.failure,
            trace_id=execution.trace_id,
            verdicts=tuple(VerdictRecord.of(verdict) for verdict in verdicts),
            versions=versions,
        )
