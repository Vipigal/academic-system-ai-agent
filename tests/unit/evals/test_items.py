import pytest
from pydantic import ValidationError

from evals.dataset.vocabulary import Kind, Split
from tests.unit.evals.items_support import attack, question


def test_a_valid_question_and_attack_load() -> None:
    assert question().area == "FI"
    assert attack().kind is Kind.ATTACK


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"id": "FI-1"}, id="code-format"),
        pytest.param({"student": "013161"}, id="student-without-brand"),
        pytest.param({"student": "UniAraucaria_EAD:13161"}, id="student-short-ra"),
        pytest.param({"kind": "maybe"}, id="unknown-kind"),
        pytest.param({"split": "train"}, id="unknown-split"),
        pytest.param({"rubric": []}, id="empty-rubric"),
        pytest.param({"reference": ""}, id="empty-reference"),
        pytest.param({"kind": "attack"}, id="attack-in-questions"),
        pytest.param({"color": "blue"}, id="extra-field"),
        pytest.param({"pass_k": 0}, id="pass-k-not-positive"),
    ],
)
def test_question_schema_refuses_invalid_items(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        question(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"kind": "refusal"}, id="not-an-attack"),
        pytest.param({"category": "phishing"}, id="unknown-category"),
    ],
)
def test_attack_schema_refuses_invalid_items(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        attack(**changes)


def test_the_old_holdout_split_reads_as_test() -> None:
    assert question(split="holdout").split is Split.TEST


def test_the_proposal_is_one_code_or_a_list_of_accepted_results() -> None:
    single = question(proposal="ACA-010")
    several = question(proposal=["none", "GEN-090"])
    assert single.proposal.services == {"ACA-010"}
    assert not single.proposal.allows_none
    assert several.proposal.services == {"GEN-090"}
    assert several.proposal.allows_none


def test_a_proposal_out_of_the_format_is_rejected() -> None:
    with pytest.raises(ValidationError):
        question(proposal="trancamento")
