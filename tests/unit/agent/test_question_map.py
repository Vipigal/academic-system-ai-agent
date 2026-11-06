import re
from pathlib import Path
from typing import get_type_hints

from api.application.agent.student_tools import StudentTools
from api.application.agent.tools.registry import ToolDefinition, ToolRegistry
from api.domain.ontology.catalog import ONTOLOGIES
from api.domain.ontology.model import Origin
from tests.agent_map import QUESTIONS

CATALOG = Path(__file__).parents[3] / "docs" / "question-catalog.md"
QUESTION_HEADING = re.compile(r"^### ([A-Z]{2}-\d{2})\.", re.MULTILINE)
MAX_TOOLS_PER_QUESTION = 3
WITHOUT_TOOL = frozenset({"SR-02", "RE-01", "RE-02", "RE-03", "RE-06", "RE-07", "RE-09"})
RELATION_ONLY_TARGETS: frozenset[str] = frozenset()
ANSWERED_WITH_DATA = frozenset({Origin.CONFIRMED, Origin.INFERRED})


def catalog_codes() -> list[str]:
    return QUESTION_HEADING.findall(CATALOG.read_text(encoding="utf-8"))


def registered_tools() -> tuple[ToolDefinition, ...]:
    groups = get_type_hints(StudentTools).values()
    return tuple(tool for group in groups for tool in ToolRegistry.describe(group))


def mapped_tools() -> set[str]:
    return {tool for question in QUESTIONS for tool in question.tools}


def mapped_ontologies() -> set[str]:
    return {key for question in QUESTIONS for key in question.ontologies}


def test_every_catalog_question_is_mapped_once() -> None:
    codes = [question.code for question in QUESTIONS]
    assert len(catalog_codes()) == 60
    assert sorted(codes) == sorted(catalog_codes())


def test_every_mapped_tool_is_registered_and_every_tool_is_mapped() -> None:
    assert mapped_tools() == {tool.name for tool in registered_tools()}


def test_no_question_needs_more_than_three_tools() -> None:
    assert all(len(question.tools) <= MAX_TOOLS_PER_QUESTION for question in QUESTIONS)
    assert all(len(set(question.tools)) == len(question.tools) for question in QUESTIONS)


def test_only_the_questions_without_tool_have_no_tool() -> None:
    assert {question.code for question in QUESTIONS if not question.tools} == WITHOUT_TOOL


def test_every_question_exercises_known_ontologies() -> None:
    known = {ontology.key for ontology in ONTOLOGIES}
    assert all(question.ontologies for question in QUESTIONS)
    assert mapped_ontologies() <= known


def test_every_ontology_appears_in_some_question() -> None:
    assert {ontology.key for ontology in ONTOLOGIES} <= mapped_ontologies()


def test_ontologies_answered_with_data_are_declared_by_some_tool() -> None:
    declared = {ontology.key for tool in registered_tools() for ontology in tool.ontologies}
    required = {ontology.key for ontology in ONTOLOGIES if ontology.origin in ANSWERED_WITH_DATA}
    assert required - declared == RELATION_ONLY_TARGETS


def test_relation_only_targets_are_relation_targets() -> None:
    targets = {relation.target for ontology in ONTOLOGIES for relation in ontology.relations}
    assert targets >= RELATION_ONLY_TARGETS
