from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages.ai import UsageMetadata

from api.application.agent import events
from api.application.agent.history import PastAssistantMessage, PastToolCall, PastUserMessage
from api.application.agent.student_agent import StudentAgent
from api.application.agent.tools.finance import FinanceTools
from api.application.finance.service import FinancialService
from api.application.shared.tool_result import ToolResult
from tests.unit.agent import agent_support as support
from tests.unit.agent.student_stubs import STUB_DATA, stub_service


async def test_the_model_asks_a_tool_and_the_final_answer_comes_out() -> None:
    finance = stub_service(FinancialService)
    tools = support.registered_of(FinanceTools(finance))
    model = support.RecordingModel(
        responses=[support.call("get_financial_summary"), support.answer()]
    )

    run = await support.agent_with(model, tools).run("Quanto devo?")

    finance.get_financial_summary.assert_awaited_once_with()
    result = support.tool_results(run.events)[0]
    assert (result.tool_name, result.status) == ("get_financial_summary", "ok")
    assert (run.text, run.stop_reason) == (support.FINAL_ANSWER, events.StopReason.COMPLETED)


async def test_the_tool_result_comes_back_to_the_model_as_json() -> None:
    model = support.RecordingModel(
        responses=[support.call("get_financial_summary"), support.answer()]
    )

    run = await support.agent_with(model).run("Quanto devo?")

    tool_message = model.seen[1][-1]
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.content == ToolResult.ok(STUB_DATA).model_dump_json()
    assert support.tool_results(run.events)[0].seen_by_model == tool_message.content


async def test_validated_arguments_reach_the_handler_with_their_types() -> None:
    finance = stub_service(FinancialService)
    arguments = {"status": "overdue", "period": "2026-10", "page": {"limit": 5}}
    model = support.RecordingModel(
        responses=[support.call("list_invoices", arguments), support.answer()]
    )

    await support.agent_with(model, support.registered_of(FinanceTools(finance))).run("Faturas")

    received = finance.list_invoices.await_args.args
    assert (received[0].value, received[1], received[2]) == ("overdue", None, "2026-10")
    assert received[3].limit == 5


async def test_stream_emits_application_events_in_order() -> None:
    text = "Você deve R$ 10,00."
    model = support.RecordingModel(
        responses=[support.call("get_financial_summary"), support.answer(text)]
    )

    emitted = [event async for event in support.agent_with(model).stream("Quanto devo?")]

    assert isinstance(emitted[0], events.ToolCallRequested)
    assert isinstance(emitted[1], events.ToolResultReceived)
    assert emitted[1].tool_call_id == emitted[0].tool_call_id
    assert all(isinstance(delta, events.TextDelta) for delta in emitted[2:-1])
    assert emitted[-1] == events.AgentFinished(
        text, events.StopReason.COMPLETED, events.TokenUsage()
    )


async def test_the_answer_arrives_in_several_deltas() -> None:
    text = "Você deve R$ 10,00."
    model = support.RecordingModel(responses=[support.answer(text)])

    emitted = [event async for event in support.agent_with(model).stream("Quanto devo?")]

    deltas = [event.text for event in emitted if isinstance(event, events.TextDelta)]
    assert len(deltas) > 1
    assert "".join(deltas) == text


async def test_token_usage_adds_up_across_the_model_calls() -> None:
    usage = UsageMetadata(input_tokens=10, output_tokens=3, total_tokens=13)
    first = support.call("get_financial_summary")
    first.usage_metadata = usage
    last = support.answer()
    last.usage_metadata = usage

    run = await support.agent_with(support.RecordingModel(responses=[first, last])).run("Devo?")

    assert run.usage == events.TokenUsage(tokens_in=20, tokens_out=6)


async def test_the_system_prompt_goes_first_and_history_comes_before_the_message() -> None:
    model = support.RecordingModel(responses=[support.answer()])
    past_call = PastToolCall("old", "list_payments", {"year": 2026}, '{"status": "ok"}')
    history = (
        PastUserMessage("Oi"),
        PastAssistantMessage("Vou olhar", (past_call,)),
        PastAssistantMessage("Pagou tudo"),
    )

    await support.agent_with(model).run("E agora?", history)

    seen = model.seen[0]
    assert [type(message) for message in seen] == [
        SystemMessage,
        HumanMessage,
        AIMessage,
        ToolMessage,
        AIMessage,
        HumanMessage,
    ]
    assert seen[3].content == '{"status": "ok"}'
    assert seen[-1].content == "E agora?"


async def test_callbacks_of_the_request_see_the_model_call() -> None:
    class Spy(BaseCallbackHandler):
        def __init__(self) -> None:
            self.started = 0

        def on_chat_model_start(self, *_: object, **__: object) -> None:
            self.started += 1

    spy = Spy()
    runtime = support.runtime_with(support.RecordingModel(responses=[support.answer()]))

    await StudentAgent(runtime, (), "trace", (spy,)).run("Oi")

    assert spy.started == 1


async def test_parallel_tool_calls_in_one_message_each_get_their_result() -> None:
    parallel = AIMessage(
        content="",
        tool_calls=[
            *support.call("get_financial_summary", call_id="a").tool_calls,
            *support.call("list_agreements", call_id="b").tool_calls,
        ],
    )
    model = support.RecordingModel(responses=[parallel, support.answer()])

    run = await support.agent_with(model).run("Devo?")

    received = {item.tool_call_id: item.tool_name for item in support.tool_results(run.events)}
    assert received == {"a": "get_financial_summary", "b": "list_agreements"}
