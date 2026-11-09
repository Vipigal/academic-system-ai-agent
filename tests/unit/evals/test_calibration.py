import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import pytest

from evals.calibration.__main__ import CalibrateCli
from evals.calibration.cases import CalibrationCase, CalibrationCases, CalibrationLabel, Tampering
from evals.calibration.run import CalibrationRun
from evals.golden.loader import GoldenLoader
from evals.golden.vocabulary import Split
from evals.judge.port import JudgeAnswer
from evals.judge.verdicts import CriterionOutcome, CriterionVerdict, ItemVerdict, JudgeRequest

CASES = CalibrationCases.load()


def test_the_set_has_twenty_of_each_class_with_every_kind_of_tampering() -> None:
    labels = Counter(case.label for case in CASES)
    assert labels == {CalibrationLabel.CORRECT: 20, CalibrationLabel.TAMPERED: 20}
    kinds = {case.tampering for case in CASES if case.label is CalibrationLabel.TAMPERED}
    assert kinds == set(Tampering)
    assert len({case.id for case in CASES}) == 40


def test_the_cases_use_only_dev_items_outside_the_declared_divergences() -> None:
    items = {item.id: item for item in GoldenLoader.load().items}
    assert all(items[case.item].split is Split.DEV for case in CASES)
    assert {case.item for case in CASES}.isdisjoint({"FI-03", "SR-05"})


def test_a_correct_case_is_the_reference_and_a_tampered_case_is_not() -> None:
    items = {item.id: item for item in GoldenLoader.load().items}
    for case in CASES:
        is_reference = case.answer == items[case.item].reference
        assert is_reference is (case.label is CalibrationLabel.CORRECT), case.id


class LabelJudge:
    model = "claude-sonnet-5-5"

    def __init__(self, wrong: frozenset[str] = frozenset()) -> None:
        self._wrong = wrong
        self._labels = {case.id: case.label for case in CASES}

    async def judge(self, batch: Sequence[JudgeRequest]) -> JudgeAnswer:
        return JudgeAnswer(verdicts=tuple(map(self._verdict, batch)))

    def _verdict(self, request: JudgeRequest) -> ItemVerdict:
        correct = self._labels[request.id] is CalibrationLabel.CORRECT
        approved = correct is not (request.id in self._wrong)
        outcome = CriterionOutcome.APPROVED if approved else CriterionOutcome.REJECTED
        return ItemVerdict(
            id=request.id,
            criteria=tuple(
                CriterionVerdict(criterion=number, reasoning="Motivo.", verdict=outcome)
                for number, _ in enumerate(request.rubric, start=1)
            ),
        )


def run_with(judge: LabelJudge, output: Path, cases: tuple[CalibrationCase, ...] = CASES) -> int:
    return CalibrateCli.execute(CalibrationRun(cases, output), judge, 10)


def test_a_perfect_judge_meets_the_target(tmp_path: Path) -> None:
    assert run_with(LabelJudge(), tmp_path) == 0
    result = json.loads((tmp_path / "calibration.json").read_text(encoding="utf-8"))
    assert (result["tpr"]["right"], result["tnr"]["right"]) == (20, 20)
    assert result["judge_model"] == "claude-sonnet-5-5"
    assert "META ATINGIDA" in (tmp_path / "calibration.md").read_text(encoding="utf-8")


def test_two_errors_in_a_class_still_meet_the_target(tmp_path: Path) -> None:
    assert run_with(LabelJudge(frozenset({"CAL-21", "CAL-22"})), tmp_path) == 0


def test_three_errors_in_a_class_miss_the_target_and_list_the_reasoning(tmp_path: Path) -> None:
    code = run_with(LabelJudge(frozenset({"CAL-21", "CAL-22", "CAL-23"})), tmp_path)
    assert code == 1
    result = json.loads((tmp_path / "calibration.json").read_text(encoding="utf-8"))
    assert result["tnr"]["right"] == 17
    miss = result["misses"][0]
    assert miss["tampering"] == "value"
    assert miss["criteria"][0]["reasoning"] == "Motivo."
    assert "ABAIXO DA META" in (tmp_path / "calibration.md").read_text(encoding="utf-8")


def test_an_unknown_verdict_does_not_approve_a_correct_answer(tmp_path: Path) -> None:
    class UnknownJudge(LabelJudge):
        def _verdict(self, request: JudgeRequest) -> ItemVerdict:
            verdict = super()._verdict(request)
            if request.id != "CAL-01":
                return verdict
            unknown = CriterionVerdict(
                criterion=1, reasoning="Sem base.", verdict=CriterionOutcome.UNKNOWN
            )
            return verdict.model_copy(update={"criteria": (unknown, *verdict.criteria[1:])})

    assert run_with(UnknownJudge(), tmp_path) == 0
    result = json.loads((tmp_path / "calibration.json").read_text(encoding="utf-8"))
    assert result["tpr"]["right"] == 19


def test_a_subset_never_meets_the_target_and_resumes(tmp_path: Path) -> None:
    assert run_with(LabelJudge(), tmp_path, CASES[:2]) == 2
    assert "INCOMPLETA:** 2 respostas" in (tmp_path / "calibration.md").read_text(encoding="utf-8")
    assert run_with(LabelJudge(), tmp_path, CASES) == 0


def test_the_parser_requires_the_output() -> None:
    with pytest.raises(SystemExit):
        CalibrateCli.parser().parse_args([])
