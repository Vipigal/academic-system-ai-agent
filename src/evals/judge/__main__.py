import argparse
import asyncio
import sys
from pathlib import Path

from evals.dashboard.page import DashboardPage
from evals.judge.agent_file import JudgeAgent
from evals.judge.claude_code import ClaudeCodeJudge
from evals.judge.port import JudgeFailedError
from evals.judge.session import JudgingSession
from evals.run_files import RunFiles

DEFAULT_BATCH_SIZE = 10


class JudgeCli:
    @staticmethod
    def parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="python -m evals.judge")
        parser.add_argument("--run-dir", type=Path, required=True)
        parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
        parser.add_argument("--limit", type=int)
        return parser

    @classmethod
    def main(cls, command: list[str]) -> int:
        arguments = cls.parser().parse_args(command)
        files = RunFiles(arguments.run_dir)
        session = JudgingSession(ClaudeCodeJudge(JudgeAgent.load()), files)
        try:
            outcome = asyncio.run(session.run(arguments.batch_size, arguments.limit))
        except JudgeFailedError as error:
            DashboardPage.write()
            missing = len(session.pending())
            sys.stderr.write(f"{error}\nRode de novo para retomar: {missing} faltam\n")
            return 1
        DashboardPage.write()
        sys.stdout.write(
            f"Julgados: {outcome.judged}, recusados: {outcome.rejected}, "
            f"pendentes: {outcome.pending}\n"
        )
        return 0


if __name__ == "__main__":
    sys.exit(JudgeCli.main(sys.argv[1:]))
