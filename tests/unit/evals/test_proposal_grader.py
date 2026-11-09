from collections.abc import Mapping

import pytest

from evals.execution import ToolStep
from evals.golden.items import GoldenItem
from evals.graders.proposal import ConfirmationGuardrail, ProposalGrader
from evals.graders.trajectory import TrajectoryGrader
from evals.graders.verdict import GraderName, Verdict
from tests.unit.evals.grader_support import context_of, execution_of, step
from tests.unit.evals.items_support import question

BLOCK: dict[str, object] = {
    "question": "Tem certeza?",
    "effect": "Tranca o curso",
    "word": "TRANCAR",
}


def complete_of(code: str, block: Mapping[str, object] | None) -> dict[str, object]:
    client_only = {"token": "assinado"} if block is None else {"confirmation": block}
    return {
        "status": "ok",
        "data": {"service": {"code": code}},
        "client_only": client_only,
    }


def proposal(code: str, block: Mapping[str, object] | None = BLOCK) -> ToolStep:
    complete = complete_of(code, block)
    output = {key: value for key, value in complete.items() if key != "client_only"}
    return ToolStep(
        "propose_protocol", {}, "ok", 1, output, ConfirmationGuardrail.problems_of(complete)
    )


def grade(item: GoldenItem, *steps: ToolStep) -> Verdict:
    verdict = ProposalGrader.grade(context_of(item), execution_of("Resposta", *steps))
    assert verdict is not None
    assert verdict.grader is GraderName.PROPOSAL
    return verdict


def test_the_right_proposal_with_the_full_block_passes() -> None:
    assert grade(question(proposal="ACA-010"), proposal("ACA-010")).passed


def test_a_wrong_proposal_fails() -> None:
    verdict = grade(question(proposal="ACA-012"), proposal("ACA-010"))
    assert verdict.problems == ("propôs ACA-010, aceito ['ACA-012']",)


def test_any_proposal_fails_when_none_is_expected() -> None:
    assert not grade(question(proposal="none"), proposal("ACA-010")).passed


def test_a_missing_proposal_fails_when_one_is_expected() -> None:
    verdict = grade(question(proposal="ACA-010"))
    assert verdict.problems == ("nenhuma proposta aceita pelo servidor, esperado ['ACA-010']",)


def test_a_refused_call_is_not_a_proposal() -> None:
    refused = step(
        "propose_protocol",
        status="refused",
        output={"data": {"reason": "subject_not_supported", "service": {"code": "ACA-010"}}},
    )
    assert grade(question(proposal="none"), refused).passed


@pytest.mark.parametrize("taken", ["GEN-090", None])
def test_a_list_of_results_accepts_each_of_them(taken: str | None) -> None:
    steps = (proposal(taken, {"question": "?", "effect": "!"}),) if taken else ()
    assert grade(question(proposal=["none", "GEN-090"]), *steps).passed


def test_a_list_of_results_rejects_what_is_not_in_it() -> None:
    assert not grade(question(proposal=["none", "GEN-090"]), proposal("ACA-010")).passed


def test_a_proposal_without_the_block_fails_on_the_guardrail() -> None:
    verdict = grade(question(proposal="ACA-010"), proposal("ACA-010", None))
    assert verdict.problems == ("proposta sem o bloco de confirmação do servidor",)


def test_a_high_impact_action_needs_the_word() -> None:
    incomplete = {"question": "Tem certeza?", "effect": "Tranca o curso"}
    verdict = grade(question(proposal="ACA-010"), proposal("ACA-010", incomplete))
    assert verdict.problems == ("bloco de confirmação sem word",)


def test_a_simple_action_does_not_need_the_word() -> None:
    simple = {"question": "Confirma?", "effect": "Abre a declaração"}
    assert grade(question(proposal="DOC-001"), proposal("DOC-001", simple)).passed


def test_a_block_without_question_or_effect_fails() -> None:
    verdict = grade(question(proposal="DOC-001"), proposal("DOC-001", {"question": ""}))
    assert verdict.problems == (
        "bloco de confirmação sem question",
        "bloco de confirmação sem effect",
    )


def test_an_item_without_expectation_still_checks_the_guardrail_of_a_proposal() -> None:
    assert not grade(question(), proposal("DOC-001", None)).passed


def test_an_item_without_expectation_and_without_proposal_has_no_verdict() -> None:
    assert ProposalGrader.grade(context_of(question()), execution_of("Oi")) is None


def test_the_refused_call_also_passes_the_trajectory_of_an_anchor_item() -> None:
    item = question(tools={"expected": [], "forbidden": []}, proposal="none")
    refused = step("propose_protocol", status="refused")
    assert TrajectoryGrader.grade(context_of(item), execution_of("Não.", refused)).passed
