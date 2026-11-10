from collections.abc import Iterator, Sequence

from evals.calibration.cases import CalibrationCase, CalibrationLabel, Tampering
from evals.dataset.parts import FrozenModel
from evals.judge.verdicts import CriterionOutcome, JudgedVerdict, JudgeRequest

CLASS_SIZE = 20
TARGET_PER_CLASS = 18


class ClassScore(FrozenModel):
    right: int
    judged: int
    total: int

    @property
    def meets_target(self) -> bool:
        return self.judged == self.total == CLASS_SIZE and self.right >= TARGET_PER_CLASS


class CalibrationCriterion(FrozenModel):
    text: str
    verdict: CriterionOutcome
    reasoning: str


class CalibrationMiss(FrozenModel):
    id: str
    item: str
    label: CalibrationLabel
    tampering: Tampering | None
    answer: str
    criteria: tuple[CalibrationCriterion, ...]


class CalibrationResult(FrozenModel):
    judge_model: str | None
    tpr: ClassScore
    tnr: ClassScore
    pending: tuple[str, ...]
    misses: tuple[CalibrationMiss, ...]

    @property
    def complete(self) -> bool:
        return not self.pending and self.tpr.total == self.tnr.total == CLASS_SIZE

    @property
    def met_target(self) -> bool:
        return self.tpr.meets_target and self.tnr.meets_target


class CalibrationScoring:
    def __init__(
        self,
        cases: Sequence[CalibrationCase],
        requests: Sequence[JudgeRequest],
        verdicts: Sequence[JudgedVerdict],
    ) -> None:
        self._cases = cases
        self._requests = {request.id: request for request in requests}
        self._verdicts = {verdict.id: verdict for verdict in verdicts}

    def result(self) -> CalibrationResult:
        models = sorted({verdict.judge_model for verdict in self._verdicts.values()})
        return CalibrationResult(
            judge_model=", ".join(models) or None,
            tpr=self._score(CalibrationLabel.CORRECT),
            tnr=self._score(CalibrationLabel.TAMPERED),
            pending=tuple(case.id for case in self._cases if case.id not in self._verdicts),
            misses=tuple(self._misses()),
        )

    def _score(self, label: CalibrationLabel) -> ClassScore:
        cases = [case for case in self._cases if case.label is label]
        judged = [case for case in cases if case.id in self._verdicts]
        right = sum(self._is_right(case) for case in judged)
        return ClassScore(right=right, judged=len(judged), total=len(cases))

    def _is_right(self, case: CalibrationCase) -> bool:
        approved = self._verdicts[case.id].passed
        return approved is (case.label is CalibrationLabel.CORRECT)

    def _misses(self) -> Iterator[CalibrationMiss]:
        for case in self._cases:
            if case.id in self._verdicts and not self._is_right(case):
                yield CalibrationMiss(
                    id=case.id,
                    item=case.item,
                    label=case.label,
                    tampering=case.tampering,
                    answer=case.answer,
                    criteria=tuple(self._criteria_of(case)),
                )

    def _criteria_of(self, case: CalibrationCase) -> Iterator[CalibrationCriterion]:
        rubric = self._requests[case.id].rubric
        criteria = self._verdicts[case.id].criteria
        for text, criterion in zip(rubric, criteria, strict=True):
            yield CalibrationCriterion(
                text=text, verdict=criterion.verdict, reasoning=criterion.reasoning
            )
