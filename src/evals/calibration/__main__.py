import argparse
import asyncio
import sys
from pathlib import Path

from evals.calibration.cases import CalibrationCase, CalibrationCases
from evals.calibration.report import CalibrationReport
from evals.calibration.run import CalibrationRun
from evals.calibration.scoring import CalibrationResult
from evals.judge.agent_file import JudgeAgent
from evals.judge.claude_code import ClaudeCodeJudge
from evals.judge.port import Judge, JudgeFailedError

DEFAULT_BATCH_SIZE = 10
EXIT_BELOW_TARGET = 1
EXIT_INCOMPLETE = 2


class CalibrateCli:
    @staticmethod
    def parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="python -m evals.calibration")
        parser.add_argument("--output", type=Path, required=True)
        parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
        parser.add_argument("--items", nargs="+", default=[])
        return parser

    @staticmethod
    def exit_code(result: CalibrationResult) -> int:
        if not result.complete:
            return EXIT_INCOMPLETE
        return 0 if result.met_target else EXIT_BELOW_TARGET

    @classmethod
    def execute(cls, run: CalibrationRun, judge: Judge, batch_size: int) -> int:
        run.prepare()
        try:
            asyncio.run(run.judge(judge, batch_size))
        except JudgeFailedError as error:
            sys.stderr.write(f"{error}\nRode de novo para retomar\n")
            run.finish()
            return EXIT_BELOW_TARGET
        result = run.finish()
        sys.stdout.write(CalibrationReport.render(result))
        return cls.exit_code(result)

    @staticmethod
    def _cases_of(items: list[str]) -> list[CalibrationCase]:
        cases = CalibrationCases.load()
        return [case for case in cases if not items or case.id in items]

    @classmethod
    def main(cls, command: list[str]) -> int:
        arguments = cls.parser().parse_args(command)
        run = CalibrationRun(cls._cases_of(arguments.items), arguments.output)
        return cls.execute(run, ClaudeCodeJudge(JudgeAgent.load()), arguments.batch_size)


if __name__ == "__main__":
    sys.exit(CalibrateCli.main(sys.argv[1:]))
