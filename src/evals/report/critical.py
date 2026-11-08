from collections.abc import Iterator

from evals.critical_consistency import PROPOSAL_NOTE, CriticalConsistency
from evals.critical_rule import CriticalFailure, CriticalRule
from evals.graders.verdict import GraderName
from evals.report.indicators import CriticalRow, CriticalRows
from evals.report.tables import MarkdownTable
from evals.run_data import RunData

PROBLEM_SEPARATOR = "; "
LIST_SEPARATOR = ", "


class FailureLine:
    @staticmethod
    def of(key: str, grader: GraderName, problems: tuple[str, ...]) -> str:
        name = grader.value
        joined = PROBLEM_SEPARATOR.join(problems)
        return f"- {key}, {name}: {joined}"

    @classmethod
    def of_critical(cls, failure: CriticalFailure) -> str:
        return cls.of(failure.key, failure.grader, failure.problems)


class CriticalSection:
    def __init__(self, data: RunData) -> None:
        self._data = data
        self._result = CriticalRule.result(data.manifest, data.records)

    def opening(self) -> Iterator[str]:
        state = self._result.state.value
        reason = self._result.reason
        yield f"**Rodada {state} pela regra crítica:** {reason}"
        yield ""
        yield from map(FailureLine.of_critical, self._result.failures)
        yield from self._named("Execuções que faltam", self._result.missing_executions)
        yield from self._named("Críticos fora da rodada", self._result.unplanned_critical_items)
        yield from self._named("Críticos refeitos na retomada", self._data.redone_critical)
        yield ""

    def table(self) -> Iterator[str]:
        summary = CriticalConsistency.of(self._data.manifest, self._data.records)
        yield "## Itens críticos"
        yield ""
        yield summary.note
        yield ""
        yield from self._notes()
        header = ("Item", "k", "Aprovadas", summary.label, "Proposta", "Trajetória", "Rubrica")
        rows = map(self._row, CriticalRows.of(self._data))
        yield from MarkdownTable.of(header, rows)
        yield ""

    @staticmethod
    def _notes() -> Iterator[str]:
        yield "A rubrica aparece ao lado e não reprova a rodada sozinha."
        yield ""
        yield PROPOSAL_NOTE
        yield ""

    @staticmethod
    def _row(row: CriticalRow) -> tuple[str, ...]:
        mark = "sim" if row.passed_all else "não"
        approved = f"{row.approved}/{row.planned}"
        graders = (row.proposal, row.trajectory, row.rubric)
        return (row.item, str(row.planned), approved, mark, *graders)

    @staticmethod
    def _named(title: str, keys: tuple[str, ...]) -> Iterator[str]:
        if keys:
            joined = LIST_SEPARATOR.join(keys)
            yield f"- {title}: {joined}"
