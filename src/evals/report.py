from collections.abc import Iterator

from evals.golden.vocabulary import Split
from evals.page.results_page import ResultsPage
from evals.records import ExecutionRecord
from evals.report_critical import CriticalSection, FailureLine
from evals.report_indicators import MEDIAN, TAIL
from evals.report_tables import MarkdownTable, Shown
from evals.run_data import RunData
from evals.run_files import RunFiles
from evals.run_metrics import (
    GroupedAccuracy,
    JudgedResult,
    Percentile,
    Repeatability,
    ResultsByName,
    RunCost,
)

MEASURE_HEADER = ("Medida", "Valor")


class OverviewSection:
    def __init__(self, data: RunData) -> None:
        self._data = data
        self._records = data.records
        self._judged = JudgedResult(data.verdicts)

    def lines(self) -> Iterator[str]:
        yield "## Resumo"
        yield ""
        yield from MarkdownTable.of(MEASURE_HEADER, self._measures())
        yield ""

    def _measures(self) -> Iterator[tuple[str, str]]:
        yield from self._volumes()
        yield from self._quality()
        yield from PerformanceMeasures.of(self._records)

    def _volumes(self) -> Iterator[tuple[str, str]]:
        records = self._records
        planned = len(self._data.manifest.planned_keys)
        finished = len(records)
        failed = sum(1 for record in records if record.error)
        yield "Execuções", f"{finished} de {planned}"
        yield "Execuções com erro", str(failed)
        yield "Refeitas na retomada", str(len(self._data.redone_keys))
        holdout = [record for record in records if record.split is Split.HOLDOUT]
        yield "Execuções no holdout", str(len(holdout))
        yield "Execuções sem julgamento", str(self._unjudged(failed))
        yield "Vereditos unknown do juiz", str(self._judged.unknown(records))

    def _unjudged(self, failed: int) -> int:
        judged = self._judged.judged_of(self._records)
        return len(self._records) - failed - len(judged)

    def _quality(self) -> Iterator[tuple[str, str]]:
        judged = self._judged
        deterministic = Repeatability.results_by_item(self._records, lambda record: record.passed)
        with_rubric = Repeatability.results_by_item(
            judged.judged_of(self._records), judged.with_rubric
        )
        stable = Repeatability.stable(deterministic)
        yield "Itens", str(len(deterministic))
        pass_at_one = Repeatability.pass_at_one(deterministic)
        yield "pass@1 médio, determinísticos", Shown.share(pass_at_one)
        yield "pass@1 médio, com a rubrica", self._rubric_share(with_rubric)
        yield "Estabilidade entre repetições", f"{stable.passed} de {stable.total} itens"

    @staticmethod
    def _rubric_share(results: ResultsByName) -> str:
        if not results:
            return "sem julgamento"
        return Shown.share(Repeatability.pass_at_one(results))


class PerformanceMeasures:
    @staticmethod
    def of(records: tuple[ExecutionRecord, ...]) -> Iterator[tuple[str, str]]:
        total = [record.total_ms for record in records]
        firsts = (record.first_token_ms for record in records)
        first = [value for value in firsts if value is not None]
        for title, values in (("total", total), ("até o primeiro token", first)):
            yield f"Latência {title}, p50", Shown.milliseconds(Percentile.of(values, MEDIAN))
            yield f"Latência {title}, p95", Shown.milliseconds(Percentile.of(values, TAIL))
        yield "Tokens de entrada", str(sum(record.tokens_in for record in records))
        yield "Tokens de saída", str(sum(record.tokens_out for record in records))
        yield "Custo", Shown.cost(RunCost.total(records))


class DetailSection:
    def __init__(self, data: RunData) -> None:
        self._data = data
        self._records = data.records

    def configuration(self) -> Iterator[str]:
        manifest = self._data.manifest
        versions = manifest.versions
        yield "## Configuração"
        yield ""
        yield from MarkdownTable.of(
            ("Campo", "Valor"),
            (
                ("Modelo", versions.model),
                ("Effort", versions.effort),
                ("Prompt", versions.prompt_version),
                ("Hash das skills", versions.skills_hash),
                ("Hash das descrições das tools", versions.tools_hash),
                ("Commit", manifest.commit),
                ("Working tree limpa", "sim" if manifest.worktree_clean else "não"),
                ("Início", manifest.started_at),
            ),
        )
        yield ""

    def accuracy(self) -> Iterator[str]:
        judged = JudgedResult(self._data.verdicts).accuracy(self._records)
        graders = (*GroupedAccuracy.by_grader(self._records), judged)
        yield from MarkdownTable.accuracy("Acerto por grader", graders)
        by_area = GroupedAccuracy.by(self._records, lambda record: record.area)
        yield from MarkdownTable.accuracy("Acerto por área", by_area)
        by_kind = GroupedAccuracy.by(self._records, lambda record: record.kind.value)
        yield from MarkdownTable.accuracy("Acerto por kind", by_kind)

    def failures(self) -> Iterator[str]:
        yield "## Falhas dos graders"
        yield ""
        for record in self._records:
            for verdict in record.verdicts:
                if not verdict.passed:
                    yield FailureLine.of(record.key, verdict.grader, verdict.problems)
        yield ""


class RunReport:
    @staticmethod
    def render(data: RunData) -> str:
        critical = CriticalSection(data)
        detail = DetailSection(data)
        lines = (
            "# Relatório do eval",
            "",
            *critical.opening(),
            *detail.configuration(),
            *OverviewSection(data).lines(),
            *critical.table(),
            *detail.accuracy(),
            *detail.failures(),
        )
        return "\n".join(lines)

    @classmethod
    def write(cls, files: RunFiles) -> RunData:
        data = RunData.load(files)
        files.report.write_text(cls.render(data), encoding="utf-8")
        files.page.write_text(ResultsPage.render(data), encoding="utf-8")
        return data
