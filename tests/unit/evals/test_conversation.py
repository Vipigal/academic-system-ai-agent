import json
from pathlib import Path

from api.application.agent import events as agent_events
from api.application.agent.agent_errors import AgentTimeoutError
from api.application.agent.history import PastAssistantMessage, PastToolCall, PastUserMessage
from evals.dashboard.page import DashboardPage
from evals.graders.verdict import GraderName
from tests.unit.evals import agent_script
from tests.unit.evals import run_support as support
from tests.unit.evals.items_support import question

EARLIER = "Como fiquei na AV1?"
LATER = "Solicite trancamento de matricula de Direito Empresarial"
SEEN = "visto pelo modelo"
ANSWER = "Não existe trancamento de disciplina."
WITH_HISTORY = question(
    id="TR-13",
    pass_k=5,
    proposal="none",
    question=LATER,
    history=[EARLIER],
    tools={"expected": [], "forbidden": []},
)
WITHOUT_HISTORY = question(
    id="TR-01",
    pass_k=5,
    proposal="none",
    question=LATER,
    tools={"expected": [], "forbidden": []},
)


def grades_turn() -> tuple[agent_events.AgentEvent, ...]:
    complete = {"status": "ok", "client_only": {"token": agent_script.SIGNED_VALUE}}
    return (
        agent_events.ToolCallRequested("7", "list_grades", {"term": "2026/2"}),
        agent_events.ToolResultReceived("7", "list_grades", "ok", SEEN, complete, 4),
        *agent_script.answer_events("Sua AV1 foi 8."),
    )


def conversation(prior: tuple[agent_events.AgentEvent, ...]) -> agent_script.ConversationDriver:
    def script(asked: str) -> tuple[agent_events.AgentEvent, ...]:
        return prior if asked == EARLIER else agent_script.answer_events(ANSWER)

    return agent_script.ConversationDriver(agent_script.ScriptedAgent(script))


async def test_the_earlier_turn_is_run_and_delivered_as_past_to_the_final_one(
    tmp_path: Path,
) -> None:
    driver = conversation(grades_turn())
    await support.run_items(tmp_path, driver, [(WITH_HISTORY, 1)])

    asked = [message for message, _ in driver.agent.calls]
    assert asked == [EARLIER, LATER]
    assert driver.agent.calls[0][1] == ()
    call = PastToolCall("7", "list_grades", {"term": "2026/2"}, SEEN)
    assert driver.agent.calls[1][1] == (
        PastUserMessage(EARLIER),
        PastAssistantMessage("Sua AV1 foi 8.", (call,)),
    )


async def test_only_the_last_turn_reaches_the_execution(tmp_path: Path) -> None:
    driver = conversation(agent_script.proposal_events("ACA-010", "Preparei o pedido."))
    data = await support.run_items(tmp_path, driver, [(WITH_HISTORY, 1)])
    record = support.record_of(data, "TR-13#1")

    assert (record.steps, record.answer, record.error) == ((), ANSWER, None)
    assert (record.question, record.history) == (LATER, (EARLIER,))
    assert all(verdict.passed for verdict in record.verdicts)
    assert GraderName.PROPOSAL in {verdict.grader for verdict in record.verdicts}


async def test_tokens_add_up_every_turn_while_the_answer_is_the_last_one(tmp_path: Path) -> None:
    data = await support.run_items(tmp_path, conversation(grades_turn()), [(WITH_HISTORY, 1)])
    record = support.record_of(data, "TR-13#1")

    assert (record.tokens_in, record.tokens_out) == (2000, 400)
    assert record.cost_usd is not None


async def test_a_prior_turn_that_hits_the_limit_fails_the_execution(tmp_path: Path) -> None:
    limited = agent_script.answer_events("...", agent_events.StopReason.MODEL_CALL_LIMIT)
    driver = conversation(limited)
    data = await support.run_items(tmp_path, driver, [(WITH_HISTORY, 1)])
    record = support.record_of(data, "TR-13#1")

    assert record.error == "PriorTurnError"
    assert not record.passed
    assert [message for message, _ in driver.agent.calls] == [EARLIER]
    assert (record.tokens_in, record.tokens_out) == (1000, 200)


async def test_a_prior_turn_that_fails_fails_the_execution(tmp_path: Path) -> None:
    def script(asked: str) -> tuple[agent_events.AgentEvent, ...]:
        raise AgentTimeoutError(asked)

    driver = agent_script.ConversationDriver(agent_script.ScriptedAgent(script))
    data = await support.run_items(tmp_path, driver, [(WITH_HISTORY, 1)])

    assert support.record_of(data, "TR-13#1").error == "AgentTimeoutError"
    assert len(driver.agent.calls) == 1


async def test_without_history_the_agent_gets_only_the_question(tmp_path: Path) -> None:
    driver = conversation(grades_turn())
    data = await support.run_items(tmp_path, driver, [(WITHOUT_HISTORY, 1)])
    record = support.record_of(data, "TR-01#1")

    assert driver.agent.calls == [(LATER, ())]
    assert record.history == ()
    assert (record.tokens_in, record.tokens_out) == (1000, 200)


async def test_the_judge_request_carries_only_the_earlier_questions(tmp_path: Path) -> None:
    await support.run_items(tmp_path, conversation(grades_turn()), [(WITH_HISTORY, 1)])
    line = (tmp_path / "judge_requests.jsonl").read_text(encoding="utf-8").splitlines()[0]
    request = json.loads(line)

    assert request["history"] == [EARLIER]
    assert request["question"] == LATER
    assert "Sua AV1 foi 8." not in line
    assert "gpt-6-luna" not in line


async def test_the_dashboard_shows_the_context_without_client_only(tmp_path: Path) -> None:
    await support.run_items(tmp_path / "rodada", conversation(grades_turn()), [(WITH_HISTORY, 1)])
    page = DashboardPage.render(tmp_path)

    assert EARLIER in page
    assert "client_only" not in page
    assert agent_script.SIGNED_VALUE not in page
    assert "client_only" not in (tmp_path / "rodada" / "executions.jsonl").read_text(
        encoding="utf-8"
    )
