from langchain_core.messages import ToolMessage

from api.application.agent.tools.protocol import ProtocolTools
from api.application.protocol.service import ProtocolService
from api.application.shared.tool_result import ToolResult
from tests.unit.agent import agent_support as support
from tests.unit.agent.student_stubs import stub_service

SIGNED = "assinatura-da-proposta"
PROPOSAL_ARGUMENTS = {"action": "declaracao_de_matricula", "enrollment": "UniSaoPaulo:181722"}


def signed_protocol_tools() -> ProtocolTools:
    service = stub_service(ProtocolService)
    proposal = ToolResult.ok("proposta")
    service.propose_protocol.return_value = proposal.with_client_only({"token": SIGNED})
    return ProtocolTools(service)


def script() -> support.RecordingModel:
    request = support.call("propose_protocol", PROPOSAL_ARGUMENTS)
    return support.RecordingModel(responses=[request, support.answer()])


async def test_client_only_stays_out_of_what_the_model_receives() -> None:
    model = script()

    run = await support.agent_with(model, support.registered_of(signed_protocol_tools())).run("Oi")

    assert SIGNED not in str([message.content for messages in model.seen for message in messages])
    assert SIGNED not in support.tool_results(run.events)[0].seen_by_model


async def test_client_only_reaches_the_stream_event() -> None:
    run = await support.agent_with(script(), support.registered_of(signed_protocol_tools())).run(
        "Oi"
    )

    complete = support.tool_results(run.events)[0].complete
    assert complete["client_only"] == {"token": SIGNED}
    assert complete["data"] == "proposta"


async def test_results_without_client_only_do_not_get_the_field() -> None:
    model = support.RecordingModel(
        responses=[support.call("get_financial_summary"), support.answer()]
    )

    run = await support.agent_with(model).run("Oi")

    assert "client_only" not in support.tool_results(run.events)[0].complete


async def test_client_only_stays_out_of_the_tool_message_dump_that_tracing_reads() -> None:
    model = script()

    await support.agent_with(model, support.registered_of(signed_protocol_tools())).run("Oi")

    tool_message = model.seen[1][-1]
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.artifact is not None
    assert SIGNED not in tool_message.model_dump_json()
    assert SIGNED not in str(tool_message.model_dump())
    assert SIGNED not in repr(tool_message)
