import json
from http import HTTPStatus

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from tests.e2e.e2e_settings import e2e_settings
from tests.e2e.running_api import running_api
from tests.e2e.student_flow import (
    LIST_TOOL,
    PROPOSE_TOOL,
    FlowResult,
    StudentFlow,
    outputs_text,
    tools_called,
)
from tests.e2e.turn_model import TurnModel
from tests.integration.chat.chat_client import ChatClient
from tests.integration.protocol.rolled_back import RolledBackBank
from tests.unit.agent.agent_support import call

PROPOSAL_TEXT = "Quero abrir um pedido."
LISTING_TEXT = "Quais são os meus protocolos?"
PROPOSED = "Preparei o pedido para você confirmar."
LISTED = "Aqui estão os seus protocolos."
PROPOSAL_ARGUMENTS = {"action": "informacoes_gerais", "enrollment": "UniSaoPaulo:180017"}


def scripted() -> TurnModel:
    return TurnModel(
        responses=[],
        turns=[
            [call(PROPOSE_TOOL, PROPOSAL_ARGUMENTS), AIMessage(PROPOSED)],
            [call(LIST_TOOL), AIMessage(LISTED)],
        ],
    )


async def whole_flow(
    bank: RolledBackBank, model: TurnModel | None = None
) -> tuple[FlowResult, str]:
    with running_api(bank, e2e_settings(), model or scripted()) as api:
        result = await StudentFlow(api.client, PROPOSAL_TEXT, LISTING_TEXT).run()
        return result, api.log.getvalue()


async def test_login_chat_proposal_confirmation_and_listing_over_http(bank: RolledBackBank) -> None:
    result, _ = await whole_flow(bank)

    assert tools_called(result.proposal) == [PROPOSE_TOOL]
    assert result.confirmation.status_code == HTTPStatus.CREATED
    assert tools_called(result.listing) == [LIST_TOOL]
    assert result.number in outputs_text(result.listing)


async def test_the_proposal_token_comes_in_the_stream_for_the_client(
    bank: RolledBackBank,
) -> None:
    result, _ = await whole_flow(bank)

    assert "client_only" in outputs_text(result.proposal)
    assert result.confirmation.json()["status"]


async def test_the_next_turn_sees_the_confirmation_event_before_the_new_question(
    bank: RolledBackBank,
) -> None:
    model = scripted()
    result, _ = await whole_flow(bank, model)

    next_turn = model.seen[-2]
    event, question = next_turn[-2:]
    assert (type(event), type(question)) == (SystemMessage, HumanMessage)
    assert result.number in event.text
    assert question.text == LISTING_TEXT
    assert [type(message) for message in model.seen[0]] == [SystemMessage, HumanMessage]


async def chat_log_entries(bank: RolledBackBank) -> list[dict[str, str]]:
    with running_api(bank, e2e_settings(), scripted()) as api:
        chat = await ChatClient.logged_in(api.client)
        conversation = await chat.create_conversation()
        api.log.truncate(0)
        api.log.seek(0)
        await chat.send(conversation, PROPOSAL_TEXT)
        entries = [json.loads(line) for line in api.log.getvalue().splitlines()]
        return [entry for entry in entries if entry["logger"].startswith("api.")]


async def test_a_chat_request_logs_one_request_id_and_one_trace_id(bank: RolledBackBank) -> None:
    lines = await chat_log_entries(bank)

    request_ids = {entry["request_id"] for entry in lines}
    trace_ids = {entry["trace_id"] for entry in lines}
    assert {entry["logger"] for entry in lines} >= {
        "api.bootstrap.request_log",
        "api.application.chat.recorded_turn",
    }
    assert len(request_ids) == 1
    assert len(trace_ids) == 1
    assert all(request_ids | trace_ids)
    assert "POST /chat 200" in lines[-1]["message"]


async def test_the_end_of_a_turn_is_logged_without_the_conversation_text(
    bank: RolledBackBank,
) -> None:
    lines = await chat_log_entries(bank)

    finished = [entry["message"] for entry in lines if entry["logger"].endswith("recorded_turn")]
    written = json.dumps(lines)
    assert len(finished) == 1
    assert all(part in finished[0] for part in ("modelo-de-teste", "latency_ms", "completed"))
    assert PROPOSAL_TEXT not in written
    assert PROPOSED not in written


async def test_without_langfuse_a_request_emits_no_langfuse_warning(bank: RolledBackBank) -> None:
    result, written = await whole_flow(bank)

    assert result.confirmation.status_code == HTTPStatus.CREATED
    assert "langfuse" not in {json.loads(line)["logger"] for line in written.splitlines()}
