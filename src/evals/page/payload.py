from collections.abc import Iterator

from evals.critical_consistency import CriticalConsistency
from evals.critical_rule import CriticalRule, RoundResult
from evals.golden.parts import FrozenModel
from evals.judge.verdicts import CriterionOutcome
from evals.page.review_sample import ReviewCard, ReviewSample
from evals.records import ExecutionRecord, StepRecord, VerdictRecord
from evals.report_indicators import CriticalRow, CriticalRows, RunIndicators
from evals.run_data import RunData


class PageIndicator(FrozenModel):
    label: str
    value: str


class PageCriterion(FrozenModel):
    text: str
    verdict: CriterionOutcome
    reasoning: str


class PageExecution(FrozenModel):
    key: str
    item_id: str
    area: str
    kind: str
    critical: bool
    question: str
    answer: str
    reference: str | None
    passed: bool
    error: str | None
    total_ms: float
    tokens_in: int
    tokens_out: int
    steps: tuple[StepRecord, ...]
    verdicts: tuple[VerdictRecord, ...]
    judge_outcome: CriterionOutcome | None
    judge_model: str | None
    criteria: tuple[PageCriterion, ...]
    trace_url: str | None


class PagePayload(FrozenModel):
    run_id: str
    state: str
    reason: str
    problems: tuple[str, ...]
    indicators: tuple[PageIndicator, ...]
    consistency_label: str
    consistency_note: str
    critical: tuple[CriticalRow, ...]
    executions: tuple[PageExecution, ...]
    review: tuple[ReviewCard, ...]


class PageExecutions:
    def __init__(self, data: RunData) -> None:
        self._data = data

    def all(self) -> Iterator[PageExecution]:
        for record in self._data.records:
            yield self._of(record)

    def _of(self, record: ExecutionRecord) -> PageExecution:
        verdict = self._data.verdicts.get(record.key)
        request = self._data.requests.get(record.key)
        return PageExecution(
            key=record.key,
            item_id=record.item_id,
            area=record.area,
            kind=record.kind.value,
            critical=record.critical,
            question=record.question,
            answer=record.answer,
            reference=request.reference if request else None,
            passed=record.passed,
            error=record.error,
            total_ms=record.total_ms,
            tokens_in=record.tokens_in,
            tokens_out=record.tokens_out,
            steps=record.steps,
            verdicts=record.verdicts,
            judge_outcome=verdict.outcome if verdict else None,
            judge_model=verdict.judge_model if verdict else None,
            criteria=tuple(self._criteria(record.key)),
            trace_url=self._trace_url(record),
        )

    def _criteria(self, key: str) -> Iterator[PageCriterion]:
        verdict = self._data.verdicts.get(key)
        request = self._data.requests.get(key)
        if verdict is None or request is None:
            return
        for text, criterion in zip(request.rubric, verdict.criteria, strict=True):
            yield PageCriterion(text=text, verdict=criterion.verdict, reasoning=criterion.reasoning)

    def _trace_url(self, record: ExecutionRecord) -> str | None:
        prefix = self._data.manifest.trace_url_prefix
        if prefix is None or record.trace_id is None:
            return None
        return f"{prefix}{record.trace_id}"


class PageIndicators:
    @staticmethod
    def of(data: RunData) -> Iterator[PageIndicator]:
        for label, value in RunIndicators.of(data):
            yield PageIndicator(label=label, value=value)


class PagePayloads:
    @classmethod
    def of(cls, data: RunData) -> PagePayload:
        manifest = data.manifest
        result = CriticalRule.result(manifest, data.records)
        summary = CriticalConsistency.of(manifest, data.records)
        return PagePayload(
            run_id=f"{manifest.commit}:{manifest.started_at}",
            state=result.state.value,
            reason=result.reason,
            problems=tuple(cls._problems(result, data)),
            indicators=tuple(PageIndicators.of(data)),
            consistency_label=summary.label,
            consistency_note=summary.note,
            critical=tuple(CriticalRows.of(data)),
            executions=tuple(PageExecutions(data).all()),
            review=ReviewSample.of(data),
        )

    @staticmethod
    def _problems(result: RoundResult, data: RunData) -> Iterator[str]:
        for failure in result.failures:
            joined = "; ".join(failure.problems)
            grader = failure.grader.value
            yield f"{failure.key}, {grader}: {joined}"
        if result.missing_executions:
            yield "Execuções que faltam: " + ", ".join(result.missing_executions)
        if result.unplanned_critical_items:
            yield "Críticos fora da rodada: " + ", ".join(result.unplanned_critical_items)
        if data.redone_critical:
            yield "Críticos refeitos na retomada: " + ", ".join(data.redone_critical)
