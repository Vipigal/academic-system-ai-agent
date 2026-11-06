import logging
from unittest.mock import MagicMock

import pytest

from api.application.agent.events import ToolResultReceived
from api.application.agent.langchain_tools import UNEXPECTED_FAILURE
from api.application.agent.tools.registry import ToolRegistry
from api.application.shared.tool_input_error import ToolInputError
from api.application.shared.tool_result import ToolResult
from api.domain.ontology.finance_charges import DIVIDA
from tests.unit.agent import agent_support as support


class ExplodingTools:
    def __init__(self, error: Exception) -> None:
        self._error = error

    @support.described("Sempre falha.")
    @ToolRegistry.declares(DIVIDA)
    async def explode(self) -> ToolResult[str]:
        raise self._error


class WrongReturnTools:
    @support.described("Devolve outra coisa em tempo de execução.")
    @ToolRegistry.declares(DIVIDA)
    async def misbehave(self) -> ToolResult[str]:
        return MagicMock()


async def run_explosion(error: Exception) -> tuple[ToolResultReceived, str]:
    tools = support.registered_of(ExplodingTools(error))
    model = support.RecordingModel(responses=[support.call("explode"), support.answer()])
    run = await support.agent_with(model, tools).run("Teste")
    return support.tool_results(run.events)[0], run.text


async def test_an_unexpected_failure_becomes_a_generic_error_and_the_turn_ends() -> None:
    result, text = await run_explosion(RuntimeError("SELECT cpf FROM segredo"))

    assert result.status == "error"
    assert result.complete["explanation"] == UNEXPECTED_FAILURE
    assert "segredo" not in result.seen_by_model
    assert "RuntimeError" not in result.seen_by_model
    assert text == support.FINAL_ANSWER


async def test_an_unexpected_failure_is_logged_with_the_trace_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.ERROR):
        await run_explosion(RuntimeError("falhou"))

    record = next(item for item in caplog.records if item.name.endswith("langchain_tools"))
    assert getattr(record, "trace_id", None) == "trace-teste"
    assert getattr(record, "tool", None) == "explode"


async def test_an_expected_tool_error_returns_its_own_paragraph() -> None:
    paragraph = "O período precisa ser AAAA-MM. Exemplo: 2026-10."

    result, text = await run_explosion(ToolInputError(paragraph))

    assert result.status == "invalid"
    assert result.complete["explanation"] == paragraph
    assert text == support.FINAL_ANSWER


async def test_a_handler_that_breaks_the_contract_does_not_end_the_turn() -> None:
    tools = support.registered_of(WrongReturnTools())
    model = support.RecordingModel(responses=[support.call("misbehave"), support.answer()])

    run = await support.agent_with(model, tools).run("Teste")

    result = support.tool_results(run.events)[0]
    assert UNEXPECTED_FAILURE in result.seen_by_model
    assert run.text == support.FINAL_ANSWER


@pytest.mark.parametrize("reserved", ["config", "run_manager", "self"])
async def test_an_argument_that_collides_with_the_framework_does_not_end_the_turn(
    reserved: str,
) -> None:
    call = support.call("get_financial_summary", {reserved: 1})
    model = support.RecordingModel(responses=[call, support.answer()])

    run = await support.agent_with(model).run("Teste")

    assert len(support.tool_results(run.events)) == 1
    assert run.text == support.FINAL_ANSWER


async def test_a_tool_that_does_not_exist_is_reported_to_the_model() -> None:
    model = support.RecordingModel(responses=[support.call("delete_everything"), support.answer()])

    run = await support.agent_with(model).run("Teste")

    assert support.tool_results(run.events)[0].status == "invalid"
    assert run.text == support.FINAL_ANSWER
