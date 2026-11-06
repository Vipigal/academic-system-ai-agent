from collections.abc import Iterable
from pathlib import Path

from evals.calibration import CalibrationResult, CalibrationScoring
from evals.calibration_cases import CalibrationCase, CalibrationCases
from evals.calibration_report import CalibrationReport
from evals.golden.loader import GoldenLoader
from evals.judge.port import Judge
from evals.judge.session import JudgingSession
from evals.judge.verdicts import JudgedVerdict, JudgeRequest
from evals.run_files import JsonLines, RunFiles

RESULT_JSON = "calibration.json"
RESULT_MARKDOWN = "calibration.md"


class CalibrationRun:
    def __init__(self, cases: Iterable[CalibrationCase], output: Path) -> None:
        self._cases = tuple(cases)
        self._output = output
        self._files = RunFiles(output)

    def prepare(self) -> None:
        self._output.mkdir(parents=True, exist_ok=True)
        known = {request.id for request in self._requests()}
        golden = GoldenLoader.load()
        for request in CalibrationCases.requests_of(self._cases, golden.items):
            if request.id not in known:
                JsonLines.append(self._files.judge_requests, request)

    async def judge(self, judge: Judge, batch_size: int) -> None:
        await JudgingSession(judge, self._files).run(batch_size)

    def finish(self) -> CalibrationResult:
        verdicts = JsonLines.read(self._files.judge_verdicts, JudgedVerdict)
        result = CalibrationScoring(self._cases, self._requests(), verdicts).result()
        content = result.model_dump_json(indent=2)
        (self._output / RESULT_JSON).write_text(content, encoding="utf-8")
        report = CalibrationReport.render(result)
        (self._output / RESULT_MARKDOWN).write_text(report, encoding="utf-8")
        return result

    def _requests(self) -> list[JudgeRequest]:
        return JsonLines.read(self._files.judge_requests, JudgeRequest)
