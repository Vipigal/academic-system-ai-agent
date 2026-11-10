import inspect

from langchain_core.utils.function_calling import convert_to_openai_tool

from api.application.agent.langchain_tools import LangchainTools
from api.application.agent.tools.finance import FinanceTools
from api.application.agent.tools.registry import RegisteredTool
from api.application.finance.service import FinancialService
from api.domain.protocol.action import ProtocolAction
from tests.unit.agent.agent_support import registered_of
from tests.unit.agent.student_stubs import stub_service, stub_student

DESCRIBED_ARGUMENTS = {"propose_protocol": {"action", "enrollment", "subject"}}


def test_name_and_description_come_from_the_definition() -> None:
    tool = registered_of(FinanceTools(stub_service(FinancialService)))[0]

    converted = LangchainTools("trace").convert(tool)

    assert converted.name == tool.definition.name
    assert converted.description == tool.definition.description


def test_the_visible_schema_has_the_signature_parameters_and_no_identity() -> None:
    for tool in stub_student().registry().tools:
        function = convert_to_openai_tool(LangchainTools("trace").convert(tool))["function"]
        properties = set(function["parameters"].get("properties", {}))
        assert properties == set(inspect.signature(tool.handler).parameters)
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


def test_the_proposal_schema_describes_each_argument_and_requires_the_enrollment() -> None:
    tools = {tool.definition.name: tool for tool in stub_student().registry().tools}

    function = convert_to_openai_tool(LangchainTools("t").convert(tools["propose_protocol"]))

    parameters = function["function"]["parameters"]
    properties = parameters["properties"]
    assert set(properties) == {"action", "enrollment", "subject"}
    assert set(parameters["required"]) == {"action", "enrollment"}
    assert set(properties["action"]["enum"]) == {item.value for item in ProtocolAction}
    assert all(properties[name]["description"] for name in properties)
    assert "$defs" not in parameters


def described_arguments(tool: RegisteredTool) -> set[str]:
    function = convert_to_openai_tool(LangchainTools("t").convert(tool))["function"]
    properties = function["parameters"].get("properties", {})
    return {name for name, field in properties.items() if "description" in field}


def test_only_the_tools_with_a_described_argument_get_a_description() -> None:
    for tool in stub_student().registry().tools:
        assert described_arguments(tool) == set(DESCRIBED_ARGUMENTS.get(tool.definition.name, {}))


def test_converting_twice_gives_the_same_schema() -> None:
    tool = stub_student().registry().tools[0]

    first = convert_to_openai_tool(LangchainTools("a").convert(tool))
    second = convert_to_openai_tool(LangchainTools("b").convert(tool))

    assert first == second
