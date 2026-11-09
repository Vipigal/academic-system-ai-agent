import pytest

from api.application.academic.service import AcademicService
from api.application.agent.tools import academic, finance, lms
from api.application.agent.tools.ui import ToolUi
from api.application.finance.service import FinancialService
from api.application.lms.service import LmsService
from api.application.shared.page import FIRST_PAGE
from api.application.shared.tool_result import ToolResult
from tests.unit.agent import agent_support as support
from tests.unit.agent.student_stubs import stub_service

SHOWN_TOOLS = [
    (
        finance.FinanceTools(stub_service(FinancialService)),
        "get_financial_summary",
        finance.SUMMARY_UI,
    ),
    (academic.AcademicTools(stub_service(AcademicService)), "get_curriculum", academic.PROGRESS_UI),
    (lms.LmsTools(stub_service(LmsService)), "list_online_exams", lms.EXAMS_UI),
]


@pytest.mark.parametrize(("group", "name", "ui"), SHOWN_TOOLS)
async def test_show_ui_adds_the_tool_phrase_and_keeps_the_data(
    group: object, name: str, ui: str
) -> None:
    tool = next(tool for tool in support.registered_of(group) if tool.definition.name == name)

    shown = (await tool.handler(show_ui=True)).model_dump(mode="json")
    hidden = (await tool.handler()).model_dump(mode="json")

    assert shown.pop("ui") == ui
    assert shown == hidden


def test_shown_fills_ui_and_keeps_the_data() -> None:
    result = ToolUi.shown(ToolResult.ok("resumo"), "Painel exibido ao aluno.")

    assert result.ui == "Painel exibido ao aluno."
    assert result.data == "resumo"


def test_shown_leaves_a_result_that_is_not_ok_without_ui() -> None:
    empty = ToolUi.shown(ToolResult.items(list[str]()), "Painel exibido ao aluno.")
    missed = ToolUi.shown(ToolResult[str].not_found(()), "Painel exibido ao aluno.")

    assert "ui" not in empty.model_dump(mode="json")
    assert "ui" not in missed.model_dump(mode="json")


async def test_the_model_reads_the_ui_phrase_when_it_asks_for_ui() -> None:
    request = support.call("get_financial_summary", {"show_ui": True})
    model = support.RecordingModel(responses=[request, support.answer()])

    run = await support.agent_with(model).run("Como está minha situação financeira?")

    result = support.tool_results(run.events)[0]
    assert result.complete["ui"] == finance.SUMMARY_UI
    assert finance.SUMMARY_UI in result.seen_by_model


async def test_a_call_without_show_ui_gets_no_ui_field() -> None:
    model = support.RecordingModel(
        responses=[support.call("get_financial_summary"), support.answer()]
    )

    run = await support.agent_with(model).run("Não consigo entrar no AVA. É por causa da dívida?")

    assert "ui" not in support.tool_results(run.events)[0].complete


async def test_the_model_nested_filters_reach_the_service_unpacked() -> None:
    service = stub_service(AcademicService)
    arguments = {"filters": {"semester": 3, "pending_only": True}, "show_ui": True}
    model = support.RecordingModel(
        responses=[support.call("get_curriculum", arguments), support.answer()]
    )

    tools = support.registered_of(academic.AcademicTools(service))
    run = await support.agent_with(model, tools).run("Quanto falta para eu me formar?")

    assert support.tool_results(run.events)[0].complete["ui"] == academic.PROGRESS_UI
    service.get_curriculum.assert_awaited_once_with(
        None, 3, None, pending_only=True, page=FIRST_PAGE
    )
