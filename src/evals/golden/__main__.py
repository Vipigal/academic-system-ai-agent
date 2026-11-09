import argparse
import asyncio
import sys

from evals.golden.loader import GoldenLoader
from evals.golden.oracle import Oracle
from evals.golden.query_checks import QueryChecks
from evals.golden.report import CheckReport
from evals.golden.static_checks import StaticChecks
from evals.golden.tool_names import ToolNames

CHECK = "check"


class GoldenCli:
    @staticmethod
    async def check() -> CheckReport:
        golden = GoldenLoader.load()
        problems = StaticChecks(ToolNames.registered()).run(golden)
        async with Oracle.from_environment() as oracle:
            outcome = await QueryChecks(oracle).run(golden.items)
        return CheckReport(golden, outcome.facts, [*problems, *outcome.problems])

    @classmethod
    def main(cls, arguments: list[str]) -> int:
        parser = argparse.ArgumentParser(prog="python -m evals.golden")
        parser.add_argument("command", choices=[CHECK])
        parser.parse_args(arguments)
        report = asyncio.run(cls.check())
        sys.stdout.writelines(f"{line}\n" for line in report.lines())
        return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(GoldenCli.main(sys.argv[1:]))
