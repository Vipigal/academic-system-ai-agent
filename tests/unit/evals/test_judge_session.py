from collections.abc import Sequence
from pathlib import Path

import pytest

from evals.judge.port import JudgeAnswer, JudgeFailedError
from evals.judge.session import JudgingSession
from evals.judge.verdicts import (
    CriterionOutcome,
    CriterionVerdict,
    ItemVerdict,
    JudgedVerdict,
    JudgeRequest,
)
from evals.run_files import JsonLines, RunFiles
from tests.unit.evals.judge_support import JUDGE_MODEL, REQUEST, verdict_for


class RecordingJudge:
    model = JUDGE_MODEL

    def __init__(self, failing_after: int | None = None) -> None:
        self.batches: list[list[str]] = []
        self._failing_after = failing_after

    async def judge(self, batch: Sequence[JudgeRequest]) -> JudgeAnswer:
        if self._failing_after is not None and len(self.batches) == self._failing_after:
            raise JudgeFailedError("limite de uso")
        self.batches.append([request.id for request in batch])
        return JudgeAnswer(verdicts=tuple(map(verdict_for, batch)))


def requests_in(path: Path, total: int) -> RunFiles:
    files = RunFiles(path)
    for number in range(1, total + 1):
        JsonLines.append(files.judge_requests, REQUEST.model_copy(update={"id": f"X#{number}"}))
    return files


async def test_the_session_judges_in_batches(tmp_path: Path) -> None:
    judge = RecordingJudge()
    outcome = await JudgingSession(judge, requests_in(tmp_path, 5)).run(batch_size=2)
    assert [len(batch) for batch in judge.batches] == [2, 2, 1]
    assert (outcome.judged, outcome.rejected, outcome.pending) == (5, 0, 0)


async def test_the_session_resumes_without_repeating_what_was_judged(tmp_path: Path) -> None:
    files = requests_in(tmp_path, 5)
    with pytest.raises(JudgeFailedError):
        await JudgingSession(RecordingJudge(failing_after=1), files).run(batch_size=2)

    retry = RecordingJudge()
    outcome = await JudgingSession(retry, files).run(batch_size=2)

    assert retry.batches == [["X#3", "X#4"], ["X#5"]]
    assert outcome.judged == 3
    verdicts = JsonLines.read(files.judge_verdicts, JudgedVerdict)
    assert len(verdicts) == 5
    assert {verdict.judge_model for verdict in verdicts} == {JUDGE_MODEL}


async def test_the_limit_judges_only_the_first_pending(tmp_path: Path) -> None:
    judge = RecordingJudge()
    outcome = await JudgingSession(judge, requests_in(tmp_path, 5)).run(batch_size=10, limit=3)
    assert judge.batches == [["X#1", "X#2", "X#3"]]
    assert outcome.pending == 2


class PartialJudge:
    model = JUDGE_MODEL

    async def judge(self, batch: Sequence[JudgeRequest]) -> JudgeAnswer:
        wrong = CriterionVerdict(criterion=9, reasoning="Fora.", verdict=CriterionOutcome.APPROVED)
        return JudgeAnswer(
            verdicts=(
                verdict_for(batch[0]),
                ItemVerdict(id=batch[1].id, criteria=(wrong,)),
                verdict_for(REQUEST.model_copy(update={"id": "desconhecido"})),
            )
        )


async def test_a_verdict_without_every_criterion_or_of_another_item_stays_pending(
    tmp_path: Path,
) -> None:
    files = requests_in(tmp_path, 2)
    session = JudgingSession(PartialJudge(), files)
    outcome = await session.run(batch_size=2)
    assert (outcome.judged, outcome.rejected, outcome.pending) == (1, 1, 1)
    assert [request.id for request in session.pending()] == ["X#2"]
