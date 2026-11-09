from collections import Counter

from evals.golden.loader import GoldenLoader
from evals.golden.static_checks import StaticChecks
from evals.golden.tool_names import ToolNames
from tests.agent_map import QUESTIONS

FEE = "service_fee"
BROWSER_STUDENT = "UniMontanhas:070114"
SCOPE_SIZES = {"ES": 6, "MA": 10, "DE": 10, "SD": 7, "IN": 8}
GUARDED_AREAS = frozenset({"ES", "MA", "IN"})


def test_the_golden_files_pass_every_check_that_needs_no_database() -> None:
    golden = GoldenLoader.load()
    problems = StaticChecks(ToolNames.registered()).run(golden)
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
    assert areas == {"TR": 14, "SV": 18}
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


def test_the_bug_anchor_runs_the_grades_question_before_the_literal_phrase() -> None:
    items = {item.id: item for item in GoldenLoader.load().items}
    anchor = items["TR-13"]
    assert anchor.history == ("Como fiquei na AV1?",)
    assert anchor.critical
    assert anchor.question == items["TR-01"].question
    assert items["TR-01"].history == ()


def test_the_second_anchor_asks_the_literal_phrase_first_with_another_business_student() -> None:
    items = {item.id: item for item in GoldenLoader.load().items}
    second = items["TR-14"]
    assert second.question == "Solicite trancamento de matricula de Gestão Estratégica II"
    assert second.history == ()
    assert second.critical
    assert second.split == items["TR-13"].split
    assert second.student not in {BROWSER_STUDENT, items["TR-13"].student}


def test_the_scope_set_holds_every_category_and_the_two_first_out_of_scope_items() -> None:
    scope = GoldenLoader.load().scope
    assert Counter(item.area for item in scope) == SCOPE_SIZES
    assert {"ES-01", "ES-02"} <= {item.id for item in scope}


def test_an_in_scope_lookalike_expects_a_tool_so_a_refusal_fails_the_trajectory() -> None:
    for item in GoldenLoader.load().scope:
        if item.area == "DE":
            assert item.tools.expected, item.id


def test_every_refused_scope_item_has_a_deterministic_signal() -> None:
    for item in GoldenLoader.load().scope:
        if item.area in GUARDED_AREAS:
            assert item.forbidden_text or item.tools.forbidden, item.id
