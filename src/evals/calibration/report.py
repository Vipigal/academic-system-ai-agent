from collections.abc import Iterator

from evals.calibration.scoring import CalibrationMiss, CalibrationResult, ClassScore
from evals.report.tables import MarkdownTable

SMALL_SAMPLE = "Meta: 18 em 20 em cada classe. Com 40 respostas, o intervalo de confiança é largo."
CLASS_HEADER = ("Classe", "Certas", "Julgadas", "Total")


class CalibrationReport:
    @classmethod
    def render(cls, result: CalibrationResult) -> str:
        model = result.judge_model or "sem julgamento"
        table = (
            cls._row("TPR, referências corretas aprovadas", result.tpr),
            cls._row("TNR, respostas adulteradas reprovadas", result.tnr),
        )
        return "\n".join(
            (
                "# Calibração do juiz",
                "",
                cls._verdict(result),
                "",
                f"Modelo do juiz: {model}",
                "",
                *MarkdownTable.of(CLASS_HEADER, table),
                "",
                SMALL_SAMPLE,
                "",
                "## Erros do juiz",
                "",
                *cls._misses(result),
                "",
            )
        )

    @staticmethod
    def _verdict(result: CalibrationResult) -> str:
        if not result.complete:
            judged = result.tpr.judged + result.tnr.judged
            return f"**INCOMPLETA:** {judged} respostas julgadas; a meta só vale com as 40."
        return "**META ATINGIDA**" if result.met_target else "**ABAIXO DA META**"

    @staticmethod
    def _row(title: str, score: ClassScore) -> tuple[str, ...]:
        counts = (score.right, score.judged, score.total)
        return (title, *map(str, counts))

    @classmethod
    def _misses(cls, result: CalibrationResult) -> Iterator[str]:
        if not result.misses:
            yield "Nenhum."
        for miss in result.misses:
            yield from cls._miss(miss)

    @staticmethod
    def _miss(miss: CalibrationMiss) -> Iterator[str]:
        kind = miss.tampering.value if miss.tampering else "sem adulteração"
        label = miss.label.value
        yield f"### {miss.id}, {miss.item}, {label}: {kind}"
        yield ""
        yield f"> {miss.answer}"
        yield ""
        for criterion in miss.criteria:
            verdict = criterion.verdict.value
            yield f"- `{verdict}` {criterion.text}: {criterion.reasoning}"
        yield ""
