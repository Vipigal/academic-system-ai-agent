import json
from pathlib import Path

import pytest

from api.infrastructure.tracing import Tracing
from evals.dataset.oracle_settings import OracleSettings
from evals.run_session import RunSession
from evals.selection import Epochs, RunRequest
from evals.student_driver import StudentDriver
from tests.integration.chat.span_sink import SpanSink
from tests.integration.evals.eval_containers import evaluation_container
from tests.integration.evals.run_helpers import (
    SELECTION,
    VERSIONS,
    fake_settings,
)

TRACE_ID_LENGTH = 32


def assert_files_of_the_round(directory: Path) -> None:
    assert (directory / "executions.jsonl").exists()
    manifest = json.loads((directory / "run.json").read_text(encoding="utf-8"))
    assert (manifest["versions"]["model"], len(manifest["commit"])) == ("fake", 40)
    assert manifest["trace_url_prefix"] is None


async def test_the_fake_model_produces_a_report_against_the_real_database(
    tmp_path: Path, tracing: Tracing, sink: SpanSink
) -> None:
    doubles = {Tracing: tracing}
    driver = StudentDriver(evaluation_container(doubles, fake_settings()), VERSIONS)
    request = RunRequest(SELECTION, Epochs(), tmp_path)

    data = await RunSession(driver, request).run()
    await driver.close()

    assert {record.key for record in data.records} == {"FI-01#1", "SV-01#1"}
    assert all(record.steps[0].name == "get_financial_summary" for record in data.records)
    assert all(len(record.trace_id or "") == TRACE_ID_LENGTH for record in data.records)
    assert_files_of_the_round(tmp_path)
    for sent in (b"eval.execution", b"\n\x04eval", b"tools:t"):
        assert sent in sink.received


async def test_without_langfuse_keys_the_trace_id_is_null(tmp_path: Path) -> None:
    tracing = Tracing(None, None, None, None)
    doubles = {Tracing: tracing}
    container = evaluation_container(doubles, fake_settings())
    driver = StudentDriver(container, VERSIONS)

    data = await RunSession(driver, RunRequest(SELECTION, Epochs(), tmp_path)).run()
    await driver.close()

    assert {record.trace_id for record in data.records} == {None}


async def test_the_round_reads_the_oracle_url_from_the_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / "falso.env"
    oracle_url = OracleSettings.from_environment().oracle_database_url.get_secret_value()
    env_file.write_text(f"APP_ORACLE_DATABASE_URL={oracle_url}\n", encoding="utf-8")
    monkeypatch.delenv("APP_ORACLE_DATABASE_URL")
    driver = StudentDriver(
        evaluation_container(
            {Tracing: Tracing(None, None, None, None)},
            fake_settings(),
        ),
        VERSIONS,
    )
    request = RunRequest(SELECTION, Epochs(), tmp_path / "rodada", env_file=env_file)

    data = await RunSession(driver, request).run()
    await driver.close()

    assert {record.key for record in data.records} == {"FI-01#1", "SV-01#1"}
