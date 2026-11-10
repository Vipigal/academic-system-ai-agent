from collections import Counter

from evals.dataset.loader import DatasetLoader
from evals.dataset.vocabulary import Suite
from tests.agent_map import QUESTIONS

BROWSER_STUDENT = "UniMontanhas:070114"
SCOPE_SIZES = {"ES": 6, "MA": 10, "DE": 10, "SD": 7, "IN": 8}
GUARDED_AREAS = frozenset({"ES", "MA", "IN"})


def test_expected_tools_come_from_the_question_map() -> None:
    expected = {item.id: item.tools.expected for item in DatasetLoader.load().suites[Suite.QUALITY]}
    assert expected == {question.code: question.tools for question in QUESTIONS}


def test_the_protocol_suite_covers_every_service_and_gates_the_lock_items() -> None:
    dataset = DatasetLoader.load()
    protocol = dataset.suites[Suite.PROTOCOL]
    assert Counter(item.area for item in protocol) == {"TR": 14, "SV": 18}
    anchors = {item.id for item in protocol if item.area == "TR"}
    assert {item.id for item in dataset.items if item.gated} == {"PR-08", *anchors}


def test_no_anchor_item_forbids_the_call_that_may_be_refused() -> None:
    for item in DatasetLoader.load().suites[Suite.PROTOCOL]:
        assert "propose_protocol" not in item.tools.forbidden, item.id


def test_the_bug_anchor_runs_the_grades_question_before_the_literal_phrase() -> None:
    items = {item.id: item for item in DatasetLoader.load().items}
    anchor = items["TR-13"]
    assert anchor.history == ("Como fiquei na AV1?",)
    assert anchor.gated
    assert anchor.question == items["TR-01"].question
    assert items["TR-01"].history == ()


def test_the_second_anchor_asks_the_literal_phrase_first_with_another_business_student() -> None:
    items = {item.id: item for item in DatasetLoader.load().items}
    second = items["TR-14"]
    assert second.question == "Solicite trancamento de matricula de Gestão Estratégica II"
    assert second.history == ()
    assert second.gated
    assert second.split == items["TR-13"].split
    assert second.student not in {BROWSER_STUDENT, items["TR-13"].student}


def test_the_scope_set_holds_every_category_and_the_two_first_out_of_scope_items() -> None:
    scope = DatasetLoader.load().suites[Suite.SCOPE]
    assert Counter(item.area for item in scope) == SCOPE_SIZES
    assert {"ES-01", "ES-02"} <= {item.id for item in scope}


def test_an_in_scope_lookalike_expects_a_tool_so_a_refusal_fails_the_trajectory() -> None:
    for item in DatasetLoader.load().suites[Suite.SCOPE]:
        if item.area == "DE":
            assert item.tools.expected, item.id


def test_every_refused_scope_item_has_a_deterministic_signal() -> None:
    for item in DatasetLoader.load().suites[Suite.SCOPE]:
        if item.area in GUARDED_AREAS:
            assert item.forbidden_text or item.tools.forbidden, item.id
