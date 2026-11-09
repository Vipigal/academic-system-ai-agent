from pathlib import Path

import pytest

from evals.driver_factory import DriverFactory
from evals.records import ExecutionRecord
from evals.run_files import JsonLines, RunFiles
from evals.run_manifest import RunConflictError
from evals.run_session import RunSession
from evals.selection import GoldenSource, ItemSelection, Repetitions, RunRequest
from tests.integration.evals.run_helpers import SELECTION, fake_settings

ACTIONS = frozenset({GoldenSource.PROTOCOL_ACTIONS})


async def test_a_resumed_run_executes_only_what_is_missing(tmp_path: Path) -> None:
    driver = DriverFactory.create(fake_settings())
    request = RunRequest(SELECTION, Repetitions(), tmp_path)
    await RunSession(driver, request).run()
    executions = RunFiles(tmp_path).executions
    first_run = executions.read_text(encoding="utf-8").splitlines()
    executions.write_text(f"{first_run[0]}\n", encoding="utf-8")

    await RunSession(driver, request).run()
    await driver.close()

    lines = JsonLines.read(executions, ExecutionRecord)
    assert lines[0].model_dump_json() == first_run[0]
    assert {line.key for line in lines} == {"FI-01#1", "TR-01#1"}
    assert len(lines) == 2


async def test_a_run_refuses_a_directory_of_another_configuration(tmp_path: Path) -> None:
    driver = DriverFactory.create(fake_settings())
    request = RunRequest(SELECTION, Repetitions(), tmp_path)
    await RunSession(driver, request).run()
    other_settings = fake_settings().model_copy(update={"agent_effort": "medium"})
    other = DriverFactory.create(other_settings)

    with pytest.raises(RunConflictError):
        await RunSession(other, request).run()
    await driver.close()
    await other.close()


async def test_two_selections_of_the_same_size_do_not_mix_in_a_directory(tmp_path: Path) -> None:
    driver = DriverFactory.create(fake_settings())
    first = ItemSelection(ACTIONS, only=frozenset({"TR-01"}))
    other = ItemSelection(ACTIONS, only=frozenset({"TR-02"}))
    await RunSession(driver, RunRequest(first, Repetitions(), tmp_path)).run()

    with pytest.raises(RunConflictError):
        await RunSession(driver, RunRequest(other, Repetitions(), tmp_path)).run()
    await driver.close()


async def test_a_run_refuses_a_directory_of_another_composition(tmp_path: Path) -> None:
    driver = DriverFactory.create(fake_settings())
    await RunSession(driver, RunRequest(SELECTION, Repetitions(), tmp_path)).run()
    larger = RunRequest(SELECTION, Repetitions(default=2), tmp_path)

    with pytest.raises(RunConflictError):
        await RunSession(driver, larger).run()
    await driver.close()
