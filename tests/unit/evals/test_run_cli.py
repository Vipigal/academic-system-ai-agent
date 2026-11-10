from pathlib import Path

import pytest

from evals.dataset.loader import DatasetLoader
from evals.run import RESULTS_DIRECTORY, RunCli
from evals.selection import RunPlan

DELIVERY_ROUND = (
    "--model gpt-6-luna --effort low --suite quality security protocol "
    "--output src/evals/results/rodada"
)
SCOPE_ROUND = "--model gpt-6-luna --suite scope --split dev test --epochs 3"


def planned_by(command: str) -> int:
    request = RunCli.request_of(RunCli.parser().parse_args(command.split()))
    items = request.selection.pick(DatasetLoader.load())
    return len(RunPlan.of(items, request.epochs))


def test_the_delivery_round_command_plans_155_executions() -> None:
    assert planned_by(DELIVERY_ROUND) == 155


def test_the_scope_round_plans_three_epochs_of_every_scope_item() -> None:
    assert planned_by(SCOPE_ROUND) == 41 * 3


def test_the_default_runs_the_dev_quality_items_with_the_epochs() -> None:
    assert planned_by("--model gpt-6-luna --effort low --epochs 3") == 40 * 3 + 5


def test_the_security_suite_is_an_option() -> None:
    assert planned_by("--model fake --suite security") == 21


def test_the_output_defaults_to_the_results_directory() -> None:
    arguments = RunCli.parser().parse_args(["--model", "fake", "--effort", "low"])
    assert RunCli.request_of(arguments).output == RESULTS_DIRECTORY / "fake-low"
    assert Path("src/evals/results").resolve() == RESULTS_DIRECTORY


def test_an_unknown_suite_is_rejected() -> None:
    with pytest.raises(SystemExit):
        RunCli.parser().parse_args(["--model", "fake", "--suite", "outros"])
