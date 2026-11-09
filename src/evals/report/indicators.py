from collections.abc import Iterator

from evals.critical_consistency import ConsistencySummary, CriticalConsistency
from evals.golden.parts import FrozenModel
from evals.graders.verdict import GraderName
from evals.records import ExecutionRecord
from evals.report.metrics import JudgedResult, Percentile, Repeatability, RunCost
from evals.report.tables import Shown
from evals.run_data import RunData

MEDIAN = 0.5
TAIL = 0.95


class CriticalRow(FrozenModel):
    item: str
    planned: int
    approved: int
    passed_all: bool
    proposal: str
    trajectory: str
    rubric: str


class CriticalRows:
    @classmethod
    def of(cls, data: RunData) -> Iterator[CriticalRow]:
        judged = JudgedResult(data.verdicts)
        for item in CriticalConsistency.of(data.manifest, data.records).items:
            runs = [record for record in data.records if record.item_id == item.item]
            rubric = judged.accuracy(runs)
            unknown = judged.unknown(runs)
            yield CriticalRow(
                item=item.item,
                planned=item.planned,
                approved=item.approved,
                passed_all=item.passed_all,
                proposal=cls._share_of(runs, GraderName.PROPOSAL),
                trajectory=cls._share_of(runs, GraderName.TRAJECTORY),
                rubric=f"{rubric.passed}/{rubric.total}, {unknown} unknown",
            )

    @staticmethod
    def _share_of(runs: list[ExecutionRecord], grader: GraderName) -> str:
        results = [v.passed for run in runs for v in run.verdicts if v.grader is grader]
        if not results:
            return "sem dado"
        passed = sum(results)
        total = len(results)
        return f"{passed}/{total}"


class ConsistencyIndicators:
    @staticmethod
    def of(summary: ConsistencySummary) -> Iterator[tuple[str, str]]:
        passing = summary.passing_items
        total = len(summary.items)
        approved = summary.attempts_approved
        planned = summary.attempts_planned
        yield summary.label, f"{passing} de {total} itens críticos"
        rate = Shown.share(summary.attempt_rate)
        yield "Taxa por tentativa", f"{rate} ({approved}/{planned})"


class RunIndicators:
    @classmethod
    def of(cls, data: RunData) -> Iterator[tuple[str, str]]:
        yield from ConsistencyIndicators.of(CriticalConsistency.of(data.manifest, data.records))
        yield from cls._quality(data)
        yield from cls._latency(data.records)
        yield "Custo", Shown.cost(RunCost.total(data.records))
        yield "Modelo", data.manifest.versions.model
        yield "Commit", data.manifest.commit

    @staticmethod
    def _quality(data: RunData) -> Iterator[tuple[str, str]]:
        judged = JudgedResult(data.verdicts)
        results = Repeatability.results_by_item(data.records, lambda record: record.passed)
        rubric = judged.accuracy(data.records)
        unknown = judged.unknown(data.records)
        yield "pass@1 médio", Shown.share(Repeatability.pass_at_one(results))
        yield "Critérios aprovados", Shown.criteria(judged.criteria(data.records))
        yield "Rubrica", f"{rubric.passed} aprovadas de {rubric.total} julgadas, {unknown} unknown"

    @staticmethod
    def _latency(records: tuple[ExecutionRecord, ...]) -> Iterator[tuple[str, str]]:
        total = [record.total_ms for record in records]
        yield "Latência p50", Shown.milliseconds(Percentile.of(total, MEDIAN))
        yield "Latência p95", Shown.milliseconds(Percentile.of(total, TAIL))
