from types import FunctionType

from langchain_core.utils.function_calling import convert_to_openai_tool

from api.application.agent.langchain_tools import LangchainTools
from api.application.agent.tool_schema import SCHEMAS, ToolSchema
from api.application.agent.tools.finance import FinanceTools
from api.application.finance.service import FinancialService
from tests.unit.agent.agent_support import registered_of
from tests.unit.agent.student_stubs import stub_service, stub_student


def test_name_and_description_come_from_the_definition() -> None:
    tool = registered_of(FinanceTools(stub_service(FinancialService)))[0]

    converted = LangchainTools("trace").convert(tool)

    assert converted.name == tool.definition.name
    assert converted.description == tool.definition.description


def test_the_visible_schema_has_the_signature_parameters_and_no_identity() -> None:
    for tool in stub_student().registry().tools:
        function = convert_to_openai_tool(LangchainTools("trace").convert(tool))["function"]
        properties = set(function["parameters"].get("properties", {}))
        assert properties == set(ToolSchema.of(tool.handler).guides)
        assert not {"person_id", "cpf", "student_id"} & properties


def test_the_visible_schema_shows_enums_ranges_and_formats_without_references() -> None:
    tools = {tool.definition.name: tool for tool in stub_student().registry().tools}

    function = convert_to_openai_tool(LangchainTools("t").convert(tools["list_invoices"]))

    parameters = function["function"]["parameters"]
    properties = parameters["properties"]
    assert properties["page"]["properties"]["limit"]["maximum"] == 100
    assert {"paid", "overdue"} <= set(properties["status"]["anyOf"][0]["enum"])
    assert properties["period"]["anyOf"][0]["pattern"]
    assert "$defs" not in parameters


def test_the_curriculum_filters_are_one_nested_object_without_references() -> None:
    tools = {tool.definition.name: tool for tool in stub_student().registry().tools}

    function = convert_to_openai_tool(LangchainTools("t").convert(tools["get_curriculum"]))

    parameters = function["function"]["parameters"]
    filters = parameters["properties"]["filters"]
    assert set(parameters["properties"]) == {"enrollment", "filters", "page", "show_ui"}
    assert set(filters["properties"]) == {"semester", "subject", "pending_only"}
    assert filters["additionalProperties"] is False
    assert "$defs" not in parameters


def test_converting_twice_does_not_change_the_cached_schema() -> None:
    tool = stub_student().registry().tools[0]

    first = convert_to_openai_tool(LangchainTools("a").convert(tool))
    second = convert_to_openai_tool(LangchainTools("b").convert(tool))

    assert first == second


def test_the_schema_is_cached_by_function_never_by_bound_method() -> None:
    first = stub_student().registry().tools
    second = stub_student().registry().tools

    for left, right in zip(first, second, strict=True):
        assert left.handler != right.handler
        assert ToolSchema.of(left.handler) is ToolSchema.of(right.handler)
    assert SCHEMAS
    assert all(isinstance(key, FunctionType) for key in SCHEMAS)
