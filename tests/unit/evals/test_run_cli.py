from pathlib import Path

import pytest

from evals.golden.loader import GoldenLoader
from evals.run import RESULTS_DIRECTORY, RunCli
from evals.selection import RunPlan

BASELINE = (
    "--model gpt-6-luna --effort low --golden questions redteam protocol_actions "
    "--include-holdout protocol_actions --repeat 1 --critical-repeat 5 "
    "--output src/evals/results/baseline-trancamento"
)


def planned_by(command: str) -> int:
    request = RunCli.request_of(RunCli.parser().parse_args(command.split()))
    items = request.selection.pick(GoldenLoader.load())
    return len(RunPlan.of(items, request.repetitions))


def test_the_baseline_command_plans_146_executions() -> None:
    assert planned_by(BASELINE) == 146


def test_the_command_of_the_spec_runs_dev_questions_with_repetitions() -> None:
    assert planned_by("--model gpt-6-luna --effort low --split dev --repeat 3") == 41 * 3


def test_the_red_team_is_an_option() -> None:
    assert planned_by("--model fake --golden redteam") == 21


def test_the_output_defaults_to_the_results_directory() -> None:
    arguments = RunCli.parser().parse_args(["--model", "fake", "--effort", "low"])
    assert RunCli.request_of(arguments).output == RESULTS_DIRECTORY / "fake-low"
    assert Path("src/evals/results").resolve() == RESULTS_DIRECTORY


def test_an_unknown_golden_file_is_rejected() -> None:
    with pytest.raises(SystemExit):
        RunCli.parser().parse_args(["--model", "fake", "--golden", "outros"])
