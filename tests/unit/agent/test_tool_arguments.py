import json
from typing import Annotated

import pytest
from langchain_core.utils.function_calling import convert_to_openai_tool

from api.application.agent.langchain_tools import LangchainTools
from api.application.agent.tool_arguments import (
    FIRST_PAGE_ARGUMENT,
    BoundedPage,
    PageArgument,
    ToolArguments,
)
from api.application.agent.tools.registry import ToolContractError
from api.application.shared.tool_parameters import Teaching
from api.application.shared.tool_result import ToolResult
from tests.unit.agent import agent_support as support

NOTE_TEACHING = Teaching("um recado curto, em texto", "recado-de-exemplo")


class TaughtTools:
    @support.described("Recebe um recado e uma página.")
    async def taught(
        self, note: Annotated[str, NOTE_TEACHING], page: PageArgument = FIRST_PAGE_ARGUMENT
    ) -> ToolResult[str]:
        return ToolResult.ok(f"{note}:{page.limit}")


class UntaughtTools:
    @support.described("Recebe um recado sem texto de ensino.")
    async def untaught(self, note: str) -> ToolResult[str]:
        return ToolResult.ok(note)


def test_the_teaching_is_read_from_the_signature() -> None:
    arguments = ToolArguments.model_of(TaughtTools().taught)

    assert ToolArguments.teaching_at(arguments, ("note",)) == NOTE_TEACHING


def test_the_teaching_stays_out_of_the_schema_the_model_sees() -> None:
    tool = support.registered_of(TaughtTools())[0]

    shown = json.dumps(
        convert_to_openai_tool(LangchainTools("t").convert(tool)), ensure_ascii=False
    )

    assert NOTE_TEACHING.accepted not in shown
    assert NOTE_TEACHING.example not in shown


def test_a_parameter_without_teaching_is_refused_at_conversion() -> None:
    tool = support.registered_of(UntaughtTools())[0]

    with pytest.raises(ToolContractError, match="note"):
        LangchainTools("t").convert(tool)


def test_a_page_request_reaches_the_model_bounded_and_taught() -> None:
    arguments = ToolArguments.model_of(TaughtTools().taught)

    limit = ToolArguments.teaching_at(arguments, ("page", "limit"))

    assert arguments.model_fields["page"].annotation is BoundedPage
    assert limit.accepted == "um inteiro de 1 a 100"


def test_the_model_is_inferred_once_per_function_never_per_student() -> None:
    first, second = TaughtTools(), TaughtTools()

    assert first.taught != second.taught
    assert ToolArguments.model_of(first.taught) is ToolArguments.model_of(second.taught)
