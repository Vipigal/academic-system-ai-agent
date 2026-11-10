from collections.abc import Iterator

from evals.gate import GateRule
from evals.report.metrics import Accuracy, JudgedResult, Percentile, RunCost
from evals.report.tables import Shown
from evals.run_data import RunData

MEDIAN = 0.5
TAIL = 0.95


class RunSummary:
    @classmethod
    def render(cls, data: RunData) -> str:
        return "".join(f"{line}\n" for line in cls.lines(data))

    @classmethod
    def lines(cls, data: RunData) -> Iterator[str]:
        result = data.result
        graders = Accuracy.of("graders", [record.passed for record in data.records])
        pass_k = GateRule.pass_k(data.manifest, data.records)
        yield f"Rodada {result.state}: {len(result.failures)} falhas de gate"
        yield f"Graders: {cls.accuracy(graders)}"
        yield f"Juiz: {cls.accuracy(JudgedResult(data.verdicts).accuracy(data.records))}"
        yield f"{pass_k.label}: {pass_k.passing_items} de {pass_k.items} itens de gate"
        yield cls.latency([record.total_ms for record in data.records])
        yield f"Custo: {Shown.cost(RunCost.total(data.records))}"

    @staticmethod
    def latency(totals: list[float]) -> str:
        p50 = Shown.milliseconds(Percentile.of(totals, MEDIAN))
        p95 = Shown.milliseconds(Percentile.of(totals, TAIL))
        return f"Latência: p50 {p50}, p95 {p95}"

    @staticmethod
    def accuracy(accuracy: Accuracy) -> str:
        if not accuracy.total:
            return "sem dados"
        low, high = accuracy.interval
        interval = f"[{Shown.share(low)}, {Shown.share(high)}]"
        return f"{Shown.share(accuracy.share)} {interval}, n = {accuracy.total}"
