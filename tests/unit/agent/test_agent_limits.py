import asyncio

import pytest

from api.application.agent.agent_errors import AgentTimeoutError
from api.application.agent.agent_stream import NO_ANSWER_TEXT
from api.application.agent.events import StopReason, TextDelta
from api.application.agent.tools import finance as finance_tools
from api.application.finance.service import FinancialService
from api.application.shared.tool_result import ToolResult
from tests.unit.agent import agent_support as support
from tests.unit.agent.student_stubs import stub_service


class SlowTools:
    @support.described("Nunca termina a tempo.")
    async def wait_forever(self) -> ToolResult[str]:
        await asyncio.sleep(5)
        return ToolResult.ok("tarde")


async def test_the_model_call_limit_ends_with_a_text_for_the_student() -> None:
    model = support.RecordingModel(responses=[support.call("get_financial_summary")])

    run = await support.agent_with(model, limits=support.limits_with(model_calls=2)).run("Teste")

    assert len(model.seen) == 2
    assert (run.stop_reason, run.text) == (StopReason.MODEL_CALL_LIMIT, NO_ANSWER_TEXT)
    assert isinstance(run.events[-2], TextDelta)


async def test_an_empty_final_message_still_gives_the_student_a_text() -> None:
    model = support.RecordingModel(responses=[support.answer("")])

    run = await support.agent_with(model).run("Teste")

    assert (run.stop_reason, run.text) == (StopReason.COMPLETED, NO_ANSWER_TEXT)


async def test_the_tool_call_limit_blocks_the_extra_call_and_the_model_answers() -> None:
    finance = stub_service(FinancialService)
    run = await support.agent_with(
        support.RecordingModel(
            responses=[
                support.call("get_financial_summary", call_id="c1"),
                support.call("get_financial_summary", call_id="c2"),
                support.answer(),
            ]
        ),
        support.registered_of(finance_tools.FinanceTools(finance)),
        support.limits_with(tool_calls=1),
    ).run("Teste")

    finance.get_financial_summary.assert_awaited_once()
    assert [item.status for item in support.tool_results(run.events)] == ["ok", "invalid"]
    assert run.text == support.FINAL_ANSWER


async def test_the_timeout_covers_the_whole_execution() -> None:
    model = support.RecordingModel(responses=[support.call("wait_forever"), support.answer()])
    agent = support.agent_with(
        model, support.registered_of(SlowTools()), support.limits_with(timeout_seconds=0.05)
    )

    with pytest.raises(AgentTimeoutError):
        await agent.run("Teste")
