import argparse
import asyncio
import sys
from pathlib import Path

from evals.dashboard.page import DashboardPage
from evals.dataset.vocabulary import Split, Suite
from evals.driver_factory import DriverFactory
from evals.report.summary import RunSummary
from evals.run_data import RunData
from evals.run_manifest import RunConflictError
from evals.run_session import RunSession
from evals.selection import Epochs, ItemSelection, RunRequest, SelectionError

RESULTS_DIRECTORY = Path(__file__).parent / "results"
SUITES = [suite.value for suite in Suite]
SPLITS = [split.value for split in Split]
ONE_OR_MORE = "+"


class RunCli:
    @classmethod
    def parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="python -m evals.run")
        parser.add_argument("--model", required=True)
        parser.add_argument("--effort", default="low")
        parser.add_argument("--epochs", type=int, default=1)
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
                suites=frozenset(map(Suite, arguments.suite)),
                splits=frozenset(map(Split, arguments.split)),
                only=frozenset(arguments.items),
            ),
            epochs=Epochs(arguments.epochs),
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
        sys.stdout.write(RunSummary.render(data))
        DashboardPage.write()
        return data.result.exit_code

    @staticmethod
    def _selection_options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--suite", nargs=ONE_OR_MORE, choices=SUITES, default=[Suite.QUALITY])
        parser.add_argument("--split", nargs=ONE_OR_MORE, choices=SPLITS, default=[Split.DEV])
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
