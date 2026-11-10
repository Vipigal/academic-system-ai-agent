from collections import Counter
from collections.abc import Iterator

from evals.dashboard.views import CriterionView, GraderView, PassKView, Rate
from evals.dataset.loader import DatasetLoader
from evals.dataset.parts import FrozenModel
from evals.gate import GateFailure, GateRule
from evals.records import ExecutionRecord
from evals.report.approval import RoundApproval
from evals.report.metrics import Accuracy, Consistency, JudgedResult, Percentile, RunCost
from evals.run_data import RunData

MEDIAN = 0.5
TAIL = 0.95


class ExecutionView(FrozenModel):
    key: str
    item: str
    area: str
    kind: str
    split: str
    gated: bool
    history: tuple[str, ...]
    question: str
    answer: str
    error: str | None
    total_ms: float
    tools: tuple[str, ...]
    graders: dict[str, GraderView]
    criteria: tuple[CriterionView, ...]
    trace_url: str | None


class RunView(FrozenModel):
    name: str
    started_at: str
    commit: str
    model: str
    prompt_version: str
    suites: dict[str, int]
    approval: str
    approval_reasons: tuple[str, ...]
    state: str
    gate_failures: tuple[str, ...]
    gated_executions: int
    graders: Rate
    judge: Rate
    gate: PassKView
    consistency: PassKView
    p50_ms: float | None
    p95_ms: float | None
    cost_usd: float | None
    executions: tuple[ExecutionView, ...]


class RunViews:
    @classmethod
    def of(cls, name: str, data: RunData) -> RunView:
        graders = Accuracy.of("graders", [record.passed for record in data.records])
        judge = JudgedResult(data.verdicts).accuracy(data.records)
        approval = RoundApproval.of(data.result, graders, judge)
        return RunView(
            name=name,
            started_at=data.manifest.started_at,
            commit=data.manifest.commit[:7],
            model=cls._model(data),
            prompt_version=data.manifest.versions.prompt_version,
            suites=cls._suites(data),
            approval=approval.state,
            approval_reasons=approval.reasons,
            state=data.result.state,
            gate_failures=tuple(cls._failures(data.result.failures)),
            gated_executions=len(data.manifest.gated_keys),
            graders=Rate.of(graders),
            judge=Rate.of(judge),
            gate=PassKView.of(GateRule.pass_k(data.manifest, data.records)),
            consistency=PassKView.of(Consistency.of(data.records)),
            p50_ms=cls._latency(data, MEDIAN),
            p95_ms=cls._latency(data, TAIL),
            cost_usd=cls._cost(data),
            executions=tuple(ExecutionViews.of(data, record) for record in data.records),
        )

    @staticmethod
    def _model(data: RunData) -> str:
        versions = data.manifest.versions
        return f"{versions.model} · {versions.effort}"

    @staticmethod
    def _latency(data: RunData, share: float) -> float | None:
        return Percentile.of([record.total_ms for record in data.records], share)

    @staticmethod
    def _cost(data: RunData) -> float | None:
        cost = RunCost.total(data.records)
        return None if cost is None else float(cost)

    @staticmethod
    def _suites(data: RunData) -> dict[str, int]:
        dataset = DatasetLoader.load()
        suite_of = {
            item.id: suite.value for suite, items in dataset.suites.items() for item in items
        }
        items = {record.item_id for record in data.records}
        counts = Counter(suite_of.get(item, "outra") for item in items)
        return dict(counts.most_common())

    @staticmethod
    def _failures(failures: tuple[GateFailure, ...]) -> Iterator[str]:
        graders: dict[str, list[str]] = {}
        for failure in failures:
            graders.setdefault(failure.key, []).append(failure.grader.value)
        for key, names in graders.items():
            joined = ", ".join(names)
            yield f"{key} · {joined}"


class ExecutionViews:
    @classmethod
    def of(cls, data: RunData, record: ExecutionRecord) -> ExecutionView:
        prefix = data.manifest.trace_url_prefix
        trace = record.trace_id
        return ExecutionView(
            key=record.key,
            item=record.item_id,
            area=record.area,
            kind=record.kind,
            split=record.split,
            gated=record.gated,
            history=record.history,
            question=record.question,
            answer=record.answer,
            error=record.error,
            total_ms=record.total_ms,
            tools=tuple(step.name for step in record.steps),
            graders={
                verdict.grader.value: GraderView(passed=verdict.passed, problems=verdict.problems)
                for verdict in record.verdicts
            },
            criteria=tuple(cls._criteria(data, record.key)),
            trace_url=f"{prefix}{trace}" if prefix and trace else None,
        )

    @staticmethod
    def _criteria(data: RunData, key: str) -> Iterator[CriterionView]:
        verdict = data.verdicts.get(key)
        request = data.requests.get(key)
        if verdict is None or request is None:
            return
        for criterion in verdict.criteria:
            text = request.rubric[criterion.criterion - 1]
            yield CriterionView(text=text, verdict=criterion.verdict, reasoning=criterion.reasoning)


class DashboardPayload(FrozenModel):
    runs: tuple[RunView, ...]
