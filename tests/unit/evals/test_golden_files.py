from collections import Counter

from evals.golden.catalog import QuestionCatalog
from evals.golden.loader import GoldenLoader
from evals.golden.static_checks import StaticChecks
from evals.golden.tool_names import ToolNames
from tests.agent_map import QUESTIONS

FEE = "service_fee"


def test_the_golden_files_pass_every_check_that_needs_no_database() -> None:
    golden = GoldenLoader.load()
    problems = StaticChecks(QuestionCatalog.load(), ToolNames.registered()).run(golden)
    assert [problem.render() for problem in problems] == []


def test_expected_tools_come_from_the_question_map() -> None:
    expected = {item.id: item.tools.expected for item in GoldenLoader.load().questions}
    assert expected == {question.code: question.tools for question in QUESTIONS}


def test_the_protocol_actions_cover_every_service_and_mark_the_critical_items() -> None:
    golden = GoldenLoader.load()
    areas = Counter(item.area for item in golden.actions)
    services = {
        item.id: next(call.params["service"] for call in item.evidence if call.name == FEE)
        for item in golden.actions
        if item.area == "SV"
    }
    assert areas == {"TR": 12, "SV": 18, "ES": 2}
    assert len(set(services.values())) == 18
    anchors = {item.id for item in golden.actions if item.area == "TR"}
    assert {item.id for item in golden.items if item.critical} == {"PR-08", *anchors}


def test_a_service_with_a_fee_expects_no_proposal_and_a_free_one_expects_itself() -> None:
    for item in GoldenLoader.load().actions:
        if item.area != "SV":
            continue
        fee = next(call for call in item.evidence if call.name == FEE)
        expected = (fee.params["service"],) if fee.expect == "0" else ("none",)
        assert item.proposal.accepted == expected, item.id


def test_no_anchor_item_forbids_the_call_that_may_be_refused() -> None:
    for item in GoldenLoader.load().actions:
        assert "propose_protocol" not in item.tools.forbidden, item.id
