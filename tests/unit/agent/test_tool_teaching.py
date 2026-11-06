import pytest
from langchain_core.messages import BaseMessage

from api.application.agent.skill_library import SkillLibrary
from api.application.agent.tool_arguments import GUIDES, ParameterGuide
from api.application.agent.tool_schema import ToolSchema
from api.application.agent.tools.registry import RegisteredTool, ToolRegistry
from api.application.agent.tools.skill_tools import SkillTools
from tests.unit.agent import agent_support as support
from tests.unit.agent.student_stubs import stub_student

WRONG_VALUES: dict[str, tuple[object, ...]] = {
    "term": ("2026-2", 2026),
    "course": (123,),
    "modality": ("remoto", 1),
    "unit": (7,),
    "area": ("biologia", 1),
    "enrollment": ("013161", 13161),
    "semester": ("terceiro",),
    "subject": (5,),
    "pending_only": ("talvez",),
    "page": (2, {"limit": 0}, {"limit": 101}, {"limit": "muitos"}, {"offset": -1}, {"foo": 1}),
    "status": ("pago", 3),
    "kind": ("boleto",),
    "period": ("2026-1", "out/2026", 2026),
    "year": ("dois mil",),
    "service": (9,),
    "number": (20260024630,),
    "message": (1,),
    "query": (1,),
}
REQUIRED: dict[str, dict[str, object]] = {
    "list_subject_professors": {"subject": "ADM0104"},
    "get_protocol": {"number": "20260024630"},
    "propose_protocol": {"service": "DOC-001", "message": "Preciso de uma declaração."},
    "list_material_views": {"subject": "ADM0104"},
    "load_skill": {"area": "finance"},
}
RAW_VALIDATOR_TEXTS = ("Input should", "validation error", "pydantic", "Field required", "type=")


def all_tools() -> tuple[RegisteredTool, ...]:
    return (*stub_student().registry().tools, *ToolRegistry(SkillTools(SkillLibrary.load())).tools)


def wrong_calls() -> list[tuple[str, str, object]]:
    cases: list[tuple[str, str, object]] = []
    for tool in all_tools():
        for parameter in ToolSchema.of(tool.handler).guides:
            cases.extend(
                (tool.definition.name, parameter, value) for value in WRONG_VALUES[parameter]
            )
    return cases


def leaf_of(parameter: str, value: object) -> tuple[str, str]:
    if isinstance(value, dict):
        key = next(iter(value))
        return f"{parameter}.{key}", key
    return parameter, parameter


def guide_of(tool_name: str, leaf: str) -> ParameterGuide:
    schemas = {tool.definition.name: ToolSchema.of(tool.handler) for tool in all_tools()}
    return schemas[tool_name].guides.get(leaf) or GUIDES[leaf]


async def teach_and_correct(tool_name: str, wrong: dict[str, object]) -> str:
    valid = REQUIRED.get(tool_name, {})
    responses: list[BaseMessage] = [
        support.call(tool_name, wrong, call_id="errada"),
        support.call(tool_name, valid, call_id="certa"),
        support.answer(),
    ]

    run = await support.agent_with(support.RecordingModel(responses=responses)).run("Pergunta")

    results = support.tool_results(run.events)
    assert [item.status for item in results] == ["invalid", "ok"]
    assert run.text == support.FINAL_ANSWER
    explanation = str(results[0].complete["explanation"])
    assert tool_name in explanation
    assert not [raw for raw in RAW_VALIDATOR_TEXTS if raw in explanation]
    return explanation


def test_the_teaching_covers_the_twenty_tools() -> None:
    assert len(all_tools()) == 20
    covered = {name for name, _, _ in wrong_calls()}
    without_parameters = {
        tool.definition.name for tool in all_tools() if not ToolSchema.of(tool.handler).guides
    }
    assert covered | without_parameters == {tool.definition.name for tool in all_tools()}


@pytest.mark.parametrize(("tool_name", "parameter", "value"), wrong_calls())
async def test_each_wrong_parameter_teaches_and_the_model_corrects_itself(
    tool_name: str, parameter: str, value: object
) -> None:
    arguments = {**REQUIRED.get(tool_name, {}), parameter: value}

    explanation = await teach_and_correct(tool_name, arguments)

    path, leaf = leaf_of(parameter, value)
    assert f"`{path}`" in explanation
    if leaf == "foo":
        assert "não existe" in explanation
    else:
        guide = guide_of(tool_name, leaf)
        assert guide.accepted in explanation
        assert guide.example in explanation


@pytest.mark.parametrize("tool_name", [tool.definition.name for tool in all_tools()])
async def test_an_unknown_parameter_teaches_in_every_tool(tool_name: str) -> None:
    arguments = {**REQUIRED.get(tool_name, {}), "person_id": "alguem"}

    explanation = await teach_and_correct(tool_name, arguments)

    assert "`person_id`" in explanation
    assert "não existe" in explanation


@pytest.mark.parametrize("tool_name", sorted(REQUIRED))
async def test_a_missing_required_parameter_teaches(tool_name: str) -> None:
    explanation = await teach_and_correct(tool_name, {})

    for parameter in REQUIRED[tool_name]:
        assert f"`{parameter}`" in explanation
    assert "obrigatório" in explanation


async def test_a_parameter_of_a_tool_without_parameters_shows_the_valid_call() -> None:
    explanation = await teach_and_correct("get_financial_summary", {"limit": 3})

    assert "não recebe parâmetros" in explanation
    assert "{}" in explanation


async def test_several_wrong_parameters_get_one_sentence_each() -> None:
    explanation = await teach_and_correct("list_invoices", {"status": "pago", "period": "x"})

    assert "`status`" in explanation
    assert "paid" in explanation
    assert "`period`" in explanation
    assert "2026-10" in explanation


async def test_enum_values_come_from_the_type() -> None:
    explanation = await teach_and_correct("list_protocols", {"status": "aberto"})

    for value in ("in_progress", "resolved", "cancelled"):
        assert value in explanation


async def test_a_huge_input_is_not_echoed_whole() -> None:
    explanation = await teach_and_correct("list_invoices", {"period": "x" * 5000})

    assert "x" * 81 not in explanation
