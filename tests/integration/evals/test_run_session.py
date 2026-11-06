import json
from pathlib import Path

from api.bootstrap.singletons import Singletons
from api.infrastructure.tracing import Tracing
from evals.run_session import RunSession
from evals.selection import Repetitions, RunRequest
from evals.student_driver import StudentDriver
from tests.integration.chat.span_sink import SpanSink
from tests.integration.evals.run_helpers import SELECTION, VERSIONS, fake_settings

TRACE_ID_LENGTH = 32


def assert_files_of_the_round(directory: Path) -> None:
    assert "Rodada" in (directory / "report.md").read_text(encoding="utf-8")
    assert "Rodada" in (directory / "report.html").read_text(encoding="utf-8")
    manifest = json.loads((directory / "run.json").read_text(encoding="utf-8"))
    assert (manifest["versions"]["model"], len(manifest["commit"])) == ("fake", 40)
    assert manifest["trace_url_prefix"] is None


async def test_the_fake_model_produces_a_report_against_the_real_database(
    tmp_path: Path, tracing: Tracing, sink: SpanSink
) -> None:
    driver = StudentDriver(Singletons.create(fake_settings()), tracing, VERSIONS)
    request = RunRequest(SELECTION, Repetitions(default=1, critical=2), tmp_path)

    data = await RunSession(driver, request).run()
    await driver.close()

    assert {record.key for record in data.records} == {"FI-01#1", "TR-01#1", "TR-01#2"}
    assert all(record.steps[0].name == "get_financial_summary" for record in data.records)
    assert all(len(record.trace_id or "") == TRACE_ID_LENGTH for record in data.records)
    assert_files_of_the_round(tmp_path)
    for sent in (b"eval.execution", b"\n\x04eval", b"tools:t"):
        assert sent in sink.received


async def test_without_langfuse_keys_the_trace_id_is_null(tmp_path: Path) -> None:
    tracing = Tracing(None, None, None, None)
    driver = StudentDriver(Singletons.create(fake_settings()), tracing, VERSIONS)

    data = await RunSession(driver, RunRequest(SELECTION, Repetitions(), tmp_path)).run()
    await driver.close()

    assert {record.trace_id for record in data.records} == {None}
