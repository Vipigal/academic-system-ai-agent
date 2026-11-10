from pathlib import Path

from api.infrastructure.tracing import Tracing
from api.persistence.core.database import Database
from evals.graders.verdict import GraderName
from evals.records import ExecutionRecord
from evals.run_session import RunSession
from evals.selection import Epochs, ItemSelection, RunRequest
from evals.student_driver import StudentDriver
from tests.doubles.scripted_model import ScriptedChatModel
from tests.integration.evals.run_helpers import PROTOCOL_SUITE, VERSIONS, scripted_container
from tests.unit.agent.agent_support import answer, call

SELECTION = ItemSelection(PROTOCOL_SUITE, only=frozenset({"TR-07"}))
SCRIPTED_MODEL = ScriptedChatModel(
    responses=[
        call(
            "propose_protocol",
            {"action": "trancar_curso_inteiro", "enrollment": "UniSaoPaulo:181722"},
        ),
        answer("Preparei o pedido."),
    ]
)


def failed_checks(record: ExecutionRecord) -> dict[GraderName, tuple[str, ...]]:
    return {check.grader: check.problems for check in record.verdicts if not check.passed}


def assert_without_client_only(content: str) -> None:
    assert "client_only" not in content
    assert "eyJ" not in content
    assert "Tem certeza" not in content


async def test_a_real_proposal_passes_the_guardrail_and_keeps_client_only_out(
    tmp_path: Path, database: Database, tracing: Tracing
) -> None:
    driver = StudentDriver(scripted_container(database, SCRIPTED_MODEL, tracing), VERSIONS)
    request = RunRequest(SELECTION, Epochs(), tmp_path)

    data = await RunSession(driver, request).run()

    assert failed_checks(data.records[0]) == {}
    for name in ("executions.jsonl", "judge_requests.jsonl"):
        assert_without_client_only((tmp_path / name).read_text(encoding="utf-8"))
