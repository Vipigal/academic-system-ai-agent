from evals.dataset.parts import FrozenModel
from evals.gate import PassK
from evals.judge.verdicts import CriterionOutcome
from evals.report.metrics import Accuracy


class Rate(FrozenModel):
    passed: int
    total: int
    low: float
    high: float

    @classmethod
    def of(cls, accuracy: Accuracy) -> Rate:
        low, high = accuracy.interval
        return cls(passed=accuracy.passed, total=accuracy.total, low=low, high=high)


class PassKView(FrozenModel):
    label: str
    passing: int
    items: int

    @classmethod
    def of(cls, pass_k: PassK) -> PassKView:
        return cls(label=pass_k.label, passing=pass_k.passing_items, items=pass_k.items)


class GraderView(FrozenModel):
    passed: bool
    problems: tuple[str, ...]


class CriterionView(FrozenModel):
    text: str
    verdict: CriterionOutcome
    reasoning: str
