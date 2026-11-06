from collections.abc import Iterator
from dataclasses import dataclass
from itertools import batched

from evals.judge.port import Judge
from evals.judge.verdicts import ItemVerdict, JudgedVerdict, JudgeRequest
from evals.run_files import JsonLines, RunFiles


@dataclass(frozen=True, slots=True)
class JudgingOutcome:
    judged: int
    rejected: int
    pending: int


class JudgingSession:
    def __init__(self, judge: Judge, files: RunFiles) -> None:
        self._judge = judge
        self._files = files

    def pending(self) -> list[JudgeRequest]:
        requests = JsonLines.read(self._files.judge_requests, JudgeRequest)
        verdicts = JsonLines.read(self._files.judge_verdicts, JudgedVerdict)
        judged = {verdict.id for verdict in verdicts}
        return [request for request in requests if request.id not in judged]

    async def run(self, batch_size: int, limit: int | None = None) -> JudgingOutcome:
        pending = self.pending()
        chosen = pending[:limit] if limit is not None else pending
        judged = 0
        for batch in batched(chosen, batch_size, strict=False):
            judged += await self._judged(batch)
        return JudgingOutcome(judged, len(chosen) - judged, len(pending) - judged)

    async def _judged(self, batch: tuple[JudgeRequest, ...]) -> int:
        answer = await self._judge.judge(batch)
        accepted = list(self._accepted(batch, answer.verdicts))
        for verdict in accepted:
            line = JudgedVerdict(**dict(verdict), judge_model=self._judge.model)
            JsonLines.append(self._files.judge_verdicts, line)
        return len(accepted)

    @staticmethod
    def _accepted(
        batch: tuple[JudgeRequest, ...], verdicts: tuple[ItemVerdict, ...]
    ) -> Iterator[ItemVerdict]:
        requests = {request.id: request for request in batch}
        for verdict in verdicts:
            request = requests.pop(verdict.id, None)
            if request is not None and verdict.covers(request):
                yield verdict
