import argparse
import asyncio
import sys
from pathlib import Path

from evals.critical_rule import CriticalRule
from evals.driver_factory import DriverFactory
from evals.golden.vocabulary import Split
from evals.report.markdown import RunReport
from evals.run_data import RunData
from evals.run_manifest import RunConflictError
from evals.run_session import RunSession
from evals.selection import GoldenSource, ItemSelection, Repetitions, RunRequest, SelectionError

RESULTS_DIRECTORY = Path(__file__).parent / "results"
GOLDEN_FILES = [source.value for source in GoldenSource]
ONE_OR_MORE = "+"


class RunCli:
    @classmethod
    def parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="python -m evals.run")
        parser.add_argument("--model", required=True)
        parser.add_argument("--effort", default="low")
        parser.add_argument("--repeat", type=int, default=1)
        parser.add_argument("--critical-repeat", type=int)
        parser.add_argument("--concurrency", type=int)
        parser.add_argument("--output", type=Path)
        parser.add_argument("--env-file", type=Path)
        cls._selection_options(parser)
        return parser

    @staticmethod
    def request_of(arguments: argparse.Namespace) -> RunRequest:
        output = arguments.output or RESULTS_DIRECTORY / f"{arguments.model}-{arguments.effort}"
        return RunRequest(
            selection=ItemSelection(
                sources=frozenset(map(GoldenSource, arguments.golden)),
                split=Split(arguments.split),
                holdout_from=frozenset(map(GoldenSource, arguments.include_holdout)),
                only=frozenset(arguments.items),
            ),
            repetitions=Repetitions(arguments.repeat, arguments.critical_repeat),
            output=output,
            concurrency=arguments.concurrency,
            env_file=arguments.env_file,
        )

    @classmethod
    def main(cls, command: list[str]) -> int:
        parser = cls.parser()
        arguments = parser.parse_args(command)
        try:
            data = asyncio.run(cls._execute(arguments))
        except (SelectionError, RunConflictError) as error:
            parser.error(str(error))
        sys.stdout.write(RunReport.render(data))
        return CriticalRule.result(data.manifest, data.records).exit_code

    @staticmethod
    def _selection_options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--split", choices=list(Split), type=Split, default=Split.DEV)
        parser.add_argument(
            "--golden", nargs=ONE_OR_MORE, choices=GOLDEN_FILES, default=[GoldenSource.QUESTIONS]
        )
        parser.add_argument(
            "--include-holdout", nargs=ONE_OR_MORE, choices=GOLDEN_FILES, default=[]
        )
        parser.add_argument("--items", nargs=ONE_OR_MORE, default=[])

    @classmethod
    async def _execute(cls, arguments: argparse.Namespace) -> RunData:
        settings = DriverFactory.settings_for(arguments.model, arguments.effort, arguments.env_file)
        driver = DriverFactory.create(settings)
        try:
            return await RunSession(driver, cls.request_of(arguments)).run()
        finally:
            await driver.close()


if __name__ == "__main__":
    sys.exit(RunCli.main(sys.argv[1:]))
