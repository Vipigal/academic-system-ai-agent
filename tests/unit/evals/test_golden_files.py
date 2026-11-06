from evals.golden.catalog import QuestionCatalog
from evals.golden.loader import GoldenLoader
from evals.golden.static_checks import StaticChecks
from evals.golden.tool_names import ToolNames
from tests.agent_map import QUESTIONS


def test_the_golden_files_pass_every_check_that_needs_no_database() -> None:
    golden = GoldenLoader.load()
    problems = StaticChecks(QuestionCatalog.load(), ToolNames.registered()).run(golden)
    assert [problem.render() for problem in problems] == []


def test_expected_tools_come_from_the_question_map() -> None:
    expected = {item.id: item.tools.expected for item in GoldenLoader.load().questions}
    assert expected == {question.code: question.tools for question in QUESTIONS}
